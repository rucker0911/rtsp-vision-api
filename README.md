# rtsp-vision-api

以 Django 建立的 RTSP 攝影機設定與串流管理 API 專案，目前提供最小可運作的 Camera 設備管理與查詢功能。

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
3. **啟動開發伺服器**
   ```bash
   uv run manage.py migrate
   uv run manage.py runserver
   ```
4. 在瀏覽器開啟 `http://127.0.0.1:8000/api/cameras/` 測試 API 是否正常。

---

## 環境變數設定

### Django 相關

| 變數 | 說明 | 範例 |
|------|------|------|
| `DJANGO_SECRET_KEY` | Django 密鑰（正式環境必填） | 用 `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` 產生 |
| `DJANGO_DEBUG` | 除錯模式 | `True` / `False` |
| `DJANGO_ALLOWED_HOSTS` | 允許的 Host（逗號分隔） | `127.0.0.1,localhost` |

### 資料庫（PostgreSQL）

專案預設使用 PostgreSQL，可於 `.env` 調整：

| 變數 | 說明 | 範例 |
|------|------|------|
| `DB_NAME` | 資料庫名稱 | `rtsp_vision` |
| `DB_USER` | 資料庫使用者 | `postgres` |
| `DB_PASSWORD` | 資料庫密碼 | `your_password` |
| `DB_HOST` | 資料庫位址 | `localhost` |
| `DB_PORT` | 資料庫連接埠 | `5432` |

未設定時，開發環境會使用 `settings.py` 中的預設值；正式環境請務必設定 `DJANGO_SECRET_KEY`、正確的 DB 連線資訊，並將 `DJANGO_DEBUG=False`。

---

## 主要功能概觀（目前進度）

### Cameras App

- **Model：`CameraSource`**
  - `device_id`：設備編號（唯一）
  - `name`：攝影機名稱
  - `stream_url`：串流 URL（例如 RTSP）
  - `web_port`：Web 存取埠號
  - `rtsp_port`：RTSP 埠號
  - `cctv_user` / `cctv_pass`：CCTV 登入帳號與密碼（不會在 API 回傳中曝光）
  - `is_enabled`：是否啟用
  - `created_at` / `updated_at`：建立與更新時間

- **API：取得啟用中的攝影機列表**
  - URL：`GET /api/cameras/`
  - 回傳範例：
    ```json
    {
      "code": "success",
      "data": [
        {
          "id": 1,
          "device_id": "CAM001",
          "name": "Front Door",
          "stream_url": "rtsp://example.com/stream1",
          "web_port": 8080,
          "rtsp_port": 554,
          "is_enabled": true
        }
      ]
    }
    ```

---

## Django 管理後台

1. 建立超級使用者：
   ```bash
   uv run manage.py createsuperuser
   ```
2. 啟動伺服器後，於瀏覽器開啟 `http://127.0.0.1:8000/admin/`，以剛建立的帳號登入，即可在後台管理 `CameraSource` 等資料。

---

## 測試

專案使用 Django 的測試框架，並對 `cameras` app 提供最小 API 測試：

```bash
uv run manage.py test cameras
```

