# rtsp-vision-api

以 Django + DRF 建立的 RTSP 攝影機設定與串流管理 API 專案，提供攝影機設備的完整 CRUD 管理，並透過 Celery 定期進行 TCP 連線狀態檢查與歷史記錄。

---

## 開發環境快速啟動

1. **建立虛擬環境與安裝依賴**
   ```bash
   uv sync
   ```

2. **複製環境變數範例**
   ```bash
   cp .env.example .env
   ```
   > 至少填入 `DJANGO_SECRET_KEY`，其餘保留預設值即可開發。

3. **啟動 PostgreSQL + RabbitMQ**
   ```bash
   docker compose up -d
   ```
   > 確認狀態：`docker compose ps`  
   > RabbitMQ 管理介面：`http://localhost:15672`（帳密預設 `guest / guest`）

4. **執行資料庫 Migration**
   ```bash
   uv run manage.py migrate
   ```

5. **建立管理員帳號（首次）**
   ```bash
   uv run manage.py createsuperuser
   ```

6. **啟動服務**
   ```bash
   # Django API Server
   uv run manage.py runserver

   # Celery Worker（執行排程任務）
   uv run celery -A config worker --loglevel=info

   # Celery Beat（每分鐘觸發連線檢查、每週觸發 Log 清理）
   uv run celery -A config beat --loglevel=info
   ```

7. **確認 API 正常**
   ```
   http://127.0.0.1:8000/health/
   http://127.0.0.1:8000/api/schema/swagger-ui/
   ```

---

## 環境變數設定

### Django

| 變數 | 說明 | 預設 |
|------|------|------|
| `DJANGO_SECRET_KEY` | 密鑰（正式環境必填） | insecure dev key |
| `DJANGO_DEBUG` | 除錯模式 | `True` |
| `DJANGO_ALLOWED_HOSTS` | 允許的 Host（逗號分隔） | `127.0.0.1,localhost` |
| `CORS_ALLOWED_ORIGINS` | 允許的 CORS 來源（正式環境必填） | — |
| `TOKEN_EXPIRY_HOURS` | API Token 有效時數 | `24` |

### 資料庫（PostgreSQL）

| 變數 | 說明 | 預設 |
|------|------|------|
| `DB_NAME` | 資料庫名稱 | `rtsp_vision` |
| `DB_USER` | 使用者 | `postgres` |
| `DB_PASSWORD` | 密碼 | — |
| `DB_HOST` | 位址 | `localhost` |
| `DB_PORT` | 連接埠 | `5432` |
| `DB_CONN_MAX_AGE` | 連線池保留秒數 | `60` |

### RabbitMQ（Celery Broker）

| 變數 | 說明 | 預設 |
|------|------|------|
| `RABBITMQ_URL` | AMQP 連線字串 | `amqp://guest:guest@localhost:5672//` |

### 其他

| 變數 | 說明 | 預設 |
|------|------|------|
| `STATUS_LOG_RETENTION_DAYS` | 連線歷史保留天數 | `90` |

> 正式環境必填：`DJANGO_SECRET_KEY`、`DB_PASSWORD`、`DJANGO_DEBUG=False`、`DJANGO_ALLOWED_HOSTS`  
> 測試環境需確認 DB User 具備 `CREATEDB` 權限，否則 `manage.py test` 會失敗。

---

## API 端點

### 認證

| Method | URL | 說明 | 需要 Token |
|--------|-----|------|-----------|
| `POST` | `/api/auth/login/` | 取得 API Token | 否 |
| `POST` | `/api/auth/logout/` | 撤銷目前的 Token | 是 |

> Token 有效期由 `TOKEN_EXPIRY_HOURS` 控制（預設 24 小時），每次登入重新產生。  
> 所有 Camera API 需帶 Header：`Authorization: Token <token>`

### 攝影機管理

| Method | URL | 說明 |
|--------|-----|------|
| `GET` | `/api/cameras/` | 取得啟用中的攝影機列表（支援分頁與篩選） |
| `POST` | `/api/cameras/create/` | 新增或更新攝影機（Upsert） |
| `GET` | `/api/cameras/{device_id}/` | 取得單筆攝影機資料 |
| `DELETE` | `/api/cameras/{device_id}/` | 停用攝影機（軟刪除） |
| `GET` | `/api/cameras/{device_id}/status/` | 查詢即時連線狀態 |
| `GET` | `/api/cameras/{device_id}/history/` | 查詢連線狀態歷史與在線率 |

**`GET /api/cameras/` Query Params**

| 參數 | 型別 | 說明 | 預設 |
|------|------|------|------|
| `page` | int | 頁碼 | `1` |
| `page_size` | int | 每頁筆數（最大 100） | `20` |
| `name` | string | 名稱模糊搜尋 | — |
| `is_online` | bool | 篩選連線狀態（`true` / `false`） | — |

**`GET /api/cameras/{device_id}/history/` Query Params**

| 參數 | 型別 | 說明 |
|------|------|------|
| `from_date` | date | 開始日期（`YYYY-MM-DD`） |
| `to_date` | date | 結束日期（`YYYY-MM-DD`） |
| `page` / `page_size` | int | 分頁 |

