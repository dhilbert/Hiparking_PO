# routes/car_routes.py
from flask import Blueprint, request, render_template
from services.car_service import find_orders_by_car

car_routes = Blueprint("car", __name__)

@car_routes.route("/car-search", methods=["GET"])
def car_search():

    car_no = request.args.get("carno")
    results = []
    searched = False

    if car_no:
        searched = True
        results = find_orders_by_car(car_no)

    return render_template(
        "car_search.html",
        results=results,
        searched=searched
    )
