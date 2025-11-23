"""
/routes/sql_routes.py

SQL 실행 페이지를 제공하며,
사용자가 입력한 SQL을 prod/stage DB에서 실행하고
결과를 표로 출력하거나 엑셀로 다운로드하는 기능을 제공한다.

sql_page()        : SQL 입력 페이지 렌더링
sql_run()         : SQL 실행 후 결과 화면 렌더링
sql_download_excel() : SQL 결과를 엑셀 파일로 다운로드
"""

from flask import Blueprint, render_template, request, send_file
import pandas as pd
from io import BytesIO
from config.db_config import run_query

sql_routes = Blueprint("sql_routes", __name__)


@sql_routes.route("/", methods=["GET"])
def sql_page():
    """SQL 입력 화면 렌더링"""
    return render_template("sql_page.html")


@sql_routes.route("/run", methods=["POST"])
def sql_run():
    """SQL 실행 후 결과 테이블 렌더링"""
    env = request.form.get("env", "prod")
    sql = request.form.get("sql", "").strip()

    if not sql:
        return render_template(
            "result_table.html",
            rows=[],
            env=env,
            sql=sql,
            error_msg="SQL이 비어 있습니다.",
            rows_json="[]"
        )

    try:
        rows = run_query(env, sql)

        return render_template(
            "result_table.html",
            rows=rows,
            env=env,
            sql=sql,
            error_msg=None,
            rows_json=pd.DataFrame(rows).to_json(orient="records")
        )

    except Exception as e:
        return render_template(
            "result_table.html",
            rows=[],
            env=env,
            sql=sql,
            error_msg=str(e),
            rows_json="[]"
        )


@sql_routes.route("/download_excel", methods=["POST"])
def sql_download_excel():
    """SQL 실행 결과를 엑셀 파일로 다운로드"""
    rows_json = request.form.get("rows_json", "")

    if not rows_json:
        return "NO DATA"

    df = pd.read_json(rows_json)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="sql_result.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
