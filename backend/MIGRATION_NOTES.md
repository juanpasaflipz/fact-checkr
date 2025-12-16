# Celery to Cloud Tasks Migration Notes

## 1. Current Celery Usage

### Initialization
- **`backend/app/worker.py`**: Initializes `Celery` app, configures queues and schedule.

### Task Definitions
- **`backend/app/tasks/whatsapp.py`**: `process_message` (via `@celery_app.task`).
- **`backend/app/tasks/scraper.py`**: Uses `@shared_task`.
- **`backend/app/tasks/blog_generation.py`**: Uses `@shared_task`.
- **`backend/app/tasks/credit_topup.py`**: Uses `@shared_task`.
- **`backend/app/tasks/health_check.py`**: Uses `@shared_task`.
- **`backend/app/tasks/fact_check.py`**: (Commented out)
- **`backend/app/tasks/market_intelligence.py`**: (Commented out)
- **`backend/app/tasks/market_notifications.py`**: (Commented out)

### Task Invocation
- **`backend/app/routers/whatsapp.py`**: Calls `celery_app.send_task("app.tasks.whatsapp.process_message", ...)`

### Redis Usage
- **Celery Broker/Backend**: Configured in `worker.py`.
- **OAuth State**: `backend/app/routers/auth.py` uses Redis for storing OAuth state with a fallback to in-memory storage. Current implementation handles missing Redis gracefully.

## 2. Migration Plan

### Architecture
- **Infrastructure**: Google Cloud Tasks (managing queues/retries) + Cloud Run (hosting workers).
- **Triggers**: FastAPI endpoints (`/tasks/*`) acting as push targets.
- **Auth**: OIDC tokens (Cloud Run IAM) or `X-Task-Secret` fallback.
- **Idempotency**: New `task_runs` table in Postgres.

### Refactor Steps
1.  **Remove Celery**: Delete `worker.py`, remove `@celery_app.task` decorators. Move logic to standard service functions.
2.  **Remove Redis**: Remove from `requirements.txt` and `docker-compose.yml`. `auth.py` will fallback to in-memory (note: in-memory state has limitations in multi-instance Cloud Run, but is outside immediate scope of async refactor; consider cookie-based state or DB-based state for production robustness).
3.  **Cloud Tasks Client**: Implement `infra/cloud_tasks.py`.
4.  **Task Router**: Implement `routers/cloud_tasks.py` with endpoints corresponding to old tasks.
5.  **Database**: Add `task_runs` table for idempotency.
