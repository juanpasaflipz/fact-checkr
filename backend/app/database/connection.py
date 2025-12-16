from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import DisconnectionError, OperationalError
import os
import time
import logging

logger = logging.getLogger(__name__)

from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

# Lazy-loaded engine and session to prevent blocking at import time
_engine = None
_SessionLocalClass = None


def get_engine():
    """Lazily create and return the database engine"""
    global _engine
    if _engine is None:
        logger.info("Creating database engine...")
        # Connection pool settings - increased for production to handle concurrent requests
        # pool_size: number of connections to maintain persistently
        # max_overflow: additional connections that can be created on demand
        # Total max connections = pool_size + max_overflow
        pool_size = settings.DB_POOL_SIZE
        max_overflow = settings.DB_MAX_OVERFLOW
        
        _engine = create_engine(
            DATABASE_URL,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=30,              # Timeout waiting for connection from pool
            pool_recycle=1800,            # Recycle connections after 30 minutes
            pool_pre_ping=True,           # Verify connection is alive before using
            echo=False,                   # Set to True for SQL debugging
            connect_args={
                "connect_timeout": 10,    # Connection establishment timeout
                "keepalives": 1,          # Enable TCP keepalives
                "keepalives_idle": 30,    # Start keepalives after 30s of inactivity
                "keepalives_interval": 10,  # Send keepalive every 10s
                "keepalives_count": 5,    # Max keepalive packets before considering connection dead
            }
        )
        
        logger.info(f"Database engine created with pool_size={pool_size}, max_overflow={max_overflow} (max connections: {pool_size + max_overflow})")
        
        # Add connection event listener
        @event.listens_for(_engine, "connect")
        def set_connection_timeout(dbapi_conn, connection_record):
            """Set connection-level timeouts"""
            try:
                with dbapi_conn.cursor() as cursor:
                    cursor.execute("SET statement_timeout = 60000")  # 60 seconds
                    cursor.execute("SET idle_in_transaction_session_timeout = 60000")
            except Exception as e:
                logger.warning(f"Could not set connection timeouts: {e}")
        
        logger.info("Database engine created successfully")
    return _engine


# Backwards compatibility: engine as module-level (lazily evaluated via get_engine)
# This is safe because it's only evaluated when accessed
engine = None  # Placeholder - use get_engine() instead


def _get_session_local_class():
    """Lazily create and return the SessionLocal factory class"""
    global _SessionLocalClass
    if _SessionLocalClass is None:
        _SessionLocalClass = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocalClass


class _LazySessionLocal:
    """Wrapper to make SessionLocal() work lazily"""
    def __call__(self):
        return _get_session_local_class()()
    
    def __getattr__(self, name):
        return getattr(_get_session_local_class(), name)


# Use a class instance for SessionLocal that acts like the original
SessionLocal = _LazySessionLocal()


def get_db():
    """Dependency for FastAPI endpoints with retry logic and automatic commit/rollback"""
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
        
        # Auto-commit if there are pending changes and we're still in a transaction
        # This ensures changes are saved even if route doesn't explicitly commit
        if db and db.is_active:
            try:
                # Check if there are pending changes
                has_changes = (
                    len(db.new) > 0 or 
                    len(db.dirty) > 0 or 
                    len(db.deleted) > 0
                )
                
                if has_changes:
                    # Try to commit - this will work if we're still in a transaction
                    # If the route already committed, this might raise an error which we'll handle
                    try:
                        db.commit()
                        logger.debug("Transaction auto-committed successfully")
                    except Exception as commit_error:
                        # Check if error is because transaction was already committed/closed
                        error_str = str(commit_error).lower()
                        error_type = type(commit_error).__name__
                        
                        # Common SQLAlchemy errors when transaction is already closed
                        if any(phrase in error_str for phrase in [
                            "no transaction", 
                            "already closed",
                            "connection is closed",
                            "this session is closed"
                        ]) or "InvalidRequestError" in error_type:
                            # Transaction was already committed/closed by the route - that's fine
                            logger.debug("Transaction was already committed by route handler")
                        else:
                            # Real error - log it but don't fail silently
                            # Some errors might be recoverable, so we'll rollback and log
                            logger.warning(f"Error during auto-commit (may be expected if route already committed): {commit_error}")
                            try:
                                # Try to rollback if possible
                                if db.is_active:
                                    db.rollback()
                            except:
                                pass
                            # Don't re-raise - route might have already committed successfully
                            
            except Exception as e:
                # If checking/committing fails, log but don't fail the request
                # This could happen if session is in an unexpected state
                logger.warning(f"Error in auto-commit check (non-critical): {e}")
                
    except Exception as e:
        # Rollback on any exception if session is still active
        if db and db.is_active:
            try:
                db.rollback()
                logger.debug(f"Transaction rolled back due to exception: {type(e).__name__}")
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {rollback_error}")
        raise
    finally:
        if db:
            try:
                db.close()
            except:
                pass


def get_db_session():
    """
    Context manager for database sessions in Celery tasks and other non-FastAPI contexts.
    Ensures proper commit/rollback handling.
    
    Usage:
        with get_db_session() as db:
            # Use db here
            db.add(something)
            # Auto-commits on successful exit, rolls back on exception
    """
    db = SessionLocal()
    try:
        yield db
        # Auto-commit on successful exit if there are changes
        if db.is_active:
            try:
                has_changes = (
                    len(db.new) > 0 or 
                    len(db.dirty) > 0 or 
                    len(db.deleted) > 0
                )
                if has_changes:
                    db.commit()
                    logger.debug("Task session auto-committed successfully")
            except Exception as commit_error:
                error_str = str(commit_error).lower()
                if any(phrase in error_str for phrase in [
                    "no transaction", 
                    "already closed",
                    "connection is closed"
                ]):
                    logger.debug("Task session was already committed")
                else:
                    logger.warning(f"Error during task auto-commit: {commit_error}")
                    if db.is_active:
                        try:
                            db.rollback()
                        except:
                            pass
    except Exception as e:
        # Rollback on exception
        if db.is_active:
            try:
                db.rollback()
                logger.debug(f"Task session rolled back due to exception: {type(e).__name__}")
            except Exception as rollback_error:
                logger.error(f"Error during task rollback: {rollback_error}")
        raise
    finally:
        if db:
            try:
                db.close()
            except:
                pass
