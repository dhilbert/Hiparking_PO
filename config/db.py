import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

# ===================================================
# DB 환경을 선택하는 함수 (env="stage"/"prod")
# ===================================================

def get_db_config(env="stage"):
    env = env.lower().strip()

    if env == "prod":
        host = os.getenv("PROD_DB_HOST")
        port = int(os.getenv("PROD_DB_PORT"))
        user = os.getenv("PROD_DB_USER")
        password = os.getenv("PROD_DB_PASSWORD")
        database = os.getenv("PROD_DB_NAME")
    else:
        host = os.getenv("STAGE_DB_HOST")
        port = int(os.getenv("STAGE_DB_PORT"))
        user = os.getenv("STAGE_DB_USER")
        password = os.getenv("STAGE_DB_PASSWORD")
        database = os.getenv("STAGE_DB_NAME")

    return {
        "host": host,
        "user": user,
        "password": password,
        "database": database,
        "port": port,
        "cursorclass": pymysql.cursors.DictCursor,
        "charset": "utf8mb4"
    }

# ===================================================
# 공통 쿼리 함수
# ===================================================

def query_db(sql, params=None, env="stage"):
    config = get_db_config(env)
    conn = pymysql.connect(**config)

    with conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
