from datetime import date, datetime, time, timedelta

from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from apps.api.models import UsageLog, User, UserSubscription
from apps.api.schemas import (
    UserPlanUpdateRequest,
    UserStatusUpdateRequest,
    UserSummary,
    UserUpdateRequest,
    UsageItem,
    UsageResponse,
)
from configs.settings import settings


def _admin_user_id_set() -> set[int]:
    out: set[int] = set()
    for item in settings.admin_user_ids.split(","):
        raw = item.strip()
        if not raw:
            continue
        try:
            out.add(int(raw))
        except ValueError:
            continue
    return out


def has_active_pro_subscription(db: Session, user_id: int) -> bool:
    now = datetime.utcnow()
    row = (
        db.query(UserSubscription)
        .filter(
            UserSubscription.user_id == user_id,
            UserSubscription.plan == "pro",
            UserSubscription.status == "active",
            UserSubscription.expires_at > now,
        )
        .order_by(desc(UserSubscription.expires_at))
        .first()
    )
    return row is not None


def get_active_subscription(db: Session, user_id: int) -> UserSubscription | None:
    now = datetime.utcnow()
    return (
        db.query(UserSubscription)
        .filter(
            UserSubscription.user_id == user_id,
            UserSubscription.status == "active",
            UserSubscription.expires_at > now,
        )
        .order_by(desc(UserSubscription.expires_at))
        .first()
    )


def activate_pro_subscription(
    db: Session,
    user: User,
    source: str = "telegram_stars",
    amount_usd: float = 1.99,
    duration_days: int = 30,
    telegram_payment_charge_id: str | None = None,
) -> UserSubscription:
    now = datetime.utcnow()
    active = get_active_subscription(db, user.id)
    starts_from = now
    if active and active.plan == "pro" and active.expires_at > now:
        starts_from = active.expires_at

    expires_at = starts_from + timedelta(days=duration_days)
    sub = UserSubscription(
        user_id=user.id,
        plan="pro",
        source=source,
        amount_usd=amount_usd,
        starts_at=now,
        expires_at=expires_at,
        status="active",
        telegram_payment_charge_id=telegram_payment_charge_id,
    )
    user.plan = "pro"
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def ensure_user_plan_status(db: Session, user: User) -> str:
    if user.role == "admin" or user.id in _admin_user_id_set():
        return "team"
    if user.plan == "pro" and not has_active_pro_subscription(db, user.id):
        user.plan = "free"
        db.commit()
    return user.plan


def rate_limit_guard(db: Session, user: User) -> None:
    if user.role == "admin" or user.id in _admin_user_id_set():
        return

    recent = datetime.utcnow() - timedelta(minutes=1)
    request_count = db.query(UsageLog).filter(UsageLog.user_id == user.id, UsageLog.timestamp >= recent).count()
    if request_count >= settings.default_rate_limit_per_minute:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")


def daily_quota_guard(db: Session, user: User) -> None:
    if user.role == "admin" or user.id in _admin_user_id_set():
        return

    plan_limits = {
        "free": settings.free_plan_daily_limit,
        "pro": settings.pro_plan_daily_limit,
        "team": settings.team_plan_daily_limit,
    }

    plan = ensure_user_plan_status(db, user)
    limit = plan_limits.get(plan)
    if not limit or limit <= 0:
        return

    start_day = datetime.combine(date.today(), time.min)
    count = db.query(UsageLog).filter(UsageLog.user_id == user.id, UsageLog.timestamp >= start_day).count()
    if count >= limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Daily quota reached")


def estimate_tokens(question: str, answer: str) -> int:
    return max(1, (len(question) + len(answer)) // 4)


def estimate_cost(tokens: int, per_1k: float = 0.002) -> float:
    return round((tokens / 1000.0) * per_1k, 6)


def append_usage(db: Session, user_id: int, query: str, tokens: int, cost: float) -> None:
    db.add(UsageLog(user_id=user_id, query=query, tokens=tokens, cost=cost))
    db.commit()


def load_usage(user: User, db: Session) -> UsageResponse:
    rows = db.query(UsageLog).filter(UsageLog.user_id == user.id).order_by(desc(UsageLog.timestamp)).limit(100).all()
    items = [UsageItem(query=r.query, tokens=r.tokens, cost=r.cost, timestamp=r.timestamp) for r in rows]
    return UsageResponse(
        total_queries=len(items),
        total_tokens=sum(i.tokens for i in items),
        total_cost=round(sum(i.cost for i in items), 6),
        items=items,
    )


def list_users(db: Session, limit: int = 100) -> list[UserSummary]:
    users = db.query(User).order_by(desc(User.created_at)).limit(limit).all()
    return [
        UserSummary(
            id=u.id,
            email=u.email,
            plan=u.plan,
            role=u.role,
            status=u.status,
            created_at=u.created_at,
        )
        for u in users
    ]


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def update_user(db: Session, user_id: int, payload: UserUpdateRequest) -> UserSummary:
    user = get_user_or_404(db, user_id)
    if payload.plan is not None:
        user.plan = payload.plan
    if payload.role is not None:
        user.role = payload.role
    if payload.status is not None:
        user.status = payload.status
    db.commit()
    db.refresh(user)
    return UserSummary(id=user.id, email=user.email, plan=user.plan, role=user.role, status=user.status, created_at=user.created_at)


def update_user_plan(db: Session, user_id: int, payload: UserPlanUpdateRequest) -> UserSummary:
    return update_user(db, user_id, UserUpdateRequest(plan=payload.plan))


def update_user_status(db: Session, user_id: int, payload: UserStatusUpdateRequest) -> UserSummary:
    return update_user(db, user_id, UserUpdateRequest(status=payload.status))
