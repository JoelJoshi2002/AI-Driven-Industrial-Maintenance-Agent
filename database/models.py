# database/models.py
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

# 1. Update the Machine Table
class Machine(SQLModel, table=True):
    __tablename__ = "machines"
    # Add this line 👇
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    model_name: str
    location: Optional[str] = None
    install_date: datetime = Field(default_factory=datetime.now)

# 2. Update the Sensor Logs Table
class SensorLog(SQLModel, table=True):
    __tablename__ = "sensor_logs"
    # Add this line 👇
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    machine_id: int = Field(foreign_key="machines.id")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    air_temp_k: float
    process_temp_k: float
    rpm: float
    torque_nm: float
    tool_wear_min: float
    target: int = 0
    failure_type: str = "Normal"

# (MachineStatus doesn't need this because it has table=False by default)
class MachineStatus(SQLModel):
    machine_id: int
    model_name: str
    status: str
    temperature: float
    timestamp: datetime