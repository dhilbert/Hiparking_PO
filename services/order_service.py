from config.db import query_db
from utils.json_safe import json_safe

def get_trade(shop_no):
    sql = "SELECT * FROM tb_trade WHERE shop_order_no=%s"
    rows = query_db(sql, (shop_no,))
    return [json_safe(r) for r in rows]

def get_order_sheet(osid):
    sql = "SELECT * FROM tb_business_order_sheet WHERE order_sheet_no=%s"
    rows = query_db(sql, (osid,))
    return [json_safe(r) for r in rows]
