from typing import List

from afdian_pay.utils.spec import StructSpec


class Order(StructSpec, kw_only=True, frozen=True):
    out_trade_no: str
    user_id: str
    user_private_id: str
    plan_id: str
    month: int
    total_amount: str
    show_amount: str
    status: int
    remark: str
    product_type: int
    sku_detail: list


class QueryOrderData(StructSpec, kw_only=True, frozen=True):
    list: List[Order]
    total_count: int
    total_page: int


class QueryOrderResponse(StructSpec, kw_only=True, frozen=True):
    ec: int
    em: str
    data: QueryOrderData
