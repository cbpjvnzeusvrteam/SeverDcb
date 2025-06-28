from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

TOKEN = "7053031372:AAGGOnE72JbZat9IaXFqa-WRdv240vSYjms"
API_MAIL = "https://10minutemail.net/address.api.php"
WEBHOOK_URL = f"https://severdcb.onrender.com/{TOKEN}"  # ✅ Thay bằng link thật của bạn!

app = Flask(__name__)

# ========== Bot Commands ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Mail 10p bot hoạt động!\nDùng: /new /get /check /read")

async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(API_MAIL + "?new=1").json()
    await update.message.reply_text(f"📬 Mail mới: {res['mail_get_mail']}\n🔑 Key: {res['mail_get_key']}\n⏳ Thời gian còn lại: {res['mail_left_time']}s")

async def get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(API_MAIL).json()
    await update.message.reply_text(f"📨 Email hiện tại: {res['mail_get_mail']}\n🔗 URL: {res['permalink']['url']}\n🔑 Key: {res['permalink']['key']}")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(API_MAIL).json()
    if not res.get("mail_list"):
        await update.message.reply_text("📭 Hộp thư trống.")
        return
    mail = res["mail_list"][0]
    await update.message.reply_text(f"📥 Từ: {mail['from']}\n✉️ Chủ đề: {mail['subject']}\n🕒 Thời gian: {mail['datetime2']}")

async def read(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(API_MAIL).json()
    if not res.get("mail_list"):
        await update.message.reply_text("📭 Không có thư để đọc.")
        return
    mail_id = res["mail_list"][0]["mail_id"]
    key = res["mail_get_key"]
    detail = requests.get(f"https://10minutemail.net/mail.api.php?mailid={mail_id}&k={key}").json()
    await update.message.reply_text(f"📖 Nội dung:\n{detail.get('mail_body', '[Không có nội dung]')}")

# ========== Webhook Receiver ==========
@app.route(f"/{TOKEN}", methods=["POST"])
async def receive():
    update = Update.de_json(request.get_json(force=True), bot)
    await app_bot.process_update(update)
    return "ok"

# ========== Run ==========
if __name__ == "__main__":
    bot = Bot(token=TOKEN)
    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("new", new))
    app_bot.add_handler(CommandHandler("get", get))
    app_bot.add_handler(CommandHandler("check", check))
    app_bot.add_handler(CommandHandler("read", read))

    bot.delete_webhook(drop_pending_updates=True)
    bot.set_webhook(url=WEBHOOK_URL)

    app.run(host="0.0.0.0", port=8080)