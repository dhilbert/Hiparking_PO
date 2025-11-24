from flask import Blueprint, request, jsonify
from services.report_service import report_by_date

report_routes = Blueprint("report", __name__)

@report_routes.get("/api/report/date")
def rpt():
    start = request.args.get("start")
    end = request.args.get("end")
    return jsonify(report_by_date(start, end))
