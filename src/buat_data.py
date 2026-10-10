import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

NODES = [
    ("N01", "Datacenter",   "10.0.0.1", -6.2088, 106.8456),
    ("N02", "Datacenter",   "10.0.0.2", -6.9175, 107.6191),
    ("N03", "Core-Gateway", "10.0.1.1", -7.2575, 112.7521),
    ("N04", "Core-Gateway", "10.0.1.2", -7.7956, 110.3695),
    ("N05", "Edge-A",       "10.0.2.1",  3.5952,  98.6722),
    ("N06", "Edge-A",       "10.0.2.2", -0.9471, 100.4172),
]

def buat_sqlite():
    path = DATA / "network.db"
    if path.exists():
        path.unlink()
    with sqlite3.connect(path) as conn:
        conn.execute("""CREATE TABLE network_nodes (
            node_id TEXT PRIMARY KEY, cluster_group TEXT, ip_address TEXT,
            latitude REAL, longitude REAL)""")
        conn.executemany("INSERT INTO network_nodes VALUES (?,?,?,?,?)", NODES)
    print("SQLite OK:", path)

def isi_access():
    import pyodbc
    path = DATA / "monitoring.accdb"
    if not path.exists():
        print("File monitoring.accdb belum ada di folder data. Buat dulu lewat aplikasi Access.")
        return
    conn_str = (r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
                rf"DBQ={path};")
    conn = pyodbc.connect(conn_str, autocommit=True)
    cur = conn.cursor()
    try:
        cur.execute("DROP TABLE system_logs")
    except pyodbc.Error:
        pass
    cur.execute("""CREATE TABLE system_logs (
        log_id COUNTER PRIMARY KEY,
        [timestamp] DATETIME,
        node_id TEXT(10),
        severity_level TEXT(10),
        metric_value DOUBLE)""")

    levels = ["Low", "Medium", "High", "Critical"]
    t = datetime(2026, 10, 1, 0, 0)
    for _ in range(96):                      # 1 hari, interval 15 menit
        for n in NODES:
            sev = random.choices(levels, weights=[50, 30, 15, 5])[0]
            val = round(random.uniform(10, 80), 2)
            cur.execute(
                "INSERT INTO system_logs ([timestamp], node_id, severity_level, metric_value) "
                "VALUES (?,?,?,?)", (t, n[0], sev, val))
        t += timedelta(minutes=15)
    conn.close()
    print("Access OK:", path)

if __name__ == "__main__":
    buat_sqlite()
    isi_access()