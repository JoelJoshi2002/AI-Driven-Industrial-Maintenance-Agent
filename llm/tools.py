import os
import requests
import chromadb
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from .anomaly_detector import AnomalyDetector

API_URL = "http://127.0.0.1:8000"

# --- OPTIMIZATION: Load Embedding Model Once ---
# Using bge-base-en-v1.5 as specified in requirements
_embedding_model = None
def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = HuggingFaceEmbeddings(
            model_name="BAAI/bge-base-en-v1.5",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    return _embedding_model

# --- TOOL 1: SPECIFIC CHECK ---
# llm/tools.py

# llm/tools.py

@tool
def check_machine_status(machine_id: int):
    """Checks the status of a SPECIFIC machine by its ID and performs autonomous anomaly detection."""
    try:
        response = requests.get(f"{API_URL}/machines/{machine_id}")
        
        if response.status_code == 404:
            return f"Status: Machine {machine_id} does not exist. Stop."
        if response.status_code == 500:
            return f"Status: Server Error. Stop."

        if response.status_code == 200:
            data = response.json()
            
            # Perform autonomous anomaly detection
            analysis = AnomalyDetector.analyze_machine(data)
            
            # Build response with sensor readings and detected anomalies
            response_text = (
                f"Machine ID: {machine_id}\n"
                f"Model: {data.get('model_name')}\n"
                f"Status: {analysis['status']}\n"
                f"--- SENSOR READINGS ---\n"
                f"Temperature: {data.get('temperature')} K (Normal: 300-315 K)\n"
                f"RPM: {data.get('rpm')} (Normal: 1200-1800)\n"
                f"Torque: {data.get('torque')} Nm (Normal: 40-60 Nm)\n"
                f"Tool Wear: {data.get('tool_wear')} min (Limit: 200 min)\n"
            )
            
            # Add anomaly details if any detected
            if analysis['anomalies']:
                response_text += f"\n--- DETECTED ANOMALIES ({analysis['anomaly_count']}) ---\n"
                for anomaly in analysis['anomalies']:
                    response_text += (
                        f"\n[{anomaly['severity']}] {anomaly['type']} ({anomaly['code']})\n"
                        f"Description: {anomaly['description']}\n"
                        f"Action: {anomaly['recommended_action']}\n"
                    )
            else:
                response_text += "\n✓ No anomalies detected. All sensors within normal parameters.\n"
            
            return response_text
        return f"Error: API status {response.status_code}"
    except Exception as e:
        return f"Connection Error: {str(e)}"

# --- TOOL 2: MANUAL LOOKUP ---
@tool
def lookup_manual(query: str) -> str:
    """Searches technical manuals for repair procedures, calibration guides, and safety specifications.
    
    Use this tool to find repair steps for specific error codes or issues.
    Examples: "FF-001 fan failure", "MS-001 motor strain", "thermal runaway", "power failure"
    
    Args:
        query: A string describing the issue or error code to search for
    
    Returns:
        Technical manual excerpts with repair procedures
    """
    try:
        # Handle case where query might be passed incorrectly
        # Sometimes LLM tries to pass dict or other formats
        if isinstance(query, dict):
            # Extract query from dict if LLM passes it that way
            query = query.get('query', query.get('text', str(query)))
        elif not isinstance(query, str):
            # Convert to string if it's not already
            query = str(query)
        
        # Clean up the query string
        query = str(query).strip()
        
        # Remove any function call syntax that might have leaked in
        if query.startswith('<function=') or 'function=' in query:
            # Extract just the JSON part if present
            import re
            json_match = re.search(r'\{[^}]+\}', query)
            if json_match:
                import json
                try:
                    query_dict = json.loads(json_match.group())
                    query = query_dict.get('query', str(query_dict))
                except:
                    query = query.split('}')[-1].strip('"').strip("'")
        
        if not query or not query.strip():
            return "Error: Query must be a non-empty string. Provide the error code or issue description."
        
        query = str(query).strip()

        client = chromadb.HttpClient(host='localhost', port=8001)  # Updated port
        collection = client.get_collection(name="technical_manuals")
        
        model = get_embedding_model()
        query_vec = model.embed_query(query)
        
        # Retrieve top 3 results for better context
        results = collection.query(query_embeddings=[query_vec], n_results=3)
        
        if not results: return "No results found in technical manual."
        docs = results.get('documents')
        metadatas = results.get('metadatas', [])
        
        if not docs or not docs[0]: return "No manual entry found for this query."
        
        # Combine multiple results if available
        response = "Technical Manual Excerpts:\n\n"
        for i, doc in enumerate(docs[0][:3]):  # Limit to 3 results
            page_info = ""
            if metadatas and metadatas[0] and i < len(metadatas[0]):
                page = metadatas[0][i].get('page', 'Unknown')
                page_info = f" [Page {page}]"
            response += f"--- Excerpt {i+1}{page_info} ---\n{doc}\n\n"
            
        return response
    except Exception as e:
        return f"Manual Search Error: {str(e)}" 

# --- TOOL 3: SMART SCAN (ARMORED) ---
# return_direct=True is important: for "check all machines" we want to return the scan
# output directly, and *not* have the LLM attempt additional tool calls (like lookup_manual),
# which can be fragile and may fail tool-call generation.
@tool(return_direct=True)
def scan_for_failures(dummy: str = ""):
    """
    Scans the ENTIRE plant and performs autonomous anomaly detection on all machines.
    Use for 'How are all machines?' or 'Any errors?'.
    """
    try:
        response = requests.get(f"{API_URL}/machines/status")
        
        if response.status_code == 200:
            data = response.json()
            
            # --- CRITICAL FIX: Ensure data is a List ---
            if data is None:
                return "Error: API returned 'None' (null)."
            if not isinstance(data, list):
                return f"Error: API returned unexpected format: {type(data)}"
            # -------------------------------------------

            # Perform anomaly detection on all machines
            all_analyses = []
            for machine in data:
                analysis = AnomalyDetector.analyze_machine(machine)
                all_analyses.append(analysis)
            
            # Filter machines with anomalies
            machines_with_issues = [a for a in all_analyses if a['anomaly_count'] > 0]
            
            if not machines_with_issues:
                return "✓ All machines are functioning normally. No anomalies detected."
            
            # Build detailed report with ACTUAL sensor values for each machine
            report = f"⚠️ {len(machines_with_issues)} MACHINE(S) WITH ISSUES:\n\n"
            for analysis in machines_with_issues[:10]:  # Limit to 10 machines to avoid token overflow
                # Find the original machine data to get sensor values
                machine_data = next((m for m in data if m.get('machine_id') == analysis['machine_id']), None)
                
                report += f"--- Machine {analysis['machine_id']} ({analysis['model_name']}) ---\n"
                report += f"Status: {analysis['status']}\n"
                
                # Include ACTUAL sensor values
                if machine_data:
                    report += f"SENSOR READINGS:\n"
                    report += f"  Temperature: {machine_data.get('temperature', 'N/A')} K (Normal: 300-315 K)\n"
                    report += f"  RPM: {machine_data.get('rpm', 'N/A')} (Normal: 1200-1800)\n"
                    report += f"  Torque: {machine_data.get('torque', 'N/A')} Nm (Normal: 40-60 Nm)\n"
                    report += f"  Tool Wear: {machine_data.get('tool_wear', 'N/A')} min (Limit: 200 min)\n"
                
                # List anomalies with codes
                report += f"DETECTED ANOMALIES ({analysis['anomaly_count']}):\n"
                for anomaly in analysis['anomalies']:
                    report += f"  [{anomaly['severity']}] {anomaly['type']} ({anomaly['code']})\n"
                    report += f"    Description: {anomaly['description']}\n"
                report += "\n"
            
            if len(machines_with_issues) > 10:
                report += f"... and {len(machines_with_issues) - 10} more machines with issues.\n"
            
            return report
            
        return f"Error: Could not scan. API Status: {response.status_code}"
    except Exception as e:
        return f"Scan Error: {str(e)}"