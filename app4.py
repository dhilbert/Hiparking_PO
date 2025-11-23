from flask import Flask, render_template_string, request, send_file
import pandas as pd
import io
import time
from app3 import one_generation_statistics  # 비교 로직

app = Flask(__name__)

# ------------------------------------------------------
# HTML 템플릿
# ------------------------------------------------------
HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>1G ↔ 2G 비교도구</title>
<link rel="stylesheet"
 href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">

<script>
function showLoading() {
    document.getElementById("loading").style.display = "block";
}
</script>

<style>
#loading {
    display:none;
    font-size:20px;
    font-weight:bold;
    color:#444;
}
table {
    font-size: 13px;
}
</style>
</head>

<body class="p-4">

<h2 class="mb-4">1G ↔ 2G 자동 비교도구</h2>

<form method="POST" onsubmit="showLoading()">
  <div class="row mb-3">
    <div class="col-3">
      <label>시작일</label>
      <input type="date" name="start_date" class="form-control"
             value="{{ start_date }}">
    </div>
    <div class="col-3">
      <label>종료일</label>
      <input type="date" name="end_date" class="form-control"
             value="{{ end_date }}">
    </div>
    <div class="col-2 d-flex align-items-end">
      <button type="submit" class="btn btn-primary w-100">조회</button>
    </div>
  </div>
</form>

<div id="loading">
  🔍 조회 중... 잠시만 기다려주세요!
</div>

{% if summary %}
<hr>

<h4>요약</h4>
<ul>
  <li>총 비교 건수: <b>{{ summary.total_compared }}</b></li>
  <li>차이 발생 건수: <b>{{ summary.total_diff }}</b></li>
</ul>

<a href="/download_diff" class="btn btn-danger btn-sm">🔻 Diff 엑셀 다운로드</a>
<a href="/download_full" class="btn btn-secondary btn-sm">🔻 전체 비교 엑셀 다운로드</a>

<hr>

<h4 class="mt-4">차이 목록 (미리보기)</h4>
<div style="max-height:500px; overflow:auto;">
<table class="table table-bordered table-striped">
  <thead>
    <tr>
      {% for col in diff_columns %}
        <th>{{ col }}</th>
      {% endfor %}
    </tr>
  </thead>
  <tbody>
    {% for row in diff_rows %}
    <tr>
      {% for col in diff_columns %}
        <td>{{ row[col] }}</td>
      {% endfor %}
    </tr>
    {% endfor %}
  </tbody>
</table>
</div>
{% endif %}

</body>
</html>
"""

# 글로벌 저장
EXCEL_DIFF = None
EXCEL_FULL = None


# ------------------------------------------------------
# ROUTE
# ------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    global EXCEL_DIFF, EXCEL_FULL

    today = time.strftime("%Y-%m-%d")

    # ------------------------
    # GET 첫페이지
    # ------------------------
    if request.method == "GET":
        return render_template_string(
            HTML,
            start_date=today,
            end_date=today,
            summary=None,
            diff_columns=[],
            diff_rows=[]
        )

    # ------------------------
    # POST: 실제 비교 수행
    # ------------------------
    start_date = request.form["start_date"]
    end_date = request.form["end_date"]

    stat = one_generation_statistics(env="prod")
    stat.set_range(start_date, end_date)
    result = stat.compare_all()

    summary = result["summary"]
    compare_log = result["compare_log"]

    # ------- DMS 기준 컬럼 추출 -------
    if compare_log:
        sample_dms = compare_log[0]["dms_raw"]
        dms_keys = list(sample_dms.keys())
    else:
        dms_keys = []

    diff_columns = ["TicketID", "ApprovalType(DMS)", "ApprovalType(BASE)"]
    for k in dms_keys:
        diff_columns.append(f"{k}(DMS)")
        diff_columns.append(f"{k}(BASE)")

    # ------- Diff 테이블 -------
    diff_rows = []
    for row in compare_log:
        if len(row["diff_list"]) == 0:
            continue

        dms_raw = row["dms_raw"]
        base_raw = row["base_raw"]

        r = {
            "TicketID": row["TicketID"],
            "ApprovalType(DMS)": dms_raw.get("ApprovalType"),
            "ApprovalType(BASE)": base_raw.get("ApprovalType"),
        }
        for k in dms_keys:
            r[f"{k}(DMS)"] = dms_raw.get(k)
            r[f"{k}(BASE)"] = base_raw.get(k)
        diff_rows.append(r)

    EXCEL_DIFF = pd.DataFrame(diff_rows)

    # ------- 전체 비교 엑셀 -------
    full_rows = []
    for row in compare_log:
        dms_raw = row["dms_raw"]
        base_raw = row["base_raw"]

        rr = {
            "TicketID": row["TicketID"],
            "ApprovalType(DMS)": dms_raw.get("ApprovalType"),
            "ApprovalType(BASE)": base_raw.get("ApprovalType"),
            "DiffCount": len(row["diff_list"]),
        }
        for k in dms_keys:
            rr[f"{k}(DMS)"] = dms_raw.get(k)
            rr[f"{k}(BASE)"] = base_raw.get(k)

        full_rows.append(rr)

    EXCEL_FULL = pd.DataFrame(full_rows)

    return render_template_string(
        HTML,
        start_date=start_date,
        end_date=end_date,
        summary=summary,
        diff_columns=diff_columns,
        diff_rows=diff_rows
    )


# ------------------------------------------------------
# DOWNLOAD
# ------------------------------------------------------
@app.route("/download_diff")
def download_diff():
    global EXCEL_DIFF
    if EXCEL_DIFF is None:
        return "NO DATA"

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        EXCEL_DIFF.to_excel(writer, index=False)
    output.seek(0)
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        download_name="diff_result.xlsx",
        as_attachment=True
    )


@app.route("/download_full")
def download_full():
    global EXCEL_FULL
    if EXCEL_FULL is None:
        return "NO DATA"

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        EXCEL_FULL.to_excel(writer, index=False)
    output.seek(0)
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        download_name="full_compare.xlsx",
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
