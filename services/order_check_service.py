# services/order_check_service.py

import pymysql
import os
import base64
from dotenv import load_dotenv

load_dotenv()

# =============================
# DB 설정
# =============================
DB_STAGE = {
    "host": os.getenv("STAGE_DB_HOST"),
    "port": int(os.getenv("STAGE_DB_PORT")),
    "user": os.getenv("STAGE_DB_USER"),
    "password": os.getenv("STAGE_DB_PASSWORD"),
    "database": os.getenv("STAGE_DB_NAME"),
    "cursorclass": pymysql.cursors.DictCursor,
    "charset": "utf8mb4"
}

DB_PROD = {
    "host": os.getenv("PROD_DB_HOST"),
    "port": int(os.getenv("PROD_DB_PORT")),
    "user": os.getenv("PROD_DB_USER"),
    "password": os.getenv("PROD_DB_PASSWORD"),
    "database": os.getenv("PROD_DB_NAME"),
    "cursorclass": pymysql.cursors.DictCursor,
    "charset": "utf8mb4"
}


# =============================
# 환경 자동 판별
# =============================
def detect_env(raw):
    if not raw:
        return "stage"
    raw = raw.lower()

    if "biz-portal-prod" in raw:
        return "prod"

    if "biz-portal-stage" in raw:
        return "stage"

    return "prod"   # 기본 prod 사용


# =============================
# 안전한 JSON 변환
# =============================
def make_json_safe(row):
    safe = {}
    for k, v in row.items():
        if isinstance(v, bytes):
            try:
                safe[k] = v.decode("utf-8", errors="replace")
            except:
                safe[k] = base64.b64encode(v).decode("utf-8")
        else:
            safe[k] = v
    return safe


# =============================
# DB 조회 공통 함수
# =============================
def query_db(env, sql, params=None):
    config = DB_PROD if env == "prod" else DB_STAGE
    conn = pymysql.connect(**config)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [make_json_safe(r) for r in rows]


# =============================
# UUID 추출
# =============================
def extract_key(raw):
    if not raw:
        return raw

    raw = raw.strip()

    # URL을 그대로 넣었을 때
    if "order/" in raw:
        try:
            return raw.split("order/")[1].split("/")[0]
        except:
            return raw

    return raw


# =============================
# 핵심: 주문 정보 통합 조회
# =============================
def load_data(env, raw_key):
    key = extract_key(raw_key)

    # UUID → OrderSheetID 조회
    if len(key) == 36:
        rows = query_db(env,
            """
            SELECT order_sheet_no
            FROM tb_business_order_sheet
            WHERE business_order_sheet_id = UNHEX(REPLACE(%s, '-', ''));
            """,
            (key,)
        )
        if rows:
            key = rows[0]["order_sheet_no"]

    # vtb_dms_order 조회
    vtb = query_db(
        env,
        """
        SELECT *
        FROM vtb_dms_order
        WHERE TicketID=%s OR OrderSheetID=%s
        ORDER BY ApprovalType DESC;
        """,
        (key, key)
    )

    # 취소 테이블 조회
    cancel = query_db(
        env,
        """
        SELECT *
        FROM vtb_dms_order_cancel
        WHERE TicketID IN (
            SELECT TicketID FROM vtb_dms_order WHERE OrderSheetID=%s
        ) OR TicketID=%s;
        """,
        (key, key)
    )

    # trade 조회
    trade = query_db(
        env,
        """
        SELECT *
        FROM tb_trade
        WHERE shop_order_no=%s;
        """,
        (key,)
    )

    return key, vtb, cancel, trade
