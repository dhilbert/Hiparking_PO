from flask import Flask, render_template, request, jsonify, send_file
from services.query_service import run_sql_query, export_to_excel

app = Flask(__name__)


# =========================================
# HOME PAGE (메뉴 정리됨)
# =========================================
@app.route("/")
def home():

    data_query = [
        {
            "title": "통합 데이터 조회",
            "desc": "모든 데이터를 통합 조회",
            "url": "/dms",
            "grad_from": "#3b82f6",
            "grad_to": "#2563eb",
            "icon": "lucide-database"
        },
        {
            "title": "쿼리 실행",
            "desc": "PROD / STAGE SQL 실행",
            "url": "/query",
            "grad_from": "#ff6b35",
            "grad_to": "#ff8c5a",
            "icon": "lucide-terminal"
        }
    ]

    analytics = []     # 숨김
    reports = []       # 숨김

    return render_template(
        "home.html",
        data_query=data_query,
        analytics=analytics,
        reports=reports
    )


# =========================================
# OUR TEAM PAGE
# =========================================
@app.route("/ours")
def ours():

    leader = {
        "name": "정윤구 PO",
        "role": "PO실 팀장 / 서비스 총괄"
    }

    members = [
        {"name": "윤희동 과장", "role": "기발 & 서비스 기획"},
        {"name": "김수연 과장", "role": "UX/UI & 정책 기획"},
        {"name": "오종승 사원", "role": "기발 & 서비스 기획"},
        {"name": "백지우 사원", "role": "UX/UI"},
        {"name": "김예랑 사원", "role": "UX/UI"}
    ]

    return render_template("ours.html", leader=leader, members=members)


# =========================================
# 통합 데이터 조회 (기존 dms)
# =========================================
@app.route("/dms")
def dms():

    date = request.args.get("date")
    sheet = request.args.get("ordersheet")
    car = request.args.get("carno")

    searched = bool(date or sheet or car)

    results = []

    if searched:
        # 예시 데이터
        results = [
            {
                "OrderSheetID": "0000010H251120000162",
                "CarNo": "12가3456",
                "FromDate": "2025-11-20",
                "ToDate": "2025-11-21",
                "Status": "IN_USE",
                "Price": 15000
            }
        ]

    return render_template(
        "dms.html",
        results=results,
        searched=searched
    )


# =========================================
# 쿼리 실행 PAGE (app1)
# =========================================
@app.route("/query")
def query_page():
    return render_template("query.html")


# SQL 실행 API
@app.route("/query/exec", methods=["POST"])
def query_exec():
    data = request.json
    sql = data.get("sql")
    env = data.get("env", "prod")

    try:
        rows = run_sql_query(sql, env)
        return jsonify({"result": "OK", "rows": rows})
    except Exception as e:
        return jsonify({"result": "ERROR", "message": str(e)})


# SQL 엑셀 다운로드
@app.route("/query/download", methods=["POST"])
def query_download():
    data = request.json
    sql = data.get("sql")
    env = data.get("env", "prod")

    output = export_to_excel(sql, env)

    return send_file(
        output,
        as_attachment=True,
        download_name="query_result.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )



# =========================================
# RUN
# =========================================
if __name__ == "__main__":
    app.run(debug=True, port=5002)
