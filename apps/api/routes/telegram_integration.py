from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session
import httpx

from apps.api.database import get_db
from apps.api.services.auth_service import require_admin
from apps.api.services.telegram_service import (
    PRO_PRICE_USD,
    activate_pro_for_telegram_user,
    get_or_create_user_for_telegram,
    plan_text_for_user,
    process_telegram_question,
)
from configs.settings import settings


router = APIRouter(prefix="/integrations/telegram", tags=["telegram"])
admin_router = APIRouter(prefix="/integrations/telegram", tags=["telegram-admin"], dependencies=[Depends(require_admin)])
PRO_PAYLOAD = "gxp_pro_30d"


def _ensure_telegram_enabled() -> None:
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=503, detail="TELEGRAM_BOT_TOKEN is not configured")


def _validate_webhook_secret(secret_header: str | None) -> None:
    expected = settings.telegram_webhook_secret
    if not expected:
        raise HTTPException(status_code=503, detail="TELEGRAM_WEBHOOK_SECRET is not configured")
    if secret_header != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram webhook secret")


def _format_reply(answer: str, citations: list[dict]) -> str:
    def _fmt_loc(item: dict) -> str:
        sec = item.get("section") or "n/a"
        p1 = item.get("page_start")
        p2 = item.get("page_end")
        if p1 and p2:
            page = f"p.{p1}" if p1 == p2 else f"p.{p1}-{p2}"
            return f"{page}, {sec}"
        if p1:
            return f"p.{p1}, {sec}"
        return sec

    lines = [answer.strip()]
    if citations:
        lines.append("\nSources:")
        for item in citations[:3]:
            src = item.get("source", "unknown")
            lines.append(f"- {src} ({_fmt_loc(item)})")
    return "\n".join(lines)


async def _telegram_api_call(method: str, payload: dict) -> dict:
    _ensure_telegram_enabled()
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/{method}"
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


async def _send_telegram_message(chat_id: int, text: str) -> None:
    await _telegram_api_call("sendMessage", {"chat_id": chat_id, "text": text})


async def _send_stars_invoice(chat_id: int) -> None:
    await _telegram_api_call(
        "sendInvoice",
        {
            "chat_id": chat_id,
            "title": settings.telegram_pro_title,
            "description": f"{settings.telegram_pro_description} Price: ${PRO_PRICE_USD}",
            "payload": PRO_PAYLOAD,
            "currency": "XTR",
            "prices": [{"label": "Pro 30 days", "amount": settings.telegram_pro_price_stars}],
            "provider_token": "",
        },
    )


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    _validate_webhook_secret(x_telegram_bot_api_secret_token)

    update = await request.json()

    pre_checkout_query = update.get("pre_checkout_query")
    if pre_checkout_query:
        ok = pre_checkout_query.get("invoice_payload") == PRO_PAYLOAD
        await _telegram_api_call(
            "answerPreCheckoutQuery",
            {
                "pre_checkout_query_id": pre_checkout_query.get("id"),
                "ok": ok,
                "error_message": "Invalid payment payload" if not ok else None,
            },
        )
        return {"ok": True, "handled": "pre_checkout_query"}

    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"ok": True, "ignored": True}

    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    if "id" not in chat or "id" not in sender:
        return {"ok": True, "ignored": True}

    chat_id = int(chat["id"])
    tg_user_id = int(sender["id"])

    if message.get("successful_payment"):
        charge_id = message["successful_payment"].get("telegram_payment_charge_id")
        text = activate_pro_for_telegram_user(db, tg_user_id, chat_id, charge_id)
        await _send_telegram_message(chat_id, text)
        return {"ok": True, "handled": "successful_payment"}

    text = (message.get("text") or "").strip()
    if not text:
        return {"ok": True, "ignored": True}

    if text.startswith("/start"):
        await _send_telegram_message(chat_id, "Chao ban. Dung /plan de xem goi, /upgrade de mua Pro.")
        return {"ok": True, "handled": "start"}

    if text.startswith("/plan"):
        user = get_or_create_user_for_telegram(db, tg_user_id, chat_id)
        await _send_telegram_message(chat_id, plan_text_for_user(db, user))
        return {"ok": True, "handled": "plan"}

    if text.startswith("/upgrade"):
        if not settings.telegram_stars_enabled:
            await _send_telegram_message(chat_id, "Stars payment dang tat. Vui long lien he admin.")
        else:
            await _send_stars_invoice(chat_id)
        return {"ok": True, "handled": "upgrade"}

    result = process_telegram_question(
        db=db,
        telegram_user_id=tg_user_id,
        telegram_chat_id=chat_id,
        question=text,
    )

    await _send_telegram_message(chat_id, _format_reply(result["answer"], result.get("citations", [])))

    return {"ok": True, "user_id": result["user_id"], "tokens_used": result["tokens_used"]}


@admin_router.get("/webhook/info")
async def telegram_webhook_info():
    _ensure_telegram_enabled()
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/getWebhookInfo"
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


@admin_router.post("/webhook/set")
async def telegram_webhook_set():
    _ensure_telegram_enabled()
    if not settings.telegram_webhook_url:
        raise HTTPException(status_code=400, detail="TELEGRAM_WEBHOOK_URL is not configured")
    if not settings.telegram_webhook_secret:
        raise HTTPException(status_code=400, detail="TELEGRAM_WEBHOOK_SECRET is not configured")

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/setWebhook"
    payload = {
        "url": settings.telegram_webhook_url,
        "secret_token": settings.telegram_webhook_secret,
        "allowed_updates": ["message", "edited_message", "pre_checkout_query"],
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


@admin_router.post("/webhook/delete")
async def telegram_webhook_delete():
    _ensure_telegram_enabled()
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/deleteWebhook"
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json={"drop_pending_updates": False})
        response.raise_for_status()
        return response.json()
