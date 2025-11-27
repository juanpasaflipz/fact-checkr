import logging
import sys
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="FactCheckr MX API", version="1.0.0")

# --- Health Check (Priority) ---
@app.get("/health")
async def health_check():
    """Health check endpoint - always returns 200 for Railway health checks"""
    return {
        "status": "healthy",
        "message": "API is operational"
    }

@app.on_event("startup")
async def startup_event():
    """Log when app starts"""
    logger.info("🚀 FactCheckr API starting up...")
    logger.info(f"✅ App initialized successfully")
    logger.info(f"Health endpoint available at /health")

# --- Rate Limiting ---
try:
    from app.rate_limit import setup_rate_limiting
    setup_rate_limiting(app)
except ImportError:
    logger.warning("Rate limiting module not found, skipping setup")
except Exception as e:
    logger.error(f"Rate limiting setup failed: {e}")

# --- Routers ---
try:
    from app.routers import auth, subscriptions, usage, whatsapp, telegraph
    
    app.include_router(auth.router)
    app.include_router(subscriptions.router)
    app.include_router(usage.router)
    app.include_router(whatsapp.router)
    app.include_router(telegraph.router)
    logger.info("✅ Routers registered successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import routers: {e}")
except Exception as e:
    logger.error(f"❌ Failed to register routers: {e}")

# --- CORS Middleware ---
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://factcheckr.mx").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Exception Handlers ---
@app.exception_handler(OperationalError)
async def database_error_handler(request: Request, exc: OperationalError):
    """Handle database connection errors gracefully"""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=503,
        content={"detail": "Service temporarily unavailable (Database Error)"},
    )

@app.get("/")
async def root():
    return {"message": "Fact Checkr API is running"}

