import logging
import sys
import os
import traceback
from typing import List, Optional
from datetime import timedelta, datetime
from app.core.config import settings

# Configure logging FIRST before any imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True  # Override any existing configuration
)
logger = logging.getLogger(__name__)

logger.info("✅ Environment variables loaded")

# Initialize Sentry (must be done before other imports)
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_dsn = settings.SENTRY_DSN
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            # Performance monitoring
            traces_sample_rate=0.1,  # Sample 10% of transactions
            # Release health tracking
            enable_tracing=True,
            # Environment
            environment=settings.ENVIRONMENT,
        )
        logger.info("✅ Sentry monitoring initialized")
    else:
        logger.info("⚠️ SENTRY_DSN not configured - monitoring disabled")
except ImportError:
    logger.warning("⚠️ Sentry SDK not available - monitoring disabled")

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

# Import app modules
from app.database.connection import get_db
from app.database.models import (
    Claim as DBClaim, 
    Source as DBSource
)
from app.core.rate_limit import setup_rate_limiting
from app.middleware.error_handler import register_error_handlers

# Define available routers and their optional dependencies
CORE_ROUTERS = ['auth', 'subscriptions', 'usage', 'whatsapp', 'telegraph', 'health']
OPTIONAL_ROUTERS = {
    'intelligence': {'available': False, 'dependencies': []},
    'markets': {'available': False, 'dependencies': []},
    'market_votes': {'available': False, 'dependencies': []},
    'market_intelligence': {'available': False, 'dependencies': []},
    'tokens': {'available': False, 'dependencies': []},
    'review': {'available': False, 'dependencies': []},
    'quota': {'available': False, 'dependencies': []},
    'trending': {'available': False, 'dependencies': []},
    'analytics': {'available': False, 'dependencies': []},
    'keywords': {'available': False, 'dependencies': []},
    'blog': {'available': False, 'dependencies': []},
    'chat': {'available': False, 'dependencies': []},
}

# Load core routers (always required)
core_router_modules = {}
for router_name in CORE_ROUTERS:
    try:
        module = __import__(f'app.routers.{router_name}', fromlist=[router_name])
        core_router_modules[router_name] = module
        logger.info(f"✅ Core router '{router_name}' loaded successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to load core router '{router_name}': {e}")
        raise  # Core routers are required

# Load optional routers (gracefully handle missing ones)
optional_router_modules = {}
for router_name, config in OPTIONAL_ROUTERS.items():
    try:
        module = __import__(f'app.routers.{router_name}', fromlist=[router_name])
        optional_router_modules[router_name] = module
        OPTIONAL_ROUTERS[router_name]['available'] = True
        logger.info(f"✅ Optional router '{router_name}' loaded successfully")
    except ImportError as e:
        logger.warning(f"⚠️ Optional router '{router_name}' not available: {e}")
        continue

ROUTERS_AVAILABLE = True

logger.info("=" * 50)
logger.info("Initializing FactCheckr API...")
logger.info("=" * 50)

# Initialize FastAPI app
try:
    app = FastAPI(title="FactCheckr MX API", version="1.0.0")
    logger.info("✅ FastAPI app created")
except Exception as e:
    logger.error(f"❌ Failed to create FastAPI app: {e}")
    logger.error(traceback.format_exc())
    raise

# --- CORS Middleware (CRITICAL: Add BEFORE routes) ---
# Default CORS origins: localhost for dev, Railway domain, Vercel, and custom domain
# Default CORS origins now loaded from settings
cors_origins = settings.CORS_ORIGINS
# Ensure it's a list (should be handled by Pydantic but being safe)
if isinstance(cors_origins, str):
    cors_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]

# FORCE CRITICAL ORIGINS: Ensure app.factcheck.mx is always allowed, even if CORS_ORIGINS is set
critical_origins = [
    "https://app.factcheck.mx",
    "https://www.app.factcheck.mx",
    "https://factcheck.mx",
    "https://www.factcheck.mx",
    "https://fact-check-mx-934bc.web.app",
    "https://fact-check-mx-934bc.firebaseapp.com"
]
for origin in critical_origins:
    if origin not in cors_origins:
        cors_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    # Tighter regex: strictly matches fact-checkr-*.vercel.app (previews)
    allow_origin_regex=r"https://fact-checkr-.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"✅ CORS middleware configured with origins: {cors_origins} + Vercel regex")

