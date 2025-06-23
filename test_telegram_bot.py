import httpx

BOT_TOKEN = "...................."
CHAT_ID = ".........."  # твой chat_id
MESSAGE = "Привет! Это тест от ENS-бота."

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
params = {"chat_id": CHAT_ID, "text": MESSAGE}

response = httpx.get(url, params=params)
print(response.json())
