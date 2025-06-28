from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes
)
import asyncio, json, os, io, random, requests
from datetime import datetime, timedelta
import threading

# --- Cấu hình ---
TOKEN = "7053031372:AAGGOnE72JbZat9IaXFqa-WRdv240vSYjms"
API_KEY = "xai-q0jvC2nF7oYL0gwGTRSUg8Np95zXnEwJlc0gFjSOtVh9eEygErOFChWCYao6X4mKvdF6R4UKNa8SSt7u"
PORT = int(os.environ.get("PORT", 10000))
USER_DATA_DIR = "user_data"
USERS_FILE = "users.json"
START_TIME = datetime.now()

if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

# --- Flask giữ port ---
app = Flask(__name__)
@app.route("/")
def index():
    return "<h3>🤖 Bot đang hoạt động!</h3>"

def get_user_file(uid):
    return os.path.join(USER_DATA_DIR, f"zprojectxdcb_{uid}.json")

def load_user_data(uid):
    path = get_user_file(uid)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"history": [], "created": datetime.now().isoformat()}

def save_user_data(uid, data):
    with open(get_user_file(uid), "w") as f:
        json.dump(data, f)

def load_all_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return []

def save_all_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f)

# --- Các hàm lệnh ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = load_all_users()
    if uid not in users:
        users.append(uid)
        save_all_users(users)

    await update.message.reply_text(
        "🤖 Bot Zproject X Dương Công Bằng\n"
        "• /ask <câu hỏi>\n"
        "• /img <mô tả ảnh>\n"
        "• /history – Lịch sử hỏi\n"
        "• /export – Xuất file lịch sử\n"
        "• /help – Trợ giúp"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 Lệnh hỗ trợ:\n"
        "• /ask <câu hỏi> – Hỏi AI\n"
        "• /img <mô tả> – Tạo ảnh AI\n"
        "• /history – Xem câu hỏi gần đây\n"
        "• /export – Tải lịch sử hỏi đáp"
    )

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    question = ' '.join(context.args)

    if not question:
        return await update.message.reply_text("❗ Vui lòng nhập câu hỏi sau /ask")

    try:
        with open("prompt.txt", "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
    except:
        system_prompt = "Bạn là trợ lý AI Zproject X Duong Cong Bang."

    msg = await update.message.reply_text("⏳ Đang suy nghĩ...")

    payload = {
        "model": "grok-3-latest",
        "stream": False,
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
    }

    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        res = requests.post("https://api.x.ai/v1/chat/completions", json=payload, headers=headers, timeout=30)
        reply = res.json()['choices'][0]['message']['content']
    except:
        return await msg.edit_text("❌ Lỗi gọi API.")

    history = load_user_data(uid)
    history["history"].append({"q": question, "a": reply})
    save_user_data(uid, history)

    reply_text = f"<b>📨 Câu hỏi:</b> <i>{question}</i>\n\n<b>🤖 Trả lời:</b>\n"

    if len(reply) > 3800:
        buffer = io.StringIO()
        buffer.write(f"Câu hỏi: {question}\n\nTrả lời:\n{reply}")
        buffer.seek(0)
        await update.message.reply_document(
            document=InputFile(buffer, filename="long_reply.txt"),
            caption="📄 Trả lời dài, gửi file nè!"
        )
    else:
        await msg.edit_text(reply_text + reply, parse_mode="HTML")

async def img_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = ' '.join(context.args)
    if not prompt:
        return await update.message.reply_text("📸 Dùng: /img mô_tả")

    await update.message.reply_text("🎨 Đang tạo ảnh...")
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
    try:
        await update.message.reply_photo(photo=url, caption=f"🖼️ Prompt: {prompt}")
    except:
        await update.message.reply_text("❌ Lỗi khi gửi ảnh.")

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = load_user_data(uid)
    if not data["history"]:
        return await update.message.reply_text("📭 Bạn chưa hỏi gì cả.")

    text = "📚 <b>Lịch sử câu hỏi gần đây:</b>\n"
    for i, qa in enumerate(data["history"][-5:], 1):
        text += f"{i}. <i>{qa['q'][:50]}{'...' if len(qa['q']) > 50 else ''}</i>\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = load_user_data(uid)
    if not data["history"]:
        return await update.message.reply_text("📭 Không có dữ liệu để xuất.")

    buffer = io.StringIO()
    for i, qa in enumerate(data["history"], 1):
        buffer.write(f"{i}. Q: {qa['q']}\nA: {qa['a']}\n{'-'*40}\n")
    buffer.seek(0)
    await update.message.reply_document(InputFile(buffer, filename="history.txt"), caption="📁 Lịch sử hỏi")

# --- Tự động reset sau 24h ---
async def auto_reset():
    while True:
        files = os.listdir(USER_DATA_DIR)
        for file in files:
            path = os.path.join(USER_DATA_DIR, file)
            with open(path, "r") as f:
                data = json.load(f)
            created = datetime.fromisoformat(data.get("created", datetime.now().isoformat()))
            if datetime.now() - created > timedelta(hours=24):
                os.remove(path)
                uid = file.replace("zprojectxdcb_", "").replace(".json", "")
                try:
                    await bot_app.bot.send_message(chat_id=int(uid), text="⏳ Dữ liệu của bạn đã được xóa sau 24h.")
                except: pass
        await asyncio.sleep(3600)

# --- Tự động gửi tin nhắn vui ---
async def auto_fun_messages():
    fallback = ["🌞 Chào bạn! Hôm nay bạn ổn chứ?", "🎉 Mỗi ngày là một cơ hội!"]
    while True:
        await asyncio.sleep(random.randint(10800, 18000))  # 3 - 5 tiếng
        msg = random.choice(fallback)
        for uid in load_all_users():
            try:
                await bot_app.bot.send_message(chat_id=uid, text=msg)
            except: pass

# --- Khởi động bot polling ---
async def setup_bot_polling():
    global bot_app
    bot_app = ApplicationBuilder().token(TOKEN).build()

    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("help", help_command))
    bot_app.add_handler(CommandHandler("ask", ask_command))
    bot_app.add_handler(CommandHandler("img", img_command))
    bot_app.add_handler(CommandHandler("export", export_command))
    bot_app.add_handler(CommandHandler("history", history_command))

    asyncio.create_task(auto_reset())
    asyncio.create_task(auto_fun_messages())

    print("🤖 Đang chạy polling...")
    await bot_app.run_polling()

# --- Khởi động Flask + bot ---
if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT)).start()
    asyncio.run(setup_bot_polling())