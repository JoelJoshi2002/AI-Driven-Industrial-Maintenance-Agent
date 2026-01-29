# 🚀 Quick Start Guide

## Prerequisites

Before starting, ensure you have:
- **Docker** and **Docker Compose** installed
- **Python 3.9+** installed
- **Groq API Key** (get one at https://console.groq.com/)

## Step-by-Step Setup

### Step 1: Environment Setup

1. **Create/Update `.env` file** in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### Step 2: Start Infrastructure Services

Start MariaDB and ChromaDB using Docker Compose:

```bash
docker-compose up -d mariadb chromadb
```

Wait for services to be healthy (about 30-60 seconds). Check status:

```bash
docker-compose ps
```

You should see both services as "healthy" or "running".

### Step 3: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Initialize Database

**Option A: Using SQL script (Recommended)**
```bash
mysql -h localhost -u user -pindustrial_secret_password industrial_db < scripts/init.sql
```

**Option B: Using Python**
```bash
python -c "from database.connection import engine; from database.models import Machine, SensorLog; from sqlmodel import SQLModel; SQLModel.metadata.create_all(engine)"
```

**Option C: Using Python script**
```bash
python scripts/generate_data.py
```
(This will also seed some initial data)

### Step 5: Prepare Sensor Data

Place your sensor data CSV file at:
- `data/real_sensor_data.csv` OR
- `data/real_sensors.csv`

The CSV should have columns: Air Temp, Process Temp, RPM, Torque, Tool Wear, Target, and failure type flags.

**Note**: If you don't have sensor data, you can use the `generate_data.py` script or download the AI4I dataset.

### Step 6: Ingest Technical Manual

Place your technical manual PDF at `data/printer_manual.pdf`, then:

```bash
python scripts/ingest_vectors.py
```

**If you don't have a manual:**
- You can create a sample one using `scripts/create_sample_manual.py` (if available)
- Or use any technical documentation PDF
- The system will chunk and embed it for RAG retrieval

### Step 7: (Optional) Stream Sensor Data

To simulate live sensor streaming for demo purposes:

```bash
# Stream at real-time speed (slow, for production-like demo)
python scripts/sensor_stream.py

# Stream at 10x speed (faster demo)
python scripts/sensor_stream.py 10

# Stream at 1x speed starting from row 500
python scripts/sensor_stream.py 1 500
```

**Note**: This step is optional. You can also use pre-loaded data or run it in the background.

### Step 8: Start FastAPI Backend

**Option A: Using Docker**
```bash
docker-compose up api
```

**Option B: Local Development (Recommended for debugging)**
```bash
uvicorn web.api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

Test it:
```bash
curl http://localhost:8000/
# Should return: {"status":"online"}
```

### Step 9: Launch Streamlit Dashboard

In a **new terminal** (keep FastAPI running):

```bash
# Make sure you're in the project directory
cd industrial-agent

# Activate virtual environment if not already active
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Run Streamlit
streamlit run dashboard.py
```

The dashboard will automatically open in your browser at `http://localhost:8501`

## 🎯 Running the Complete System

### All Services Running

You should have these running simultaneously:

1. **MariaDB** (Docker) - Port 3306
2. **ChromaDB** (Docker) - Port 8001
3. **FastAPI** (Terminal 1) - Port 8000
4. **Streamlit Dashboard** (Terminal 2) - Port 8501
5. **Sensor Stream** (Terminal 3, Optional) - Background process

### Quick Check Commands

```bash
# Check Docker services
docker-compose ps

# Test API
curl http://localhost:8000/machines/status

# Check database connection
python check_connections.py

# Test agent
python brain_test.py
```

## 🎬 Testing the System

### Test Chat Interface

1. Open the Streamlit dashboard at `http://localhost:8501`
2. Go to the "💬 AI Assistant" tab
3. Try these queries:
   - "Check machine 3"
   - "How do I fix Machine 3?"
   - "What's wrong with all machines?"
   - "How do I calibrate the extruder?"
   - "What is the maximum operating temperature?"

### Test Analytics Dashboard

1. Go to the "📈 Live Analytics" tab
2. Select multiple machines from the dropdown
3. View Temperature, RPM, and Torque trends
4. Toggle "Show Combined Multi-Metric View" for comprehensive visualization

## 🐛 Troubleshooting

### Port Conflicts

If ports are already in use:

```bash
# Check what's using the ports
# Windows:
netstat -ano | findstr :8000
netstat -ano | findstr :8501

# Linux/Mac:
lsof -i :8000
lsof -i :8501
```

### Database Connection Issues

```bash
# Wait for MariaDB to fully initialize
docker-compose logs mariadb

# Test connection
python check_connections.py

# Reset database (WARNING: Deletes all data)
docker-compose down -v
docker-compose up -d mariadb chromadb
# Then re-run Step 4
```

### ChromaDB Connection Issues

```bash
# Check ChromaDB is running
docker-compose ps chromadb

# Check ChromaDB logs
docker-compose logs chromadb

# Verify port mapping (should be 8001)
docker-compose ps
```

### Agent Not Responding

1. Check Groq API key in `.env` file
2. Verify FastAPI is running: `curl http://localhost:8000/`
3. Check agent logs in Streamlit terminal
4. Test agent directly: `python brain_test.py`

### Missing Dependencies

```bash
# Reinstall all dependencies
pip install -r requirements.txt --upgrade

# If specific package fails, install individually
pip install langchain-groq
pip install chromadb
pip install sqlmodel
```

## 📝 Common Workflows

### Fresh Start (Clean Setup)

```bash
# 1. Stop all services
docker-compose down -v

# 2. Remove data volumes (optional, deletes all data)
rm -rf data/mariadb data/chroma

# 3. Start fresh
docker-compose up -d mariadb chromadb
# Wait 60 seconds

# 4. Initialize database
mysql -h localhost -u user -pindustrial_secret_password industrial_db < scripts/init.sql

# 5. Ingest manual
python scripts/ingest_vectors.py

# 6. Start services
uvicorn web.api:app --reload &
streamlit run dashboard.py
```

### Development Mode

```bash
# Terminal 1: FastAPI with auto-reload
uvicorn web.api:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Streamlit
streamlit run dashboard.py

# Terminal 3: Sensor stream (optional)
python scripts/sensor_stream.py 10
```

## 🎉 Success Indicators

You'll know everything is working when:

✅ Docker services show "healthy" status  
✅ API returns `{"status":"online"}` at `http://localhost:8000/`  
✅ Dashboard loads at `http://localhost:8501`  
✅ Chat interface responds to queries  
✅ Analytics show sensor data (if streaming is active)  
✅ Agent provides repair instructions (if manual is ingested)

---

**Need Help?** Check the main [README.md](README.md) for detailed documentation.
