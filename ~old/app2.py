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

app = Flask(__name__, static_folder="static")
CORS(app)

# =========================================
# DB CONFIG
# =========================================
DB_STAGE = {
    "host": os.getenv("STAGE_DB_HOST"),
    "port": int(os.getenv("STAGE_DB_PORT")),
    "user": os.getenv("STAGE_DB_USER"),
    "password": os.getenv("STAGE_DB_PASSWORD"),
    "database": os.getenv("STAGE_DB_NAME"),
    "cursorclass": pymysql.cursors.DictCursor,
    "charset": "utf8mb4"
}

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
# 환경 감지
# =========================================
def detect_env(raw):
    if not raw:
        return "stage"
    raw = raw.lower()
    if "biz-portal-prod" in raw:
        return "prod"
    if "biz-portal-stage" in raw:
        return "stage"
    return "stage"

# =========================================
# JSON safe convert
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
# 공통 DB 조회 함수
# =========================================
def query_db(env, sql, params=None):
    config = DB_STAGE if env == "stage" else DB_PROD
    conn = pymysql.connect(**config)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [make_json_safe(r) for r in rows]

# =========================================
# key 추출
# =========================================
def extract_key(raw):
    if not raw:
        return raw
    raw = raw.strip()

    if "order/" in raw:
        try:
            return raw.split("order/")[1].split("/")[0]
        except:
            return raw

    return raw

# =========================================
# 조회 로직(엑셀/화면 공통)
# =========================================
def load_data(env, raw_key):
    key = extract_key(raw_key)

    # UUID → OrderSheetID 변환
    if len(key) == 36:
        rows = query_db(env, """
            SELECT order_sheet_no
            FROM tb_business_order_sheet
            WHERE business_order_sheet_id = UNHEX(REPLACE(%s, '-', ''));
        """, (key,))
        if rows:
            key = rows[0]["order_sheet_no"]

    # vtb_dms_order 우선 조회
    vtb = query_db(env, """
        SELECT *
        FROM vtb_dms_order
        WHERE TicketID=%s OR OrderSheetID=%s
        ORDER BY ApprovalType DESC;
    """, (key, key))

    # vtb_dms_order_cancel
    cancel = query_db(env, """
        SELECT *
        FROM vtb_dms_order_cancel
        WHERE TicketID IN (
            SELECT TicketID FROM vtb_dms_order WHERE OrderSheetID=%s
        ) OR TicketID=%s;
    """, (key, key))

    # trade
    trade = query_db(env, """
        SELECT *
        FROM tb_trade
        WHERE shop_order_no=%s;
    """, (key,))

    return key, vtb, cancel, trade

# =========================================
# HOME PAGE
# =========================================
@app.route("/")
def home():
    return render_template_string("""
    {% extends "layout.html" %}

    {% block content %}

    <input type="text" id="searchKey" placeholder="검색어 입력" style="width:70%;">
    <button class="btn-run" onclick="search()">조회</button>
    <button class="btn-run" onclick="downloadExcel()">엑셀 다운로드</button>

    <div id="loading" style="display:none;margin-top:20px;">⏳ 로딩중...</div>
    <div id="results"></div>

    <script>
    let lastKey = "";

    function toTable(name, rows) {
        const count = rows?.length ?? 0;

        let keys = rows.length ? Object.keys(rows[0]) : [];
        let header = keys.map(k=>`<th>${k}</th>`).join("");
        let body = rows.map(r=>{
            return "<tr>" + keys.map(k=>`<td>${r[k] ?? ""}</td>`).join("") + "</tr>";
        }).join("");

        return `
            <div class='table-block'>
                <h3>${name} (${count}개)</h3>
                <table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table>
            </div>
        `;
    }

    function search() {
        const key = document.getElementById("searchKey").value;
        if (!key) { alert("입력하세요."); return; }

        lastKey = key;

        document.getElementById("loading").style.display="block";
        document.getElementById("results").innerHTML="";

        fetch(`/order-info?key=` + encodeURIComponent(key))
            .then(res => res.json())
            .then(data => {
                let html = "";
                html += toTable("vtb_dms_order", data.vtb_dms_order);
                html += toTable("vtb_dms_order_cancel", data.vtb_dms_order_cancel);
                html += toTable("tb_trade", data.tb_trade);
                document.getElementById("results").innerHTML = html;
            })
            .finally(() => {
                document.getElementById("loading").style.display="none";
            });
    }

    function downloadExcel() {
        if (!lastKey) {
            alert("먼저 조회하세요.");
            return;
        }
        window.location.href = "/download-excel?key=" + encodeURIComponent(lastKey);
    }
    </script>

    {% endblock %}
    """)

# =========================================
# 조회 API
# =========================================
@app.route("/order-info")
def order_info():
    raw_key = request.args.get("key")
    env = detect_env(raw_key)

    key, vtb, cancel, trade = load_data(env, raw_key)

    return jsonify({
        "env": env,
        "key": key,
        "vtb_dms_order": vtb,
        "vtb_dms_order_cancel": cancel,
        "tb_trade": trade
    })

# =========================================
# 엑셀 다운로드
# =========================================
@app.route("/download-excel")
def download_excel():
    raw_key = request.args.get("key")
    env = detect_env(raw_key)

    key, vtb, cancel, trade = load_data(env, raw_key)

    output = BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")

    pd.DataFrame(vtb).to_excel(writer, index=False, sheet_name="vtb_dms_order")
    pd.DataFrame(cancel).to_excel(writer, index=False, sheet_name="vtb_dms_order_cancel")
    pd.DataFrame(trade).to_excel(writer, index=False, sheet_name="tb_trade")

    writer.close()
    output.seek(0)

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{key}_{now}.xlsx"

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
