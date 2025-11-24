from flask import Blueprint, request, jsonify
from services.order_service import get_trade, get_order_sheet

order_routes = Blueprint("order", __name__)

@order_routes.get("/api/order/trade")
def trade():
    osid = request.args.get("osid")
    return jsonify(get_trade(osid))

@order_routes.get("/api/order/sheet")
def sheet():
    osid = request.args.get("osid")
    return jsonify(get_order_sheet(osid))
