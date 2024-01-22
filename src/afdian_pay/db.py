import os

from psycopg_pool import ConnectionPool

db_pool = ConnectionPool(os.environ["PG_URL"], prepare_threshold=None)

# with db_pool.connection() as conn:
#     conn.execute(
#         """
#         CREATE TABLE IF NOT EXISTS afdian_sku (
#             value INT PRIMARY KEY,
#             sku TEXT NOT NULL
#         );
#     """
#     )
#     conn.execute(
#         """
#         CREATE TABLE IF NOT EXISTS afdian_origin_order (
#             out_trade_no TEXT PRIMARY KEY,
#             msg TEXT,
#             content JSONB
#         );
#     """
#     )
#     conn.execute(
#         """
#         CREATE TABLE IF NOT EXISTS afdian_order (
#             id TEXT PRIMARY KEY,
#             status TEXT NOT NULL,
#             price INT NOT NULL,
#             business_name TEXT NOT NULL,
#             business_data JSONB NOT NULL
#         );
#     """
#     )
