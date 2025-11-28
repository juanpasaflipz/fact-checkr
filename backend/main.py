import logging
import sys
import os
import traceback

# Configure logging FIRST before any imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True  # Override any existing configuration
)
logger = logging.getLogger(__name__)

logger.info("=" * 50)
logger.info("Initializing FactCheckr API...")
logger.info("=" * 50)

try:
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from dotenv import load_dotenv
    from sqlalchemy.exc import OperationalError
    logger.info("✅ Core imports successful")
except Exception as e:
    logger.error(f"❌ Core import failed: {e}")
    logger.error(traceback.format_exc())
    raise

# Load environment variables
load_dotenv()
logger.info("✅ Environment variables loaded")

# Initialize FastAPI app
try:
    app = FastAPI(title="FactCheckr MX API", version="1.0.0")
    logger.info("✅ FastAPI app created")
except Exception as e:
    logger.error(f"❌ Failed to create FastAPI app: {e}")
    logger.error(traceback.format_exc())
    raise

# --- CORS Middleware (CRITICAL: Add BEFORE routes) ---
# Default CORS origins: localhost for dev, Railway domain, and custom domain
default_origins = "http://localhost:3000,https://factcheck.mx,https://www.factcheck.mx,https://fact-checkr-production.up.railway.app"
cors_origins = os.getenv("CORS_ORIGINS", default_origins).split(",")
# Clean up any empty strings from splitting
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel preview deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"✅ CORS middleware configured with origins: {cors_origins}")

# --- Health Check (Priority) ---
@app.get("/health")
async def health_check():
    """Health check endpoint - always returns 200 for Railway health checks"""
    return {
        "status": "healthy",
        "message": "API is operational"
    }

logger.info("✅ Health check endpoint registered")

@app.on_event("startup")
async def startup_event():
    """Log when app starts"""
    logger.info("🚀 FactCheckr API starting up...")
    logger.info("✅ App initialized successfully")
    logger.info("✅ Health endpoint available at /health")
    logger.info("=" * 50)

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
    logger.info("✅ Router modules imported")
    
    app.include_router(auth.router, prefix="/api", tags=["auth"])
    app.include_router(subscriptions.router, prefix="/api", tags=["subscriptions"])
    app.include_router(usage.router, prefix="/api", tags=["usage"])
    app.include_router(whatsapp.router, prefix="/api", tags=["whatsapp"])
    app.include_router(telegraph.router, prefix="/api", tags=["telegraph"])
    logger.info("✅ All routers registered successfully")
except ImportError as e:
    logger.warning(f"⚠️ Failed to import routers: {e}")
    logger.warning(traceback.format_exc())
except Exception as e:
    logger.warning(f"⚠️ Failed to register routers: {e}")
    logger.warning(traceback.format_exc())

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

