from flask import Blueprint, request, jsonify
from services.log_service import log_add, log_all, log_delete, log_update
from datetime import datetime

log_routes = Blueprint("log", __name__)

@log_routes.get("/api/log")
def list_logs():
    return jsonify(log_all())

@log_routes.post("/api/log")
def add_log():
    text = request.json.get("text")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_add(text, ts)
    return jsonify({"ok": True})

@log_routes.delete("/api/log/<int:id>")
def delete_log(id):
    log_delete(id)
    return jsonify({"ok": True})
