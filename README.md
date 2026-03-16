# rtsp-vision-api

## 環境設定

1. 複製 `.env.example` 為 `.env`
2. 在 `.env` 中填入所需變數（見下方「應放入 .env 的變數」）
3. 執行 `uv sync` 安裝依賴後，使用 `uv run manage.py runserver` 啟動

## 應放入 .env 的變數（勿提交到 Git）

| 變數 | 說明 | 範例 |
|------|------|------|
| `DJANGO_SECRET_KEY` | Django 密鑰（正式環境必填） | 用 `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` 產生 |
| `DJANGO_DEBUG` | 除錯模式 | `True` / `False` |
| `DJANGO_ALLOWED_HOSTS` | 允許的 Host（逗號分隔） | `127.0.0.1,localhost` |

未設定時，開發環境會使用預設值；正式環境請務必設定 `DJANGO_SECRET_KEY` 並將 `DJANGO_DEBUG=False`。
