"""
LLM agent wiring for the Maintenance Assistant.

IMPORTANT: This module uses the **classic** LangChain agents API via `langchain_classic`.
This avoids the import issues you were seeing with `create_tool_calling_agent`
and `AgentExecutor` in `langchain.agents` for LangChain 0.3+.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Classic agents live in `langchain_classic`, not `langchain.agents`.
from langchain_classic.agents import AgentExecutor
from langchain_classic.agents.tool_calling_agent.base import create_tool_calling_agent

from .tools import check_machine_status, lookup_manual, scan_for_failures

load_dotenv()


SYSTEM_PROMPT = """You are a Senior Field Engineer for industrial 3D printers.
You NEVER say "read the manual" – you ARE the manual.

Your tools:
- `check_machine_status(machine_id:int)`: returns latest sensor readings + anomaly analysis for ONE machine.
- `scan_for_failures()`: returns a summary of anomalies across ALL machines.
- `lookup_manual(query:str)`: retrieves step-by-step procedures and safety warnings from the technical manual.

MAINTENANCE FLOW (reactive repair):
- If the user asks about a specific machine (e.g. "check machine 3", "how do I fix machine 3"):
  1) Call `check_machine_status(<id>)` FIRST to see ACTUAL sensor data and anomaly codes.
  2) From that tool output, extract the anomaly codes (e.g. FF-001 fan failure, MS-001 motor strain, TR-001 thermal runaway).
  3) Call `lookup_manual()` with a short query that includes those codes and a few words of context.
  4) Answer with:
     - A short diagnosis that cites the REAL sensor values (temperature, RPM, torque, tool wear).
     - Then a numbered list of concrete repair steps from the manual, including tool sizes and safety warnings.

- If the user asks for fleet status (e.g. "check all machines", "how are all machines"):
  1) Call `scan_for_failures()` and STOP.
  2) Do NOT call `lookup_manual()` for fleet scans.
  3) Ask the user which specific machine to fix if any are flagged.

COMMISSIONING / SAFETY FLOW (no live sensor check):
- If the user asks about setup, calibration, or specs (e.g. "how to calibrate extruder", "what is max temperature"):
  - Go straight to `lookup_manual()` with a clear query.

GENERAL STYLE:
- Be concise, specific, and practical.
- Always include safety notes when touching hotend, mains voltage, or moving axes.
- Do NOT ask the user to open or read the manual; give them the exact steps instead.
"""


def get_agent_executor() -> AgentExecutor:
    """Create a classic LangChain AgentExecutor wired to our tools."""
    llm = ChatGroq(
        model_name="llama-3.1-8b-instant",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    # Tool list used by the agent
    tools = [check_machine_status, lookup_manual, scan_for_failures]
    for i, t in enumerate(tools):
        if t is None:
            raise ValueError(
                f"CRITICAL ERROR: Tool at index {i} is None. Check llm/tools.py imports."
            )

    # Classic tool-calling agent prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    # Create a tool-calling agent (classic API)
    agent = create_tool_calling_agent(llm, tools, prompt)

    # Wrap in AgentExecutor so `.invoke({"input": ..., "chat_history": ...})` works
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
    )


# Global instance imported by the Streamlit dashboard
agent_executor = get_agent_executor()