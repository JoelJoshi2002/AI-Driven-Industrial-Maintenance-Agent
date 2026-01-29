import os
from sqlmodel import Session, create_engine

def _build_database_url() -> str:
    """
    Build a DB URL that works in both local dev and Docker.

    Priority:
    1) DATABASE_URL env var (e.g. docker-compose sets this for the api container)
    2) DB_* env vars (host/port/user/password/name)
    3) safe local default
    """
    direct = os.getenv("DATABASE_URL")
    if direct:
        return direct

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER", "user")
    password = os.getenv("DB_PASSWORD", "industrial_secret_password")
    name = os.getenv("DB_NAME", "industrial_db")

    return f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{name}"


DATABASE_URL = _build_database_url()
engine = create_engine(DATABASE_URL, echo=False)

def get_session():
    with Session(engine) as session:
        yield session