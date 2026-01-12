import os

TOKEN = os.getenv("TOKEN")
ADMIN_ID_RAW = os.getenv("ADMIN_ID")

if TOKEN is None or ADMIN_ID_RAW is None:
    raise Exception("❌ Thiếu TOKEN hoặc ADMIN_ID trong Environment Variables")

ADMIN_ID_RAW = ADMIN_ID_RAW.strip()

if not ADMIN_ID_RAW.isdigit():
    raise Exception("❌ ADMIN_ID phải là số")

ADMIN_ID = int(ADMIN_ID_RAW)



# ===== DATABASE =====
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    login_password TEXT,
    withdraw_password TEXT,
    balance INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS deposits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    status TEXT DEFAULT 'pending'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# ===== UTIL =====
def log_action(user_id, action):
    cursor.execute(
        "INSERT INTO user_logs(user_id, action) VALUES (?,?)",
        (user_id, action)
    )
    conn.commit()

async def notify_admin(context, text):
    await context.bot.send_message(ADMIN_ID, text)

def random_username():
    return ''.join(random.choices(string.ascii_lowercase, k=6)) + str(random.randint(100,999))

def is_beautiful(stk):
    bad = ["000","111","222","333","444","555","666","777","888","999",
           "1234","2345","3456","4567","5678","6789","9876","8765"]
    return any(b in stk for b in bad)

def random_stk_12():
    while True:
        stk = ''.join(str(random.randint(0,9)) for _ in range(12))
        if not is_beautiful(stk):
            return stk

# ===== MENU =====
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Random tài khoản", callback_data="rand_acc")],
        [InlineKeyboardButton("🔐 Cài MK đăng nhập", callback_data="set_login")],
        [InlineKeyboardButton("💸 Cài MK rút", callback_data="set_withdraw")],
        [InlineKeyboardButton("💳 Random STK 12 số", callback_data="rand_stk")],
        [InlineKeyboardButton("💰 Nạp tiền", callback_data="wallet")],
        [InlineKeyboardButton("🆘 Hỗ trợ", callback_data="support")]
    ])

SET_LOGIN, SET_WITHDRAW = range(2)

# ===== HANDLERS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user.id,))
    conn.commit()

    await update.message.reply_text("🤖 BOT HỖ TRỢ PUBLIC", reply_markup=main_menu())

    await notify_admin(context, f"👤 USER MỚI\nID: {user.id}\n@{user.username}")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "rand_acc":
        tk = random_username()
        cursor.execute("UPDATE users SET username=? WHERE user_id=?", (tk, uid))
        conn.commit()
        log_action(uid, "random_account")
        await q.message.reply_text(f"🎲 TK mới: `{tk}`", parse_mode="Markdown")
        await notify_admin(context, f"🎲 RANDOM TK\nUser: {uid}\nTK: {tk}")

    elif q.data == "rand_stk":
        stk = random_stk_12()
        log_action(uid, "random_stk")
        await q.message.reply_text(f"💳 STK: `{stk}`", parse_mode="Markdown")

    elif q.data == "set_login":
        await q.message.reply_text("🔐 Nhập MK đăng nhập:")
        return SET_LOGIN

    elif q.data == "set_withdraw":
        await q.message.reply_text("💸 Nhập MK rút:")
        return SET_WITHDRAW

    elif q.data == "wallet":
        await q.message.reply_text(
            "💰 Gửi: `NAP <số tiền>`\nVD: NAP 50000",
            parse_mode="Markdown"
        )

    elif q.data == "support":
        await q.message.reply_text("🆘 Liên hệ admin")

    return ConversationHandler.END

async def save_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute(
        "UPDATE users SET login_password=? WHERE user_id=?",
        (update.message.text, update.effective_user.id)
    )
    conn.commit()
    await notify_admin(context, f"🔐 CÀI MK ĐĂNG NHẬP\nUser: {update.effective_user.id}")
    await update.message.reply_text("✅ Đã lưu MK đăng nhập")
    return ConversationHandler.END

async def save_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute(
        "UPDATE users SET withdraw_password=? WHERE user_id=?",
        (update.message.text, update.effective_user.id)
    )
    conn.commit()
    await notify_admin(context, f"💸 CÀI MK RÚT\nUser: {update.effective_user.id}")
    await update.message.reply_text("✅ Đã lưu MK rút")
    return ConversationHandler.END

async def deposit_request(update, context):
    if not update.message.text.startswith("NAP"):
        return
    try:
        amount = int(update.message.text.split()[1])
        uid = update.effective_user.id

        cursor.execute(
            "INSERT INTO deposits(user_id, amount) VALUES (?,?)",
            (uid, amount)
        )
        conn.commit()

        await update.message.reply_text("⏳ Đã gửi yêu cầu nạp")
        await notify_admin(
            context,
            f"💰 YÊU CẦU NẠP\nUser: {uid}\nSố tiền: {amount}\nDuyệt: /duyet_{uid}_{amount}"
        )
    except:
        await update.message.reply_text("❌ Sai cú pháp")

async def approve(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    data = update.message.text.replace("/duyet_", "").split("_")
    uid, amount = int(data[0]), int(data[1])

    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, uid))
    conn.commit()

    await notify_admin(context, f"✅ DUYỆT NẠP\nUser: {uid}\n+{amount}")
    await context.bot.send_message(uid, f"✅ Nạp thành công {amount}")

# ===== RUN =====
app = ApplicationBuilder().token(TOKEN).build()

conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(buttons)],
    states={
        SET_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_login)],
        SET_WITHDRAW: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_withdraw)]
    },
    fallbacks=[]
)

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^NAP"), deposit_request))
app.add_handler(CommandHandler("duyet", approve))
app.add_handler(conv)

app.run_polling()
