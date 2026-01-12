from flask import Flask, request, jsonify
import requests, os, sqlite3, random, base64, json
from datetime import datetime

app = Flask(__name__)

# ===== ENV =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
API_KEY = os.environ.get("API_KEY")

TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ===== DATABASE =====
db = sqlite3.connect("data.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0,
    pass_login TEXT,
    pass_withdraw TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS deposits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    status TEXT
)
""")
db.commit()

# ===== TOOLS =====
def tg(method, data):
    requests.post(f"{TG_API}/{method}", json=data)

def menu(chat_id):
    tg("sendMessage", {
        "chat_id": chat_id,
        "text": "📋 *MENU*",
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "🎲 Random TK", "callback_data": "rand_tk"}],
                [{"text": "🔐 Cài MK đăng nhập", "callback_data": "set_login"}],
                [{"text": "💸 Cài MK rút", "callback_data": "set_withdraw"}],
                [{"text": "💰 Nạp tiền", "callback_data": "deposit"}]
            ]
        }
    })

def random_username():
    return "user" + str(random.randint(100000,999999))

def random_stk():
    while True:
        s = "".join(str(random.randint(0,9)) for _ in range(12))
        if not (s == s[0]*12):
            return s

# ===== WEBHOOK =====
@app.route("/telegram", methods=["POST"])
def telegram():
    data = request.get_json() or {}

    if "message" in data:
        msg = data["message"]
        uid = msg["chat"]["id"]
        text = msg.get("text","")

        cur.execute("INSERT OR IGNORE INTO users(user_id,username) VALUES(?,?)",
                    (uid, msg["from"].get("username","")))
        db.commit()

        if text == "/start":
            menu(uid)

    if "callback_query" in data:
        q = data["callback_query"]
        uid = q["from"]["id"]
        cid = q["message"]["chat"]["id"]
        action = q["data"]

        if action == "rand_tk":
            payload = {
                "tk": random_username(),
                "stk": random_stk(),
                "time": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            encoded = base64.b64encode(json.dumps(payload).encode()).decode()
            tg("sendMessage", {"chat_id": cid, "text": f"📦 `{encoded}`", "parse_mode":"Markdown"})

        elif action == "deposit":
            tg("sendMessage", {"chat_id": cid, "text": "💰 Nhập số tiền muốn nạp:"})

        elif action == "set_login":
            tg("sendMessage", {"chat_id": cid, "text": "🔐 Gửi mật khẩu đăng nhập mới:"})

        elif action == "set_withdraw":
            tg("sendMessage", {"chat_id": cid, "text": "💸 Gửi mật khẩu rút mới:"})

    return "ok"

# ===== ADMIN API =====
@app.route("/admin/approve", methods=["POST"])
def approve():
    if request.headers.get("X-API-KEY") != API_KEY:
        return "unauthorized", 401

    data = request.json
    uid = data["user_id"]
    amount = data["amount"]

    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, uid))
    db.commit()

    tg("sendMessage", {"chat_id": uid, "text": f"✅ Nạp thành công {amount}đ"})
    return {"ok": True}

# ===== ROOT =====
@app.route("/")
def home():
    return "Bot Telegram FULL đang chạy OK"

# ===== RUN =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
