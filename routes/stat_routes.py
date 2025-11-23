"""
/routes/stat_routes.py

통계 조회 페이지 기능을 담당하며,
비즈포탈 주문 상세 URL을 입력하면 OrderSheetID를 추출하여
DMS 매출 테이블(vtb_dms_order) 데이터를 조회하는 기능을 제공한다.

stat_page()        : 통계 입력 페이지 렌더링
stat_search()      : URL에서 주문번호 추출 후 데이터 조회 + 결과 렌더링
stat_download_excel() : 조회 결과를 엑셀로 다운로드
"""

from flask import Blueprint, render_template, request, send_file
import pandas as pd
from io import BytesIO
from config.db_config import run_query

stat_routes = Blueprint("stat_routes", __name__)


@stat_routes.route("/", methods=["GET"])
def stat_page():
    """통계 입력 페이지 렌더링"""
    return render_template("stat_page.html")


@stat_routes.route("/search", methods=["POST"])
def stat_search():
    """URL 입력 → OrderSheetID 추출 → DMS 데이터 조회 + 결과 테이블 렌더링"""
    url = request.form.get("url", "").strip()

    if not url:
        return render_template(
            "result_table.html",
            rows=[],
            error_msg="URL이 비어 있습니다.",
            rows_json="[]"
        )

    try:
        # URL에서 마지막 UUID 추출
        order_sheet_id = url.split("/")[-1].split("?")[0]

        sql = """
            SELECT *
            FROM vtb_dms_order
            WHERE OrderSheetID = %s
            ORDER BY ApprovalType DESC
        """

        rows = run_query("prod", sql, (order_sheet_id,))

        return render_template(
            "result_table.html",
            rows=rows,
            error_msg=None,
            rows_json=pd.DataFrame(rows).to_json(orient="records")
        )

    except Exception as e:
        return render_template(
            "result_table.html",
            rows=[],
            error_msg=str(e),
            rows_json="[]"
        )


@stat_routes.route("/download_excel", methods=["POST"])
def stat_download_excel():
    """조회 결과를 엑셀 파일로 다운로드"""
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
        download_name="stat_result.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
