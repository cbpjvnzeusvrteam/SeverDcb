from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
import requests

TOKEN = "7053031372:AAGGOnE72JbZat9IaXFqa-WRdv240vSYjms"

# ==== Các lệnh bot ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Xin chào! Dùng /new để tạo mail 10p nhé.")

async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get("https://10minutemail.net/address.api.php?new=1").json()
    await update.message.reply_text(
        f"📬 Mail: {res['mail_get_mail']}\n🔑 Key: {res['mail_get_key']}\n⏳ Còn lại: {res['mail_left_time']}s"
    )

# ==== Chạy bot ====
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new))
    print("🤖 Bot đang chạy...")
    app.run_polling()