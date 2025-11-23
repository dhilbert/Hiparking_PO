"""
/routes/trade_api.py

Trade(거래) 관련 API 엔드포인트 모듈이며,
단순 테스트 및 주문 상태 확인용 API를 제공한다.

test()  : API 정상 동작 테스트용 엔드포인트
order() : 특정 주문 ID 전달받아 간단한 JSON 반환
"""

from flask import Blueprint, jsonify

trade_api = Blueprint("trade_api", __name__)


@trade_api.route("/test", methods=["GET"])
def test():
    """API 정상 동작 테스트"""
    return jsonify({"msg": "trade api ok"})


@trade_api.route("/order/<order_id>", methods=["GET"])
def order(order_id):
    """order_id를 받아 간단한 주문 상태 정보 반환"""
    return jsonify({
        "order_id": order_id,
        "status": "ok"
    })
