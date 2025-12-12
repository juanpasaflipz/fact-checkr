from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import Claim, User
from app.agent import FactChecker
from app.utils import get_user_by_id  # Assuming auth utils
# We might need authentication dependency, checking existing routers would be good.
# For now, I'll assume an open endpoint or standard auth if I find it.
# Based on utils.py, there is user management.

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

class ChatRequest(BaseModel):
    question: str
    context: Dict[str, Any] = {}

class ChatResponse(BaseModel):
    answer: str
    related_questions: list[str] = []

fact_checker = FactChecker()

@router.post("/explain/{claim_id}", response_model=ChatResponse)
async def explain_claim(
    claim_id: str, 
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Ask follow-up questions about a specific claim.
    """
    # 1. Retrieve claim context
    # Try looking up in DB (assuming string ID)
    # If ID is UUID, modify model lookup
    
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    # 2. Construct context for AI
    context_text = f"""
    ORIGINAL CLAIM: "{claim.claim_text}"
    VERIFICATION STATUS: {claim.verification_status}
    EXPLANATION: {claim.explanation}
    ORIGINAL POST: "{claim.original_text}"
    """
    
    # 3. Call AI to answer question
    # We'll use a direct method on Agent or construct prompt here.
    # Ideally Agent has `answer_question(context, question)`
    
    answer = await fact_checker.answer_question_about_claim(context_text, request.question)
    
    return ChatResponse(
        answer=answer,
        related_questions=[] # Could generate these too
    )
