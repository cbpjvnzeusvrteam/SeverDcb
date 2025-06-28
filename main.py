from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import requests, os, json, asyncio, io
from datetime import datetime, timedelta
import threading, random

TOKEN = "7053031372:AAGGOnE72JbZat9IaXFqa-WRdv240vSYjms"
API_KEY = "xai-q0jvC2nF7oYL0gwGTRSUg8Np95zXnEwJlc0gFjSOtVh9eEygErOFChWCYao6X4mKvdF6R4UKNa8SSt7u"

USER_DATA_DIR = "user_data"
USERS_FILE = "users.json"

if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

PORT = int(os.environ.get("PORT", 8080))
app = Flask(__name__)

@app.route('/')
def index():
    return "<h2>🤖 Zproject X Duong Cong Bang đang hoạt động!</h2>"

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

async def auto_reset():
    while True:
        for file in os.listdir(USER_DATA_DIR):
            path = os.path.join(USER_DATA_DIR, file)
            with open(path, 'r') as f:
                data = json.load(f)
            created = datetime.fromisoformat(data.get("created", datetime.now().isoformat()))
            if datetime.now() - created > timedelta(hours=24):
                uid = file.replace(".json", "")
                os.remove(path)
                try:
                    await app_bot.bot.send_message(chat_id=int(uid), text="⚠️ Dữ liệu của bạn đã được reset sau 24h")
                except:
                    pass
        await asyncio.sleep(3600)

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    cid = update.effective_chat.id
    name = update.effective_user.full_name
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
        system_prompt = f"Bạn là trợ lý AI Zproject X Duong Cong Bang."

    msg = await update.message.reply_text("⏳", reply_to_message_id=update.message.message_id)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
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
        res = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=payload, timeout=10)
        reply = res.json()['choices'][0]['message']['content']
    except:
        return await msg.edit_text("❌ Lỗi khi gọi API Zproject")

    # Format code nếu có
    def format_reply(text):
        if "```" in text:
            parts = text.split("```")
            new_parts = []
            for i, part in enumerate(parts):
                new_parts.append(f"<pre>{part.strip()}</pre>" if i % 2 == 1 else part)
            return ''.join(new_parts)
        elif any(line.strip().startswith(('def ', 'class ', 'import ', '#include')) for line in text.splitlines()):
            return f"<pre>{text.strip()}</pre>"
        return text.strip()

    formatted_reply = format_reply(reply)

    user_data = load_user_data(uid)
    user_data['history'].append({"q": question, "a": reply})
    save_user_data(uid, user_data)

    reply_text = f"<b>📨 Câu hỏi:</b> <i>{question}</i>\n\n<b>🤖 Zproject X Duong Cong Bằng:</b>\n"

    MAX_LENGTH = 4000
    if len(reply_text + formatted_reply) > MAX_LENGTH:
        filename = f"zprojectxdcb_{random.randint(1000, 9999)}.txt"
        buffer = io.StringIO()
        buffer.write(f"Câu hỏi: {question}\n\nTrả lời:\n{reply}\n")
        buffer.seek(0)
        await update.message.reply_document(
            document=InputFile(buffer, filename=filename),
            caption=f"📁 Vì câu trả lời quá dài nên gửi file nhé @{username}",
            reply_to_message_id=update.message.message_id
        )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔁 Trả lời lại", callback_data=f"retry|{uid}|{question}")]
        ])
        await msg.edit_text(
            reply_text + formatted_reply,
            parse_mode='HTML',
            reply_markup=keyboard
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    if len(data) < 3:
        return
    action, uid, question = data

    if str(query.from_user.id) != uid:
        return await query.message.reply_text("⚠️ Bạn không được phép tương tác với câu hỏi của người khác")

    update.message = query.message
    context.args = question.split()
    await ask_command(update, context)

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = load_user_data(uid)
    if not data['history']:
        return await update.message.reply_text("❗ Bạn chưa có dữ liệu để xuất")

    buffer = io.StringIO()
    buffer.write(f"LỊCH SỬ HỎI ĐÁP - {update.effective_user.full_name}\n\n")
    for i, qa in enumerate(data['history'], 1):
        buffer.write(f"{i}. Q: {qa['q']}\nA: {qa['a']}\n{'-'*40}\n")
    buffer.seek(0)

    await update.message.reply_document(document=InputFile(buffer, filename="history.txt"), caption="📁 Lịch sử hỏi")

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = load_user_data(uid)
    if not data['history']:
        return await update.message.reply_text("📭 Bạn chưa hỏi gì cả hôm nay")

    text = "🕘 <b>Lịch sử câu hỏi gần đây:</b>\n"
    for i, qa in enumerate(data['history'][-5:], 1):
        text += f"{i}. <i>{qa['q'][:50]}</i>\n"
    await update.message.reply_text(text, parse_mode='HTML')

async def img_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    all_users = load_all_users()
    if cid not in all_users:
        all_users.append(cid)
        save_all_users(all_users)

    prompt = ' '.join(context.args)
    if not prompt:
        return await update.message.reply_text("📷 Dùng: /img mô_tả_ảnh")

    await update.message.reply_text("🖼️ Đang tạo ảnh...", reply_to_message_id=update.message.message_id)
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
    await update.message.reply_photo(photo=url, caption=f"📸 Prompt: <b>{prompt}</b>", parse_mode='HTML')

async def auto_send_fun_messages():
    fallback = [
        "🌞 Chào bạn! Hôm nay bạn đã cười chưa?",
        "💬 Nếu bạn đang buồn, hãy hỏi tôi một câu nhé!",
        "🎉 Mỗi ngày là một cơ hội, bạn tuyệt vời lắm!",
        "🌈 Luôn luôn có lý do để mỉm cười!"
    ]

    while True:
        await asyncio.sleep(random.randint(10800, 18000))  # 3 - 5 tiếng
        prompt = None
        try:
            with open("prompt-1709.txt", "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            if lines:
                prompt = random.choice(lines)
        except:
            prompt = None

        if prompt:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "grok-3-latest",
                "stream": False,
                "temperature": 0.7,
                "messages": [
                    {"role": "system", "content": "Bạn là Zproject X Duong Cong Bang, AI thân thiện và vui nhộn."},
                    {"role": "user", "content": prompt}
                ]
            }
            try:
                res = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=payload, timeout=10)
                message = res.json()['choices'][0]['message']['content']
            except:
                message = random.choice(fallback)
        else:
            message = random.choice(fallback)

        for uid in load_all_users():
            try:
                await app_bot.bot.send_message(chat_id=uid, text=message)
            except Exception as e:
                print(f"❗ Không gửi được tới {uid}: {e}")

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
        "━━━━━━━━━━━━━━━━\n"
        "• /ask <câu hỏi> – Hỏi AI Zproject\n"
        "• /img <mô tả ảnh> – Tạo ảnh AI\n"
        "• /export – Xuất lịch sử hỏi đáp\n"
        "• /history – Xem câu hỏi gần đây\n"
        "━━━━━━━━━━━━━━━━\n"
        "🔄 Zproject X Duong Cong Bang DepZai Hog:v \n"
        "✨ AI bởi Zproject X Dương Công Bằng"
    )

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start_command))
    app_bot.add_handler(CommandHandler("help", help_command))
    app_bot.add_handler(CommandHandler("ask", ask_command))
    app_bot.add_handler(CommandHandler("export", export_command))
    app_bot.add_handler(CommandHandler("history", history_command))
    app_bot.add_handler(CommandHandler("img", img_command))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))

    asyncio.get_event_loop().create_task(auto_reset())
    asyncio.get_event_loop().create_task(auto_send_fun_messages())

    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT)).start()
    app_bot.run_polling()