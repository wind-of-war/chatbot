# Telegram Deploy Checklist (VPS)

Checklist này giúp bạn deploy Telegram integration và test end-to-end nhanh nhất.

## 1) Prerequisites

- Domain đã trỏ về VPS (ví dụ: `api.yourdomain.com`)
- HTTPS hoạt động (Telegram bắt buộc HTTPS cho webhook)
- VPS đã chạy API service
- Có Telegram Bot Token từ BotFather

## 2) Cấu hình `.env`

Điền các biến sau:

```env
TELEGRAM_BOT_TOKEN=123456789:AA....
TELEGRAM_WEBHOOK_SECRET=replace-with-random-secret
TELEGRAM_WEBHOOK_URL=https://api.yourdomain.com/integrations/telegram/webhook
ADMIN_EMAILS=admin@example.com
```

Gợi ý tạo secret nhanh:

```bash
openssl rand -hex 24
```

## 3) Deploy services

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

Kiểm tra health:

```bash
curl -sS https://api.yourdomain.com/health
```

## 4) Tạo admin account và login

### 4.1 Register admin

```bash
curl -sS -X POST "https://api.yourdomain.com/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"StrongPass123!"}'
```

Nếu đã có user, dùng login.

### 4.2 Login và lưu token

```bash
ADMIN_TOKEN=$(curl -sS -X POST "https://api.yourdomain.com/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"StrongPass123!"}' | jq -r '.access_token')

echo "$ADMIN_TOKEN"
```

## 5) Kiểm tra Telegram webhook hiện tại

```bash
curl -sS -X GET "https://api.yourdomain.com/integrations/telegram/webhook/info" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## 6) Set webhook

```bash
curl -sS -X POST "https://api.yourdomain.com/integrations/telegram/webhook/set" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Kiểm tra lại:

```bash
curl -sS -X GET "https://api.yourdomain.com/integrations/telegram/webhook/info" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Bạn cần thấy `url` đúng bằng `TELEGRAM_WEBHOOK_URL`.

## 7) Test webhook endpoint trực tiếp (không qua Telegram)

Lệnh này giả lập Telegram gọi webhook.

```bash
curl -sS -X POST "https://api.yourdomain.com/integrations/telegram/webhook" \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Bot-Api-Secret-Token: replace-with-random-secret" \
  -d '{
    "update_id": 999001,
    "message": {
      "message_id": 1,
      "date": 1710000000,
      "text": "GDP warehouse temperature?",
      "chat": {"id": 123456789, "type": "private"},
      "from": {"id": 123456789, "is_bot": false, "first_name": "Test"}
    }
  }'
```

Kỳ vọng:
- API trả JSON `{"ok": true, ...}`
- Bot gửi message phản hồi về Telegram chat id tương ứng

## 8) Test thật trên Telegram app

- Mở chat với bot
- Gửi câu hỏi tiếng Việt/Anh, ví dụ:
  - `GDP quy dinh nhiet do kho thuoc la bao nhieu?`
  - `What is GDP warehouse temperature requirement?`

Kiểm tra log API:

```bash
docker compose -f infra/docker-compose.yml logs -f api
```

## 9) Test admin endpoints liên quan

### 9.1 Management overview

```bash
curl -sS -X GET "https://api.yourdomain.com/management/overview" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### 9.2 List users (xem user Telegram vừa tạo)

```bash
curl -sS -X GET "https://api.yourdomain.com/admin/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## 10) Rollback webhook (nếu cần)

```bash
curl -sS -X POST "https://api.yourdomain.com/integrations/telegram/webhook/delete" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## 11) Troubleshooting nhanh

- `401 Invalid Telegram webhook secret`:
  - Header `X-Telegram-Bot-Api-Secret-Token` không khớp `TELEGRAM_WEBHOOK_SECRET`
- `503 TELEGRAM_BOT_TOKEN is not configured`:
  - Thiếu `TELEGRAM_BOT_TOKEN`
- Telegram webhook không nhận update:
  - HTTPS không hợp lệ hoặc firewall chặn cổng 443
  - Kiểm tra `webhook/info` để xem `last_error_message`
- Không trả lời được câu hỏi:
  - Kiểm tra Qdrant/Redis/API logs
  - Kiểm tra ingestion/indexing đã chạy chưa

## 12) (Tùy chọn) Chạy polling mode thay webhook

```bash
docker compose -f infra/docker-compose.yml --profile telegram-polling up -d telegram-bot
```

Khi dùng polling mode, nên `deleteWebhook` trước để tránh xung đột.

## 13) (Khuyến nghị) Cập nhật kho tài liệu hàng tháng

Trên VPS:

```bash
cd /opt/gxp-ai-platform
chmod +x scripts/update_regulatory_corpus.sh scripts/install_docs_update_timer.sh
./scripts/install_docs_update_timer.sh
```

Xem log job cập nhật tài liệu:

```bash
sudo journalctl -u gxp-docs-monthly.service -f
```

Auto update khi copy/sửa file trong `data/raw`:

```bash
sudo systemctl status gxp-docs-watch.path --no-pager
sudo journalctl -u gxp-docs-watch.service -f
tail -f /opt/gxp-ai-platform/logs/docs_update_watcher.log
```

## 14) Đồng bộ code VPS với GitHub

Repo đang dùng:

```bash
https://github.com/wind-of-war/chatbot
```

Trên VPS:

```bash
cd /opt/gxp-ai-platform
chmod +x scripts/sync_from_github.sh
./scripts/sync_from_github.sh
```

Script sẽ:
- fetch code mới nhất từ `origin/main`
- reset tracked files về đúng commit GitHub
- restart `gxp-api` và `gxp-telegram-bot`

Không ảnh hưởng:
- `.env`
- `gxp_platform.db`
- `data/raw`
- `data/processed`
- `data/embeddings`
- `data/qdrant_local`
