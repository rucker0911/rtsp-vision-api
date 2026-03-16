def sql_insert(table, insertDict):
    iKeysStr = ','.join(insertDict.keys())
    iValuesStr = ','.join(f"'{str(x)}'" if isinstance(
        x, str) else str(x) for x in insertDict.values())
    sqlStr = f'''INSERT INTO {table} ({iKeysStr}) VALUES ({iValuesStr})'''
    return sqlStr


def sql_update(table, whereDict, updateDict):
    updateSetList = []
    for k, v in updateDict.items():
        if isinstance(v, str):
            updateSetList.append(f"{k}='{v}'")
        else:
            updateSetList.append(f"{k}='{v}'")
    updateSetStr = ', '.join(updateSetList)

    whereList = []
    for k, v in whereDict.items():
        if isinstance(v, str):
            whereList.append(f"{k}='{v}'")
        else:
            whereList.append(f"{k}='{v}'")
    whereSetStr = ' AND '.join(whereList)

    sqlStr = f"UPDATE {table} SET {updateSetStr} WHERE {whereSetStr}"
    return sqlStr


def sql_delete(table, whereDict):
    deleteSetList = []
    for k, v in whereDict.items():
        if isinstance(v, str):
            deleteSetList.append(f"{k}='{v}'")
        else:
            deleteSetList.append(f"{k}='{v}'")
    whereStr = ' AND '.join(deleteSetList)
    sqlStr = f'''DELETE FROM {table} WHERE {whereStr}'''
    return sqlStr


def sql_insert_if_not_exists(table, insertDict, conflictColumns, updateDict):
    updateSetList = []
    for k, v in updateDict.items():
        updateSetList.append(f"{k} = EXCLUDED.{k}")
    updateSetStr = ', '.join(updateSetList)

    iKeysStr = ', '.join(insertDict.keys())
    iValuesStr = ", ".join(f"'{str(x)}'" if isinstance(
        x, str) else str(x) for x in insertDict.values())

    sqlStr = f'''
        INSERT INTO {table} ({iKeysStr}) VALUES ({iValuesStr})
        ON CONFLICT ({conflictColumns}) DO UPDATE SET {updateSetStr}
    '''
    return sqlStr


# def sql_select(table, whereDict, columns):
#     whereSetList = []
#     for k, v in whereDict.items():
#         if isinstance(v, str):
#             whereSetList.append(f"{k}='{v}'")
#         elif isinstance(v, dict) and "$gte" in v and "$lt" in v:
#             whereSetList.append(f"{k} BETWEEN '{v['$gte']}' AND '{v['$lt']}'")
#         else:
#             whereSetList.append(f"{k}='{v}'")
#     whereStr = ' AND '.join(whereSetList)
#     sqlStr = f'''SELECT {columns} FROM {table} WHERE {whereStr}'''
#     return sqlStr

def sql_select(table, whereDict, columns, update_column=None):
    whereSetList = []
    start_time = whereDict.pop("startTime", None)
    end_time = whereDict.pop("endTime", None)

    if start_time and end_time and update_column != None:
        whereSetList.append(f"{update_column} BETWEEN '{start_time}' AND '{end_time}'")
    for k, v in whereDict.items():
        if isinstance(v, str):
            whereSetList.append(f"{k}='{v}'")
        elif isinstance(v, dict) and "$gte" in v and "$lt" in v:
            whereSetList.append(f"{k} BETWEEN '{v['$gte']}' AND '{v['$lt']}'")
        else:
            whereSetList.append(f"{k}='{v}'")
    
    whereStr = ' AND '.join(whereSetList)
    sqlStr = f'''SELECT {columns} FROM {table} WHERE {whereStr}'''
    return sqlStr

def sql_select_DESC(table, whereDict, columns, orderBy=None, limit=None):
    whereSetList = []
    for k, v in whereDict.items():
        if isinstance(v, str):
            whereSetList.append(f"{k}='{v}'")
        else:
            whereSetList.append(f"{k}={v}")
    whereStr = ' AND '.join(whereSetList)

    sqlStr = f'''SELECT {columns} FROM {table}'''
    if whereStr:
        sqlStr += f' WHERE {whereStr}'
    if orderBy:
        sqlStr += f' ORDER BY {orderBy} DESC'
    if limit:
        sqlStr += f' LIMIT {limit}'

    return sqlStr

def sql_insert_if_not_exist(table, insert_dict, where_list, update_dict):
    # 生成更新的 SQL 語句
    update_set_list = []
    for k, v in update_dict.items():
        update_set_list.append(f'"{k}"=\'{v}\'')  # 用雙引號包裹欄位名
    update_set_str = ', '.join(update_set_list)

    # 生成插入的 SQL 語句
    i_keys_str = ', '.join(f'"{key}"' for key in insert_dict.keys())
    i_values_str = "'" + "','".join(str(x) for x in insert_dict.values()) + "'"

    # 生成 ON CONFLICT 子句
    on_str = ', '.join(f'"{key}"' for key in where_list)

    # 組合成最終的 SQL 語句
    sql_str = f"""
        INSERT INTO {table} ({i_keys_str}) 
        VALUES ({i_values_str}) 
        ON CONFLICT ({on_str}) 
        DO UPDATE SET {update_set_str};
    """
    return sql_str

