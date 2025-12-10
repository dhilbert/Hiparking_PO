from flask import Blueprint, render_template, request
from services.refund_service import RefundCalculator

refund_routes = Blueprint("refund_routes", __name__)

@refund_routes.route("/refund", methods=["GET", "POST"])
def refund_page():
    result = None

    if request.method == "POST":
        calc = RefundCalculator(
            FromDate=request.form.get("FromDate"),
            ToDate=request.form.get("ToDate"),
            buy_count=1,

            MonthPrice_1=int(request.form.get("MonthPrice_1")),
            MonthPrice_2=int(request.form.get("MonthPrice_2")),
            MonthPrice_3=int(request.form.get("MonthPrice_3")),
            MonthPrice_4=int(request.form.get("MonthPrice_4")),
            MonthPrice_5=int(request.form.get("MonthPrice_5")),
            MonthPrice_6=int(request.form.get("MonthPrice_6")),
            MonthPrice_7=int(request.form.get("MonthPrice_7")),
            MonthPrice_8=int(request.form.get("MonthPrice_8")),
            MonthPrice_9=int(request.form.get("MonthPrice_9")),
            MonthPrice_10=int(request.form.get("MonthPrice_10")),
            MonthPrice_11=int(request.form.get("MonthPrice_11")),
            MonthPrice_12=int(request.form.get("MonthPrice_12")),

            cap_weekday=int(request.form.get("cap_weekday")),
            cap_sat=int(request.form.get("cap_sat")),
            cap_sun=int(request.form.get("cap_sun")),

            refund_count=int(request.form.get("refund_count")),
            refund_date=request.form.get("refund_date"),
        )

        result = calc.refundCalc()

    return render_template("refund.html", result=result)