# --- Static Files ---
from fastapi.staticfiles import StaticFiles
static_dir = os.path.join(os.path.dirname(__file__), "app/static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
logger.info(f"✅ Static files mounted at /static from {static_dir}")

# --- Health Check (Priority) ---


@app.on_event("startup")
async def startup_event():
    """Log when app starts"""
    logger.info("🚀 FactCheckr API starting up...")
    
    # Validate Stripe configuration
    try:
        from app.config.stripe_config import log_stripe_config_status
        log_stripe_config_status()
    except Exception as e:
        logger.warning(f"⚠️  Stripe configuration validation failed: {e}")
    
    logger.info("✅ App initialized successfully")
    logger.info("✅ Health endpoint available at /health")
    logger.info("=" * 50)

# --- Rate Limiting ---
try:
    setup_rate_limiting(app)
except Exception as e:
    logger.error(f"Rate limiting setup failed: {e}")

# --- Exception Handlers ---
register_error_handlers(app)

# --- Router Registration ---
if ROUTERS_AVAILABLE:
    # Register core routers
    for router_name, module in core_router_modules.items():
        try:
            if router_name == 'intelligence':
                app.include_router(module.router)  # Intelligence router has its own prefix
            elif router_name == 'health':
                # Health endpoints were originally at root /health and /health/detailed
                app.include_router(module.router)
            else:
                app.include_router(module.router, prefix="/api", tags=[router_name])
            logger.info(f"✅ Core router '{router_name}' registered")
        except Exception as e:
            logger.error(f"❌ Failed to register core router '{router_name}': {e}")
            raise

    # Register optional routers
    for router_name, module in optional_router_modules.items():
        try:
            if router_name == 'intelligence':
                app.include_router(module.router)  # Intelligence router has its own prefix
            elif router_name == 'trending':
                app.include_router(module.router)  # Trending router already has /api/v1/trending prefix
            elif router_name == 'keywords':
                app.include_router(module.router, prefix="/api", tags=["keywords"])
            elif router_name in ['market_votes', 'market_intelligence', 'tokens']:
                app.include_router(module.router)  # These routers have their own /api prefix
            else:
                app.include_router(module.router, prefix="/api", tags=[router_name])
            logger.info(f"✅ Optional router '{router_name}' registered")
        except Exception as e:
            logger.warning(f"⚠️ Failed to register optional router '{router_name}': {e}")
            continue

    # Register share router
    try:
        from app.routers import share
        app.include_router(share.router, prefix="/api", tags=["share"])
        logger.info("✅ Share router registered")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register share router: {e}")

    # Register tasks router (CRITICAL for Cloud Run / Scheduler)
    try:
        from app.routers import tasks
        app.include_router(tasks.router, prefix="/api") # Router itself has /tasks prefix so this becomes /api/tasks
        logger.info("✅ Tasks router registered")
    except Exception as e:
        logger.error(f"❌ Failed to register tasks router: {e}")

    # Register Cloud Tasks router (HTTP targets)
    try:
        from app.routers import cloud_tasks
        app.include_router(cloud_tasks.router) # Router has /tasks prefix
        logger.info("✅ Cloud Tasks router registered")
    except Exception as e:
        logger.error(f"❌ Failed to register cloud_tasks router: {e}")
    
    # Register NEW Refactored Routers (Claims, Topics, etc.)
    try:
        from app.routers import claims, topics, sources, entities, stats
        
        # Include without /api prefix to maintain backward compatibility
        app.include_router(claims.router)
        app.include_router(topics.router)
        app.include_router(sources.router)
        app.include_router(entities.router)
        app.include_router(stats.router)
        
        logger.info("✅ Refactored routers (claims, topics, sources, entities, stats) registered")
    except Exception as e:
        logger.error(f"❌ Failed to register refactored routers: {e}")
        logger.error(traceback.format_exc())

@app.get("/")
def root():
    return {"message": "Fact Checkr API v1.1 (CORS Fixed)"}
