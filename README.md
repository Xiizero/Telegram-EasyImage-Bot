# Telegram EasyImage Bot

一个 Telegram 机器人，用于将图片上传到 EasyImages2.0 图床。

## 功能
- `/start`: 获取欢迎消息。
- 支持上传图片（photo 或 document 类型），返回 URL 和 Markdown 链接。
- 用户权限控制（通过 ALLOWED_USERS 环境变量）。

## 功能展示
![VID_20250308212655](https://img.sss.wiki/i/data/2025/03/08/z7us1h.gif)

## 部署教程
### Docker 命令行部署
**拉取镜像:**
     - 从 Docker Hub 拉取镜像：

```
docker pull xiizero/tgeasyimgebot:latest
```

**运行容器:**
   - 使用以下命令运行容器，替换为你的实际环境变量值：

```
docker run -d \
    -e TELEGRAM_BOT_TOKEN= \
    -e EASYIMAGE_API_URL= \
    -e EASYIMAGE_TOKEN= \
    -e ALLOWED_USERS= \
    --name tg-easyimage-bot \
    xiizero/tgeasyimgebot:latest

```
   - 检查日志：
```
docker logs tg-easyimage-bot
```

   - 预期输出:[2025-03-08 12:00:00] 启动 Telegram Bot...

### Docker Compose 部署
```
version: '3.8'
services:
  tg-easyimage-bot:
    image: xiizero/tgeasyimgebot:latest
    container_name: tg-easyimage-bot
    environment:
      - TELEGRAM_BOT_TOKEN=
      - EASYIMAGE_API_URL=
      - EASYIMAGE_TOKEN=
      - ALLOWED_USERS=
    restart: always
```

### 环境变量含义

- TELEGRAM_BOT_TOKEN:
  - 含义: Telegram 提供的 Bot Token，由 @BotFather 生成，用于认证机器人身份。
  - 示例: 1234567890:ABCDEFGHIJKL
  - 必填: 是，必须与你创建的机器人匹配。

- EASYIMAGE_API_URL:
  - 含义: EasyImages2.0 图床的 API 端点，用于上传图片。
  - 示例: https://xxx.xxx.xxx/api/index.php
  - 必填: 是，必须指向你的图床服务器地址。

- EASYIMAGE_TOKEN:
  - 含义: EasyImages2.0 提供的认证 Token，用于访问 API。
  - 示例: your-easyimage-token
  - 必填: 是，必须与你的图床配置一致。

- ALLOWED_USERS:
  - 含义: 允许使用机器人的 Telegram 用户 ID 列表，多个 ID 用逗号分隔。如果留空，所有用户均可使用。
  - 示例: 123456789,987654321
  - 必填: 否，留空或不设置时默认开放给所有用户。
