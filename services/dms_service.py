from config.db import query_db
from utils.json_safe import json_safe

def get_dms_by_date(start, end):
    sql = """
        SELECT *
        FROM vtb_dms_order
        WHERE LastModifiedDate BETWEEN %s AND %s
        ORDER BY ApprovalType DESC
    """
    rows = query_db(sql, (f"{start} 00:00:00", f"{end} 23:59:59"))
    return [json_safe(r) for r in rows]


def get_dms_cancel_by_ordersheet(osid):
    sql = """
        SELECT *
        FROM vtb_dms_order_cancel
        WHERE TicketID IN (
            SELECT TicketID FROM vtb_dms_order WHERE OrderSheetID = %s
        )
    """
    rows = query_db(sql, (osid,))
    return [json_safe(r) for r in rows]
