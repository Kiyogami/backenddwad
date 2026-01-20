import hmac
import hashlib
import os
import time
import json
from urllib.parse import quote

# Use the token we set in .env
BOT_TOKEN = "8480641475:AAFNkL7nVozfnBo8GOhbBPR9jE3YjewjVVU"

def generate_test_data():
    user = {
        "id": 123456789,
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "language_code": "en"
    }
    user_json = json.dumps(user).replace(" ", "") # Minify json for consistency if needed, but standard dumps with spaces is safer if consistent
    # Actually telegram minifies it? "user" value is a JSON string.
    
    auth_date = int(time.time())
    
    data = {
        "auth_date": str(auth_date),
        "query_id": "AAHdF6IQAAAAAN0XohDhrPgC",
        "user": user_json
    }
    
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(data.items(), key=lambda kv: kv[0])
    )
    
    secret_key = hmac.new(
        key="WebAppData".encode("utf-8"),
        msg=BOT_TOKEN.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    
    computed_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    
    # URL encode the user json for the final string
    init_data = f"auth_date={auth_date}&query_id={data['query_id']}&user={quote(user_json)}&hash={computed_hash}"
    print(init_data)

if __name__ == "__main__":
    generate_test_data()
