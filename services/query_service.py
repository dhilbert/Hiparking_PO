import pandas as pd
import base64
import re
from io import BytesIO
from config.db_config import run_query

# 엑셀에서 불가능한 문자 제거
ILLEGAL_RE = re.compile(r"[\x00-\x08\x0B-\x1F\x7F]")

def clean_excel_value(v):
    if isinstance(v, str):
        return ILLEGAL_RE.sub("", v)
    return v


def make_json_safe(row):
    safe = {}
    for k, v in row.items():
        if isinstance(v, bytes):
            try:
                v = v.decode("utf-8", errors="replace")
            except:
                v = base64.b64encode(v).decode("utf-8")

        safe[k] = clean_excel_value(v)
    return safe


# ================================
# SET 문 자동 처리 + 여러 SELECT 결과 모두 반환
# ================================
def run_sql_query(sql: str, env: str):

    stmts = [s.strip() for s in sql.split(";") if s.strip()]

    session_vars = {}
    all_results = []

    for stmt in stmts:

        # SET 처리
        if stmt.lower().startswith("set "):
            m = re.match(r"set\s+(@\w+)\s*=\s*(.*)", stmt, re.IGNORECASE)
            if m:
                var_name = m.group(1).strip()
                raw_value = m.group(2).strip()

                if (raw_value.startswith("'") and raw_value.endswith("'")) or \
                   (raw_value.startswith('"') and raw_value.endswith('"')):
                    raw_value = raw_value[1:-1]

                session_vars[var_name] = raw_value
            continue

        # SELECT 문 처리
        processed_sql = stmt

        # 변수 치환
        for k, v in session_vars.items():
            processed_sql = processed_sql.replace(k, f"'{v}'")

        # 실행
        rows = run_query(env, processed_sql)
        result = [make_json_safe(r) for r in rows]

        all_results.append({
            "sql": processed_sql,
            "rows": result
        })

    return all_results   # 여러 결과 반환


# ================================
# 여러 개 SELECT → 시트 여러개 생성
# ================================
def export_to_excel(sql: str, env: str):

    results = run_sql_query(sql, env)
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for idx, item in enumerate(results):
            df = pd.DataFrame(item["rows"])
            if df.empty:
                df = pd.DataFrame({"message": ["데이터 없음"]})

            df.to_excel(writer, sheet_name=f"result_{idx+1}", index=False)

    output.seek(0)
    return output
