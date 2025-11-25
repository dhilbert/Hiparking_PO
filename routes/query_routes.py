from flask import Blueprint, request, jsonify, send_file, render_template
from services.query_service import run_sql_query, export_to_excel
from datetime import datetime

query_bp = Blueprint("query", __name__)

# -----------------------------
# 쿼리 실행 페이지
# -----------------------------
@query_bp.route("/query-run")
def query_run_page():
    return render_template("query.html")


# -----------------------------
# SQL 실행 API
# -----------------------------
@query_bp.route("/query-run/exec", methods=["POST"])
def exec_sql():
    data = request.json
    sql = data.get("sql")
    env = data.get("env", "prod")   # prod / stage

    try:
        rows = run_sql_query(sql, env)
        return jsonify({"result": "OK", "rows": rows})
    except Exception as e:
        return jsonify({"result": "ERROR", "message": str(e)})


# -----------------------------
# 엑셀 다운로드
# -----------------------------
@query_bp.route("/query-run/download", methods=["POST"])
def download_sql_excel():
    data = request.json
    sql = data.get("sql")
    env = data.get("env", "prod")

    output = export_to_excel(sql, env)
    filename = f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
