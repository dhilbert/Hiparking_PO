import time
from datetime import datetime, timedelta
from config.db_config import run_query


class one_generation_statistics:

    def __init__(self, env="stage"):
        self.env = env
        self.start_date = None
        self.end_date = None

    # -------------------------------------------------------
    # 날짜 범위 설정
    # -------------------------------------------------------
    def set_range(self, start_date, end_date):
        self.start_date = start_date + " 00:00:00"
        self.end_date = end_date + " 23:59:59"

    # -------------------------------------------------------
    # normalize helper
    # -------------------------------------------------------
    def nv(self, v):
        if v in [None, "", "0", 0]:
            return None
        return v

    def normalize_timestamp(self, value):
        if value in [None, ""]:
            return None

        if hasattr(value, "strftime"):
            return value.strftime("%Y%m%d%H%M%S")

        if isinstance(value, str) and "-" in value:
            try:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d%H%M%S")
            except:
                return None

        return value

    def normalize_ymd(self, value):
        if value in [None, ""]:
            return None
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, str):
            return value[:10]
        return value

    # -------------------------------------------------------
    # TB_ORDER + TB_TRADE bulk 로딩 (positive/negative 분리)
    # -------------------------------------------------------
    def load_base_bulk(self, ticket_list):
        if not ticket_list:
            return {}

        in_list = "','".join(ticket_list)

        sql = f"""
            SELECT 
                tb.order_no,
                tb.hi_dms_idx,
                tb.car_number,
                tb.service_start_dt,
                tb.service_end_dt,
                tb.pay_method_type,
                tb.status AS tb_status,

                tt.status AS tt_status,
                tt.amount,
                tt.transaction_date,
                tt.card_no,
                tt.approval_no,
                tt.pg_cno,
                tt.cash_auth_no,
                tt.cash_tran_date,
                tt.cash_auth_value

            FROM tb_order tb
            LEFT JOIN tb_trade tt
                ON tb.order_no = tt.shop_order_no
            WHERE tb.order_no IN ('{in_list}')
            ORDER BY tb.order_no ASC, tt.amount DESC;
        """

        rows = run_query(self.env, sql)
        base_map = {}

        # 티켓별로 rows 묶기
        for r in rows:
            t = r.get("order_no")
            if t not in base_map:
                base_map[t] = {"positive": None, "negative": None}

            amt = r.get("amount") or 0

            if amt > 0:
                base_map[t]["positive"] = r
            elif amt < 0:
                base_map[t]["negative"] = r

        return base_map

    # -------------------------------------------------------
    # DMS TicketID 목록 로드
    # -------------------------------------------------------
    def load_dms_list(self):
        sql = f"""
            SELECT *
            FROM vtb_dms_order
            WHERE LastModifiedDate BETWEEN '{self.start_date}' AND '{self.end_date}'
              AND (business_order_sheet_seq IS NULL OR business_order_sheet_seq = '');
        """
        return run_query(self.env, sql)

    # -------------------------------------------------------
    # compare A/C 상태별로 각각 수행
    # -------------------------------------------------------
    def compare_one(self, dms_row, base_row):
        """한 개 row(A or C)를 비교한다."""

        compare = [
            ("HiDmsIdx", dms_row.get("HiDmsIdx"), base_row.get("HiDmsIdx")),
            ("VehicleRegisterationNo", dms_row.get("VehicleRegisterationNo"), base_row.get("VehicleRegisterationNo")),

            ("FromDate",
             self.normalize_ymd(dms_row.get("FromDate")),
             self.normalize_ymd(base_row.get("FromDate"))),

            ("ToDate",
             self.normalize_ymd(dms_row.get("ToDate")),
             self.normalize_ymd(base_row.get("ToDate"))),

            ("PaymentType", dms_row.get("PaymentType"), base_row.get("PaymentType")),
            ("ApprovalType", dms_row.get("ApprovalType"), base_row.get("ApprovalType")),

            ("TransactionDate",
             self.normalize_timestamp(dms_row.get("TransactionDate")),
             self.normalize_timestamp(base_row.get("TransactionDate"))),

            ("SalesPrice", dms_row.get("SalesPrice"), base_row.get("SalesPrice")),

            ("CreditCardNo", dms_row.get("CreditCardNo"), base_row.get("CreditCardNo")),
            ("CreditCardApprovalNo", dms_row.get("CreditCardApprovalNo"), base_row.get("CreditCardApprovalNo")),
            ("TransactionID", dms_row.get("TransactionID"), base_row.get("TransactionID")),

            ("CashbillID", dms_row.get("CashbillID"), base_row.get("CashbillID")),
            ("CashTradeDate", dms_row.get("CashTradeDate"), base_row.get("CashTradeDate")),
        ]

        if dms_row.get("PaymentType") in ["CASH", "VIRTUAL_ACCT"]:
            compare.append(
                ("CashIdentifyNo",
                 dms_row.get("CashIdentifyNo"),
                 base_row.get("CashIdentifyNo"))
            )

        row_diff = []
        for field, dv, bv in compare:
            d = self.nv(dv)
            b = self.nv(bv)
            if d != b:
                row_diff.append({
                    "field": field,
                    "dms": d,
                    "base": b
                })

        return row_diff

    # -------------------------------------------------------
    # 전체 비교 수행
    # -------------------------------------------------------
    def compare_all(self):

        dms_rows = self.load_dms_list()
        ticket_list = list({r["TicketID"] for r in dms_rows})

        base_map = self.load_base_bulk(ticket_list)

        diff_list = []
        compare_log = []

        for dms in dms_rows:
            ticket = dms["TicketID"]
            dms_type = dms["ApprovalType"]  # A or C

            if ticket not in base_map:
                diff_list.append({
                    "TicketID": ticket,
                    "ApprovalType": dms_type,
                    "field": "Base missing",
                    "dms": "exists",
                    "base": None
                })
                continue

            # --- 핵심: 승인(A) / 취소(C) 분기 처리 ---
            if dms_type == "A":
                base_ref = base_map[ticket]["positive"]
            else:  # C
                base_ref = base_map[ticket]["negative"]

            if base_ref is None:
                diff_list.append({
                    "TicketID": ticket,
                    "ApprovalType": dms_type,
                    "field": "BASE row missing for this status",
                    "dms": "exists",
                    "base": None
                })
                continue

            # BASE row 변환
            brow = {
                "HiDmsIdx": base_ref.get("hi_dms_idx"),
                "VehicleRegisterationNo": base_ref.get("car_number"),
                "FromDate": base_ref.get("service_start_dt"),
                "ToDate": base_ref.get("service_end_dt"),

                "PaymentType": (
                    "CASH" if base_ref.get("pay_method_type") == "VIRTUAL_ACCT"
                    else base_ref.get("pay_method_type")
                ),
                "ApprovalType": dms_type,  # 중요: A/C는 DMS와 같은 상태로 비교

                "SalesPrice": abs(base_ref.get("amount") or 0),
                "TransactionDate": base_ref.get("transaction_date"),
                "CreditCardNo": base_ref.get("card_no"),
                "CreditCardApprovalNo": base_ref.get("approval_no"),
                "TransactionID": base_ref.get("pg_cno"),

                "CashbillID": base_ref.get("cash_auth_no"),
                "CashTradeDate": base_ref.get("cash_tran_date"),
                "CashIdentifyNo": (
                    base_ref.get("cash_auth_value")
                    if base_ref.get("pay_method_type") in ["CASH", "VIRTUAL_ACCT"]
                    else None
                ),
            }

            row_diff = self.compare_one(dms, brow)

            compare_log.append({
                "TicketID": ticket,
                "ApprovalType": dms_type,
                "dms_raw": dms,
                "base_raw": brow,
                "diff_list": row_diff
            })

            for d in row_diff:
                diff_list.append({
                    "TicketID": ticket,
                    "ApprovalType": dms_type,
                    "field": d["field"],
                    "dms": d["dms"],
                    "base": d["base"]
                })

        summary = {
            "diff_found": len(diff_list) > 0,
            "total_compared": len(compare_log),
            "total_diff": len(diff_list)
        }

        return {
            "summary": summary,
            "diff_list": diff_list,
            "compare_log": compare_log
        }


# 실행 테스트
if __name__ == "__main__":
    start = time.time()

    stat = one_generation_statistics(env="prod")
    stat.set_range("2025-11-21", "2025-11-23")

    result = stat.compare_all()

    print(result["summary"])
    print(f"걸린 시간: {time.time() - start:.4f} 초")
