from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from apps.api.middleware.auth import hash_password
from apps.api.models import TelegramLink, User
from apps.api.services.chat_service import ask_question_for_user
from apps.api.services.usage_service import (
    activate_pro_subscription,
    daily_quota_guard,
    ensure_user_plan_status,
    get_active_subscription,
    rate_limit_guard,
)
from configs.settings import settings

PRO_PRICE_USD = 1.99


def _telegram_admin_id_set() -> set[int]:
    out: set[int] = set()
    for item in settings.telegram_admin_user_ids.split(","):
        raw = item.strip()
        if not raw:
            continue
        try:
            out.add(int(raw))
        except ValueError:
            continue
    return out


def get_or_create_user_for_telegram(db: Session, telegram_user_id: int, telegram_chat_id: int) -> User:
    is_admin_telegram = telegram_user_id in _telegram_admin_id_set()

    link = db.query(TelegramLink).filter(TelegramLink.telegram_user_id == telegram_user_id).first()
    if link:
        user = db.query(User).filter(User.id == link.user_id).first()
        if user:
            if link.telegram_chat_id != telegram_chat_id:
                link.telegram_chat_id = telegram_chat_id
            if is_admin_telegram and user.role != "admin":
                user.role = "admin"
                user.plan = "team"
                db.commit()
            return user

    email = f"tg_{telegram_user_id}@telegram-user.example.com"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            password_hash=hash_password(f"telegram-{telegram_user_id}"),
            plan="team" if is_admin_telegram else "free",
            role="admin" if is_admin_telegram else "user",
            status="active",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not link:
        link = TelegramLink(user_id=user.id, telegram_user_id=telegram_user_id, telegram_chat_id=telegram_chat_id)
        db.add(link)
        db.commit()

    return user


def plan_text_for_user(db: Session, user: User) -> str:
    plan = ensure_user_plan_status(db, user)
    active = get_active_subscription(db, user.id)
    expiry_txt = ""
    if active and active.plan == "pro":
        expiry_txt = f"\n- Pro expiry (UTC): {active.expires_at.strftime('%Y-%m-%d %H:%M')}"

    return (
        "Plans:\n"
        f"- Free: {settings.free_plan_daily_limit} questions/day\n"
        f"- Pro: ${PRO_PRICE_USD}/month, up to {settings.pro_plan_daily_limit} questions/day\n"
        "- Team/Admin: internal policy\n\n"
        f"Current plan: {plan}{expiry_txt}\n"
        "Use /upgrade to buy Pro via Telegram Stars."
    )


def quota_reached_text() -> str:
    return (
        f"Ban da het luot Free ({settings.free_plan_daily_limit} cau/ngay).\n"
        f"Nang cap Pro ${PRO_PRICE_USD}/thang de tiep tuc.\n"
        "Gui /upgrade de thanh toan bang Telegram Stars."
    )


def activate_pro_for_telegram_user(
    db: Session,
    telegram_user_id: int,
    telegram_chat_id: int,
    charge_id: str | None = None,
) -> str:
    user = get_or_create_user_for_telegram(db, telegram_user_id, telegram_chat_id)
    sub = activate_pro_subscription(
        db=db,
        user=user,
        source="telegram_stars",
        amount_usd=PRO_PRICE_USD,
        duration_days=30,
        telegram_payment_charge_id=charge_id,
    )
    return (
        "Thanh toan thanh cong.\n"
        f"Pro da kich hoat den {sub.expires_at.strftime('%Y-%m-%d %H:%M UTC')}."
    )


def process_telegram_question(db: Session, telegram_user_id: int, telegram_chat_id: int, question: str) -> dict:
    user = get_or_create_user_for_telegram(db, telegram_user_id, telegram_chat_id)
    safe_question = question.encode("ascii", "ignore").decode()
    print(
        f"[TG] user_id={user.id} telegram_user_id={telegram_user_id} chat_id={telegram_chat_id} "
        f"question={safe_question!r}",
        flush=True,
    )

    try:
        rate_limit_guard(db, user)
        daily_quota_guard(db, user)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            return {
                "user_id": user.id,
                "answer": quota_reached_text(),
                "citations": [],
                "tokens_used": 0,
            }
        raise

    result = ask_question_for_user(db=db, user=user, question=question)
    safe_answer = result["answer"].encode("ascii", "ignore").decode()
    print(
        f"[TG] user_id={user.id} answer={safe_answer!r} citations={len(result['citations'])}",
        flush=True,
    )
    return {
        "user_id": user.id,
        "answer": result["answer"],
        "citations": result["citations"],
        "tokens_used": result["tokens_used"],
    }
