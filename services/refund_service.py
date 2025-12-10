# services/refund_service.py
import calendar
import math
from datetime import datetime, timedelta


class RefundCalculator:
    """
    정기권 환불 계산기 (최종 완전체)
    """

    def __init__(
        self,
        FromDate: str,
        ToDate: str,
        buy_count: int,

        MonthPrice_1: int,
        MonthPrice_2: int,
        MonthPrice_3: int,
        MonthPrice_4: int,
        MonthPrice_5: int,
        MonthPrice_6: int,
        MonthPrice_7: int,
        MonthPrice_8: int,
        MonthPrice_9: int,
        MonthPrice_10: int,
        MonthPrice_11: int,
        MonthPrice_12: int,

        cap_weekday: int,
        cap_sat: int,
        cap_sun: int,

        refund_count: int,
        refund_date: str
    ):
        self.fromDate = FromDate
        self.toDate = ToDate
        self.buy_count = buy_count

        self.price_monthly = [
            MonthPrice_1, MonthPrice_2, MonthPrice_3,
            MonthPrice_4, MonthPrice_5, MonthPrice_6,
            MonthPrice_7, MonthPrice_8, MonthPrice_9,
            MonthPrice_10, MonthPrice_11, MonthPrice_12,
        ]

        self.cap_weekday = cap_weekday
        self.cap_sat = cap_sat
        self.cap_sun = cap_sun

        self.refund_count = refund_count
        self.refund_date = refund_date

    # =========================================
    # 시작월 비례 계산
    # =========================================
    def calculate_start_price(self):
        dt = datetime.strptime(self.fromDate, "%Y-%m-%d")
        day = dt.day
        month = dt.month
        last_day = calendar.monthrange(dt.year, month)[1]

        monthly_price = self.price_monthly[month - 1]

        if day < 11:
            proportional = monthly_price
        else:
            proportional = math.floor((monthly_price / last_day) * (last_day - day + 1))

        return {
            "start_price": proportional,
            "explain": f"{monthly_price}원 중 {day}일 시작 → 비례 적용 = {proportional}원"
        }

    # =========================================
    # 중간월 full price
    # =========================================
    def middle_month_prices(self):
        start_dt = datetime.strptime(self.fromDate, "%Y-%m-%d")
        end_dt = datetime.strptime(self.toDate, "%Y-%m-%d")
        start_m = start_dt.month
        end_m = end_dt.month

        middle_prices = []
        for m in range(start_m + 1, end_m):
            middle_prices.append(self.price_monthly[m - 1])

        return middle_prices

    # =========================================
    # 종료월 full price
    # =========================================
    def end_month_price(self):
        end_dt = datetime.strptime(self.toDate, "%Y-%m-%d")
        return self.price_monthly[end_dt.month - 1]

    # =========================================
    # 평일/토/일 카운트 (기이용금)
    # =========================================
    def count_usage_and_cost(self):
        start_dt = datetime.strptime(self.fromDate, "%Y-%m-%d")
        end_dt = datetime.strptime(self.refund_date, "%Y-%m-%d")

        weekday = saturday = sunday = 0

        d = start_dt
        while d <= end_dt:
            w = d.weekday()
            if w <= 4: weekday += 1
            elif w == 5: saturday += 1
            else: sunday += 1
            d += timedelta(days=1)

        usage_cost = (
            weekday * self.cap_weekday +
            saturday * self.cap_sat +
            sunday * self.cap_sun
        )

        explain = (
            f"평일({weekday})*{self.cap_weekday} + "
            f"토요일({saturday})*{self.cap_sat} + "
            f"일요일({sunday})*{self.cap_sun} "
            f"= {usage_cost}원"
        )

        return {
            "usage_cost": usage_cost,
            "weekday": weekday,
            "saturday": saturday,
            "sunday": sunday,
            "explain": explain
        }

    # =========================================
    # 월별 매출 분배 구조 생성
    # =========================================
    def create_monthly_sales(self, start_price, middle_prices, end_price):
        sales = [start_price] + middle_prices + [end_price]
        return sales

    # =========================================
    # LIFO 방식 환불 배분
    # =========================================
    def distribute_refund(self, monthly_sales, refund_amount):
        refund_dist = [0] * len(monthly_sales)
        remain = refund_amount

        for i in reversed(range(len(monthly_sales))):
            if remain <= 0:
                break

            can_refund = min(monthly_sales[i], remain)
            refund_dist[i] = can_refund
            remain -= can_refund

        final_sales = [monthly_sales[i] - refund_dist[i] for i in range(len(monthly_sales))]

        return refund_dist, final_sales

    # =========================================
    # 메인 계산
    # =========================================
    def refundCalc(self):
        # 1) 시작월
        start_info = self.calculate_start_price()
        start_price = start_info["start_price"]

        # 2) 중간월
        middle_prices = self.middle_month_prices()
        middle_total = sum(middle_prices)

        # 3) 종료월
        end_price = self.end_month_price()

        # 4) 정기권 총매출
        total_parking_pass_price = start_price + middle_total + end_price

        # 5) 기이용금
        usage_info = self.count_usage_and_cost()
        usage_cost = usage_info["usage_cost"]

        # 6) 취소 수수료
        cancel_fee = math.floor((total_parking_pass_price - usage_cost) * 0.2)

        # 7) 환불액
        refund_amount = usage_cost + cancel_fee

        # 8) 월별 매출 배열
        monthly_sales = self.create_monthly_sales(start_price, middle_prices, end_price)

        # 9) 환불 분배
        refund_dist, final_sales = self.distribute_refund(monthly_sales, refund_amount)

        return {
            "start_price": start_price,
            "middle_prices": middle_prices,
            "end_price": end_price,
            "middle_total": middle_total,

            "total_parking_pass_price": total_parking_pass_price,
            "usage_cost": usage_cost,
            "cancel_fee": cancel_fee,
            "refund_amount": refund_amount,

            "monthly_sales": monthly_sales,
            "refund_dist": refund_dist,
            "final_sales": final_sales,

            "explain_start": start_info["explain"],
            "explain_usage": usage_info["explain"],
            "explain_cancel": f"({total_parking_pass_price} - {usage_cost}) * 0.2 = {cancel_fee}",
            "explain_refund": f"usage_cost({usage_cost}) + cancel_fee({cancel_fee}) = {refund_amount}",
        }
