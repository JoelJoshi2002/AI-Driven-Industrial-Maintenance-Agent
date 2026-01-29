import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from sqlmodel import Session, select, func
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from langchain_core.messages import HumanMessage, AIMessage
import requests
from datetime import datetime

# --- MODULAR IMPORTS ---
from database.connection import engine
from database.models import Machine, SensorLog
from llm.anomaly_detector import AnomalyDetector

try:
    from llm.agent import agent_executor
    AGENT_AVAILABLE = True
except Exception as e:
    st.error(f"⚠️ Agent could not be loaded: {e}")
    AGENT_AVAILABLE = False

# 1. Page Config
st.set_page_config(page_title="Industrial AI Agent", page_icon="🏭", layout="wide")
load_dotenv()

# --- FUNCTION: FETCH DATA ---
def get_live_status():
    try:
        with Session(engine) as session:
            subquery = (
                select(SensorLog.machine_id, func.max(SensorLog.timestamp).label("max_time"))
                .group_by(SensorLog.machine_id).subquery()
            )
            statement = (
                select(Machine.id, Machine.model_name, SensorLog.failure_type, 
                      SensorLog.air_temp_k, SensorLog.process_temp_k, SensorLog.rpm, 
                      SensorLog.torque_nm, SensorLog.tool_wear_min, SensorLog.timestamp)
                .join(SensorLog, Machine.id == SensorLog.machine_id)
                .join(subquery, (SensorLog.machine_id == subquery.c.machine_id) & (SensorLog.timestamp == subquery.c.max_time))
                .order_by(Machine.id)
            )
            results = session.exec(statement).all()
            if results:
                return pd.DataFrame(results, columns=['machine_id', 'model_name', 'failure_type', 
                                                      'air_temp_k', 'process_temp_k', 'rpm', 
                                                      'torque_nm', 'tool_wear_min', 'timestamp'])
            return pd.DataFrame()
    except Exception as e:
        st.sidebar.error(f"DB Error: {e}")
        return pd.DataFrame()

def get_sensor_history(machine_ids: list, limit: int = 500):
    """Get sensor history for multiple machines."""
    try:
        # Convert numpy types to Python ints (fixes SQLModel compatibility)
        machine_ids = [int(mid) for mid in machine_ids]
        
        with Session(engine) as session:
            statement = (
                select(SensorLog.machine_id, SensorLog.timestamp, 
                      SensorLog.process_temp_k, SensorLog.rpm, SensorLog.torque_nm)
                .where(SensorLog.machine_id.in_(machine_ids))
                .order_by(SensorLog.timestamp.desc())
                .limit(limit)
            )
            results = session.exec(statement).all()
            if results:
                return pd.DataFrame(results, columns=['machine_id', 'timestamp', 
                                                      'process_temp_k', 'rpm', 'torque_nm'])
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading history: {e}")
        return pd.DataFrame()

status_df = get_live_status()

# --- SIDEBAR: LIVE STATUS ---
st.sidebar.title("🏭 Plant Status")
if not status_df.empty:
    for _, row in status_df.iterrows():
        color = "green" if row['failure_type'] == "Normal" else "red"
        icon = "✅" if row['failure_type'] == "Normal" else "🔥"
        with st.sidebar.expander(f"{icon} Machine {row['machine_id']}", expanded=(color=="red")):
            st.markdown(f"**Model:** {row['model_name']}")
            st.markdown(f"**Status:** :{color}[{row['failure_type']}]")
            st.markdown(f"**Temp:** {row['air_temp_k']:.1f} K")

# --- MAIN PAGE TABS ---
tab1, tab2 = st.tabs(["💬 AI Assistant", "📈 Live Analytics"])

# === TAB 1: THE AGENT ===
with tab1:
    st.title("🤖 Maintenance Assistant")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ex: 'How do I fix Machine 3?'"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 🧠 Memory Logic: Only keep the last 6 messages
        chat_history = []
        for msg in st.session_state.messages[-6:]: 
            if msg["role"] == "user":
                chat_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                chat_history.append(AIMessage(content=msg["content"]))

        with st.chat_message("assistant"):
            if AGENT_AVAILABLE:
                message_placeholder = st.empty()
                with st.spinner("🧠 Agent is thinking..."):
                    try:
                        response = agent_executor.invoke({
                            "input": prompt,
                            "chat_history": chat_history
                        })
                        full_response = response["output"]
                        message_placeholder.markdown(full_response)
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                    except Exception as e:
                        message_placeholder.error(f"Agent Logic Error: {e}")

