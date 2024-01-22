import os

from afdian_pay.utils.spec import StructSpec
from psycopg import Connection
from psycopg_pool import ConnectionPool


class DataStruct(StructSpec, kw_only=True, frozen=True):
    id: str


bus_pool = ConnectionPool(
    os.environ["PG_URL"],
    min_size=0,
    max_size=1,
    num_workers=1,
    kwargs={"prepare_threshold": None},
)


def deliver(conn: Connection, data: DataStruct):
    # Check if id exists in the store_order table
    cur = conn.execute("SELECT 1 FROM store_order WHERE id = %s LIMIT 1", (data.id,))
    result = cur.fetchone()

    # If result is None, it means the id does not exist in the table
    if result is None:
        raise Exception(f"ID {data.id} does not exist in the store_order table.")

    conn.execute(
        """
        UPDATE store_order
        SET paid = true
        WHERE id = %s
        """,
        (data.id,),
    )
