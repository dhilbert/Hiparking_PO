"""
/app.py

Flask 애플리케이션의 엔트리 포인트이며,
모든 Blueprint(메인·SQL·통계·운영)를 등록하고 서버를 실행하는 파일.

create_app() : Flask 앱을 생성하고 필요한 Blueprint를 등록한 뒤 app 객체를 반환하는 함수.
"""


from flask import Flask
from routes.main_routes import main_routes
from routes.sql_routes import sql_routes
from routes.stat_routes import stat_routes
from routes.ops_routes import ops_routes


def create_app():
    app = Flask(__name__, static_folder="static")

    app.register_blueprint(main_routes)
    app.register_blueprint(sql_routes, url_prefix="/sql")
    app.register_blueprint(stat_routes, url_prefix="/stat")
    app.register_blueprint(ops_routes, url_prefix="/ops")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
