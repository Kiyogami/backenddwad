from fastapi import APIRouter, Request, status
import logging
from services.telegram_service import send_telegram_message

router = APIRouter(prefix="/api/telegram", tags=["telegram"])
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def telegram_webhook(update: dict):
    """Handle incoming Telegram updates."""
    # Log incoming update for debug
    logger.info(f"Webhook update: {update}")
    
    try:
        if "message" in update:
            message = update["message"]
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")
            
            if text == "/start":
                await send_telegram_message(chat_id, "Witaj w Prascy Bandyci Shop! 🛍️\nUżyj Web App, aby złożyć zamówienie.")
            elif text == "/id":
                await send_telegram_message(chat_id, f"Twoje ID: {chat_id}")
            elif text == "/level":
                # Placeholder for level
                await send_telegram_message(chat_id, "Twój poziom: 1 (Początkujący)")
                
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        
    return {"ok": True}
