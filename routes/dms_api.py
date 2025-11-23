"""
/routes/dms_api.py

DMS 데이터를 API 형태로 조회하는 Blueprint 라우트 파일.

recent() : 최근 DMS 데이터(limit 개수)를 JSON으로 반환한다.
ticket(ticket_id) : 특정 TicketID의 DMS 데이터를 JSON으로 반환한다.
"""

from flask import Blueprint, request, jsonify
from services import dms_service

dms_api = Blueprint("dms_api", __name__)


@dms_api.route("/recent", methods=["GET"])
def recent():
    """env와 limit을 받아 최근 DMS 데이터를 JSON으로 반환한다."""
    env = request.args.get("env", "prod")
    limit = int(request.args.get("limit", 10))
    data = dms_service.get_recent_dms(env, limit)
    return jsonify(data)


@dms_api.route("/ticket/<ticket_id>", methods=["GET"])
def ticket(ticket_id):
    """TicketID에 해당하는 DMS 상세 정보를 JSON으로 반환한다."""
    env = request.args.get("env", "prod")
    data = dms_service.get_dms_ticket(env, ticket_id)
    return jsonify(data)
