from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import requests, os, json, asyncio, io
from datetime import datetime, timedelta
import threading, random

# --- Config ---
TOKEN = "7053031372:AAGGOnE72JbZat9IaXFqa-WRdv240vSYjms"
API_KEY = "xai-q0jvC2nF7oYL0gwGTRSUg8Np95zXnEwJlc0gFjSOtVh9eEygErOFChWCYao6X4mKvdF6R4UKNa8SSt7u"
PORT = int(os.environ.get("PORT", 8080))
USER_DATA_DIR = "user_data"
USERS_FILE = "users.json"
app = Flask(__name__)
app_bot = None

if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

@app.route('/')
def index():
    return "<h2>🤖 Zproject X Duong Cong Bang đang hoạt động!</h2>"

# --- Data Functions ---
def get_user_file(uid):
    return os.path.join(USER_DATA_DIR, f"zprojectxdcb_{uid}.json")

def load_user_data(uid):
    file = get_user_file(uid)
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
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

# --- Commands ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    users = load_all_users()
    if cid not in users:
        users.append(cid)
        save_all_users(users)
    await update.message.reply_text(
        "🤖 Bot by Zproject X Duong Cong Bang\n"
        "👉 Admin: @zproject2\n"
        "👉 Group: @zproject4"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 Hướng dẫn sử dụng Bot Zproject:\n"
        "• /ask <câu hỏi> – Hỏi AI Zproject\n"
        "• /img <mô tả ảnh> – Tạo ảnh AI\n"
        "• /export – Xuất lịch sử hỏi đáp\n"
        "• /history – Xem câu hỏi gần đây"
    )

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    cid = update.effective_chat.id
    username = update.effective_user.username or "bạn"
    question = ' '.join(context.args)

    all_users = load_all_users()
    if cid not in all_users:
        all_users.append(cid)
        save_all_users(all_users)

    if not question:
        return await update.message.reply_text("❗ Hãy nhập câu hỏi sau /ask")

    try:
        with open("prompt.txt", "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
    except:
        system_prompt = "Bạn là trợ lý AI Zproject X Duong Công Bằng."

    msg = await update.message.reply_text("⏳", reply_to_message_id=update.message.message_id)

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
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
        res = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        reply = res.json()['choices'][0]['message']['content']
    except:
        return await msg.edit_text("❌ Lỗi khi gọi API")

    def format_reply(text):
        if "```" in text:
            return "<pre>" + text.replace("```", "") + "</pre>"
        return text

    formatted = format_reply(reply)
    user_data = load_user_data(uid)
    user_data["history"].append({"q": question, "a": reply})
    save_user_data(uid, user_data)

    response = f"<b>📨 Câu hỏi:</b> <i>{question}</i>\n\n<b>🤖 Zproject:</b>\n"
    if len(response + formatted) > 4096:
        buffer = io.StringIO()
        buffer.write(f"Câu hỏi: {question}\nTrả lời:\n{reply}")
        buffer.seek(0)
        await update.message.reply_document(InputFile(buffer, filename="reply.txt"), caption="📁 Câu trả lời quá dài nên gửi file nhé.")
    else:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Trả lời lại", callback_data=f"retry|{uid}|{question}")]])
        await msg.edit_text(response + formatted, parse_mode='HTML', reply_markup=keyboard)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    if len(data) < 3:
        return await query.message.reply_text("Lỗi callback.")
    action, uid, question = data[0], data[1], "|".join(data[2:])
    if str(query.from_user.id) != uid:
        return await query.message.reply_text("⚠️ Không phải câu hỏi của bạn.")
    dummy_update = Update(update_id=update.update_id, message=query.message)
    dummy_update.effective_user = query.from_user
    dummy_update.effective_chat = query.message.chat
    context.args = question.split()
    await ask_command(dummy_update, context)

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = load_user_data(uid)
    if not data['history']:
        return await update.message.reply_text("❗ Không có dữ liệu.")
    buffer = io.StringIO()
    for i, qa in enumerate(data['history'], 1):
        buffer.write(f"{i}. Q: {qa['q']}\nA: {qa['a']}\n{'-'*40}\n")
    buffer.seek(0)
    await update.message.reply_document(InputFile(buffer, filename="history.txt"))

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = load_user_data(uid)
    if not data['history']:
        return await update.message.reply_text("📭 Chưa có câu hỏi nào.")
    msg = "🕘 <b>Lịch sử:</b>\n"
    for i, qa in enumerate(data['history'][-5:], 1):
        msg += f"{i}. <i>{qa['q'][:50]}</i>\n"
    await update.message.reply_text(msg, parse_mode='HTML')

async def img_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = ' '.join(context.args)
    if not prompt:
        return await update.message.reply_text("📷 Dùng: /img mô_tả")
    msg = await update.message.reply_text("🖼️ Đang tạo ảnh...")
    try:
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
        await update.message.reply_photo(photo=url, caption=f"📸 Prompt: <b>{prompt}</b>", parse_mode='HTML')
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Lỗi khi tạo ảnh: {e}")

# --- Background Tasks ---
async def auto_reset():
    while True:
        for file in list(os.listdir(USER_DATA_DIR)):
            try:
                path = os.path.join(USER_DATA_DIR, file)
                with open(path, 'r') as f:
                    data = json.load(f)
                created = datetime.fromisoformat(data.get("created", datetime.now().isoformat()))
                if datetime.now() - created > timedelta(hours=24):
                    uid = file.replace("zprojectxdcb_", "").replace(".json", "")
                    os.remove(path)
                    if app_bot:
                        await app_bot.bot.send_message(chat_id=int(uid), text="⚠️ Dữ liệu của bạn đã reset sau 24h.")
            except:
                pass
        await asyncio.sleep(3600)

async def auto_send_fun_messages():
    messages = ["🌞 Chào bạn! Hôm nay bạn đã cười chưa?", "🎉 Mỗi ngày là một cơ hội!", "🌈 Luôn mỉm cười nhé!"]
    while True:
        await asyncio.sleep(random.randint(10800, 18000))
        text = random.choice(messages)
        for uid in load_all_users():
            try:
                if app_bot:
                    await app_bot.bot.send_message(chat_id=uid, text=text)
            except:
                pass

# --- Main Bot Setup ---
async def setup_bot_polling():
    global app_bot
    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start_command))
    app_bot.add_handler(CommandHandler("help", help_command))
    app_bot.add_handler(CommandHandler("ask", ask_command))
    app_bot.add_handler(CommandHandler("export", export_command))
    app_bot.add_handler(CommandHandler("history", history_command))
    app_bot.add_handler(CommandHandler("img", img_command))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))

    asyncio.create_task(auto_reset())
    asyncio.create_task(auto_send_fun_messages())
    print("📡 Bot Telegram đang chạy polling...")
    await app_bot.run_polling()

if __name__ == '__main__':
    def run_flask():
        print(f"🚀 Flask server đang chạy cổng {PORT}")
        app.run(host="0.0.0.0", port=PORT)

    threading.Thread(target=run_flask).start()
    asyncio.run(setup_bot_polling())