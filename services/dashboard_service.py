# services/dashboard_service.py
from datetime import datetime, timedelta
from config.db_config import run_query


def get_today_card(env="prod"):
    sql = """
        SELECT SUM(amount) AS total
        FROM tb_trade
        WHERE status='PURCHASE_REQUEST'
          AND account_no IS NULL
          AND created_date >= %s
          AND created_date < %s
    """
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    rows = run_query(env, sql, (today, tomorrow))
    return rows[0]["total"] or 0


def get_today_cash(env="prod"):
    sql = """
        SELECT SUM(amount) AS total
        FROM tb_trade
        WHERE status='DEPOSIT_COMPLETED'
          AND account_no IS NOT NULL
          AND created_date >= %s
          AND created_date < %s
    """
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    rows = run_query(env, sql, (today, tomorrow))
    return rows[0]["total"] or 0


def get_yesterday_card(env="prod"):
    sql = """
        SELECT SUM(amount) AS total
        FROM tb_trade
        WHERE status='PURCHASE_REQUEST'
          AND account_no IS NULL
          AND created_date >= %s
          AND created_date < %s
    """
    yesterday = datetime.now().date() - timedelta(days=1)
    today = datetime.now().date()
    rows = run_query(env, sql, (yesterday, today))
    return rows[0]["total"] or 0


def get_yesterday_cash(env="prod"):
    sql = """
        SELECT SUM(amount) AS total
        FROM tb_trade
        WHERE status='DEPOSIT_COMPLETED'
          AND account_no IS NOT NULL
          AND created_date >= %s
          AND created_date < %s
    """
    yesterday = datetime.now().date() - timedelta(days=1)
    today = datetime.now().date()
    rows = run_query(env, sql, (yesterday, today))
    return rows[0]["total"] or 0


def get_dashboard_sales(env="prod"):
    today_total = get_today_card(env) + get_today_cash(env)
    yesterday_total = get_yesterday_card(env) + get_yesterday_cash(env)

    if yesterday_total == 0:
        percent = 100 if today_total > 0 else 0
    else:
        percent = round(((today_total - yesterday_total) / yesterday_total) * 100, 1)

    return {
        "today_sales": today_total,
        "yesterday_sales": yesterday_total,
        "percent": percent,
        "is_up": today_total >= yesterday_total
    }
