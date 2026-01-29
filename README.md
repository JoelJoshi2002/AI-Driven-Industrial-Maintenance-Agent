# 🏭 AI-Driven Industrial Maintenance Agent

**Integrating IoT Telemetry with Retrieval-Augmented Generation (RAG) for Predictive Repair**

---

## 📌 Overview

This project implements an **autonomous Industrial Maintenance Assistant** that combines **real-time machine telemetry** with **unstructured technical documentation** to enable predictive diagnostics and guided repair.

The system continuously monitors industrial assets, detects failures using **physics-based engineering constraints**, and retrieves **exact, step-by-step repair procedures** from manufacturer manuals using **Retrieval-Augmented Generation (RAG)** — all without human intervention.

This project is designed as a realistic **Industrial IoT + AI system**, suitable for:

- 🧪 Research & experimentation  
- 🎓 Academic evaluation  
- 🧑‍🏫 Technical demonstrations  
- 🏗️ Industrial AI system design portfolios  

---

## 🏗️ System Architecture

The system follows a **microservices architecture**, fully containerized using Docker and orchestrated via **Docker Compose**.

### Core Components

#### 🧠 The Brain (API)
FastAPI backend exposing:
- Live machine status
- Historical sensor telemetry
- Anomaly detection results

#### ❤️ The Simulator (Heartbeat)
Python service that:
- Streams time-shifted CSV telemetry
- Simulates realistic factory behavior

#### 🗄️ The Memory (Structured Database)
- MariaDB (SQL)
- Stores real-time telemetry:
  - RPM
  - Temperature
  - Torque
  - Usage time

#### 📚 The Knowledge (Vector Database)
- ChromaDB
- Stores semantic embeddings of technical manuals for RAG-based retrieval

#### 🖥️ The Interface (Frontend)
- Streamlit dashboard
- Live analytics and interactive AI maintenance agent

---

## ✨ Key Features

### 🔁 1. Live Digital Twin & Monitoring
- Time-shifted CSV replay simulates live industrial telemetry
- Real-time plots for:
  - 🌡️ Temperature
  - ⚙️ RPM
  - 🔩 Torque
- Concurrent monitoring of 10+ machines

---

### 📐 2. Physics-Based Anomaly Detection

Failures are detected using deterministic engineering constraints, ensuring full explainability:

| Failure Type      | Condition                                   |
|-------------------|---------------------------------------------|
| 🔥 Thermal Failure | Temperature < 190 °C while printing         |
| 🌀 Fan Failure     | RPM = 0 while machine is active             |
| 💪 Motor Strain    | Torque > 60 Nm                              |
| ⏳ Tool Wear       | Usage time > 200 minutes                    |

✅ No black-box ML  
✅ Fully interpretable diagnostics  

---

### 🧠 3. RAG-Based Diagnostics

The AI agent behaves like a **Senior Field Engineer**:

- *“How do I…”* → Immediate manual lookup  
- *“Machine X is broken”* → Sensor analysis → Manual retrieval  

Responses prioritize:
- ⚠️ Safety warnings  
- 🔌 Electrical risks  
- 🔥 Thermal hazards  
- ⚙️ Mechanical constraints  

---

## 📁 Project Structure

```text
industrial-agent/
├── data/
│   ├── printer_manual.pdf
│   └── real_sensor_data.csv
├── database/
│   ├── models.py
│   └── connection.py
├── llm/
│   ├── agent.py
│   ├── tools.py
│   └── anomaly_detector.py
├── scripts/
│   ├── ingest_vectors.py
│   ├── sensor_stream.py
│   ├── reset_data.py
│   └── init.sql
├── web/
│   └── api.py
├── dashboard.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
## 🚀 Quick Start (Recommended)

### 1️⃣ Prerequisites
- Docker  
- Docker Compose  
- Groq API Key  

---

### 2️⃣ Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```
## 🚀 Launch the System

```bash
docker-compose up --build
```
## 🔗 Access Points

- **Dashboard:** http://localhost:8501  
- **API Docs:** http://localhost:8000/docs  

🟢 The simulator starts automatically and begins streaming data immediately.

---

## 💻 Local Development (Without Docker)

### 1️⃣ Database Setup

Ensure MariaDB/MySQL is running locally, then initialize tables:

```bash
python -c "from database.connection import engine; from sqlmodel import SQLModel; SQLModel.metadata.create_all(engine)"
```
### 2️⃣ Start Backend API

```bash
uvicorn web.api:app --reload --port 8000
```
### 3️⃣ Start Telemetry Simulator

```bash
python -m scripts.sensor_stream
```
### 4️⃣ Launch Dashboard
```bash
streamlit run dashboard.py
```

## 🛠️ Management Utilities
### 🔄 Reset the Demo
```bash
python -m scripts.reset_data
```

### Docker alternative:

```bash
docker-compose down -v
```

##  📥 Ingest New Manuals

### Replace:

```bassh
data/printer_manual.pdf
```

### Run:

```bash
python scripts/ingest_vectors.py
```
## 🎬 Demo Flow (The "Golden" Test Case)

Follow this sequence to demonstrate the full capabilities of the system:

1.  **Launch the System:** Start the application (using Docker or manual scripts).
2.  **Verify Telemetry:** Open the dashboard and confirm that the live graphs in the "Live Analytics" tab are updating.
3.  **Wait for an Anomaly:** Watch the sidebar status indicators. Wait until a **🔥** icon appears next to a machine (e.g., Machine 4).
4.  **Ask the Agent:** Switch to the Chat tab and ask:
    > "Machine 4 is failing. What is the diagnosis and how do I fix it?"

### 🤖 Agent Behavior
Once asked, the Agent performs the following autonomous actions:
* **Queries API:** It checks the live telemetry to validate the failure (e.g., confirms RPM is 0).
* **Identifies Failure:** It diagnoses the specific issue (e.g., "Fan Failure").
* **Retrieves Knowledge:** It searches the vector database to find the exact repair steps from the technical manual.
* **Synthesizes Response:** It returns a set of actionable repair instructions complete with safety warnings.

## 🔧 Troubleshooting

### ❌ ModuleNotFoundError

### Use module execution:

```bash
python -m scripts.sensor_stream
```

### ❌ Docker Connection Refused

Use service names as hostnames inside Docker:

```text
 mariadb, api
```

### ❌ ChromaDB Port Issues

- Chroma runs internally on port **8000**
- Exposed on host as port **8001**
- Ensure `CHROMA_PORT` is configured correctly
