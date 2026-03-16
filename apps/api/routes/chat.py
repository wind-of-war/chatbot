from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.database import get_db
from apps.api.models import User
from apps.api.schemas import ChatRequest, ChatResponse, Citation
from apps.api.services.chat_service import ask_question_for_user
from apps.api.services.auth_service import get_current_user
from apps.api.services.usage_service import (
    daily_quota_guard,
    rate_limit_guard,
)


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    daily_quota_guard(db, current_user)
    rate_limit_guard(db, current_user)

    result = ask_question_for_user(db=db, user=current_user, question=payload.question)
    citations = [Citation(**c) for c in result.get("citations", [])]
    return ChatResponse(
        answer=result["answer"],
        tokens_used=result["tokens_used"],
        citations=citations,
        confidence=result.get("confidence"),
        cached=result.get("cached", False),
    )
