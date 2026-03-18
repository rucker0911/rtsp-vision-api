# rtsp-vision-api

以 Django + DRF 建立的 RTSP 攝影機設定與串流管理 API 專案，提供攝影機設備的完整 CRUD 管理功能。

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
3. **執行資料庫 Migration**
   ```bash
   uv run manage.py migrate
   ```
4. **啟動開發伺服器**
   ```bash
   uv run manage.py runserver
   ```
5. 開啟 Swagger UI 確認 API 是否正常：
   ```
   http://127.0.0.1:8000/api/schema/swagger-ui/
   ```

---

## 環境變數設定

### Django 相關

| 變數 | 說明 | 範例 |
|------|------|------|
| `DJANGO_SECRET_KEY` | Django 密鑰（正式環境必填） | 用 `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` 產生 |
| `DJANGO_DEBUG` | 除錯模式 | `True` / `False` |
| `DJANGO_ALLOWED_HOSTS` | 允許的 Host（逗號分隔） | `127.0.0.1,localhost` |

### 資料庫（PostgreSQL）

| 變數 | 說明 | 範例 |
|------|------|------|
| `DB_NAME` | 資料庫名稱 | `rtsp_vision` |
| `DB_USER` | 資料庫使用者 | `postgres` |
| `DB_PASSWORD` | 資料庫密碼 | `your_password` |
| `DB_HOST` | 資料庫位址 | `localhost` |
| `DB_PORT` | 資料庫連接埠 | `5432` |

> 正式環境請務必設定 `DJANGO_SECRET_KEY`、正確的 DB 連線資訊，並將 `DJANGO_DEBUG=False`。  
> 測試環境需確認 DB User 具備 `CREATEDB` 權限，否則 `manage.py test` 會失敗。

---

## API 端點

| Method | URL | 說明 |
|--------|-----|------|
| `GET` | `/api/cameras/` | 取得啟用中的攝影機列表 |
| `POST` | `/api/cameras/create/` | 新增或更新攝影機 |
| `GET` | `/api/cameras/{device_id}/` | 取得單筆攝影機資料 |
| `DELETE` | `/api/cameras/{device_id}/` | 停用攝影機 |

### 統一回應格式

```json
{ "code": "success", "data": { ... } }
{ "code": "missingParameter", "message": "Missing parameters.", "errors": { ... } }
{ "code": "notFound", "message": "data not found" }
{ "code": "serverError", "message": "Server error" }
```

### `CameraSource` 欄位說明

| 欄位 | 說明 | 備注 |
|------|------|------|
| `device_id` | 設備編號（唯一） | 作為 Upsert 識別鍵 |
| `name` | 攝影機名稱 | |
| `stream_url` | 串流 URL（RTSP） | |
| `web_port` | Web 存取埠號 | 範圍 1–65535 |
| `rtsp_port` | RTSP 埠號 | 範圍 1–65535 |
| `cctv_user` | CCTV 登入帳號 | 不會在 API 回傳中曝光 |
| `cctv_pass` | CCTV 登入密碼 | 不會在 API 回傳中曝光 |
| `is_enabled` | 是否啟用 | 軟刪除時設為 `false` |
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

1. 建立超級使用者：
   ```bash
   uv run manage.py createsuperuser
   ```
2. 開啟 `http://127.0.0.1:8000/admin/` 登入，即可在後台管理 `CameraSource` 資料。

---

## 測試

```bash
uv run manage.py test cameras
```

> 若出現 `permission denied to create database`，請對 DB User 執行：
> ```sql
> ALTER ROLE your_db_user CREATEDB;
> ```

---

## 專案結構

```
cameras/
  models.py         → CameraSource 資料表定義
  serializers.py    → Read / Write Serializer
  views.py          → APIView（含 LogManager 日誌）
  urls.py           → cameras 路由
  tests.py          → APITestCase 測試

config/
  settings.py       → Django 設定（含 DRF、Swagger 設定）
  urls.py           → 全域路由

utils/
  responses.py      → 回應常數與 response_with()
  exceptions.py     → 全域例外處理（custom_exception_handler）
  logManager.py     → 日誌管理（每日換檔，寫入 ./logs/）
  sqlBuild.py       → 原生 SQL 組裝工具（參數化查詢，防 Injection）
```

---

## 技術棧

| 項目 | 版本 / 說明 |
|------|------------|
| Python | 3.11+ |
| Django | 5.2+ |
| Django REST Framework | 3.16+ |
| drf-spectacular | Swagger / OpenAPI 文件 |
| PostgreSQL | 資料庫 |
| uv | 套件管理 |
