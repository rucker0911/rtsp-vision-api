---
name: add-crud-api
description: >-
  Guides adding a new CRUD API to this Django + DRF project following project conventions.
  Use when the user asks to add a new API, create a new endpoint, implement CRUD operations,
  add a new resource, or build a new Django app with REST APIs.
---

# 新增 CRUD API

依照以下 6 個步驟實作，每步完成後在 checklist 打勾。

## 開始前確認

向使用者確認：
1. **資源名稱**（例：`Camera`, `Device`）
2. **欄位清單**與型別
3. **需要哪些操作**：List / Upsert / Delete（或其子集）
4. **有無特殊驗證規則**（例：port 範圍、唯一鍵）

---

## 執行 Checklist

```
- [ ] Step 1: models.py — 欄位定義，執行 migration
- [ ] Step 2: serializers.py — Read / Write Serializer 分離
- [ ] Step 3: views.py — APIView + @extend_schema + response_with()
- [ ] Step 4: urls.py — app 路由 + config/urls.py include
- [ ] Step 5: tests.py — 四種情境測試
- [ ] Step 6: Swagger UI — 確認文件正確
```

---

## Step 1 — Model

檔案：`{app}/models.py`

- 所有欄位使用 **snake_case**
- 必備通用欄位：`is_enabled`, `created_at`, `updated_at`
- 完成後執行：
  ```bash
  uv run manage.py makemigrations
  uv run manage.py migrate
  ```

---

## Step 2 — Serializer

檔案：`{app}/serializers.py`

| Serializer | 用途 | 命名 |
|------------|------|------|
| Read | GET 回傳，不含敏感欄位 | `{Model}Serializer` |
| Write | POST 輸入驗證，含所有欄位 | `{Model}WriteSerializer` |

- 有範圍限制的欄位用 `serializers.IntegerField(min_value=..., max_value=...)`
- 有預設值的欄位用 `extra_kwargs = {"field": {"default": ...}}`

---

## Step 3 — View

檔案：`{app}/views.py`

**規則：**
- 繼承 `APIView`，每個 HTTP method 一個 method
- 每個 method 加 `@extend_schema(summary=..., description=..., request=..., responses=...)`
- 所有回應透過 `utils/responses.py` 的 `response_with()` 處理

**選擇 DB 操作方式（依場景）：**

| 場景 | 方式 |
|------|------|
| 簡單 CRUD | Django ORM |
| 複雜查詢（多表 JOIN）| 原生 SQL + `utils/sqlBuild.py`，`cursor.execute(sql, params)` |
| 需要聚合 / 統計 | 原生 SQL + Pandas |

**Upsert 標準邏輯：**
```python
instance = Model.objects.filter(unique_key=value).first()
if instance:                              # 更新 → 200
    serializer = WriteSerializer(instance, data=request.data, partial=True)
else:                                     # 新增 → 201
    serializer = WriteSerializer(data=request.data)

if not serializer.is_valid():
    return response_with(MISSING_PARAMETERS_422, error=serializer.errors)
serializer.save()
return response_with(SUCCESS_200 or SUCCESS_201)
```

**可用回應常數（`utils/responses.py`）：**

| 情境 | 常數 | HTTP |
|------|------|------|
| 查詢成功 | `SUCCESS_200` | 200 |
| 新增成功 | `SUCCESS_201` | 201 |
| 欄位驗證失敗 | `MISSING_PARAMETERS_422` | 422 |
| 業務邏輯錯誤 | `INVALID_INPUT_422` | 422 |
| 資源不存在 | `NOT_FOUND_404` | 404 |

---

## Step 4 — 路由

`{app}/urls.py`：
```python
urlpatterns = [
    path("", {Model}ListView.as_view(), name="api-{resource}-list"),
    path("create/", {Model}UpsertView.as_view(), name="api-{resource}-create"),
    path("<int:pk>/delete/", {Model}DeleteView.as_view(), name="api-{resource}-delete"),
]
```

`config/urls.py` 加入：
```python
path("api/{resource}/", include("{app}.urls")),
```

---

## Step 5 — 測試

檔案：`{app}/tests.py`，繼承 `rest_framework.test.APITestCase`

每支 API 必須覆蓋：

| 情境 | 驗證 |
|------|------|
| 正常成功 | HTTP status、`code == "success"`、DB 狀態 |
| 欄位驗證失敗 | HTTP 422、`code == "missingParameter"` |
| 資源不存在（DELETE）| HTTP 404、`code == "notFound"` |
| Upsert 更新 | HTTP 200、DB 資料確認已更新 |

- 共用測試資料抽成模組頂層常數：`VALID_PAYLOAD = {...}`
- 按操作類型分 `TestCase` class：`{Model}ListApiTests`, `{Model}CreateApiTests`

執行：
```bash
uv run manage.py test {app}
```

---

## Step 6 — Swagger 驗證

開啟 `http://127.0.0.1:8000/api/schema/swagger-ui/` 確認：
- [ ] 路由正確顯示
- [ ] `summary` / `description` 正確
- [ ] Request Body schema 正確
- [ ] Response schema 正確

---

## 詳細範例參考

完整程式碼範例請參閱 [step.md](../../../../step.md)
