import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from config import TELEGRAM_BOT_TOKEN, EASY_IMAGES_API_URL, EASY_IMAGES_API_KEY

logging.basicConfig(level=logging.INFO)

# 上传图片到 EasyImages2.0 的函数
def upload_to_easyimages(file_path: str):
    with open(file_path, 'rb') as file:
        headers = {"Authorization": f"Bearer {EASY_IMAGES_API_KEY}"}
        response = requests.post(
            f"{EASY_IMAGES_API_URL}/api/upload", 
            headers=headers, 
            files={"file": file}
        )
    response.raise_for_status()
    return response.json()

# 处理图片上传
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.photo[-1].file_id)
    file_path = "temp.jpg"
    await file.download_to_drive(file_path)

    try:
        result = upload_to_easyimages(file_path)
        await update.message.reply_text(f"上传成功！链接：{result['url']}")
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("上传失败，请稍后再试！")

# /start 命令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用图片上传机器人！请发送图片进行上传。")

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # 命令和消息处理
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # 启动机器人
    application.run_polling()

if __name__ == "__main__":
    main()
