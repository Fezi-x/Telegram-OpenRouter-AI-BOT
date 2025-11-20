import requests

BOT_TOKEN = "your token"
print(requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo").json())
