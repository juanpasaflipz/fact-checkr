from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import DisconnectionError, OperationalError
import os
import time
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/factcheckr")

# Configure connection pooling for Neon
# Optimized for Neon's pooled connections (pooler endpoint)
# Configure connection pooling for Neon
# Optimized for Neon's pooled connections (pooler endpoint)
engine = create_engine(
    DATABASE_URL,
    pool_size=3,
    max_overflow=5,
    pool_timeout=60,
    pool_recycle=1800,        # Recycle connections after 30 minutes
    pool_pre_ping=True,       # Verify connection is alive before using
    echo=False,               # Set to True for SQL debugging
    connect_args={
        "connect_timeout": 20,
        "keepalives": 1,        # Enable TCP keepalives
        "keepalives_idle": 30,  # Start keepalives after 30s of inactivity
        "keepalives_interval": 10,  # Send keepalive every 10s
        "keepalives_count": 5,  # Max keepalive packets before considering connection dead
        # Note: Neon pooled connections don't support custom startup parameters
        # Timeouts are set via the event handler after connection
    }
)

# Add connection retry logic
@event.listens_for(engine, "connect")
def set_connection_timeout(dbapi_conn, connection_record):
    """Set connection-level timeouts"""
    with dbapi_conn.cursor() as cursor:
        cursor.execute("SET statement_timeout = 60000")  # 60 seconds
        cursor.execute("SET idle_in_transaction_session_timeout = 60000")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for FastAPI endpoints with retry logic"""
    from sqlalchemy import text
    max_retries = 3
    retry_delay = 1
    db = None
    
    for attempt in range(max_retries):
        try:
            db = SessionLocal()
            # Test the connection with a simple query
            db.execute(text("SELECT 1"))
            break  # Connection successful, exit retry loop
        except (OperationalError, DisconnectionError) as e:
            if db:
                try:
                    db.close()
                except:
                    pass
                db = None
            if attempt < max_retries - 1:
                logger.warning(f"Database connection attempt {attempt + 1} failed, retrying in {retry_delay}s: {e}")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Database connection failed after {max_retries} attempts: {e}")
                raise
        except Exception as e:
            if db:
                try:
                    db.close()
                except:
                    pass
            raise
    
    # Yield the database session
    try:
        yield db
    finally:
        if db:
            try:
                db.close()
            except:
                pass
