# routes/order_check_routes.py
from flask import Blueprint, render_template, request, jsonify, send_file
from services.order_check_service import load_data, detect_env
from io import BytesIO
import pandas as pd
from datetime import datetime

order_check_routes = Blueprint("order_check", __name__, url_prefix="/order-check")


# ===============================
# 🔍 주문 통합 조회 페이지
# ===============================
@order_check_routes.route("/")
def order_check_home():
    return render_template("order_check.html")


# ===============================
# 🔍 조회 API
# ===============================
@order_check_routes.route("/order-info")
def order_info():
    raw_key = request.args.get("key", "")
    env = detect_env(raw_key)

    key, vtb, cancel, trade = load_data(env, raw_key)

    return jsonify({
        "env": env,
        "key": key,
        "vtb_dms_order": vtb,
        "vtb_dms_order_cancel": cancel,
        "tb_trade": trade
    })


# ===============================
# 🔍 엑셀 다운로드
# ===============================
@order_check_routes.route("/download-excel")
def download_excel():
    raw_key = request.args.get("key", "")
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
