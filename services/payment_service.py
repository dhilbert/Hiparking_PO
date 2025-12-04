# services/payment_service.py
from datetime import datetime, timedelta
from config.db_config import run_query


# ---------------------------------------------------
# 최근 7일 매출 (카드 + 현금)
# ---------------------------------------------------
def get_daily_sales(env="prod"):
    today = datetime.now().date()
    result = []

    for i in range(7):
        day = today - timedelta(days=6 - i)
        next_day = day + timedelta(days=1)

        # 카드
        sql_card = """
            SELECT SUM(amount) AS total
            FROM tb_trade
            WHERE status='PURCHASE_REQUEST'
              AND account_no IS NULL
              AND created_date >= %s AND created_date < %s
        """

        # 현금
        sql_cash = """
            SELECT SUM(amount) AS total
            FROM tb_trade
            WHERE status='DEPOSIT_COMPLETED'
              AND account_no IS NOT NULL
              AND created_date >= %s AND created_date < %s
        """

        card = run_query(env, sql_card, (day, next_day))[0]["total"] or 0
        cash = run_query(env, sql_cash, (day, next_day))[0]["total"] or 0

        result.append({
            "date": day.strftime("%m/%d"),
            "total": card + cash
        })

    return result


# ---------------------------------------------------
# 결제수단별 매출액 비율
# ---------------------------------------------------
def get_payment_amount(env="prod"):
    sql_card = """
        SELECT SUM(amount) AS total
        FROM tb_trade
        WHERE status='PURCHASE_REQUEST'
          AND account_no IS NULL
    """
    sql_cash = """
        SELECT SUM(amount) AS total
        FROM tb_trade
        WHERE status='DEPOSIT_COMPLETED'
          AND account_no IS NOT NULL
    """

    card = run_query(env, sql_card)[0]["total"] or 0
    cash = run_query(env, sql_cash)[0]["total"] or 0

    return {"card": card, "cash": cash}


# ---------------------------------------------------
# 결제수단별 매출 건수 비율
# ---------------------------------------------------
def get_payment_count(env="prod"):
    sql_card = """
        SELECT COUNT(*) AS cnt
        FROM tb_trade
        WHERE status='PURCHASE_REQUEST'
          AND account_no IS NULL
    """

    sql_cash = """
        SELECT COUNT(*) AS cnt
        FROM tb_trade
        WHERE status='DEPOSIT_COMPLETED'
          AND account_no IS NOT NULL
    """

    card = run_query(env, sql_card)[0]["cnt"] or 0
    cash = run_query(env, sql_cash)[0]["cnt"] or 0

    return {"card": card, "cash": cash}


# ---------------------------------------------------
# 🔥 시간대별 매출액 (카드 + 현금)
# ---------------------------------------------------
def get_hourly_sales(env="prod"):

    # 카드
    sql_card = """
        SELECT HOUR(created_date) AS hr, SUM(amount) AS total
        FROM tb_trade
        WHERE status='PURCHASE_REQUEST'
          AND account_no IS NULL
        GROUP BY HOUR(created_date)
        ORDER BY hr;
    """

    # 현금
    sql_cash = """
        SELECT HOUR(created_date) AS hr, SUM(amount) AS total
        FROM tb_trade
        WHERE status='DEPOSIT_COMPLETED'
          AND account_no IS NOT NULL
        GROUP BY HOUR(created_date)
        ORDER BY hr;
    """

    rows_card = run_query(env, sql_card)
    rows_cash = run_query(env, sql_cash)

    map_card = {r["hr"]: r["total"] for r in rows_card}
    map_cash = {r["hr"]: r["total"] for r in rows_cash}

    result = []
    for h in range(24):
        result.append({
            "hour": h,
            "total": (map_card.get(h, 0) or 0) + (map_cash.get(h, 0) or 0)
        })

    return result


# ---------------------------------------------------
# 🔥 시간대별 매출 횟수 (카드 + 현금)
# ---------------------------------------------------
def get_hourly_sales_count(env="prod"):

    sql_card = """
        SELECT HOUR(created_date) AS hr, COUNT(*) AS cnt
        FROM tb_trade
        WHERE status='PURCHASE_REQUEST'
          AND account_no IS NULL
        GROUP BY HOUR(created_date)
        ORDER BY hr;
    """

    sql_cash = """
        SELECT HOUR(created_date) AS hr, COUNT(*) AS cnt
        FROM tb_trade
        WHERE status='DEPOSIT_COMPLETED'
          AND account_no IS NOT NULL
        GROUP BY HOUR(created_date)
        ORDER BY hr;
    """

    rows_card = run_query(env, sql_card)
    rows_cash = run_query(env, sql_cash)

    map_card = {r["hr"]: r["cnt"] for r in rows_card}
    map_cash = {r["hr"]: r["cnt"] for r in rows_cash}

    result = []
    for h in range(24):
        result.append({
            "hour": h,
            "count": (map_card.get(h, 0) or 0) + (map_cash.get(h, 0) or 0)
        })

    return result
