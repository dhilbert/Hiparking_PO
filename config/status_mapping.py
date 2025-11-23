# ===============================
# 상태 코드 → 한글명
# ===============================
STATUS_NAME_MAP = {
    "CREATION_PENDING": "생성대기",
    "CREATION_CANCEL": "생성취소",
    "PENDING": "예약대기",
    "RESERVED": "예약완료",
    "IN_USE": "이용중",
    "FINISHED": "이용종료",
    "CANCEL_REQUESTED": "취소접수",
    "CANCEL_ON_HOLD": "취소보류",
    "CANCEL_COMPLETED": "취소완료",
    "PAYMENT_PENDING": "결제보류",
    "PAYMENT_FAILED": "결제실패"
}

# ===============================
# 한글명 → 상태 코드
# ===============================
STATUS_CODE_MAP = {v: k for k, v in STATUS_NAME_MAP.items()}


# ===============================
# 함수 형태로 제공
# ===============================
def get_status_name(code):
    return STATUS_NAME_MAP.get(code, "UNKNOWN")


def get_status_code(name):
    return STATUS_CODE_MAP.get(name, "UNKNOWN")
