import os
import pymysql
import base64
import pandas as pd
from datetime import datetime
from io import BytesIO
from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
from dotenv import load_dotenv

# =========================================
# LOAD ENV
# =========================================
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# =========================================
# DB CONFIG
# =========================================
DB_PROD = {
    "host": os.getenv("PROD_DB_HOST"),
    "port": int(os.getenv("PROD_DB_PORT")),
    "user": os.getenv("PROD_DB_USER"),
    "password": os.getenv("PROD_DB_PASSWORD"),
    "database": os.getenv("PROD_DB_NAME"),
    "cursorclass": pymysql.cursors.DictCursor,
    "charset": "utf8mb4"
}

# =========================================
# STATUS NAME MAPPING
# =========================================
STATUS_NAME_MAP = {
    "CREATION_PENDING": "생성대기",
    "CREATION_CANCEL": "생성취소",
    "PENDING": "예약대기",
    "RESERVED": "예약완료",
    "IN_USE": "이용중",
    "FINISHED": "이용종료",
    "CANCEL_REQUESTED": "취소접수",
    "CANCEL_ON_HOLD": "취소보류",
    "CANCEL_COMPLETED": "취소완료",
    "PAYMENT_PENDING": "결제보류",
    "PAYMENT_FAILED": "결제실패",
}

def convert_status(code):
    if not code:
        return ""
    return STATUS_NAME_MAP.get(code, code)

# =========================================
# PAYMENT METHOD MAPPING
# =========================================
PAY_METHOD_MAP = {
    "CARD": "카드",
    "VIRTUAL_ACCT": "일회성 가상계좌",
    "FIXED_ACCT": "고정 가상계좌",
    "NO_PAYMENT": "무료"
}

def convert_payment_method(code):
    if not code:
        return ""
    return PAY_METHOD_MAP.get(code, code)

# =========================================
# JSON SAFE
# =========================================
def make_json_safe(row):
    safe = {}
    for k, v in row.items():
        if isinstance(v, bytes):
            try:
                safe[k] = v.decode("utf-8", errors="replace")
            except:
                safe[k] = base64.b64encode(v).decode("utf-8")
        else:
            safe[k] = v
    return safe

# =========================================
# QUERY FUNCTION
# =========================================
def query_db(sql, params):
    conn = pymysql.connect(**DB_PROD)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return [make_json_safe(r) for r in cursor.fetchall()]

# =========================================
# SQL_MAIN
# =========================================
SQL_MAIN = """
SELECT 
    tpl.`name` AS "주차장명",
    tbd.company_name AS "디비전명",

    CASE
        WHEN tbos.payment_method = 'CARD' THEN ttb.last_modified_date
        WHEN tbos.payment_method = 'VIRTUAL_ACCT' THEN ttb.deposit_at
        WHEN tbos.payment_method = 'FIXED_ACCT' THEN tbos.order_requested_at
        WHEN tbos.payment_method = 'NO_PAYMENT' THEN tbos.order_requested_at
        ELSE NULL
    END AS "일시",

    tp.`name` AS "상품명",
    tbos.order_sheet_no,
    tbos.order_status,
    tbos.payment_method AS "결제방식",
    ttb.acquirer_name AS "매입사",
    ttb.approval_no AS "카드승인번호",
    ttb.card_no AS "카드번호",
    ttb.res_msg AS "PG결과",
    ttb.cash_auth_no AS "무통장입금승인번호",
    ttb.account_no AS "무통장계좌번호"

FROM tb_business_order_sheet AS tbos
    LEFT JOIN rtb_business_division_product_mapping AS rbdpm
        ON tbos.business_division_product_mapping_seq = rbdpm.business_division_product_mapping_seq
    JOIN tb_product AS tp
        ON tp.product_seq = rbdpm.product_seq
    JOIN tb_parking_lot AS tpl
        ON tpl.parking_lot_seq = tp.parking_lot_seq
    JOIN tb_business_division AS tbd
        ON tbd.division_seq = rbdpm.division_seq
    LEFT JOIN tb_trade AS ttb
        ON ttb.business_order_sheet_seq = tbos.business_order_sheet_seq

WHERE tbos.last_modified_date
BETWEEN %s AND %s;
"""

# =========================================
# LOAD DATA
# =========================================
def load_data(start_date, end_date):
    rows = query_db(SQL_MAIN, (start_date, end_date))
    for r in rows:
        r["order_status"] = convert_status(r.get("order_status"))
        r["결제방식"] = convert_payment_method(r.get("결제방식"))
    return rows

# =========================================
# HOME PAGE
# =========================================
@app.route("/")
def home():
    today = datetime.now().strftime("%Y-%m-%d")

    return render_template_string("""
    {% extends "layout.html" %}
    {% block content %}

    <h2>일시 기준 조회 (PROD)</h2>

    <label>시작일</label>
    <input type="date" id="startDate" value="{{today}}">

    <label>종료일</label>
    <input type="date" id="endDate" value="{{today}}">

    <button class="btn-run" onclick="search()">조회</button>
    <button class="btn-run" onclick="downloadExcel()">엑셀 다운로드</button>

    <div id="loading" style="display:none;margin-top:15px;">⏳ 로딩중...</div>
    <div id="results" style="margin-top:20px;"></div>

    <script>
    let lastStart = "";
    let lastEnd = "";

    function toTable(rows) {
        if (!rows || rows.length === 0) return "<p>데이터 없음</p>";

        let keys = Object.keys(rows[0]);
        let header = keys.map(k => `<th>${k}</th>`).join("");
        let body = rows.map(r => {
            return "<tr>" + keys.map(k => `<td>${r[k] ?? ""}</td>`).join("") + "</tr>";
        }).join("");

        return `
            <table>
                <thead><tr>${header}</tr></thead>
                <tbody>${body}</tbody>
            </table>
        `;
    }

    function search() {
        const start = document.getElementById("startDate").value;
        const end = document.getElementById("endDate").value;

        if (!start || !end) {
            alert("날짜 입력하셈");
            return;
        }

        lastStart = start;
        lastEnd = end;

        document.getElementById("loading").style.display = "block";
        document.getElementById("results").innerHTML = "";

        fetch(`/query?start=${start}&end=${end}`)
            .then(res => res.json())
            .then(data => {
                document.getElementById("results").innerHTML = toTable(data.rows);
            })
            .finally(() => {
                document.getElementById("loading").style.display = "none";
            });
    }

    function downloadExcel() {
        if (!lastStart || !lastEnd) {
            alert("조회 먼저 하셈");
            return;
        }
        window.location.href = `/download-excel?start=${lastStart}&end=${lastEnd}`;
    }
    </script>

    {% endblock %}
    """, today=today)

# =========================================
# QUERY API
# =========================================
@app.route("/query")
def query_api():
    start = request.args.get("start")
    end = request.args.get("end")

    start_dt = f"{start} 00:00:00"
    end_dt = f"{end} 23:59:59"

    rows = load_data(start_dt, end_dt)
    return jsonify({"rows": rows})

# =========================================
# EXCEL DOWNLOAD
# =========================================
@app.route("/download-excel")
def download_excel():
    start = request.args.get("start")
    end = request.args.get("end")

    start_dt = f"{start} 00:00:00"
    end_dt = f"{end} 23:59:59"

    rows = load_data(start_dt, end_dt)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        pd.DataFrame(rows).to_excel(writer, index=False, sheet_name="결과")

    output.seek(0)
    filename = f"result_{start}_{end}.xlsx"

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =========================================
# RUN
# =========================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
