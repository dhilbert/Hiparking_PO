from config.db import query_db
from utils.json_safe import json_safe

def report_by_date(start, end):
    sql = """
        SELECT *
        FROM tb_business_order_sheet
        WHERE last_modified_date BETWEEN %s AND %s
    """
    rows = query_db(sql, (f"{start} 00:00:00", f"{end} 23:59:59"))
    return [json_safe(r) for r in rows]
