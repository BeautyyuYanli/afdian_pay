import json
import os
from datetime import datetime
from hashlib import md5
from typing import Any, Dict, List, Optional, Union
from afdian_pay.spec import StructSpec, QueryOrderData

import httpx


class Caller:
    def __init__(self, user_id: str, token: str):
        self.user_id = user_id
        self.token = token
        self.caller = httpx.Client()

    def post(self, url: str, data: dict):
        ts = int(datetime.now().timestamp())
        params = json.dumps(data)
        sign = md5(
            f"{self.token}params{params}ts{ts}user_id{self.user_id}".encode()
        ).hexdigest()
        response = httpx.request(
            "POST",
            url,
            json={
                "user_id": self.user_id,
                "params": params,
                "ts": ts,
                "sign": sign,
            },
        )
        response.raise_for_status()
        data = response.json()
        if data["ec"] != 200:
            raise Exception(f"Request failed: ec code error\n{data}")
        return data["data"]

    def orders(self, page: int = 1) -> QueryOrderData:
        return QueryOrderData.from_dict(
            self.post(
                "https://afdian.net/api/open/query-order",
                {
                    "page": page,
                },
            )
        )


caller = Caller(os.environ["AFDIAN_USER_ID"], os.environ["AFDIAN_TOKEN"])