### 系統

| Method | URL | 說明 | 需要 Token |
|--------|-----|------|-----------|
| `GET` | `/health/` | 服務健康狀態（DB / Broker） | 否 |

### 統一回應格式

```json
{ "code": "success", "data": { ... } }
{ "code": "success", "pagination": { "total": 50, "page": 1, "page_size": 20, "total_pages": 3 }, "data": [ ... ] }
{ "code": "success", "uptime_rate": 85.5, "pagination": { ... }, "data": [ ... ] }
{ "code": "missingParameter", "message": "Missing parameters.", "errors": { ... } }
{ "code": "notFound", "message": "data not found" }
{ "code": "notAuthorized", "message": "Token has expired." }
{ "code": "throttled", "message": "Too many requests. Please try again in 30 seconds." }
{ "code": "serverError", "message": "Server error" }
```

### `CameraSource` 欄位說明

| 欄位 | 說明 | 備注 |
|------|------|------|
| `device_id` | 設備編號（唯一） | Upsert 識別鍵 |
| `name` | 攝影機名稱 | |
| `stream_url` | 串流 URL（RTSP） | |
| `web_port` | Web 存取埠號 | 範圍 1–65535 |
| `rtsp_port` | RTSP 埠號 | 範圍 1–65535 |
| `cctv_user` | CCTV 登入帳號 | 選填；不會在 API 回傳中曝光 |
| `cctv_pass` | CCTV 登入密碼 | 選填；不會在 API 回傳中曝光 |
| `is_enabled` | 是否啟用 | 軟刪除時設為 `false` |
| `is_online` | 連線狀態 | Celery Beat 每分鐘更新 |
| `last_checked_at` | 最後連線檢查時間 | Celery Beat 每分鐘更新 |
| `created_at` / `updated_at` | 建立 / 更新時間 | 自動填入 |

---

## Swagger UI / API 文件

| URL | 說明 |
|-----|------|
| `/api/schema/swagger-ui/` | Swagger UI 互動式文件 |
| `/api/schema/redoc/` | ReDoc 文件 |
| `/api/schema/` | OpenAPI Schema（JSON） |

---

## Django 管理後台

開啟 `http://127.0.0.1:8000/admin/` 登入，可管理 `CameraSource`、`CameraStatusLog`、Celery Beat 排程。

---

## 測試

```bash
# 指定 app
uv run manage.py test cameras
uv run manage.py test auth_api
uv run manage.py test health

# 全部
uv run manage.py test
```

> 若出現 `permission denied to create database`，請對 DB User 執行：
> ```sql
> ALTER ROLE your_db_user CREATEDB;
> ```

---

## 專案結構

```
cameras/
  models.py         → CameraSource、CameraStatusLog 資料表
  serializers.py    → Read / Write / Status / Log Serializer
  views.py          → APIView（含分頁、篩選、歷史查詢）
  urls.py           → cameras 路由
  tasks.py          → TCP 連線檢查（並行）、StatusLog 清理
  tests.py          → APITestCase + Task mock 測試

auth_api/
  views.py          → LoginView（限流）/ LogoutView
  urls.py           → /api/auth/ 路由
  tests.py          → 含 Token 過期測試

health/
  views.py          → HealthView（DB + Broker TCP 檢查）
  urls.py           → /health/ 路由

config/
  settings.py       → Django 設定（DRF、Swagger、Celery、CORS）
  celery.py         → Celery app 初始化
  __init__.py       → 導入 celery_app
  urls.py           → 全域路由

utils/
  authentication.py → ExpiringTokenAuthentication（Token 過期機制）
  responses.py      → 回應常數與 response_with()
  exceptions.py     → 全域例外處理
  pagination.py     → 分頁工具（paginate / parse_page_params）
  throttles.py      → LoginRateThrottle（IP 限流）
  middleware.py     → RequestLoggingMiddleware（Request 日誌）
  logManager.py     → 每日換檔日誌（Asia/Taipei）
  sqlBuild.py       → 參數化 SQL 組裝工具

docker-compose.yml  → PostgreSQL + RabbitMQ 一鍵啟動
```

---

## Celery 排程任務

| 任務 | 頻率 | 說明 |
|------|------|------|
| `cameras.check_all_cameras_status` | 每分鐘 | TCP 連線檢查，更新 `is_online` / `last_checked_at`，記錄狀態變化 |
| `cameras.cleanup_status_logs` | 每週 | 清理超過 `STATUS_LOG_RETENTION_DAYS` 天的歷史記錄 |

---

## 技術棧

| 項目 | 說明 |
|------|------|
| Python 3.11+ | |
| Django 5.2+ | Web 框架 |
| Django REST Framework | API 框架 |
| drf-spectacular | Swagger / OpenAPI 文件 |
| Celery + django-celery-beat | 排程任務 |
| RabbitMQ | Celery Broker |
| PostgreSQL | 資料庫 |
| Docker Compose | 外部服務管理 |
| uv | 套件管理 |
