import telebot
from telebot import types
from flask import Flask
import os, json, io, requests, threading, time, re, uuid, random
from datetime import datetime, timedelta
from urllib.parse import quote

# --- Cấu hình ---
TOKEN = "7053031372:AAGGOnE72JbZat9IaXFqa-WRdv240vSYjms"
API_KEY = "xai-q0jvC2nF7oYL0gwGTRSUg8Np95zXnEwJlc0gFjSOtVh9eEygErOFChWCYao6X4mKvdF6R4UKNa8SSt7u"
PORT = int(os.environ.get("PORT", 10000))
USER_DATA_DIR = "user_data"
USERS_FILE = "users.json"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

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

def format_reply_with_code(reply_text):
    parts = re.split(r"(```.*?```)", reply_text, flags=re.DOTALL)
    formatted_parts = []

    for part in parts:
        if part.startswith("```") and part.endswith("```"):
            code_content = part.strip("```").strip()
            formatted_parts.append(f"<pre><code>{telebot.util.escape(code_content)}</code></pre>")
        else:
            formatted_parts.append(part)

    return "\n".join(formatted_parts)

def random_filename():
    return f"zprojectxdcb_{uuid.uuid4().hex[:8]}.txt"

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.chat.id)
    users = load_all_users()
    if uid not in users:
        users.append(uid)
        save_all_users(users)

    bot.reply_to(message,
        "🤖 Bot Zproject X Dương Công Bằng\n"
        "• /ask <câu hỏi>\n"
        "• /img <mô tả ảnh>\n"
        "• /history – Lịch sử hỏi\n"
        "• /export – Xuất file lịch sử\n"
        "• /help – Trợ giúp"
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message,
        "💡 Lệnh hỗ trợ:\n"
        "• /ask <câu hỏi> – Hỏi AI\n"
        "• /img <mô tả> – Tạo ảnh AI\n"
        "• /history – Xem câu hỏi gần đây\n"
        "• /export – Tải lịch sử hỏi đáp"
    )

@bot.message_handler(commands=['ask'])
def ask_command(message):
    uid = str(message.chat.id)
    question = message.text.replace("/ask", "").strip()

    if not question:
        return bot.reply_to(message, "❗ Vui lòng nhập câu hỏi sau /ask")

    try:
        with open("prompt.txt", "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
    except:
        system_prompt = "Bạn là trợ lý AI Zproject X Duong Cong Bang."

    msg = bot.reply_to(message, "⏳ Đang suy nghĩ...")

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
        return bot.edit_message_text("❌ Lỗi gọi API.", message.chat.id, msg.message_id)

    history = load_user_data(uid)
    history["history"].append({"q": question, "a": reply})
    save_user_data(uid, history)

    if len(reply) > 3800:
        buffer = io.StringIO()
        buffer.write(f"Câu hỏi: {question}\n\nTrả lời:\n{reply}")
        buffer.seek(0)
        bot.send_document(
            message.chat.id,
            buffer,
            visible_file_name=random_filename(),
            caption=f"📄 Trả lời dài nè {message.from_user.first_name}!",
            reply_to_message_id=message.message_id
        )
    else:
        formatted_reply = format_reply_with_code(reply)
        try:
            bot.edit_message_text(
                f"<b>📨 Câu hỏi:</b> <i>{telebot.util.escape(question)}</i>\n\n<b>🤖 Trả lời:</b>\n{formatted_reply}",
                message.chat.id,
                msg.message_id,
                reply_to_message_id=message.message_id
            )
        except:
            bot.send_message(
                message.chat.id,
                f"📨 Câu hỏi:\n{question}\n\n🤖 Trả lời:\n{reply}",
                reply_to_message_id=message.message_id
            )

@bot.message_handler(commands=['img'])
def img_command(message):
    prompt = message.text.replace("/img", "").strip()
    if not prompt:
        return bot.reply_to(message, "📸 Dùng: /img mô_tả")

    bot.reply_to(message, "🎨 Đang tạo ảnh...")
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}"
    try:
        bot.send_photo(message.chat.id, photo=url, caption=f"🖼️ Prompt: {prompt}")
    except:
        bot.send_message(message.chat.id, "❌ Lỗi khi gửi ảnh.")

@bot.message_handler(commands=['history'])
def history_command(message):
    uid = str(message.chat.id)
    data = load_user_data(uid)
    if not data["history"]:
        return bot.reply_to(message, "📭 Bạn chưa hỏi gì cả.")

    text = "📚 <b>Lịch sử câu hỏi gần đây:</b>\n"
    for i, qa in enumerate(data["history"][-5:], 1):
        text += f"{i}. <i>{qa['q'][:50]}{'...' if len(qa['q']) > 50 else ''}</i>\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['export'])
def export_command(message):
    uid = str(message.chat.id)
    data = load_user_data(uid)
    if not data["history"]:
        return bot.reply_to(message, "📭 Không có dữ liệu để xuất.")

    buffer = io.StringIO()
    for i, qa in enumerate(data["history"], 1):
        buffer.write(f"{i}. Q: {qa['q']}\nA: {qa['a']}\n{'-'*40}\n")
    buffer.seek(0)
    bot.send_document(message.chat.id, buffer, visible_file_name="history.txt", caption="📁 Lịch sử hỏi")

def auto_reset():
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
                    bot.send_message(uid, "⏳ Dữ liệu của bạn đã được xóa sau 24h.")
                except: pass
        time.sleep(3600)

def auto_fun_messages():
    fallback = ["🌞 Chào bạn! Hôm nay bạn ổn chứ?", "🎉 Mỗi ngày là một cơ hội!"]
    while True:
        time.sleep(random.randint(10800, 18000))  # 3 - 5 tiếng
        msg = random.choice(fallback)
        for uid in load_all_users():
            try:
                bot.send_message(uid, msg)
            except: pass

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT)).start()
    threading.Thread(target=auto_reset).start()
    threading.Thread(target=auto_fun_messages).start()
    print("🤖 Bot đang chạy polling...")
    bot.infinity_polling()