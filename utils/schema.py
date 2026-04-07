"""
Swagger / OpenAPI 文件用常數
僅供 @extend_schema 引用
"""

from drf_spectacular.utils import OpenApiExample

# ── 成功 ──────────────────────────────────────────────
EXAMPLE_200 = OpenApiExample(
    "成功",
    value={"code": "success"},
    response_only=True,
    status_codes=["200"],
)

EXAMPLE_201 = OpenApiExample(
    "建立成功",
    value={"code": "success"},
    response_only=True,
    status_codes=["201"],
)

# ── 用戶端錯誤 ─────────────────────────────────────────
EXAMPLE_401 = OpenApiExample(
    "未認證",
    value={"code": "notAuthorized", "message": "Invalid authentication."},
    response_only=True,
    status_codes=["401"],
)

EXAMPLE_403 = OpenApiExample(
    "無權限",
    value={"code": "notAuthorized", "message": "You are not authorised to execute this."},
    response_only=True,
    status_codes=["403"],
)

EXAMPLE_404 = OpenApiExample(
    "資源不存在",
    value={"code": "notFound", "message": "data not found"},
    response_only=True,
    status_codes=["404"],
)

EXAMPLE_422 = OpenApiExample(
    "欄位驗證失敗",
    value={"code": "missingParameter", "message": "Missing parameters.", "errors": {}},
    response_only=True,
    status_codes=["422"],
)

EXAMPLE_429 = OpenApiExample(
    "請求過於頻繁",
    value={"code": "throttled", "message": "Too many requests. Please try again in 60 seconds."},
    response_only=True,
    status_codes=["429"],
)

# ── 伺服器錯誤 ─────────────────────────────────────────
EXAMPLE_500 = OpenApiExample(
    "伺服器錯誤",
    value={"code": "serverError", "message": "Server error"},
    response_only=True,
    status_codes=["500"],
)
