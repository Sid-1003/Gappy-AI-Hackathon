import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

logger = logging.getLogger("second_brain.database")
logging.basicConfig(level=logging.INFO)

Base = declarative_base()
engine = None
db_mode = "unknown"

def init_db_engine():
    global engine, db_mode
    
    # Try connecting to MySQL first
    try:
        logger.info(f"Attempting MySQL connection to {settings.MYSQL_HOST}:{settings.MYSQL_PORT}...")
        # Check server connection and auto-create DB if missing
        server_engine = create_engine(settings.mysql_server_url, connect_args={"connect_timeout": 3})
        with server_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{settings.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
            conn.commit()
        
        # Connect to actual database
        engine = create_engine(settings.mysql_url, pool_pre_ping=True, pool_recycle=3600)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        db_mode = "MySQL"
        logger.info("Successfully connected to MySQL database engine!")
        return engine
    except Exception as e:
        logger.warning(f"MySQL connection unavailable or failed ({e}). Falling back to portable SQLite database...")
        
    # Portable SQLite Fallback
    try:
        engine = create_engine(settings.sqlite_url, connect_args={"check_same_thread": False})
        db_mode = "SQLite (Portable Mode)"
        logger.info("Initialized local SQLite database engine.")
        return engine
    except Exception as e:
        logger.error(f"Failed to initialize database engine: {e}")
        raise e

engine = init_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
