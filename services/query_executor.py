import pymysql
from config.db_config import get_db_config
import base64

def make_json_safe(row):
    safe = {}
    for k, v in row.items():
        if isinstance(v, bytes):
            try:
                safe[k] = v.decode("utf-8")
            except:
                safe[k] = base64.b64encode(v).decode("utf-8")
        else:
            safe[k] = v
    return safe

def run_query(env, sql, params=None):
    config = get_db_config(env)
    conn = pymysql.connect(**config, cursorclass=pymysql.cursors.DictCursor)

    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [make_json_safe(r) for r in rows]
    finally:
        conn.close()
