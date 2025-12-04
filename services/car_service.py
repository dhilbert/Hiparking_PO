# services/car_service.py

from config.db_config import run_query

def find_orders_by_car(car_no: str, env="prod"):
    sql = f"""
        SELECT 
            tpl.`name` AS parking_lot_name,
            tbd.company_name AS division_name,

            CASE
                WHEN tbos.payment_method = 'CARD' THEN ttb.last_modified_date
                WHEN tbos.payment_method = 'VIRTUAL_ACCT' THEN ttb.deposit_at
                WHEN tbos.payment_method = 'FIXED_ACCT' THEN tbos.order_requested_at
                WHEN tbos.payment_method = 'NO_PAYMENT' THEN tbos.order_requested_at
                ELSE NULL
            END AS event_time,

            tp.`name` AS product_name,
            tbos.order_sheet_no,
            tbos.order_status,
            tbos.payment_method,
            ttb.acquirer_name,
            ttb.approval_no,
            ttb.card_no,
            ttb.res_msg,
            ttb.cash_auth_no,
            ttb.account_no

        FROM tb_business_order_sheet AS tbos
            LEFT JOIN rtb_business_division_product_mapping AS rbdpm
                ON tbos.business_division_product_mapping_seq = rbdpm.business_division_product_mapping_seq
            JOIN tb_product AS tp
                ON tp.product_seq = rbdpm.product_seq
            JOIN tb_parking_lot AS tpl
                ON tpl.parking_lot_seq = tp.parking_lot_seq
            JOIN tb_business_division AS tbd
                ON tbd.division_seq = rbdpm.division_seq
            LEFT JOIN tb_trade AS ttb
                ON ttb.business_order_sheet_seq = tbos.business_order_sheet_seq

        WHERE tbos.business_order_sheet_seq = (
            SELECT tos.business_order_sheet_seq 
            FROM tb_order AS tos 
            WHERE tos.car_number = %s limit 1
        )
    """
    return run_query(env, sql, (car_no,))
