import pymysql
import os
from dotenv import load_dotenv
load_dotenv()

config = {
    "host": os.getenv("PROD_DB_HOST"),
    "user": os.getenv("PROD_DB_USER"),
    "password": os.getenv("PROD_DB_PASSWORD"),
    "database": os.getenv("PROD_DB_NAME"),
    "port": int(os.getenv("PROD_DB_PORT")),
}

try:
    conn = pymysql.connect(
        host=config["host"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        port=config["port"],
    )
    print("✅ PROD DB 접속 성공!")
    conn.close()
except Exception as e:
    print("❌ PROD DB 접속 실패")
    print(e)
