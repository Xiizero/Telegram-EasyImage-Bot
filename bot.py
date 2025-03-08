import os
import sys
import requests
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

# 从环境变量读取配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
EASYIMAGE_API_URL = os.getenv('EASYIMAGE_API_URL', 'https://your-easyimage-domain/api/index.php')
EASYIMAGE_TOKEN = os.getenv('EASYIMAGE_TOKEN')
ALLOWED_USERS = os.getenv('ALLOWED_USERS', '').split(',')  # 允许的用户列表，逗号分隔

if ALLOWED_USERS == ['']:
    ALLOWED_USERS = []

# 检查必需的环境变量
required_env_vars = {
    'TELEGRAM_BOT_TOKEN': TELEGRAM_BOT_TOKEN,
    'EASYIMAGE_API_URL': EASYIMAGE_API_URL,
    'EASYIMAGE_TOKEN': EASYIMAGE_TOKEN
}

for var_name, var_value in required_env_vars.items():
    if not var_value:
        sys.exit(f"Error: {var_name} 环境变量未设置")

# 添加时间戳的 print 函数，并强制刷新输出
def timestamped_print(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)

# 校验用户是否被允许
def is_user_allowed(user_id):
    return str(user_id) in ALLOWED_USERS or not ALLOWED_USERS

# 上传图片并返回 URL
def upload_image(file_path, token):
    timestamped_print(f"准备上传文件: {file_path}")
    if not os.path.exists(file_path):
        raise Exception(f"文件不存在: {file_path}")

    with open(file_path, 'rb') as file:
        # 构造 multipart/form-data 数据
        files = {'image': (os.path.basename(file_path), file, 'image/jpeg')}
        data = {'token': token}
        timestamped_print(f"发送请求到: {EASYIMAGE_API_URL}")
        response = requests.post(EASYIMAGE_API_URL, files=files, data=data)

        timestamped_print(f"API 响应状态码: {response.status_code}")
        timestamped_print(f"API 响应内容: {response.text}")

        if response.status_code == 200:
            result = response.json()
            if result.get("result") == "success" and result.get("code") == 200:
                return result["url"]
            else:
                raise Exception(f"上传失败：{result.get('message', '未知错误')}")
        else:
            raise Exception(f"上传失败，状态码：{response.status_code}")

# 处理消息（图片、文件）
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if not is_user_allowed(user_id):
        timestamped_print(f"{user_id} 用户未被授权访问")
        await update.message.reply_text("您没有权限使用此机器人。")
        return

    await update.message.reply_chat_action(ChatAction.UPLOAD_PHOTO)

    if update.message.photo:
        timestamped_print("收到图片消息")
        file_id = update.message.photo[-1].file_id
        file_path = 'temp.jpg'
    elif update.message.document and update.message.document.mime_type.startswith('image/'):
        timestamped_print("收到文件消息")
        file_id = update.message.document.file_id
        file_path = update.message.document.file_name or 'temp.jpg'
    else:
        timestamped_print("收到非图片消息")
        await update.message.reply_text("不支持的文件类型，请发送图片。")
        return

    # 下载文件并检查
    file = await context.bot.get_file(file_id)
    await file.download_to_drive(file_path)
    timestamped_print(f"文件下载完成: {file_path}")

    # 上传图片
    try:
        url = upload_image(file_path, EASYIMAGE_TOKEN)
        message = (
            f"💌 **URL:** {url}\n"
            f"🗨️ **Markdown:** `![image]({url})`"
        )
        timestamped_print(f"图床上传成功: {url}")
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        timestamped_print(f"上传图片时出错: {e}")
        await update.message.reply_text(f"上传图片时出错: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            timestamped_print(f"临时文件已删除: {file_path}")

# 处理 /start 命令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_first_name = update.message.from_user.first_name
    welcome_message = f"您好，我是一个图床机器人，{user_first_name}！请发送图片以获取上传链接。"
    await update.message.reply_text(welcome_message)

# 主函数
def main() -> None:
    timestamped_print("启动 Telegram Bot...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_message))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
