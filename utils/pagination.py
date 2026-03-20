import math


DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def paginate(queryset, page: int, page_size: int) -> tuple:
    """
    對 QuerySet 做分頁，回傳 (items, pagination_dict)。
    page_size 上限由呼叫端傳入前自行用 MAX_PAGE_SIZE 截斷。
    """
    total = queryset.count()
    total_pages = max(math.ceil(total / page_size), 1)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * page_size
    items = queryset[offset: offset + page_size]
    return items, {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def parse_page_params(query_params) -> tuple[int, int]:
    """從 request.query_params 解析 page / page_size，無效值 fallback 預設值。"""
    try:
        page = int(query_params.get("page", 1))
        page_size = min(int(query_params.get("page_size", DEFAULT_PAGE_SIZE)), MAX_PAGE_SIZE)
    except ValueError:
        page, page_size = 1, DEFAULT_PAGE_SIZE
    return page, page_size
