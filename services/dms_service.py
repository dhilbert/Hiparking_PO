"""
/services/query_executor.py

DB 연결 및 SQL 실행을 담당하는 공통 모듈.
run_query() : SQL을 실행하고 결과를 dict 리스트로 반환하는 함수.
"""

import pymysql
import base64
from config.db_config import get_db_config


def make_json_safe(row: dict):
    """
    bytes 타입 컬럼을 문자열로 변환해 JSON 출력시 오류 방지
    """
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
    """
    주어진 env(PROD/STAGE)에 맞춰 DB 연결 후 SQL 실행하는 함수.
    params가 있으면 자동 바인딩함.
    """
    config = get_db_config(env)

    conn = pymysql.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [make_json_safe(r) for r in rows]

    finally:
        conn.close()
