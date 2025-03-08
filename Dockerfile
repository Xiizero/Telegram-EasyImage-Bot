FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
COPY bot.py .
RUN pip install --no-cache-dir -r requirements.txt
ENV TELEGRAM_BOT_TOKEN=""
ENV EASYIMAGE_API_URL="https://your-easyimage-domain/api/index.php"
ENV EASYIMAGE_TOKEN=""
ENV ALLOWED_USERS=""
CMD ["python", "bot.py"]
