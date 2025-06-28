import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "7053031372:AAGGOnE72JbZat9IaXFqa-WRdv240vSYjms"
app = Flask(__name__)

API_MAIL = "https://10minutemail.net/address.api.php"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📩 Chào mừng đến với bot Mail 10 phút!\nDùng /new, /get, /check, /read")

async def new_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(API_MAIL + "?new=1").json()
    text = f"📩 Email mới: {res['mail_get_mail']}\n⏳ Còn lại: {res['mail_left_time']}s\n🔑 Key: {res['mail_get_key']}"
    await update.message.reply_text(text)

async def more_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(API_MAIL + "?more=1").json()
    text = f"📩 Thêm mail: {res['mail_get_mail']}\n⏳ Còn lại: {res['mail_left_time']}s\n🔑 Key: {res['mail_get_key']}"
    await update.message.reply_text(text)

async def get_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(API_MAIL).json()
    text = f"📨 Mail: {res['mail_get_mail']}\n🔑 Key: {res['permalink']['key']}\n🔗 Link: {res['permalink']['url']}"
    await update.message.reply_text(text)

async def check_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(API_MAIL).json()
    if not res.get("mail_list"):
        await update.message.reply_text("📭 Hộp thư trống.")
        return
    mail = res["mail_list"][0]
    text = f"📥 Thư mới:\n📧 Từ: {mail['from']}\n✉️ Chủ đề: {mail['subject']}\n🕒 {mail['datetime2']}"
    await update.message.reply_text(text)

async def read_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(API_MAIL).json()
    if not res.get("mail_list"):
        await update.message.reply_text("📭 Không có thư nào.")
        return
    mail_id = res["mail_list"][0]["mail_id"]
    mail_key = res["mail_get_key"]
    detail = requests.get(f"https://10minutemail.net/mail.api.php?mailid={mail_id}&k={mail_key}").json()
    body = detail.get("mail_body", "[Không có nội dung]")
    await update.message.reply_text(f"📖 Nội dung:\n{body}")

# Telegram Bot webhook
@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    await app_bot.process_update(update)
    return "OK"

# Main init
if __name__ == "__main__":
    from telegram import Bot
    from telegram.ext import Dispatcher

    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("new", new_mail))
    app_bot.add_handler(CommandHandler("more", more_mail))
    app_bot.add_handler(CommandHandler("get", get_mail))
    app_bot.add_handler(CommandHandler("check", check_mail))
    app_bot.add_handler(CommandHandler("read", read_mail))

    bot = Bot(token=TOKEN)
    bot.delete_webhook(drop_pending_updates=True)
    bot.set_webhook(url=f"https://YOUR_RENDER_URL/{TOKEN}")  # 🔁 Cập nhật link Render sau

    app.run(host="0.0.0.0", port=8080)