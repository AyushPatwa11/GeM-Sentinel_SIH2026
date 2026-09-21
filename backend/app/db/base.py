import os
import importlib.util
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///gem_sentinel_demo.db",
)

# Prefer the Python 3.14-compatible Psycopg 3 driver when a legacy URL does
# not specify a driver explicitly.
if importlib.util.find_spec("psycopg") is not None:
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql+psycopg2://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)

connect_args = {}
if DATABASE_URL.startswith("postgresql"):
    connect_args["connect_timeout"] = int(os.getenv("DB_CONNECT_TIMEOUT", "5"))
elif DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
