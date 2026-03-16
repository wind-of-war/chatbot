from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.database import get_db
from apps.api.schemas import UserPlanUpdateRequest, UserStatusUpdateRequest, UserSummary, UserUpdateRequest
from apps.api.services.auth_service import require_admin
from apps.api.services.usage_service import (
    get_user_or_404,
    list_users,
    update_user,
    update_user_plan,
    update_user_status,
)


router = APIRouter(prefix="/admin/users", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("", response_model=list[UserSummary])
def admin_list_users(db: Session = Depends(get_db), limit: int = 100):
    return list_users(db, limit=limit)


@router.get("/{user_id}", response_model=UserSummary)
def admin_get_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user_or_404(db, user_id)
    return UserSummary(id=user.id, email=user.email, plan=user.plan, role=user.role, status=user.status, created_at=user.created_at)


@router.patch("/{user_id}", response_model=UserSummary)
def admin_update_user(user_id: int, payload: UserUpdateRequest, db: Session = Depends(get_db)):
    return update_user(db, user_id, payload)


@router.patch("/{user_id}/plan", response_model=UserSummary)
def admin_update_user_plan(user_id: int, payload: UserPlanUpdateRequest, db: Session = Depends(get_db)):
    return update_user_plan(db, user_id, payload)


@router.patch("/{user_id}/status", response_model=UserSummary)
def admin_update_user_status(user_id: int, payload: UserStatusUpdateRequest, db: Session = Depends(get_db)):
    return update_user_status(db, user_id, payload)
