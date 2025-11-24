from flask import Flask, render_template, request

app = Flask(__name__)


# =========================================
# HOME PAGE
# =========================================
@app.route("/")
def home():

    data_query = [
        {"title": "통합 데이터 조회", "desc": "모든 데이터를 통합 조회",
         "url": "/dms", "grad_from": "#3b82f6", "grad_to": "#2563eb", "icon": "lucide-database"},

        {"title": "사용자 데이터 조회", "desc": "사용자 관리",
         "url": "/users", "grad_from": "#6366f1", "grad_to": "#4f46e5", "icon": "lucide-users"},

        {"title": "주차장 데이터 조회", "desc": "주차장 정보 조회",
         "url": "/parking", "grad_from": "#a855f7", "grad_to": "#9333ea", "icon": "lucide-car"},
    ]

    analytics = [
        {"title": "통합 분석", "desc": "전사 분석 리포트",
         "url": "/analytics", "grad_from": "#22c55e", "grad_to": "#16a34a", "icon": "lucide-bar-chart"},

        {"title": "트렌드 분석", "desc": "주간/월간 변화 분석",
         "url": "/trend", "grad_from": "#10b981", "grad_to": "#059669", "icon": "lucide-trending-up"},
    ]

    reports = [
        {"title": "통합 리포트", "desc": "전체 보고서",
         "url": "/report", "grad_from": "#ec4899", "grad_to": "#db2777", "icon": "lucide-file-text"},
    ]

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
# DMS 조회 PAGE
# =========================================
@app.route("/dms")
def dms():

    date = request.args.get("date")
    sheet = request.args.get("ordersheet")
    car = request.args.get("carno")

    searched = bool(date or sheet or car)

    # 예시 데이터
    results = []

    if searched:
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
# REPORT PAGE
# =========================================
@app.route("/report")
def report():

    start = request.args.get("start")
    end = request.args.get("end")
    type_ = request.args.get("type")

    searched = bool(start or end or type_)

    results = []

    if searched:
        results = [
            {"날짜": "2025-11-21", "매출": "150,000", "건수": 12},
            {"날짜": "2025-11-22", "매출": "210,000", "건수": 16},
        ]

    return render_template(
        "report.html",
        results=results,
        searched=searched,
        start=start,
        end=end,
        type=type_
    )


# =========================================
# COMPARE PAGE (1G ↔ 2G 비교)
# =========================================
@app.route("/compare", methods=["GET", "POST"])
def compare():

    results = []
    compared = False

    if request.method == "POST":

        file1 = request.files.get("file_1g")
        file2 = request.files.get("file_2g")

        compared = True

        # 예시 데이터 (기존 app8.py 비교 로직 연결하면 됨)
        results = [
            {"항목": "매출", "1G": "150,000", "2G": "150,000", "비고": "일치"},
            {"항목": "건수", "1G": "12", "2G": "11", "비고": "불일치"},
            {"항목": "취소건", "1G": "없음", "2G": "1건", "비고": "불일치"},
        ]

    return render_template(
        "compare.html",
        results=results,
        compared=compared
    )


# =========================================
# LOGS PAGE
# =========================================
@app.route("/logs")
def logs():

    date = request.args.get("date")
    level = request.args.get("level")
    keyword = request.args.get("keyword")

    searched = bool(date or level or keyword)

    logs = []

    if searched:
        logs = [
            {"time": "2025-11-24 03:27:42", "level": "INFO", "message": "라이브 배포 결정"},
            {"time": "2025-11-24 03:30:33", "level": "WARN", "message": "인바운드 해제 지연"},
            {"time": "2025-11-24 03:34:59", "level": "ERROR", "message": "데이터 불일치 발생"},
        ]

    return render_template(
        "logs.html",
        logs=logs,
        searched=searched,
        date=date,
        level=level,
        keyword=keyword
    )

@app.route("/search")
def search():
    q = request.args.get("q")

    if not q:
        return render_template("search.html", q=q, results=[])

    results = [
        {"type": "order", "value": "주문서 0000010H251120000162"},
        {"type": "car",   "value": "차량번호 12가3456"},
        {"type": "user",  "value": "사용자 김수연 책임"},
    ]

    return render_template("search.html", q=q, results=results)




# =========================================
# RUN
# =========================================
if __name__ == "__main__":
    app.run(debug=True, port=5000)
