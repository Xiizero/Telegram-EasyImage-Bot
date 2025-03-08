# 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制文件
COPY . .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 运行程序
CMD ["python", "bot.py"]
