# AI-Driven Industrial Maintenance Agent

**Integrating IoT Telemetry with Retrieval-Augmented Generation (RAG) for Predictive Repair**

## 🎯 Project Overview

An autonomous Industrial Maintenance Assistant that bridges the gap between **Structured Data** (live sensor readings from machinery) and **Unstructured Data** (technical repair manuals). The system monitors industrial assets in real-time, detects anomalies based on physics constraints, and instantly retrieves exact step-by-step repair protocols from manufacturer documentation without human intervention.

## 🏗️ System Architecture

The project is built on a **Microservices Architecture** deployable via Docker Compose:

- **The Brain (Backend)**: Python/FastAPI using LangChain for logic
- **The Memory (Structured DB)**: MariaDB (SQL) to store machine status, sensor logs (RPM, Temperature, Torque), and audit history
- **The Knowledge (Vector DB)**: ChromaDB to store chunked, semantic embeddings of Technical Manuals
- **The Interface (Frontend)**: Streamlit dashboard for live monitoring and chat interaction

## ✨ Key Features

### 1. Live Digital Twin & Monitoring
- Reads from CSV log files mimicking real-time IoT streams
- Time-shifting: Historical data processed as "live" events for demos
- Live dashboard plotting Temperature, RPM, and Torque curves for multiple machines simultaneously

### 2. Intelligent Anomaly Detection
The Agent autonomously analyzes sensor values against defined thresholds:
- **Thermal Runaway**: Detected if Temp drops < 190°C while printing
- **Fan Failure**: Detected if RPM = 0 during operation
- **Motor Strain**: Detected if Torque > Normal Limit
- **Temperature Anomalies**: Outside normal operating range (300-315K)
- **Tool Wear Warnings**: Exceeds recommended limits

### 3. RAG-Based Diagnostics (The Core Innovation)
- **Strict Persona**: The AI acts as a "Senior Field Engineer" - never says "Read the manual"
- **Workflow**:
  1. **Analyze**: Confirm the error using SQL sensor data
  2. **Retrieve**: Search the Vector DB for specific error codes (e.g., "Extruder Fan Error")
  3. **Instruct**: Output verbatim step-by-step repair instructions, including tool sizes and safety warnings

### 4. Lifecycle Support
The Agent handles three distinct user intents:
- **Maintenance**: Reactive repair (Checks Sensors first)
- **Commissioning**: Setup/Calibration guides (Skips Sensors, checks Manual)
- **Safety**: Compliance and specs (Skips Sensors, checks Manual)

### 5. Real-Time Monitoring & Analytics
- **Live Dashboard**: Multi-machine sensor visualization
- **Anomaly Tracking**: Real-time detection and alerting
- **Historical Analysis**: Trend analysis across multiple machines

## 🛠️ Technical Stack

- **Language**: Python 3.9+
- **Containerization**: Docker & Docker Compose
- **AI/LLM**: LangChain, Groq (Llama3/Mixtral), HuggingFace Embeddings (bge-base-en-v1.5)
- **Databases**: MariaDB (SQL), ChromaDB (Vector)
- **Frontend**: Streamlit
- **Data Handling**: Pandas (CSV Replay), SQLModel (ORM)
- **PDF Processing**: PyMuPDF (for manual ingestion only)

## 📋 Prerequisites

- Docker and Docker Compose installed
- Python 3.9+ (for local development)
- Groq API Key (for LLM access)
- Sensor data CSV file (AI4I dataset or similar)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd industrial-agent
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Start Infrastructure

```bash
docker-compose up -d mariadb chromadb
```

Wait for services to be healthy (check with `docker-compose ps`).

### 4. Initialize Database

```bash
# Install Python dependencies (if not using Docker)
pip install -r requirements.txt

# Initialize database schema
mysql -h localhost -u user -pindustrial_secret_password industrial_db < scripts/init.sql
```

Or use Python:

```bash
python -c "from database.connection import engine; from database.models import Machine, SensorLog; from sqlmodel import SQLModel; SQLModel.metadata.create_all(engine)"
```

### 5. Prepare Sensor Data

Place your sensor data CSV file at `data/real_sensor_data.csv` (or `data/real_sensors.csv`).

The CSV should have columns: Air Temp, Process Temp, RPM, Torque, Tool Wear, Target, and failure type flags.

### 6. Ingest Technical Manual

Place your technical manual PDF at `data/printer_manual.pdf`, then:

