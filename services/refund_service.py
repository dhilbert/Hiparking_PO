# services/refund_service.py
import calendar
import math
from datetime import datetime, timedelta


class RefundCalculator:
    """
    정기권 환불 계산 클래스
    - FromDate ~ ToDate 동안의 정기권 사용기간에 대해
      월별 요금, 캡 요금, 환불일자 및 환불 수량을 기반으로
      환불 금액을 계산하는 로직을 처리한다.
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
            MonthPrice_10, MonthPrice_11, MonthPrice_12
        ]

        self.cap_weekday = cap_weekday
        self.cap_sat = cap_sat
        self.cap_sun = cap_sun

        self.refund_count = refund_count
        self.refund_date = refund_date

    # ============================
    # 서비스 시작일에 대해 확인
    # ============================
    def checkFromDate(self):
        dt = datetime.strptime(self.fromDate, "%Y-%m-%d")
        fromDateDay = dt.day
        fromDateMonth = dt.month
        last_day = calendar.monthrange(dt.year, dt.month)[1]

        monthly_price = self.price_monthly[fromDateMonth - 1]

        if fromDateDay < 11:
            return monthly_price

        proportional_price = (monthly_price / last_day) * (last_day-fromDateDay+1)
        proportional_price = math.floor(proportional_price)

        return proportional_price

    # ============================
    # 시작월 제외 → 종료월까지 MM 금액 배열
    # ============================
    def getMonthsBetween(self):
        start_dt = datetime.strptime(self.fromDate, "%Y-%m-%d")
        end_dt = datetime.strptime(self.toDate, "%Y-%m-%d")

        start_month = start_dt.month
        end_month = end_dt.month

        AmountTotal = []

        for m in range(start_month + 1, end_month + 1):
            AmountTotal.append(self.price_monthly[m - 1])

        return AmountTotal

    # ============================
    # 평일, 토요일, 일요일 카운트
    # ============================
    def count_weekday_sat_sun(self):
        start_dt = datetime.strptime(self.fromDate, "%Y-%m-%d")
        end_dt = datetime.strptime(self.refund_date, "%Y-%m-%d")

        if start_dt > end_dt:
            return {"weekday": 0, "saturday": 0, "sunday": 0}

        weekday_count = 0
        saturday_count = 0
        sunday_count = 0

        current = start_dt

        while current <= end_dt:
            w = current.weekday()  # 0=월, ..., 5=토, 6=일

            if w <= 4:
                weekday_count += 1
            elif w == 5:
                saturday_count += 1
            else:
                sunday_count += 1

            current += timedelta(days=1)

        return {
            "weekday": weekday_count,
            "saturday": saturday_count,
            "sunday": sunday_count
        }

    # ============================
    # 환불액 산정
    # ============================
    def refundCalc(self):
        # -----------------------------
        # 1. 요일별 사용 일수 구하기
        # -----------------------------
        counts = self.count_weekday_sat_sun()
        weekday_cnt = counts["weekday"]
        saturday_cnt = counts["saturday"]
        sunday_cnt = counts["sunday"]

        # -----------------------------
        # 2. 기 이용 금액 계산 (캡 요금)
        # -----------------------------
        weekday_cost = weekday_cnt * self.cap_weekday
        saturday_cost = saturday_cnt * self.cap_sat
        sunday_cost = sunday_cnt * self.cap_sun

        total_usage_cost = weekday_cost + saturday_cost + sunday_cost  # 기 이용 금액

        # -----------------------------
        # 3. 시작월 금액 계산
        # -----------------------------
        proportional_price = self.checkFromDate()

        # -----------------------------
        # 4. 중간월 전체 금액 계산
        # -----------------------------
        middle_month_prices = self.getMonthsBetween()
        AmountTotal = sum(middle_month_prices)

        # -----------------------------
        # 5. 전체 정기권 금액 계산
        # -----------------------------
        total_parking_pass_price = proportional_price + AmountTotal

        # -----------------------------
        # 6. 취소 수수료 계산
        # -----------------------------
        cancel_fee = math.floor((total_parking_pass_price - total_usage_cost) * 0.2)

        return {
            "weekday_days": weekday_cnt,
            "saturday_days": saturday_cnt,
            "sunday_days": sunday_cnt,
            "weekday_cost": weekday_cost,
            "saturday_cost": saturday_cost,
            "sunday_cost": sunday_cost,
            "total_usage_cost": total_usage_cost,
            "start_month_price": proportional_price,
            "middle_month_total": AmountTotal,
            "total_parking_pass_price": total_parking_pass_price,
            "cancel_fee": cancel_fee
        }

    # ============================
    # 전체 실행
    # ============================
    def run(self):
        return {
            "from_month_price": self.checkFromDate(),
            "middle_month_prices": self.getMonthsBetween(),
            "refund_usage_costs": self.refundCalc()
        }


# ======================================
# 직접 실행 테스트용 main
# ======================================
if __name__ == "__main__":
    calc = RefundCalculator(
        FromDate="2025-07-24",
        ToDate="2025-08-31",
        buy_count=1,

        MonthPrice_1=100000,
        MonthPrice_2=100000,
        MonthPrice_3=100000,
        MonthPrice_4=100000,
        MonthPrice_5=100000,
        MonthPrice_6=100000,
        MonthPrice_7=100000,
        MonthPrice_8=100000,
        MonthPrice_9=100000,
        MonthPrice_10=100000,
        MonthPrice_11=100000,
        MonthPrice_12=100000,

        cap_weekday=10000,
        cap_sat=10000,
        cap_sun=10000,

        refund_count=1,
        refund_date="2025-07-29"
    )

    print(calc.run())
