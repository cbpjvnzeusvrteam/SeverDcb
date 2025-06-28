from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
import asyncio

TOKEN = "7053031372:AAGGOnE72JbZat9IaXFqa-WRdv240vSYjms"
API_MAIL = "https://10minutemail.net/address.api.php"

app = Flask(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📨 Bot Mail 10p đã sẵn sàng!\nDùng /new, /get, /check, /read")

async def new_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(API_MAIL + "?new=1").json()
    await update.message.reply_text(
        f"📩 Email mới: {res['mail_get_mail']}\n⏳ Còn lại: {res['mail_left_time']}s\n🔑 Key: {res['mail_get_key']}"
    )

async def get_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(API_MAIL).json()
    await update.message.reply_text(
        f"📨 Email hiện tại: {res['mail_get_mail']}\n🔗 Link: {res['permalink']['url']}\n🔑 Key: {res['permalink']['key']}"
    )

async def check_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(API_MAIL).json()
    if not res.get("mail_list"):
        await update.message.reply_text("📭 Hộp thư trống.")
        return
    mail = res["mail_list"][0]
    await update.message.reply_text(
        f"📥 Thư mới:\n📧 Từ: {mail['from']}\n✉️ Chủ đề: {mail['subject']}\n🕒 {mail['datetime2']}"
    )

async def read_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(API_MAIL).json()
    if not res.get("mail_list"):
        await update.message.reply_text("📭 Không có thư nào.")
        return
    mail_id = res["mail_list"][0]["mail_id"]
    key = res["mail_get_key"]
    detail = requests.get(f"https://10minutemail.net/mail.api.php?mailid={mail_id}&k={key}").json()
    body = detail.get("mail_body", "[Không có nội dung]")
    await update.message.reply_text(f"📖 Nội dung thư:\n{body}")

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    await app_bot.process_update(update)
    return "OK"

if __name__ == "__main__":
    bot = Bot(token=TOKEN)
    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("new", new_mail))
    app_bot.add_handler(CommandHandler("get", get_mail))
    app_bot.add_handler(CommandHandler("check", check_mail))
    app_bot.add_handler(CommandHandler("read", read_mail))

    # Webhook cho Telegram
    bot.delete_webhook(drop_pending_updates=True)
    bot.set_webhook(url=f"https://severdcb.onrender.com/{TOKEN}")

    app.run(host="0.0.0.0", port=8080)