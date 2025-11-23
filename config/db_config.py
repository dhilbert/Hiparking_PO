"""
/config/db_config.py

DB 접속 정보를 환경(stage·prod)에 따라 반환하고,
run_query() 로 SQL을 실행하는 공통 DB 유틸리티 파일.
"""

import os
import pymysql
from dotenv import load_dotenv

load_dotenv()


def get_db_config(env):
    """환경명(stage/prod)에 따라 DB 접속 정보를 반환한다."""
    if env == "prod":
        return {
            "host": os.getenv("PROD_DB_HOST"),
            "port": int(os.getenv("PROD_DB_PORT")),
            "user": os.getenv("PROD_DB_USER"),
            "password": os.getenv("PROD_DB_PASSWORD"),
            "database": os.getenv("PROD_DB_NAME"),
            "cursorclass": pymysql.cursors.DictCursor,
            "charset": "utf8mb4"
        }

    # 기본 stage
    return {
        "host": os.getenv("STAGE_DB_HOST"),
        "port": int(os.getenv("STAGE_DB_PORT")),
        "user": os.getenv("STAGE_DB_USER"),
        "password": os.getenv("STAGE_DB_PASSWORD"),
        "database": os.getenv("STAGE_DB_NAME"),
        "cursorclass": pymysql.cursors.DictCursor,
        "charset": "utf8mb4"
    }


def make_json_safe(row):
    """bytes 타입 컬럼은 UTF-8 또는 base64 문자열로 변환한다."""
    import base64
    safe = {}
    for k, v in row.items():
        if isinstance(v, bytes):
            try:
                safe[k] = v.decode("utf-8", errors="ignore")
            except:
                safe[k] = base64.b64encode(v).decode("utf-8")
        else:
            safe[k] = v
    return safe


def run_query(env, sql, params=None):
    """DB 연결 후 SQL 실행하고 결과 rows 리스트(딕셔너리)를 반환한다."""
    cfg = get_db_config(env)

    conn = pymysql.connect(**cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [make_json_safe(r) for r in rows]
    finally:
        conn.close()
