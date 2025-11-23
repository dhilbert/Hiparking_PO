"""
/routes/main_routes.py

메인 홈 화면을 렌더링하는 Blueprint 라우트 파일.

home() : 홈 페이지(home.html)를 렌더링해서 반환한다.
"""

from flask import Blueprint, render_template

main_routes = Blueprint("main_routes", __name__)


@main_routes.route("/")
def home():
    """메인 페이지를 렌더링하여 반환한다."""
    return render_template("home.html")
