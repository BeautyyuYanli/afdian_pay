import os

from afdian_pay.utils.spec import StructSpec
from psycopg import Connection
from psycopg_pool import ConnectionPool


class DataStruct(StructSpec, kw_only=True, frozen=True):
    user_id: int
    credit: int


bus_pool = ConnectionPool(
    os.environ["SETULIB_PG_URL"],
    min_size=0,
    max_size=1,
    num_workers=1,
    kwargs={"prepare_threshold": None},
)


def deliver(conn: Connection, data: DataStruct):
    cur = conn.execute(
        """
        SELECT credit FROM setulib_tg_bill_account
        WHERE user_id = %s;
        """,
        (data.user_id,),
    )
    row = cur.fetchone()
    if row is None:
        raise Exception(f"User ID {data.user_id} does not exist in the table.")

    conn.execute(
        """
        UPDATE setulib_tg_bill_account
        SET credit = %s
        WHERE user_id = %s;
        """,
        (row[0] + data.credit, data.user_id),
    )
