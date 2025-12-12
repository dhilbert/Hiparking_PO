# services/refund_service.py
import calendar
import math
from datetime import datetime, timedelta


class RefundCalculator:
    """
    정기권 환불 계산기 (HiParking 정책 최종 버전)
    - start_price
    - middle_month_prices
    - end_month_price
    - usage_cost
    - cancel_fee
    - final refund amount (고객에게 지급)
    """

    def __init__(
        self,
        FromDate: str,        # 서비스 시작일 (YYYY-MM-DD)
        ToDate: str,          # 서비스 종료일 (항상 말일)
        buy_count: int,       # 구매 수량 (현재 사용 안함)

        MonthPrice_1: int, MonthPrice_2: int, MonthPrice_3: int,
        MonthPrice_4: int, MonthPrice_5: int, MonthPrice_6: int,
        MonthPrice_7: int, MonthPrice_8: int, MonthPrice_9: int,
        MonthPrice_10: int, MonthPrice_11: int, MonthPrice_12: int,

        cap_weekday: int,     # 평일 일 최대 요금(CAP)
        cap_sat: int,         # 토요일 일 최대 요금(CAP)
        cap_sun: int,         # 일요일 일 최대 요금(CAP)

        refund_count: int,    # 환불 요청 수량 (1로 고정)
        refund_date: str      # 환불 요청일 (YYYY-MM-DD)
    ):
        # ----------------------------
        # 입력 날짜 관련 변수
        # ----------------------------
        self.fromDate = FromDate
        self.toDate = ToDate
        self.buy_count = buy_count

        # ----------------------------
        # 월별 정기권 요금 테이블
        # index 0 = 1월, index 11 = 12월
        # ----------------------------
        self.price_monthly = [
            MonthPrice_1, MonthPrice_2, MonthPrice_3,
            MonthPrice_4, MonthPrice_5, MonthPrice_6,
            MonthPrice_7, MonthPrice_8, MonthPrice_9,
            MonthPrice_10, MonthPrice_11, MonthPrice_12,
        ]

        # ----------------------------
        # CAP(일 최대 요금)
        # ----------------------------
        self.cap_weekday = cap_weekday
        self.cap_sat = cap_sat
        self.cap_sun = cap_sun

        # ----------------------------
        # 환불 요청 관련
        # ----------------------------
        self.refund_count = refund_count
        self.refund_date = refund_date

    # =====================================================================
    # ① 시작월 금액 계산 (FULL or 비례)
    # =====================================================================
    def calculate_start_price(self):
        dt = datetime.strptime(self.fromDate, "%Y-%m-%d")
        start_day = dt.day
        month = dt.month
        last_day = calendar.monthrange(dt.year, month)[1]

        full_price = self.price_monthly[month - 1]

        # HiParking 정책: 1~10일 FULL PRICE
        if start_day < 11:
            proportional = full_price
        else:
            proportional = math.floor((full_price / last_day) * (last_day - start_day + 1))

        return {
            "start_price": proportional,
            "explain": (
                f"{month}월 FULL {full_price}원, "
                f"{start_day}일 시작 → 비례 적용 = {proportional}원"
            )
        }

    # =====================================================================
    # ② 중간월 FULL PRICE 계산
    # =====================================================================
    def middle_month_prices(self):
        start_m = datetime.strptime(self.fromDate, "%Y-%m-%d").month
        end_m = datetime.strptime(self.toDate, "%Y-%m-%d").month

        middle = []
        for m in range(start_m + 1, end_m):
            middle.append(self.price_monthly[m - 1])

        return middle

    # =====================================================================
    # ③ 종료월 FULL PRICE
    # =====================================================================
    def end_month_price(self):
        end_m = datetime.strptime(self.toDate, "%Y-%m-%d").month
        return self.price_monthly[end_m - 1]

    # =====================================================================
    # ④ 기이용금 계산 (요일별 CAP 적용)
    # =====================================================================
    def count_usage_and_cost(self):
        start_dt = datetime.strptime(self.fromDate, "%Y-%m-%d")
        end_dt = datetime.strptime(self.refund_date, "%Y-%m-%d")

        weekday = saturday = sunday = 0

        d = start_dt
        while d <= end_dt:
            w = d.weekday()
            if w <= 4:
                weekday += 1
            elif w == 5:
                saturday += 1
            else:
                sunday += 1
            d += timedelta(days=1)

        usage_cost = (
            weekday * self.cap_weekday +
            saturday * self.cap_sat +
            sunday * self.cap_sun
        )

        return {
            "usage_cost": usage_cost,
            "weekday": weekday,
            "saturday": saturday,
            "sunday": sunday,
            "explain": (
                f"평일({weekday})*{self.cap_weekday} + "
                f"토요일({saturday})*{self.cap_sat} + "
                f"일요일({sunday})*{self.cap_sun} = {usage_cost}원"
            )
        }

    # =====================================================================
    # ⑤ 월별 매출 리스트 생성
    # =====================================================================
    def create_monthly_sales(self, start_price, middle_prices, end_price):
        return [start_price] + middle_prices + [end_price]

    # =====================================================================
    # ⑥ 환불액 LIFO 방식 분배 (12월 → 앞으로)
    # =====================================================================
    def distribute_refund(self, monthly_sales, refund_amount):
        refund_dist = [0] * len(monthly_sales)
        remain = refund_amount

        # 뒤에서 앞으로 (말월 → 앞월)
        for i in reversed(range(len(monthly_sales))):

            if remain <= 0:
                break

            available = monthly_sales[i]
            refund_here = min(available, remain)

            refund_dist[i] = refund_here
            remain -= refund_here

        # 정산 후 잔액
        final_sales = [
            monthly_sales[i] - refund_dist[i]
            for i in range(len(monthly_sales))
        ]

        return refund_dist, final_sales

    # =====================================================================
    # ⑦ 메인 계산 실행
    # =====================================================================
    def refundCalc(self):
        # 시작월 금액
        start_info = self.calculate_start_price()
        start_price = start_info["start_price"]

        # 중간월
        middle_prices = self.middle_month_prices()
        middle_total = sum(middle_prices)

        # 종료월 FULL PRICE
        end_price = self.end_month_price()

        # 전체 정기권 금액
        total_parking_pass_price = start_price + middle_total + end_price

        # 기이용금
        usage_info = self.count_usage_and_cost()
        usage_cost = usage_info["usage_cost"]

        # 취소 수수료 (위약금)
        cancel_fee = math.floor((total_parking_pass_price - usage_cost) * 0.2)

        # === 🔥 최종 환불 금액 (형이 원하는 공식) ===
        refund_amount = total_parking_pass_price - (usage_cost + cancel_fee)

        # 월별 매출
        monthly_sales = self.create_monthly_sales(start_price, middle_prices, end_price)

        # 환불액 LIFO 차감
        refund_dist, final_sales = self.distribute_refund(monthly_sales, refund_amount)

        return {
            # 원본 가격들
            "start_price": start_price,
            "middle_prices": middle_prices,
            "end_price": end_price,
            "middle_total": middle_total,
            "total_parking_pass_price": total_parking_pass_price,

            # 기이용금 / 수수료 / 환불액
            "usage_cost": usage_cost,
            "cancel_fee": cancel_fee,
            "refund_amount": refund_amount,

            # LIFO 결과
            "monthly_sales": monthly_sales,
            "refund_dist": refund_dist,
            "final_sales": final_sales,

            # 설명 문구
            "explain_start": start_info["explain"],
            "explain_usage": usage_info["explain"],
            "explain_cancel": (
                f"({total_parking_pass_price} - {usage_cost}) * 0.2 = {cancel_fee}원"
            ),
            "explain_refund": (
                f"{total_parking_pass_price} - (기이용금 {usage_cost} + 취소수수료 {cancel_fee}) = {refund_amount}원"
            ),
        }
