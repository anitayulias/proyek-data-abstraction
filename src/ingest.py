import os
import sqlite3
import warnings
from pathlib import Path

import pandas as pd
import psycopg2
import pyodbc

warnings.filterwarnings("ignore", category=UserWarning)

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"

PG_CONFIG = dict(
    host="localhost", port=5432, dbname="viz_abstraction",
    user="postgres", password=os.environ.get("PGPASSWORD", ""),
)


def ingest_access_data(db_path=DATA / "monitoring.accdb") -> pd.DataFrame:
    conn_str = (r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
                rf"DBQ={db_path};")
    with pyodbc.connect(conn_str) as conn:
        query = ("SELECT log_id, [timestamp], node_id, severity_level, metric_value "
                 "FROM system_logs")
        return pd.read_sql(query, conn)


def ingest_sqlite_data(db_path=DATA / "network.db") -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        query = ("SELECT node_id, cluster_group, ip_address, latitude, longitude "
                 "FROM network_nodes")
        return pd.read_sql_query(query, conn)


def ingest_postgres_data() -> pd.DataFrame:
    conn = psycopg2.connect(**PG_CONFIG)
    try:
        cur = conn.cursor()
        cur.execute("SELECT source_node, target_node, latency_ms, packet_loss "
                    "FROM topology_edges")
        df = pd.DataFrame(cur.fetchall(), columns=[d[0] for d in cur.description])
    finally:
        conn.close()
    for col in ("latency_ms", "packet_loss"):
        df[col] = pd.to_numeric(df[col])
    return df


if __name__ == "__main__":
    for nama, fn in [("Access", ingest_access_data),
                     ("SQLite", ingest_sqlite_data),
                     ("PostgreSQL", ingest_postgres_data)]:
        df = fn()
        print(f"[{nama}] {df.shape[0]} baris, {df.shape[1]} kolom")
        print(df.head(3), "\n")