# === TAB 2: ANALYTICS ===
with tab2:
    st.title("📈 Live Sensor Analytics")
    
    if not status_df.empty:
        # Multi-machine selection
        # Convert numpy types to Python ints
        machine_ids = [int(mid) for mid in sorted(status_df['machine_id'].unique())]
        
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_machines = st.multiselect(
                "Select Machines to Monitor:",
                options=machine_ids,
                default=machine_ids[:3] if len(machine_ids) >= 3 else machine_ids
            )
        with col2:
            time_window = st.selectbox("Time Window:", ["Last 500 points", "Last 1000 points", "Last 2000 points"], index=0)
            limit_map = {"Last 500 points": 500, "Last 1000 points": 1000, "Last 2000 points": 2000}
            limit = limit_map[time_window]
        
        if selected_machines:
            try:
                # Convert to list of ints (handles both numpy and Python types)
                selected_machines_int = [int(mid) for mid in selected_machines]
                # Get sensor history for selected machines
                hist_df = get_sensor_history(selected_machines_int, limit=limit)
                
                if not hist_df.empty:
                    hist_df = hist_df.sort_values("timestamp")
                    
                    # Create multi-machine plots using Plotly
                    st.subheader("🌡️ Temperature Trends")
                    fig_temp = go.Figure()
                    for machine_id in selected_machines:
                        machine_data = hist_df[hist_df['machine_id'] == machine_id]
                        if not machine_data.empty:
                            fig_temp.add_trace(go.Scatter(
                                x=machine_data['timestamp'],
                                y=machine_data['process_temp_k'],
                                mode='lines',
                                name=f'Machine {machine_id}',
                                line=dict(width=2)
                            ))
                    fig_temp.update_layout(
                        xaxis_title="Time",
                        yaxis_title="Temperature (K)",
                        hovermode='x unified',
                        height=300
                    )
                    st.plotly_chart(fig_temp, width="stretch")
                    
                    st.subheader("⚙️ RPM Trends")
                    fig_rpm = go.Figure()
                    for machine_id in selected_machines:
                        machine_data = hist_df[hist_df['machine_id'] == machine_id]
                        if not machine_data.empty:
                            fig_rpm.add_trace(go.Scatter(
                                x=machine_data['timestamp'],
                                y=machine_data['rpm'],
                                mode='lines',
                                name=f'Machine {machine_id}',
                                line=dict(width=2)
                            ))
                    fig_rpm.update_layout(
                        xaxis_title="Time",
                        yaxis_title="RPM",
                        hovermode='x unified',
                        height=300
                    )
                    st.plotly_chart(fig_rpm, width="stretch")
                    
                    st.subheader("🔧 Torque Trends")
                    fig_torque = go.Figure()
                    for machine_id in selected_machines:
                        machine_data = hist_df[hist_df['machine_id'] == machine_id]
                        if not machine_data.empty:
                            fig_torque.add_trace(go.Scatter(
                                x=machine_data['timestamp'],
                                y=machine_data['torque_nm'],
                                mode='lines',
                                name=f'Machine {machine_id}',
                                line=dict(width=2)
                            ))
                    fig_torque.update_layout(
                        xaxis_title="Time",
                        yaxis_title="Torque (Nm)",
                        hovermode='x unified',
                        height=300
                    )
                    st.plotly_chart(fig_torque, width="stretch")
                    
                    # Combined view option
                    st.subheader("📊 Combined View")
                    show_combined = st.checkbox("Show Combined Multi-Metric View", value=False)
                    if show_combined:
                        fig_combined = make_subplots(
                            rows=3, cols=1,
                            subplot_titles=('Temperature (K)', 'RPM', 'Torque (Nm)'),
                            vertical_spacing=0.1
                        )
                        
                        for machine_id in selected_machines:
                            machine_data = hist_df[hist_df['machine_id'] == machine_id]
                            if not machine_data.empty:
                                fig_combined.add_trace(
                                    go.Scatter(x=machine_data['timestamp'], y=machine_data['process_temp_k'],
                                             name=f'M{machine_id} Temp', legendgroup=f'M{machine_id}'),
                                    row=1, col=1
                                )
                                fig_combined.add_trace(
                                    go.Scatter(x=machine_data['timestamp'], y=machine_data['rpm'],
                                             name=f'M{machine_id} RPM', legendgroup=f'M{machine_id}', showlegend=False),
                                    row=2, col=1
                                )
                                fig_combined.add_trace(
                                    go.Scatter(x=machine_data['timestamp'], y=machine_data['torque_nm'],
                                             name=f'M{machine_id} Torque', legendgroup=f'M{machine_id}', showlegend=False),
                                    row=3, col=1
                                )
                        
                        fig_combined.update_layout(height=800, title_text="Multi-Machine Sensor Dashboard")
                        st.plotly_chart(fig_combined, width="stretch")
                else:
                    st.info("No sensor data available for selected machines.")
            except Exception as e:
                st.error(f"Could not load history: {e}")
        else:
            st.info("Please select at least one machine to view analytics.")
    else:
        st.warning("No machine data available. Please ensure sensor data is being streamed.")