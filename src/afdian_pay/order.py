import json
import os
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from afdian_pay.api_caller import caller
from afdian_pay.db import db_pool
from afdian_pay.spec import Order


class OrderStatus(Enum):
    created = "created"
    paid = "paid"
    delivered = "delivered"


def generate_payment_link(amount: int, remark: str):
    with db_pool.connection() as conn:
        cur = conn.execute("SELECT value, sku FROM afdian_sku")
        rows = cur.fetchall()
        value_sku_map: Dict[int, str] = {row[0]: row[1] for row in rows}

    values = list(value_sku_map.keys())
    values.sort(reverse=True)
    selected: Dict[str, int] = {}
    if amount == 0:
        selected[value_sku_map[0]] = 1
    for value in values:
        if not amount > 0:
            break
        if amount >= value:
            k = amount // value
            amount = amount % value
            selected[value_sku_map[value]] = k

    query = urlencode(
        {
            "product_type": 1,
            "plan_id": os.environ["AFDIAN_PLAN_ID"],
            "sku": json.dumps(
                [{"sku_id": k, "count": v} for k, v in selected.items()],
                separators=(",", ":"),
            ),
            "viokrz_ex": 0,
            "remark": remark,
        }
    )
    return "https://afdian.net/order/create?" + query


def create_order(id: str, price: int, business_name: str, business_data: dict):
    with db_pool.connection() as conn:
        conn.execute(
            """
            INSERT INTO afdian_order (id, status, price, business_name, business_data)
            VALUES (%s, %s, %s, %s, %s)
        """,
            (
                id,
                OrderStatus.created,
                price,
                business_name,
                json.dumps(business_data),
            ),
        )
        conn.commit()
    link = generate_payment_link(price, id)
    return link


def get_order(id: str) -> Optional[Dict[str, Any]]:
    with db_pool.connection() as conn:
        cur = conn.execute(
            """
            SELECT status, price, business_name, business_data
            FROM afdian_order
            WHERE id = %s LIMIT 1
        """,
            (id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {
            "status": row[0],
            "price": row[1],
            "business_name": row[2],
            "business_data": row[3],
        }


def sync_origin_orders():
    with db_pool.connection() as conn:
        pages: List[List[Order]] = []
        # fetch all pages
        cnt = 1
        while True:
            res = caller.orders(cnt)
            if len(res.list) == 0:
                break
            cnt += 1
            pages.append([])
            completed = False
            for order in res.list:
                if order.plan_id != os.environ["AFDIAN_PLAN_ID"]:
                    continue
                cur = conn.execute(
                    """
                    SELECT 1 FROM afdian_origin_order WHERE out_trade_no = %s LIMIT 1
                    """,
                    (order.out_trade_no,),
                )
                if cur.fetchone() is not None:
                    completed = True
                else:
                    pages[-1].append(order)

            if completed:
                break
        # process pages in reverse order
        pages.reverse()
        for page in pages:
            for order in page:
                cur = conn.execute(
                    """
                    SELECT status, price FROM afdian_order WHERE id = %s LIMIT 1
                    """,
                    (order.remark,),
                )
                order_invoice = cur.fetchone()
                if order_invoice is None:
                    conn.execute(
                        """
                        INSERT INTO afdian_origin_order (out_trade_no, msg, content)
                        VALUES (%s, %s, %s)
                        """,
                        (
                            order.out_trade_no,
                            "NO_INVOICE",
                            order.to_json().decode(),
                        ),
                    )
                elif order_invoice[0] != "created":
                    conn.execute(
                        """
                        INSERT INTO afdian_origin_order (out_trade_no, msg, content)
                        VALUES (%s, %s, %s)
                        """,
                        (
                            order.out_trade_no,
                            f"STATUS: {order_invoice[0]}",
                            order.to_json().decode(),
                        ),
                    )
                elif int(order_invoice[1]) != int(float(order.show_amount)):
                    conn.execute(
                        """
                        INSERT INTO afdian_origin_order (out_trade_no, msg, content)
                        VALUES (%s, %s, %s)
                        """,
                        (
                            order.out_trade_no,
                            f"PRICE_SHOULD_BE: {order_invoice[1]}",
                            order.to_json().decode(),
                        ),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO afdian_origin_order (out_trade_no)
                        VALUES (%s)
                        """,
                        (order.out_trade_no,),
                    )
                    conn.execute(
                        """
                        UPDATE afdian_order
                        SET status = %s
                        WHERE id = %s
                        """,
                        (
                            OrderStatus.paid,
                            order.remark,
                        ),
                    )
            # commit each page
            conn.commit()


def deliver_orders():
    with db_pool.connection() as conn:
        cur = conn.execute(
            """
            SELECT id FROM afdian_order WHERE status = %s
            """,
            (OrderStatus.paid,),
        )
        ids: List[str] = [row[0] for row in cur.fetchall()]
        for id in ids:
            cur = conn.execute(
                """
                SELECT business_name, business_data 
                FROM afdian_order 
                WHERE id = %s AND status = %s
                """,
                (
                    id,
                    OrderStatus.paid,
                ),
            )
            (name, data) = cur.fetchone()

            if name == "store":
                from afdian_pay.business.store import DataStruct, bus_pool, deliver
            else:
                raise Exception(f"Unknown business name: {name}")

            with bus_pool.connection() as bus_conn:
                deliver(bus_conn, DataStruct.from_dict(data))
                conn.execute(
                    """
                    UPDATE afdian_order
                    SET status = %s
                    WHERE id = %s
                """,
                    (
                        OrderStatus.delivered,
                        id,
                    ),
                )
                bus_conn.commit()
                conn.commit()
