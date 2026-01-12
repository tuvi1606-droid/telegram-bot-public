from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

@app.route("/")
def home():
    return "Bot is running"

@app.route("/telegram", methods=["POST"])
def telegram():
    data = request.get_json(force=True)
    print("UPDATE:", data, flush=True)

    if "message" not in data:
        return "ok"

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": "🤖 Bot đã sẵn sàng"
    })

    return "ok"
