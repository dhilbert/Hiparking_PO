from flask import Flask, render_template, request, jsonify, send_file

# ============================
# QUERY
# ============================
from services.query_service import run_sql_query, export_to_excel

# ============================
# KPI — 매출
# ============================
from services.dashboard_service import get_dashboard_sales

# ============================
# 결제 분석
# ============================
from services.payment_service import (
    get_daily_sales,
    get_payment_amount,
    get_payment_count,
    get_hourly_sales,
    get_hourly_sales_count
)

# ============================
# 가입자 분석
# ============================
from services.user_service import (
    get_today_users,
    get_yesterday_users,
    get_monthly_users,
    get_hourly_users,
    get_total_users
)

# ============================
# 차량번호 → 주문서 조회
# ============================
from services.car_service import find_orders_by_car

# ============================
# 정기권 환불 계산기
# ============================
from routes.refund_routes import refund_routes

# ============================
# 주문 통합 조회 기능
# ============================
from routes.order_check_routes import order_check_routes



# =========================================
# Flask App 생성 (★ Blueprint보다 반드시 먼저!)
# =========================================
app = Flask(__name__)


# =========================================
# Blueprint 등록 (★ app 생성 이후!)
# =========================================
app.register_blueprint(refund_routes)
app.register_blueprint(order_check_routes)



# =========================================
# HOME PAGE
# =========================================
@app.route("/")
def home():

    # ----------------------
    # 1) 매출 KPI
    # ----------------------
    sales = get_dashboard_sales("prod")

    # ----------------------
    # 2) 오늘 / 어제 가입자 수
    # ----------------------
    today_users = get_today_users("prod")
    yesterday_users = get_yesterday_users("prod")

    if yesterday_users == 0:
        user_percent = 100 if today_users > 0 else 0
    else:
        user_percent = round(((today_users - yesterday_users) / yesterday_users) * 100, 1)

    user_kpi = {
        "today": today_users,
        "yesterday": yesterday_users,
        "percent": user_percent,
        "is_up": today_users >= yesterday_users
    }

    # ----------------------
    # 3) 총 사용자 수 KPI
    # ----------------------
    total_users = get_total_users("prod")

    user_total_kpi = {
        "total": total_users,
        "delta": today_users,
        "is_up": today_users > 0
    }

    # ----------------------
    # 4) 메뉴 (좌측)
    # ----------------------
    data_query = [

        {
            "title": "쿼리 실행",
            "desc": "PROD / STAGE SQL 실행",
            "url": "/query",
            "grad_from": "#ff6b35",
            "grad_to": "#ff8c5a",
            "icon": "lucide-terminal"
        },
        {
            "title": "차량번호 주문서 조회",
            "desc": "차량번호로 비즈 주문서 자동 검색",
            "url": "/car-search",
            "grad_from": "#10b981",
            "grad_to": "#059669",
            "icon": "lucide-car"
        },
        {
            "title": "정기권 환불 계산",
            "desc": "요금표 기반 자동 환불 산정",
            "url": "/refund",
            "grad_from": "#6366f1",
            "grad_to": "#4f46e5",
            "icon": "lucide-calculator"
        },
        {
            "title": "주문 통합 조회",
            "desc": "vtb / cancel / trade 전체 조회",
            "url": "/order-check",
            "grad_from": "#8b5cf6",
            "grad_to": "#7c3aed",
            "icon": "lucide-search"
        }
    ]

    # ----------------------
    # 5) 분석 메뉴 (우측)
    # ----------------------
    analytics = [
        {
            "title": "결제액 분석",
            "desc": "최근 7일 + 결제수단 + 시간대 분석",
            "url": "/payment-analytics",
            "grad_from": "#ff9f43",
            "grad_to": "#ff6f00",
            "icon": "lucide-pie-chart"
        },
        {
            "title": "가입자 분석",
            "desc": "최근 30일 + 시간대 분석",
            "url": "/user-analytics",
            "grad_from": "#00c6ff",
            "grad_to": "#0072ff",
            "icon": "lucide-users"
        }
    ]

    return render_template(
        "home.html",
        data_query=data_query,
        analytics=analytics,
        reports=[],
        sales=sales,
        user_kpi=user_kpi,
        user_total_kpi=user_total_kpi
    )



# =========================================
# 차량번호로 주문서 조회
# =========================================
@app.route("/car-search")
def car_search():
    car_no = request.args.get("carno")

    results = []
    searched = False

    if car_no:
        searched = True
        results = find_orders_by_car(car_no)

    return render_template(
        "car_search.html",
        results=results,
        searched=searched
    )



# =========================================
# 가입자 분석 페이지
# =========================================
@app.route("/user-analytics")
def user_analytics():

    month_users = get_monthly_users("prod")
    hourly_users = get_hourly_users("prod")

    return render_template(
        "user_analytics.html",
        month_users=month_users,
        hourly_users=hourly_users
    )



# =========================================
# 결제 분석 페이지
# =========================================
@app.route("/payment-analytics")
def payment_analytics():

    daily = get_daily_sales("prod")
    amount = get_payment_amount("prod")
    count = get_payment_count("prod")
    hourly_sales = get_hourly_sales("prod")
    hourly_count = get_hourly_sales_count("prod")

    return render_template(
        "payment_analytics.html",
        daily=daily,
        amount=amount,
        count=count,
        hourly_sales=hourly_sales,
        hourly_count=hourly_count
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
# DMS
# =========================================
@app.route("/dms")
def dms():

    date = request.args.get("date")
    sheet = request.args.get("ordersheet")
    car = request.args.get("carno")

    searched = bool(date or sheet or car)
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

    return render_template("dms.html", results=results, searched=searched)



# =========================================
# QUERY 실행
# =========================================
@app.route("/query")
def query_page():
    return render_template("query.html")


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
    app.run(debug=True, port=5010)
