from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)
import requests, os, json, asyncio, io
from datetime import datetime, timedelta
import threading, random

# ==== Cấu hình bot ====
TOKEN = "7053031372:AAGGOnE72JbZat9IaXFqa-WRdv240vSYjms"
API_KEY = "xai-q0jvC2nF7oYL0gwGTRSUg8Np95zXnEwJlc0gFjSOtVh9eEygErOFChWCYao6X4mKvdF6R4UKNa8SSt7u"
PORT = int(os.environ.get("PORT", 8080))
USER_DATA_DIR = "user_data"
USERS_FILE = "users.json"

if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

app = Flask(__name__)
app_bot = None  # Biến toàn cục

# ==== Trang chủ Flask ====
@app.route('/')
def home():
    return "<h2>🤖 Zproject X Duong Cong Bang đang hoạt động!</h2>"

# ==== Hàm xử lý người dùng ====
def get_user_file(uid): return os.path.join(USER_DATA_DIR, f"zprojectxdcb_{uid}.json")

def load_user_data(uid):
    f = get_user_file(uid)
    if os.path.exists(f):
        with open(f, 'r') as file:
            return json.load(file)
    return {"history": [], "created": datetime.now().isoformat()}

def save_user_data(uid, data):
    with open(get_user_file(uid), 'w') as f:
        json.dump(data, f)

def load_all_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_all_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

# ==== Auto reset sau 24 giờ ====
async def auto_reset():
    while True:
        for file in os.listdir(USER_DATA_DIR):
            try:
                path = os.path.join(USER_DATA_DIR, file)
                with open(path, 'r') as f:
                    data = json.load(f)
                created = datetime.fromisoformat(data.get("created"))
                if datetime.now() - created > timedelta(hours=24):
                    os.remove(path)
                    uid = file.replace("zprojectxdcb_", "").replace(".json", "")
                    if app_bot:
                        await app_bot.bot.send_message(chat_id=int(uid), text="⚠️ Dữ liệu của bạn đã được reset sau 24 giờ.")
            except Exception as e:
                print(f"[RESET ERROR] {e}")
        await asyncio.sleep(3600)

# ==== Tự động gửi câu hỏi vui ====
async def auto_send_fun_messages():
    fallback = ["🌞 Chào bạn! Hôm nay bạn đã cười chưa?", "🎉 Bạn tuyệt vời lắm!", "🌈 Luôn luôn có lý do để mỉm cười!"]
    while True:
        await asyncio.sleep(random.randint(10800, 18000))  # 3-5 tiếng
        message = random.choice(fallback)

        try:
            with open("prompt-1709.txt", "r", encoding="utf-8") as f:
                prompts = [line.strip() for line in f if line.strip()]
                if prompts:
                    prompt = random.choice(prompts)
                    res = requests.post(
                        "https://api.x.ai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                        json={"model": "grok-3-latest", "stream": False, "temperature": 0.7,
                              "messages": [{"role": "system", "content": "Bạn là AI vui vẻ"},
                                           {"role": "user", "content": prompt}]},
                        timeout=15
                    )
                    res.raise_for_status()
                    message = res.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"[FUN ERROR] {e}")

        for uid in load_all_users():
            try:
                await app_bot.bot.send_message(chat_id=uid, text=message)
            except Exception as e:
                print(f"[SEND FAIL] {e}")

# ==== Các lệnh bot ====
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_chat.id)
    users = load_all_users()
    if uid not in users:
        users.append(uid)
        save_all_users(users)
    await update.message.reply_text("🤖 Bot Zproject X Dương Công Bằng đã sẵn sàng!\nDùng /ask <câu hỏi> để bắt đầu!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Hướng dẫn sử dụng:\n"
        "/start - Khởi động\n"
        "/ask <câu hỏi> - Hỏi AI\n"
        "/img <mô tả> - Tạo ảnh AI\n"
        "/export - Xuất lịch sử\n"
        "/history - Xem câu hỏi gần đây"
    )

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    question = ' '.join(context.args)
    if not question:
        return await update.message.reply_text("⚠️ Dùng: /ask nội_dung")

    users = load_all_users()
    if uid not in users:
        users.append(uid)
        save_all_users(users)

    prompt = "Bạn là AI Zproject X Dương Công Bằng, hỗ trợ thông minh, vui vẻ."
    msg = await update.message.reply_text("🤖 Đang suy nghĩ...")

    try:
        res = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={"model": "grok-3-latest", "stream": False, "temperature": 0.7,
                  "messages": [{"role": "system", "content": prompt},
                               {"role": "user", "content": question}]},
            timeout=30
        )
        res.raise_for_status()
        reply = res.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"[ASK ERROR] {e}")
        return await msg.edit_text("❌ Lỗi khi gọi API.")

    save = load_user_data(uid)
    save["history"].append({"q": question, "a": reply})
    save_user_data(uid, save)

    formatted = f"<b>📨 Câu hỏi:</b> <i>{question}</i>\n\n<b>🤖 Trả lời:</b>\n{reply}"
    if len(formatted) > 4000:
        buffer = io.StringIO()
        buffer.write(f"Câu hỏi: {question}\n\nTrả lời:\n{reply}")
        buffer.seek(0)
        return await update.message.reply_document(InputFile(buffer, "traloi.txt"), caption="📁 Câu trả lời dài quá!")
    else:
        return await msg.edit_text(formatted, parse_mode="HTML")

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = load_user_data(uid)
    if not data['history']:
        return await update.message.reply_text("📭 Không có dữ liệu.")
    buffer = io.StringIO()
    for i, qa in enumerate(data['history'], 1):
        buffer.write(f"{i}. Q: {qa['q']}\nA: {qa['a']}\n{'-'*40}\n")
    buffer.seek(0)
    await update.message.reply_document(InputFile(buffer, "history.txt"), caption="📁 Lịch sử hỏi đáp")

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = load_user_data(uid)
    if not data['history']:
        return await update.message.reply_text("📭 Không có dữ liệu.")
    lines = [f"{i+1}. <i>{x['q'][:50]}{'...' if len(x['q'])>50 else ''}</i>"
             for i, x in enumerate(data['history'][-5:])]
    await update.message.reply_text("🕘 Gần đây:\n" + "\n".join(lines), parse_mode='HTML')

async def img_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = ' '.join(context.args)
    if not prompt:
        return await update.message.reply_text("📷 Dùng: /img mô_tả_ảnh")
    msg = await update.message.reply_text("🖼️ Đang tạo ảnh...")
    try:
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
        await update.message.reply_photo(photo=url, caption=f"📸 <b>{prompt}</b>", parse_mode='HTML')
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Không tạo được ảnh: {e}")

# ==== Run polling song song Flask ====
def run_polling():
    global app_bot
    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start_command))
    app_bot.add_handler(CommandHandler("help", help_command))
    app_bot.add_handler(CommandHandler("ask", ask_command))
    app_bot.add_handler(CommandHandler("export", export_command))
    app_bot.add_handler(CommandHandler("history", history_command))
    app_bot.add_handler(CommandHandler("img", img_command))

    asyncio.create_task(auto_reset())
    asyncio.create_task(auto_send_fun_messages())

    print("🤖 Bot Telegram đang chạy ở chế độ polling...")
    app_bot.run_polling(close_loop=False)

# ==== Bắt đầu Flask + Polling ====
if __name__ == '__main__':
    threading.Thread(target=run_polling, daemon=True).start()
    print(f"🚀 Flask server đang chạy tại cổng {PORT}")
    app.run(host="0.0.0.0", port=PORT)