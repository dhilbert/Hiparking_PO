from flask import Blueprint, render_template, request
from services.refund_service import RefundCalculator

refund_routes = Blueprint("refund_routes", __name__)

@refund_routes.route("/refund", methods=["GET", "POST"])
def refund_page():

    # <-- 🔥 가장 중요한 fix: form을 항상 넘겨줘야 함
    form = request.form if request.method == "POST" else {}

    result = None

    if request.method == "POST":
        calc = RefundCalculator(
            FromDate=form.get("FromDate"),
            ToDate=form.get("ToDate"),
            buy_count=int(form.get("buy_count")),

            MonthPrice_1=int(form.get("MonthPrice_1")),
            MonthPrice_2=int(form.get("MonthPrice_2")),
            MonthPrice_3=int(form.get("MonthPrice_3")),
            MonthPrice_4=int(form.get("MonthPrice_4")),
            MonthPrice_5=int(form.get("MonthPrice_5")),
            MonthPrice_6=int(form.get("MonthPrice_6")),
            MonthPrice_7=int(form.get("MonthPrice_7")),
            MonthPrice_8=int(form.get("MonthPrice_8")),
            MonthPrice_9=int(form.get("MonthPrice_9")),
            MonthPrice_10=int(form.get("MonthPrice_10")),
            MonthPrice_11=int(form.get("MonthPrice_11")),
            MonthPrice_12=int(form.get("MonthPrice_12")),

            cap_weekday=int(form.get("cap_weekday")),
            cap_sat=int(form.get("cap_sat")),
            cap_sun=int(form.get("cap_sun")),

            refund_count=int(form.get("refund_count")),
            refund_date=form.get("refund_date")
        )
        result = calc.refundCalc()

    return render_template("refund.html", form=form, result=result)