```bash
python scripts/ingest_vectors.py
```

**Note**: If you don't have a manual, you can create a sample one or use any technical documentation PDF. The system will chunk and embed it for RAG retrieval.

### 7. Stream Sensor Data (Optional - for Demo)

To simulate live sensor streaming:

```bash
# Stream at real-time speed
python scripts/sensor_stream.py

# Stream at 10x speed (faster demo)
python scripts/sensor_stream.py 10

# Resume from specific row
python scripts/sensor_stream.py 1 500
```

### 8. Start FastAPI Backend

```bash
# Option 1: Using Docker
docker-compose up api

# Option 2: Local development
uvicorn web.api:app --reload --host 0.0.0.0 --port 8000
```

### 9. Launch Streamlit Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will be available at `http://localhost:8501`

## 🎬 Demo Flow (The "Golden" Test Case)

### Scenario: Machine 3 reports RPM: 0

1. **User Asks**: "How do I fix Machine 3?"

2. **System Response**:
   - **Diagnosis**: Identifies "Fan Failure (FF-001)" based on 0 RPM detection
   - **Retrieval**: Pulls relevant repair procedures from the Prusa Manual via RAG
   - **Action**: Lists steps: 
     - "1. Check for debris blocking the fan blades"
     - "2. Verify cable connection to fan motor"
     - "3. Test fan with multimeter..."
   - **Safety**: Warnings about hotend temperature

3. **Outcome**: User receives complete diagnostic and repair instructions directly in the chat interface

## 📁 Project Structure

```
industrial-agent/
├── data/                    # Data files (CSV, PDFs, database volumes)
├── database/                # Database models and connection
│   ├── models.py           # SQLModel definitions
│   └── connection.py       # Database connection setup
├── llm/                     # LLM agent and tools
│   ├── agent.py            # LangChain agent executor
│   ├── tools.py            # Agent tools (check status, lookup manual, scan)
│   └── anomaly_detector.py # Autonomous anomaly detection
├── scripts/                 # Utility scripts
│   ├── init.sql            # Database schema
│   ├── generate_data.py    # Data generation utilities
│   ├── ingest_vectors.py   # PDF ingestion to ChromaDB
│   └── sensor_stream.py    # CSV streaming simulator
├── utils/                   # Utility modules
├── web/                     # FastAPI backend
│   └── api.py              # REST API endpoints
├── dashboard.py             # Streamlit frontend
├── docker-compose.yml       # Docker orchestration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Configuration

### Ports
- **FastAPI**: 8000
- **ChromaDB**: 8001
- **MariaDB**: 3306
- **Streamlit**: 8501 (default)

### Database Credentials
- **User**: `user`
- **Password**: `industrial_secret_password`
- **Database**: `industrial_db`

**⚠️ Change these in production!**

## 🧪 Testing

### Test Database Connection
```bash
python check_connections.py
```

### Test Agent
```bash
python brain_test.py
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:8000/

# Get all machines status
curl http://localhost:8000/machines/status

# Get specific machine
curl http://localhost:8000/machines/3
```

## 📊 Usage Examples

### Chat Interface
- "Check machine 3"
- "How do I fix Machine 3?"
- "What's wrong with all machines?"
- "How do I calibrate the extruder?"
- "What is the maximum operating temperature?"

### Analytics Dashboard
- Select multiple machines for comparison
- View Temperature, RPM, and Torque trends
- Real-time anomaly detection and visualization

## 🐛 Troubleshooting

### ChromaDB Connection Issues
- Ensure ChromaDB is running: `docker-compose ps`
- Check port mapping (should be 8001, not 8000)
- Verify collection exists: Check `scripts/ingest_vectors.py` output

### Database Connection Errors
- Wait for MariaDB to fully initialize (check healthcheck)
- Verify credentials match in `.env` and `docker-compose.yml`
- Check network connectivity: `docker network ls`

### Agent Not Responding
- Verify Groq API key is set in `.env`
- Check agent logs for errors
- Ensure FastAPI is running and accessible


## 🔐 Security Notes

- **Never commit** `.env` files with API keys
- Change default database passwords in production
- Use environment variables for sensitive configuration
- Implement authentication for production deployments

## 📝 License

[Your License Here]

## 🤝 Contributing

[Contributing Guidelines]

## 📧 Contact

[Your Contact Information]

---

**Built with ❤️ for Industrial IoT and Predictive Maintenance**
