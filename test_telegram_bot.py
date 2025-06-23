import httpx

BOT_TOKEN = "7696594493:AAE-wlhKckvB2H0DlFYQ5O7nN1fCu_KmUaw"
CHAT_ID = "5588396810"  # твой chat_id
MESSAGE = "Привет! Это тест от ENS-бота."

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
params = {"chat_id": CHAT_ID, "text": MESSAGE}

response = httpx.get(url, params=params)
print(response.json())
