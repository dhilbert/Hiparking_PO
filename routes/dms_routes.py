from flask import Blueprint, request, jsonify
from services.dms_service import get_dms_by_date, get_dms_cancel_by_ordersheet

dms_routes = Blueprint("dms", __name__)

@dms_routes.get("/api/dms/date")
def dms_date():
    start = request.args.get("start")
    end = request.args.get("end")
    return jsonify(get_dms_by_date(start, end))
