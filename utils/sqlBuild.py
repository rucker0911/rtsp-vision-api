"""
SQL query builder — 所有函式回傳 (sql: str, params: list)。
使用方式：
    sql, params = sql_select(...)
    cursor.execute(sql, params)
"""


def sql_select(
        table: str,
        where_dict: dict,
        columns: str,
        update_column: str | None = None,
    ) -> tuple[str, list]:
    """
    建立 SELECT 查詢。
    支援一般欄位等值條件、時間範圍（startTime / endTime）、
    以及 {"$gte": ..., "$lt": ...} 範圍條件。
    """
    conditions = []
    params = []

    start_time = where_dict.get("startTime")
    end_time = where_dict.get("endTime")
    if start_time and end_time and update_column is not None:
        conditions.append(f"{update_column} BETWEEN %s AND %s")
        params.extend([start_time, end_time])

    for k, v in where_dict.items():
        if k in ("startTime", "endTime"):
            continue
        if isinstance(v, dict) and "$gte" in v and "$lt" in v:
            conditions.append(f"{k} BETWEEN %s AND %s")
            params.extend([v["$gte"], v["$lt"]])
        else:
            conditions.append(f"{k} = %s")
            params.append(v)

    where_str = " AND ".join(conditions)
    sql = f"SELECT {columns} FROM {table} WHERE {where_str}"
    return sql, params


def sql_select_desc(
        table: str,
        where_dict: dict,
        columns: str,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> tuple[str, list]:
    """建立帶有 ORDER BY DESC 與 LIMIT 的 SELECT 查詢。"""
    conditions = []
    params = []

    for k, v in where_dict.items():
        conditions.append(f"{k} = %s")
        params.append(v)

    sql = f"SELECT {columns} FROM {table}"
    if conditions:
        sql += f" WHERE {' AND '.join(conditions)}"
    if order_by:
        sql += f" ORDER BY {order_by} DESC"
    if limit is not None:
        sql += f" LIMIT {limit}"

    return sql, params


def sql_insert(table: str, insert_dict: dict) -> tuple[str, list]:
    """建立 INSERT 查詢。"""
    keys = ", ".join(insert_dict.keys())
    placeholders = ", ".join(["%s"] * len(insert_dict))
    params = list(insert_dict.values())
    sql = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
    return sql, params


def sql_update(
    table: str,
    where_dict: dict,
    update_dict: dict,
) -> tuple[str, list]:
    """建立 UPDATE 查詢。"""
    set_clauses = [f"{k} = %s" for k in update_dict]
    where_clauses = [f"{k} = %s" for k in where_dict]
    params = list(update_dict.values()) + list(where_dict.values())
    sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
    return sql, params


def sql_delete(table: str, where_dict: dict) -> tuple[str, list]:
    """建立 DELETE 查詢。"""
    where_clauses = [f"{k} = %s" for k in where_dict]
    params = list(where_dict.values())
    sql = f"DELETE FROM {table} WHERE {' AND '.join(where_clauses)}"
    return sql, params


def sql_upsert(
        table: str,
        insert_dict: dict,
        conflict_columns: list[str],
        update_dict: dict,
    ) -> tuple[str, list]:
    """
    建立 INSERT ... ON CONFLICT DO UPDATE 查詢（upsert）。
    conflict_columns：用於衝突判斷的欄位清單。
    update_dict：衝突時要更新的欄位與值。
    """
    keys = ", ".join(insert_dict.keys())
    placeholders = ", ".join(["%s"] * len(insert_dict))
    conflict_str = ", ".join(conflict_columns)
    update_clauses = [f"{k} = EXCLUDED.{k}" for k in update_dict]
    params = list(insert_dict.values())

    sql = (
        f"INSERT INTO {table} ({keys}) VALUES ({placeholders}) "
        f"ON CONFLICT ({conflict_str}) DO UPDATE SET {', '.join(update_clauses)}"
    )
    return sql, params
