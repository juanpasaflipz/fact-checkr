import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
from google.api_core.exceptions import GoogleAPICallError
from app.core.config import settings

logger = logging.getLogger(__name__)

def enqueue_task(
    task_name: str,
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = None,
    schedule_time: Optional[datetime] = None
) -> str:
    """
    Enqueues a task to Google Cloud Tasks.
    
    Args:
        task_name: logic handler name (e.g. "process_whatsapp_message")
        payload: JSON serializable dict
        idempotency_key: Optional unique key for the task (used for de-duplication if supported or in payload)
        schedule_time: When to execute the task
        
    Returns:
        The created task name/ID.
    """
    
    # Check for local sync emulation
    if settings.CLOUD_TASKS_EMULATE_SYNC.lower() == "true":
        logger.info(f"[Local] Emulating task {task_name} execution synchronously.")
        # In a real app we might have a registry, but for now we'll just log
        logger.info(f"Payload: {payload}")
        return "local-task-id"

    project = settings.GCP_PROJECT_ID
    location = settings.GCP_LOCATION
    queue = settings.CLOUD_TASKS_QUEUE
    target_url = settings.TASKS_TARGET_BASE_URL
    service_account_email = settings.TASKS_OIDC_SERVICE_ACCOUNT_EMAIL
    task_secret = settings.TASK_SECRET

    if not all([project, location, queue, target_url]):
        logger.warning("Cloud Tasks config missing. Task not enqueued.")
        return ""

    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(project, location, queue)

    # Construct the full URL
    url = f"{target_url}/tasks/{task_name}"
    
    # Task definition
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": url,
            "headers": {"Content-Type": "application/json"},
        }
    }

    # Add payload
    if payload:
        if idempotency_key:
            # We can also add idempotency key to payload if needed by the worker
            payload["_idempotency_key"] = idempotency_key
        
        task["http_request"]["body"] = json.dumps(payload).encode()

    # Auth: OIDC or Secret Header
    if service_account_email:
        task["http_request"]["oidc_token"] = {
            "service_account_email": service_account_email,
            "audience": target_url,
        }
    elif task_secret:
        # Fallback to secret header if OIDC not used (e.g. Cloud Run expecting header check)
        task["http_request"]["headers"]["X-Task-Secret"] = task_secret
    else:
        logger.warning("No OIDC SA or TASK_SECRET configured. Task endpoint might reject request.")

    # Schedule time
    if schedule_time:
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(schedule_time)
        task["schedule_time"] = timestamp

    # Deduplication using task name if idempotency_key provided
    # Cloud Tasks supports named tasks for dedup. 
    # Caution: Named tasks can't be re-created for some time after deletion/completion.
    # A safer approach requested was DB table + allow duplicate delivery. 
    # We will skip naming the task resource itself to avoid "task name already exists" limits 
    # unless we are sure. The prompt suggests "store idempotency in DB; allow duplicate task delivery".
    # So we won't set `name` on the task object itself using idempotency_key.
    
    try:
        response = client.create_task(request={"parent": parent, "task": task})
        logger.info(f"Enqueued task {response.name}")
        return response.name
    except GoogleAPICallError as e:
        logger.error(f"Failed to enqueue task: {e}")
        raise
