from fastapi import FastAPI, HTTPException, Depends
from typing import List
from pydantic import BaseModel
from datetime import datetime
from sqlmodel import Session, select, func

# Import connection logic
# These imports work because you run the app from the root folder
from database.connection import get_session
from database.models import Machine, SensorLog

# --- Explicit Response Schema ---
class MachineDetail(BaseModel):
    machine_id: int
    model_name: str
    status: str
    temperature: float
    rpm: int            
    torque: float       
    tool_wear: float    
    timestamp: datetime

app = FastAPI(title="Industrial IoT API")

@app.get("/")
def health_check():
    return {"status": "online"}

@app.get("/machines/status", response_model=List[MachineDetail])
def get_all_machines_status(session: Session = Depends(get_session)):
    try:
        # 1. Get latest log for each machine
        subquery = (
            select(SensorLog.machine_id, func.max(SensorLog.timestamp).label("max_time"))
            .group_by(SensorLog.machine_id).subquery()
        )
        statement = (
            select(Machine, SensorLog)
            .join(SensorLog, Machine.id == SensorLog.machine_id)
            .join(subquery, (SensorLog.machine_id == subquery.c.machine_id) & (SensorLog.timestamp == subquery.c.max_time))
            .order_by(Machine.id)
        )
        results = session.exec(statement).all()

        # 2. Return ALL sensor data so Agent can analyze it
        return [
            MachineDetail(
                machine_id=m.id,
                model_name=m.model_name,
                status=l.failure_type,
                temperature=l.process_temp_k,
                rpm=l.rpm,              
                torque=l.torque_nm,     
                tool_wear=l.tool_wear_min, 
                timestamp=l.timestamp
            ) for m, l in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/machines/{machine_id}", response_model=MachineDetail)
def get_machine_status(machine_id: int, session: Session = Depends(get_session)):
    try:
        machine = session.get(Machine, machine_id)
        if not machine:
            raise HTTPException(status_code=404, detail="Machine not found")

        # Get latest log
        statement = select(SensorLog).where(SensorLog.machine_id == machine_id).order_by(SensorLog.timestamp.desc()).limit(1)
        log = session.exec(statement).first()
        
        if not log:
            # Return empty/default if no logs exist yet
            return MachineDetail(
                machine_id=machine.id, 
                model_name=machine.model_name,
                status="Unknown", temperature=0, rpm=0, torque=0, tool_wear=0,
                timestamp=datetime.now()
            )

        return MachineDetail(
            machine_id=machine.id,
            model_name=machine.model_name,
            status=log.failure_type,
            temperature=log.process_temp_k,
            rpm=log.rpm,
            torque=log.torque_nm,
            tool_wear=log.tool_wear_min,
            timestamp=log.timestamp
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))