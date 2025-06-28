from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests, random
from datetime import datetime

# Token Telegram Bot
TOKEN = "7053031372:AAGGOnE72JbZat9IaXFqa-WRdv240vSYjms"
API = "https://10minutemail.net/address.api.php"
START_TIME = datetime(2025, 6, 28, 0, 0, 0)

# Danh sách ảnh gái xinh random
images = [
    "https://anhnail.com/wp-content/uploads/2024/11/Hinh-anh-gai-xinh-2k8-de-thuong.jpg",
    "https://anhnail.com/wp-content/uploads/2024/11/Hinh-gai-xinh-2009-toc-dai-cute.jpg",
    "https://anhnail.com/wp-content/uploads/2024/11/Anh-gai-xinh-2k9-toc-dai-dang-yeu.jpg",
    "https://tft.edu.vn/public/upload/2024/09/anh-gai-pho-43.webp",
    "https://hoseiki.vn/wp-content/uploads/2025/03/anh-girl-pho-20.jpg",
    "https://if24h.com/wp-content/uploads/2024/11/hinh-anh-con-gai-cute-che-mat.jpg",
    "https://imgt.taimienphi.vn/cf/Images/np/2022/8/16/anh-gai-xinh-cute-de-thuong-hot-girl-5.jpg",
    "https://cbam.edu.vn/wp-content/uploads/2024/10/anh-girl-pho-25.jpg",
    "https://i.pinimg.com/474x/4b/08/3b/4b083b831f37d3935756efc29f96fb21.jpg"
]

# Nút liên hệ admin
admin_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("👤 Liên hệ Admin", url="https://t.me/zproject2")]
])

# Hàm chèn ảnh random vào HTML
def get_random_image_html():
    link = random.choice(images)
    return f'<a href="{link}">:v</a>'

# Hàm tính thời gian hoạt động
def get_uptime_text():
    now = datetime.now()
    uptime = now - START_TIME
    hours, remainder = divmod(uptime.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    hour_now = now.hour
    period = "sáng" if hour_now < 12 else "chiều"
    hour_12 = hour_now if hour_now <= 12 else hour_now - 12
    return (
        f"🕒 <b>Bắt đầu từ:</b> {START_TIME.strftime('%d/%m/%Y')}\n"
        f"⏰ <b>Giờ hiện tại:</b> {hour_12} giờ {period}\n"
        f"⏳ <b>Đã hoạt động:</b> {int(hours)} giờ | {int(minutes)} phút | {int(seconds)} giây\n\n"
        f"{get_random_image_html()}"
    )

# Các lệnh
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.mention_html()
    msg = (
        f"👋 Xin chào {user}!\nBot tạo mail 10p:\n"
        f"/new – Tạo mail mới\n/get – Xem mail\n/check – Kiểm tra thư\n"
        f"/read – Đọc thư mới nhất\n/time – Xem thời gian hoạt động\n\n"
        f"{get_random_image_html()}"
    )
    await update.message.reply_html(msg, reply_to_message_id=update.message.message_id, reply_markup=admin_keyboard)

async def time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(get_uptime_text(), reply_to_message_id=update.message.message_id, reply_markup=admin_keyboard)

async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(f"{API}?new=1").json()
    mail = res['mail_get_mail']
    key = res['mail_get_key']
    left = res['mail_left_time']
    user = update.effective_user.mention_html()
    await update.message.reply_html(
        f"📬 <b>Email mới cho {user}</b>\n✉️ <code>{mail}</code>\n🔑 Key: <code>{key}</code>\n⏳ Còn lại: <b>{left}s</b>\n\n{get_random_image_html()}",
        reply_to_message_id=update.message.message_id,
        reply_markup=admin_keyboard
    )

async def get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(API).json()
    mail = res['mail_get_mail']
    key = res['permalink']['key']
    url = res['permalink']['url']
    await update.message.reply_html(
        f"📨 <b>Email hiện tại:</b>\n✉️ <code>{mail}</code>\n🔗 <a href='{url}'>Xem mail</a>\n🔑 Key: <code>{key}</code>\n\n{get_random_image_html()}",
        reply_to_message_id=update.message.message_id,
        reply_markup=admin_keyboard
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(API).json()
    mails = res.get("mail_list", [])
    if not mails:
        await update.message.reply_text("📭 Hộp thư trống.", reply_to_message_id=update.message.message_id, reply_markup=admin_keyboard)
        return
    mail = mails[0]
    await update.message.reply_html(
        f"📥 <b>Thư mới:</b>\n👤 Từ: <code>{mail['from']}</code>\n📝 Tiêu đề: <b>{mail['subject']}</b>\n🕒 Thời gian: {mail['datetime2']}\n\n{get_random_image_html()}",
        reply_to_message_id=update.message.message_id,
        reply_markup=admin_keyboard
    )

async def read(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(API).json()
    mails = res.get("mail_list", [])
    if not mails:
        await update.message.reply_text("📭 Không có thư nào để đọc.", reply_to_message_id=update.message.message_id, reply_markup=admin_keyboard)
        return
    mail_id = mails[0]['mail_id']
    key = res['mail_get_key']
    detail = requests.get(f"https://10minutemail.net/mail.api.php?mailid={mail_id}&k={key}").json()
    body = detail.get("mail_body", "[Không có nội dung]")
    await update.message.reply_html(f"📖 <b>Nội dung thư:</b>\n{body}\n\n{get_random_image_html()}", reply_to_message_id=update.message.message_id, reply_markup=admin_keyboard)

# Khởi chạy bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new))
    app.add_handler(CommandHandler("get", get))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("read", read))
    app.add_handler(CommandHandler("time", time))
    print("🤖 Bot Telegram đang chạy...")
    app.run_polling()