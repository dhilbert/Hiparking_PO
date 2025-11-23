"""
/routes/ops_routes.py

운영(OPS) 관련 화면을 제공하는 Blueprint 라우트 파일.

ops_home() : '운영 페이지 준비중' 문구를 출력한다.
"""

from flask import Blueprint

ops_routes = Blueprint("ops_routes", __name__)


@ops_routes.route("/")
def ops_home():
    """운영 페이지가 준비 중임을 알리는 문구 반환."""
    return "<h2>운영 페이지 준비중...</h2>"
