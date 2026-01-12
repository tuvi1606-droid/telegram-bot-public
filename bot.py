from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text
    })

@app.route("/")
def home():
    return "Bot is running"

@app.route("/telegram", methods=["POST"])
def telegram():
    data = request.get_json(force=True)
    print("UPDATE:", data, flush=True)

    message = data.get("message")
    if not message:
        return "ok"

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text.startswith("/start"):
        send_message(chat_id, "🤖 Bot đã sẵn sàng hoạt động")

    else:
        send_message(chat_id, "📌 Gõ /start để bắt đầu")

    return "ok"
