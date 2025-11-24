from flask import Blueprint, request, jsonify
from services.compare_service import compare_dms_base

compare_routes = Blueprint("compare", __name__)

@compare_routes.get("/api/compare")
def compare_api():
    start = request.args.get("start")
    end = request.args.get("end")
    return jsonify(compare_dms_base(start, end))
