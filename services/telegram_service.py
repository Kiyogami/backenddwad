import os
import aiohttp
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Token: 8480641475:AAHjWzPFE82I9Icfn0k4NHHh3x1rBbI2f7s
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8480641475:AAHjWzPFE82I9Icfn0k4NHHh3x1rBbI2f7s")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")  # ID admina do powiadomień

async def send_telegram_message(
    chat_id: int, 
    text: str,
    parse_mode: str = "HTML",
    reply_markup: Optional[Dict[str, Any]] = None
):
    """Wysyła wiadomość do chatu Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping message sending.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    resp_text = await response.text()
                    logger.error(f"Failed to send telegram message to {chat_id}: {resp_text}")
                    return False
                else:
                    logger.info(f"Sent telegram message to {chat_id}")
                    return True
    except Exception as e:
        logger.error(f"Exception sending telegram message: {e}")
        return False


async def send_order_confirmation(order_id: str, chat_id: int, customer_name: str, total: float):
    """Wysyła potwierdzenie zamówienia do klienta."""
    message = f"""
🎉 <b>Dziękujemy za zamówienie!</b>

📦 <b>Numer zamówienia:</b> {order_id}
💰 <b>Kwota:</b> {total:.2f} zł

Twoje zamówienie zostało przyjęte i jest w trakcie realizacji.
Powiadomimy Cię o każdej zmianie statusu.

<b>Prascy Bandyci</b> 🔥
"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "📦 Sprawdź status", "web_app": {"url": f"https://your-domain.com/orders/{order_id}"}}],
            [{"text": "🛍️ Wróć do sklepu", "web_app": {"url": "https://your-domain.com"}}]
        ]
    }
    
    return await send_telegram_message(chat_id, message, reply_markup=keyboard)


async def send_order_status_update(order_id: str, chat_id: int, status: str, tracking_number: Optional[str] = None):
    """Wysyła aktualizację statusu zamówienia."""
    status_messages = {
        "payment_confirmed": "✅ Płatność została potwierdzona",
        "processing": "📦 Zamówienie jest pakowane",
        "verification_pending": "🎥 Oczekuje na weryfikację wideo (H2H)",
        "verification_approved": "✅ Weryfikacja zatwierdzona",
        "verification_rejected": "❌ Weryfikacja odrzucona",
        "shipped": "🚚 Zamówienie zostało wysłane",
        "delivered": "🎉 Zamówienie dostarczone",
        "cancelled": "❌ Zamówienie anulowane"
    }
    
    status_text = status_messages.get(status, f"Status: {status}")
    
    message = f"""
<b>Aktualizacja zamówienia</b> 📬

📦 <b>Nr zamówienia:</b> {order_id}
📍 <b>Status:</b> {status_text}
"""
    
    if tracking_number:
        message += f"\n🔗 <b>Numer przesyłki:</b> {tracking_number}"
    
    message += "\n\n<b>Prascy Bandyci</b> 🔥"
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "📦 Sprawdź szczegóły", "web_app": {"url": f"https://your-domain.com/orders/{order_id}"}}]
        ]
    }
    
    return await send_telegram_message(chat_id, message, reply_markup=keyboard)


async def send_verification_reminder(order_id: str, chat_id: int):
    """Wysyła przypomnienie o weryfikacji wideo."""
    message = f"""
⚠️ <b>Przypomnienie o weryfikacji</b>

Twoje zamówienie <b>{order_id}</b> wymaga weryfikacji wideo.

Aby zakończyć proces zamówienia, nagraj krótkie wideo z dokumentem tożsamości.

📹 <b>Wymagania:</b>
• Czytelny dokument (dowód/prawo jazdy)
• Dobrze oświetlone
• Maksymalnie 30 sekund

<b>Prascy Bandyci</b> 🔥
"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🎥 Wyślij weryfikację", "web_app": {"url": f"https://your-domain.com/orders/{order_id}/verify"}}]
        ]
    }
    
    return await send_telegram_message(chat_id, message, reply_markup=keyboard)


async def notify_admin_new_order(order_id: str, customer_name: str, total: float, delivery_method: str):
    """Powiadamia admina o nowym zamówieniu."""
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID not set, skipping admin notification")
        return False
    
    message = f"""
🔔 <b>NOWE ZAMÓWIENIE!</b>

📦 <b>Zamówienie:</b> {order_id}
👤 <b>Klient:</b> {customer_name}
💰 <b>Kwota:</b> {total:.2f} zł
🚚 <b>Dostawa:</b> {delivery_method.upper()}

<a href="https://your-domain.com/admin/orders/{order_id}">Przejdź do panelu</a>
"""
    
    return await send_telegram_message(int(ADMIN_CHAT_ID), message)


async def notify_admin_verification_submitted(order_id: str, customer_name: str):
    """Powiadamia admina o przesłanej weryfikacji."""
    if not ADMIN_CHAT_ID:
        return False
    
    message = f"""
🎥 <b>NOWA WERYFIKACJA!</b>

📦 <b>Zamówienie:</b> {order_id}
👤 <b>Klient:</b> {customer_name}

Weryfikacja wymaga zatwierdzenia.
<a href="https://your-domain.com/admin/verifications">Sprawdź weryfikacje</a>
"""
    
    return await send_telegram_message(int(ADMIN_CHAT_ID), message)
