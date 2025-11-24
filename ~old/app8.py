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
# PROD DB CONFIG
# =========================================
DB_PROD = {
    "host": os.getenv("PROD_DB_HOST"),
    "port": int(os.getenv("PROD_DB_PORT")),
    "user": os.getenv("PROD_DB_USER"),
    "password": os.getenv("PROD_DB_PASSWORD"),
    "database": os.getenv("PROD_DB_NAME"),
    "cursorclass": pymysql.cursors.DictCursor,
    "charset": "utf8mb4",
}

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
# COMMON QUERY
# =========================================
def query_db(sql, params):
    conn = pymysql.connect(**DB_PROD)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return [make_json_safe(r) for r in cursor.fetchall()]


# =========================================
# SQL (그대로 적용)
# =========================================
SQL_VTB = """
SELECT *
FROM vtb_dms_order
WHERE OrderSheetID IN (
    SELECT tbos.order_sheet_no
    FROM tb_business_order_sheet AS tbos
    WHERE tbos.last_modified_date BETWEEN %s AND %s
)
ORDER BY ApprovalType DESC;
"""

SQL_CANCEL = """
SELECT *
FROM vtb_dms_order_cancel
WHERE TicketID IN (
    SELECT TicketID
    FROM vtb_dms_order
    WHERE OrderSheetID IN (
        SELECT tbos.order_sheet_no
        FROM tb_business_order_sheet AS tbos
        WHERE tbos.last_modified_date BETWEEN %s AND %s
    )
);
"""


# =========================================
# LOAD DATA
# =========================================
def load_data(start_dt, end_dt):
    vtb = query_db(SQL_VTB, (start_dt, end_dt))
    cancel = query_db(SQL_CANCEL, (start_dt, end_dt))
    return vtb, cancel


# =========================================
# HOME PAGE
# =========================================
@app.route("/")
def home():
    today = datetime.now().strftime("%Y-%m-%d")

    return render_template_string("""
    {% extends "layout.html" %}
    {% block content %}

    <h2>VTB/DMS 조회 (PROD)</h2>

    <label>시작일</label>
    <input type="date" id="startDate" value="{{today}}">

    <label>종료일</label>
    <input type="date" id="endDate" value="{{today}}">

    <button class="btn-run" onclick="search()">조회</button>
    <button class="btn-run" onclick="downloadExcel()">엑셀 다운로드</button>

    <div id="loading" style="display:none;margin-top:15px;">⏳ 로딩중...</div>
    <div id="results" style="margin-top:20px;"></div>

    <script>
    let s = "";
    let e = "";

    function makeTable(name, rows) {
        if (!rows || rows.length === 0)
            return `<p>${name}: 데이터 없음</p>`;

        let keys = Object.keys(rows[0]);
        let thead = keys.map(k => `<th>${k}</th>`).join("");
        let tbody = rows.map(r => 
            "<tr>" + keys.map(k => `<td>${r[k] ?? ""}</td>`).join("") + "</tr>"
        ).join("");

        return `
            <div class="table-block">
                <h3>${name}</h3>
                <table>
                    <thead><tr>${thead}</tr></thead>
                    <tbody>${tbody}</tbody>
                </table>
            </div>
        `;
    }

    function search() {
        s = document.getElementById("startDate").value;
        e = document.getElementById("endDate").value;
        if (!s || !e) return alert("날짜 입력!");

        document.getElementById("loading").style.display = "block";
        document.getElementById("results").innerHTML = "";

        fetch(`/query?start=${s}&end=${e}`)
            .then(res => res.json())
            .then(data => {
                let html = "";
                html += makeTable("vtb_dms_order", data.vtb);
                html += makeTable("vtb_dms_order_cancel", data.cancel);
                document.getElementById("results").innerHTML = html;
            })
            .finally(() => {
                document.getElementById("loading").style.display = "none";
            });
    }

    function downloadExcel() {
        if (!s || !e) return alert("조회 먼저!");
        window.location.href = `/download-excel?start=${s}&end=${e}`;
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

    vtb, cancel = load_data(start_dt, end_dt)
    return jsonify({"vtb": vtb, "cancel": cancel})


# =========================================
# EXCEL EXPORT
# =========================================
@app.route("/download-excel")
def download_excel():
    start = request.args.get("start")
    end = request.args.get("end")

    start_dt = f"{start} 00:00:00"
    end_dt = f"{end} 23:59:59"

    vtb, cancel = load_data(start_dt, end_dt)

    output = BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")

    pd.DataFrame(vtb).to_excel(writer, index=False, sheet_name="vtb_dms_order")
    pd.DataFrame(cancel).to_excel(writer, index=False, sheet_name="vtb_dms_order_cancel")

    writer.close()
    output.seek(0)

    filename = f"vtb_cancel_{start}_{end}.xlsx"

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# =========================================
# RUN
# =========================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

