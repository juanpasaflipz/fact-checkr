from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class BaseTaskPayload(BaseModel):
    schema_version: int = 1

class ProcessWhatsAppMessageTask(BaseTaskPayload):
    task_type: Literal["process_whatsapp_message"] = "process_whatsapp_message"
    whatsapp_message_id: str
    from_number: str
    message_text: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class IngestSourcesTask(BaseTaskPayload):
    task_type: Literal["ingest_sources"] = "ingest_sources"
    platforms: List[str] = ["twitter", "google_news"]
    since_minutes: int = 30

class VerifySourceTask(BaseTaskPayload):
    task_type: Literal["verify_source"] = "verify_source"
    source_id: int
    force: bool = False

class DetectTrendingTask(BaseTaskPayload):
    task_type: Literal["detect_trending"] = "detect_trending"
    limit: int = 20

class GenerateBlogTask(BaseTaskPayload):
    task_type: Literal["generate_blog"] = "generate_blog"
    edition: Literal["morning", "afternoon", "evening", "breaking"]
    force: bool = False

class TaskResponse(BaseModel):
    status: str
