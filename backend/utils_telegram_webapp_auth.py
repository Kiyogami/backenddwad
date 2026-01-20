import hmac
import hashlib
from urllib.parse import parse_qsl
from datetime import datetime, timezone, timedelta
from typing import Dict
import os


BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")


def parse_init_data(init_data: str) -> Dict[str, str]:
    """Parse Telegram WebApp initData (query-string) into a dict.

    Example initData format:
    "query_id=AAE...&user=%7B...%7D&auth_date=1712345678&hash=abc..."
    """
    return dict(parse_qsl(init_data, keep_blank_values=True))


def verify_telegram_webapp(init_data: str, max_age_seconds: int = 86400) -> Dict[str, str]:
    """Validate Telegram WebApp initData according to official docs.

    Returns the parsed data dict if valid, otherwise raises ValueError.
    See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    """
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not configured")

    data = parse_init_data(init_data)
    if "hash" not in data:
        raise ValueError("Missing hash in initData")

    received_hash = data.pop("hash")

    # 1) data_check_string = sorted "key=value" lines joined by '\n'
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(data.items(), key=lambda kv: kv[0])
    )

    # 2) secret_key = HMAC_SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        key="WebAppData".encode("utf-8"),
        msg=BOT_TOKEN.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()

    # 3) computed_hash = HMAC_SHA256(secret_key, data_check_string)
    computed_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise ValueError("Invalid initData hash")

    # 4) Check auth_date (not too old)
    auth_date_str = data.get("auth_date")
    if auth_date_str:
        auth_ts = int(auth_date_str)
        auth_dt = datetime.fromtimestamp(auth_ts, tz=timezone.utc)
        if datetime.now(timezone.utc) - auth_dt > timedelta(seconds=max_age_seconds):
            raise ValueError("initData too old")

    # put hash back if caller wants full dict
    data["hash"] = received_hash
    
    # Parse JSON fields (user is typically JSON-encoded)
    if "user" in data:
        try:
            import json
            data["user"] = json.loads(data["user"])
        except (json.JSONDecodeError, TypeError):
            # If parsing fails, leave as string
            pass
    
    return data
