import os
from functools import wraps

from flask import Flask, abort, request

from afdian_pay.order import create_order, deliver_orders, get_order, sync_origin_orders
from afdian_pay.spec import StructSpec

app = Flask(__name__)

STATIC_TOKEN = os.environ["STATIC_TOKEN"]


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            # Split the token from the 'Bearer ' prefix
            token = request.headers["Authorization"].split(" ")[1]
        if not token or token != STATIC_TOKEN:
            abort(403)
        return f(*args, **kwargs)

    return decorated


@app.route("/health", methods=["GET"])
def health_route():
    return "OK"


@app.route("/create_order", methods=["POST"])
@token_required
def create_order_route():
    class RequestData(StructSpec, kw_only=True, frozen=True):
        id: str
        price: int
        business_name: str
        business_data: dict

    data = RequestData.from_json(request.data)
    return create_order(
        data.id,
        data.price,
        data.business_name,
        data.business_data,
    )


@app.route("/get_order", methods=["GET"])
@token_required
def get_order_route():
    id = request.args.get("id")
    if not id:
        abort(400)
    answer = get_order(id)
    if answer is None:
        abort(404)
    return answer


@app.route("/sync_origin_orders", methods=["GET"])
@token_required
def sync_origin_orders_route():
    # Call the sync_origin_orders function
    return sync_origin_orders()


@app.route("/deliver_orders", methods=["GET"])
@token_required
def deliver_orders_route():
    # Call the deliver_orders function
    return deliver_orders()


if __name__ == "__main__":
    app.run()
