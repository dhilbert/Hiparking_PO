import os
import pymysql
import base64
from flask import Flask, request, jsonify, render_template
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
# ENV DETECT
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
# QUERY EXECUTOR
# =========================================
def query_db(sql, params=None, env="stage"):
    config = DB_STAGE if env == "stage" else DB_PROD
    conn = pymysql.connect(**config)
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [make_json_safe(r) for r in rows]

# =========================================
# KEY PARSER
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
# HOME PAGE (layout.html 사용)
# =========================================
@app.route("/")
def home_page():
    return render_template("layout.html", content="""
        <h2>DMS 조회</h2>

        <label>URL 또는 TicketID 또는 OrderSheetID</label><br>
        <input type="text" id="searchKey" placeholder="https://biz-portal-prod... 또는 ID">
        <button class="btn-run" onclick="search()">조회</button>

        <div id="loading" style="display:none;margin-top:20px;">⏳ 로딩중...</div>
        <div id="results"></div>

        <script>
        function toTable(name, rows) {
            const count = rows?.length ?? 0;
            const title = `${name} (${count}개)`;

            if (!rows || count === 0) {
                return `<div class='table-block'><h3>${title}</h3><div>데이터 없음</div></div>`;
            }

            let keys = Object.keys(rows[0]);
            let header = keys.map(k=>`<th>${k}</th>`).join("");
            let body = rows.map(r=>{
                let row = keys.map(k=>`<td>${r[k] ?? ""}</td>`).join("");
                return `<tr>${row}</tr>`;
            }).join("");

            return `<div class='table-block'><h3>${title}</h3>
                    <table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table></div>`;
        }

        function search() {
            const key = document.getElementById("searchKey").value;
            if (!key) { alert("입력하세요."); return; }

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
        </script>
    """)

# =========================================
# API
# =========================================
@app.route("/order-info", methods=["GET"])
def get_order_info():
    raw_key = request.args.get("key")
    env = detect_env(raw_key)
    key = extract_key(raw_key)

    if not key:
        return jsonify({"error": "key is required"}), 400

    try:
        # UUID → OrderSheetID
        if len(key) == 36:
            sql = """
                SELECT order_sheet_no
                FROM tb_business_order_sheet
                WHERE business_order_sheet_id = UNHEX(REPLACE(%s, '-', ''));
            """
            rows = query_db(sql, (key,), env)
            if rows:
                key = rows[0]["order_sheet_no"]

        # TicketID
        ticket_rows = query_db("SELECT TicketID FROM vtb_dms_order WHERE TicketID=%s LIMIT 1;", (key,), env)
        if ticket_rows:
            return jsonify({
                "env": env,
                "mode": "TICKET",
                "key": key,
                "vtb_dms_order": query_db("SELECT * FROM vtb_dms_order WHERE TicketID=%s ORDER BY ApprovalType DESC;", (key,), env),
                "vtb_dms_order_cancel": query_db("SELECT * FROM vtb_dms_order_cancel WHERE TicketID=%s;", (key,), env),
                "tb_trade": query_db("SELECT * FROM tb_trade WHERE shop_order_no=%s;", (key,), env)
            })

        # OrderSheetID
        order_rows = query_db("SELECT OrderSheetID FROM vtb_dms_order WHERE OrderSheetID=%s LIMIT 1;", (key,), env)
        if order_rows:
            return jsonify({
                "env": env,
                "mode": "ORDERSHEET",
                "key": key,
                "vtb_dms_order": query_db("SELECT * FROM vtb_dms_order WHERE OrderSheetID=%s ORDER BY ApprovalType DESC;", (key,), env),
                "vtb_dms_order_cancel": query_db("""
                    SELECT * FROM vtb_dms_order_cancel
                    WHERE TicketID IN (SELECT TicketID FROM vtb_dms_order WHERE OrderSheetID=%s);
                """, (key,), env),
                "tb_trade": query_db("SELECT * FROM tb_trade WHERE shop_order_no=%s;", (key,), env)
            })

        return jsonify({
            "env": env,
            "status": "not_found",
            "key": key,
            "vtb_dms_order": [],
            "vtb_dms_order_cancel": [],
            "tb_trade": []
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# =========================================
# RUN
# =========================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5065, debug=True)
