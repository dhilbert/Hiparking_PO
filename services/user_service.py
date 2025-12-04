# services/user_service.py
from datetime import datetime, timedelta
from config.db_config import run_query


# -----------------------------------------------------
# 오늘 가입자 수
# -----------------------------------------------------
def get_today_users(env="prod"):
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    sql = """
        SELECT COUNT(*) AS cnt
        FROM tb_user
        WHERE created_date >= %s
          AND created_date < %s
    """

    rows = run_query(env, sql, (today, tomorrow))
    return rows[0]["cnt"] or 0


# -----------------------------------------------------
# 어제 가입자 수
# -----------------------------------------------------
def get_yesterday_users(env="prod"):
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    sql = """
        SELECT COUNT(*) AS cnt
        FROM tb_user
        WHERE created_date >= %s
          AND created_date < %s
    """

    rows = run_query(env, sql, (yesterday, today))
    return rows[0]["cnt"] or 0


# -----------------------------------------------------
# 최근 30일 가입자 수 (일자별)
# -----------------------------------------------------
def get_monthly_users(env="prod"):
    today = datetime.now().date()
    result = []

    for i in range(30):
        day = today - timedelta(days=29 - i)
        next_day = day + timedelta(days=1)

        sql = """
            SELECT COUNT(*) AS cnt
            FROM tb_user
            WHERE created_date >= %s
              AND created_date < %s
        """

        rows = run_query(env, sql, (day, next_day))
        count = rows[0]["cnt"] or 0

        result.append({
            "date": day.strftime("%m/%d"),
            "count": count
        })

    return result


# -----------------------------------------------------
# 🔥 시간대별 가입자 수 (0~23시 전체 기간 기준)
# -----------------------------------------------------
def get_hourly_users(env="prod"):
    sql = """
        SELECT HOUR(created_date) AS hr, COUNT(*) AS cnt
        FROM tb_user
        GROUP BY HOUR(created_date)
        ORDER BY hr;
    """

    rows = run_query(env, sql)

    # 0~23시 빠진 시간대 보정
    result = []
    hours = {r["hr"]: r["cnt"] for r in rows}

    for h in range(24):
        result.append({
            "hour": h,
            "count": hours.get(h, 0)
        })

    return result


def get_total_users(env="prod"):
    sql = "SELECT COUNT(*) AS cnt FROM tb_user"
    rows = run_query(env, sql)
    return rows[0]["cnt"] or 0
