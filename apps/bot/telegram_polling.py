import asyncio

from telegram import LabeledPrice, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from apps.api.database import SessionLocal
from apps.api.services.telegram_service import (
    PRO_PRICE_USD,
    activate_pro_for_telegram_user,
    plan_text_for_user,
    process_telegram_question,
)
from configs.settings import settings


PRO_PAYLOAD = "gxp_pro_30d"


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


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Chao ban. Toi la bot GxP.\n"
        "- /plan: xem goi\n"
        "- /upgrade: nang cap Pro\n"
        "Gui cau hoi GMP/GDP/GxP bang VI/EN."
    )


async def plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user_id = update.effective_user.id
    tg_chat_id = update.effective_chat.id
    db = SessionLocal()
    try:
        from apps.api.services.telegram_service import get_or_create_user_for_telegram

        user = get_or_create_user_for_telegram(db, tg_user_id, tg_chat_id)
        text = plan_text_for_user(db, user)
    finally:
        db.close()
    await update.message.reply_text(text)


async def upgrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not settings.telegram_stars_enabled:
        await update.message.reply_text("Stars payment dang tat. Vui long lien he admin.")
        return

    chat_id = update.effective_chat.id
    await context.bot.send_invoice(
        chat_id=chat_id,
        title=settings.telegram_pro_title,
        description=f"{settings.telegram_pro_description} Price: ${PRO_PRICE_USD}",
        payload=PRO_PAYLOAD,
        currency="XTR",
        prices=[LabeledPrice("Pro 30 days", settings.telegram_pro_price_stars)],
        provider_token="",
    )


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != PRO_PAYLOAD:
        await query.answer(ok=False, error_message="Invalid payment payload")
        return
    await query.answer(ok=True)


async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.successful_payment:
        return

    tg_user_id = update.effective_user.id
    tg_chat_id = update.effective_chat.id
    charge_id = msg.successful_payment.telegram_payment_charge_id

    db = SessionLocal()
    try:
        text = await asyncio.to_thread(
            activate_pro_for_telegram_user,
            db,
            tg_user_id,
            tg_chat_id,
            charge_id,
        )
    finally:
        db.close()

    await msg.reply_text(text)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    tg_user_id = update.effective_user.id
    tg_chat_id = update.effective_chat.id

    db = SessionLocal()
    try:
        result = await asyncio.to_thread(
            process_telegram_question,
            db,
            tg_user_id,
            tg_chat_id,
            text,
        )
    finally:
        db.close()

    reply = _format_reply(result["answer"], result.get("citations", []))
    await update.message.reply_text(reply)


def main() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("plan", plan_command))
    app.add_handler(CommandHandler("upgrade", upgrade_command))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.run_polling(drop_pending_updates=False, bootstrap_retries=-1)


if __name__ == "__main__":
    main()
