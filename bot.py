import os
import sys
import requests
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
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

# 构造初始消息和键盘
def create_initial_message_and_keyboard(context: ContextTypes.DEFAULT_TYPE):
    message = (
        f"🎉 图片上传成功！\n\n"
        f"💡 点击下方按钮可直接复制对应内容"
    )
    keyboard = [
        [InlineKeyboardButton("复制直链", callback_data="copy_direct_link")],
        [InlineKeyboardButton("复制HTML", callback_data="copy_html_code")],
        [InlineKeyboardButton("复制BBCode", callback_data="copy_bbcode")],
        [InlineKeyboardButton("复制Markdown", callback_data="copy_markdown")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return message, reply_markup

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

    file = await context.bot.get_file(file_id)
    await file.download_to_drive(file_path)
    timestamped_print(f"文件下载完成: {file_path}")

    try:
        url = upload_image(file_path, EASYIMAGE_TOKEN)
        # 构造各种格式
        direct_link = url
        html_code = f"<img src=\"{url}\" alt=\"image\">"
        bbcode = f"[img]{url}[/img]"
        markdown = f"![image]({url})"

        # 存储内容到 context.user_data
        context.user_data['direct_link'] = direct_link
        context.user_data['html_code'] = html_code
        context.user_data['bbcode'] = bbcode
        context.user_data['markdown'] = markdown

        # 构造初始消息和键盘
        message, reply_markup = create_initial_message_and_keyboard(context)

        timestamped_print(f"图床上传成功: {url}")
        await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
    except Exception as e:
        timestamped_print(f"上传图片时出错: {e}")
        await update.message.reply_text(f"上传图片时出错: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            timestamped_print(f"临时文件已删除: {file_path}")

# 处理内联键盘回调
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # 确认按钮点击
    data = query.data

    # 根据 callback_data 获取对应内容
    if data == "copy_direct_link":
        content = context.user_data.get('direct_link', '未找到内容')
    elif data == "copy_html_code":
        content = context.user_data.get('html_code', '未找到内容')
    elif data == "copy_bbcode":
        content = context.user_data.get('bbcode', '未找到内容')
    elif data == "copy_markdown":
        content = context.user_data.get('markdown', '未找到内容')
    elif data == "return":
        # 返回初始页面
        message, reply_markup = create_initial_message_and_keyboard(context)
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        return
    else:
        content = "未知操作"

    # 显示复制内容，并添加返回按钮
    message = f"已为您准备好内容，请手动复制：\n`{content}`"
    keyboard = [[InlineKeyboardButton("返回", callback_data="return")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)

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
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
