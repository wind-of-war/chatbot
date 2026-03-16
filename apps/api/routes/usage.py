from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.database import get_db
from apps.api.models import User
from apps.api.schemas import UsageResponse
from apps.api.services.auth_service import get_current_user
from apps.api.services.usage_service import load_usage


router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=UsageResponse)
def usage(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return load_usage(current_user, db)
