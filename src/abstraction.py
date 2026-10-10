import json
from pathlib import Path

import networkx as nx
import pandas as pd

from ingest import ingest_access_data, ingest_sqlite_data, ingest_postgres_data

OUT = Path(__file__).resolve().parent.parent / "output"
OUT.mkdir(exist_ok=True)

SEVERITY = ["Low", "Medium", "High", "Critical"]


def tabel_dan_atribut(logs, nodes, edges):
    logs["severity_level"] = pd.Categorical(logs["severity_level"],
                                            categories=SEVERITY, ordered=True)
    nodes["cluster_group"] = nodes["cluster_group"].astype("category")

    mapping = pd.DataFrame([
        ("system_logs", "log_id", "Nominal (identifier)", "tidak dipetakan"),
        ("system_logs", "timestamp", "Temporal (Quantitative)", "Position X"),
        ("system_logs", "node_id", "Nominal", "Hue / label"),
        ("system_logs", "severity_level", "Ordinal", "Luminance"),
        ("system_logs", "metric_value", "Quantitative", "Position Y / Length"),
        ("network_nodes", "node_id", "Nominal", "Node identity"),
        ("network_nodes", "cluster_group", "Nominal", "Hue"),
        ("network_nodes", "ip_address", "Nominal", "label"),
        ("network_nodes", "latitude", "Quantitative (spatial)", "Position Y"),
        ("network_nodes", "longitude", "Quantitative (spatial)", "Position X"),
        ("topology_edges", "source_node", "Nominal", "Link start"),
        ("topology_edges", "target_node", "Nominal", "Link end"),
        ("topology_edges", "latency_ms", "Quantitative", "Link width"),
        ("topology_edges", "packet_loss", "Quantitative", "Link color/width"),
    ], columns=["tabel", "kolom", "tipe_atribut", "visual_channel"])
    mapping.to_csv(OUT / "attribute_types.csv", index=False)

    ringkasan = pd.concat({
        "system_logs": logs.describe(include="all").T,
        "network_nodes": nodes.describe(include="all").T,
        "topology_edges": edges.describe(include="all").T,
    })
    ringkasan.to_csv(OUT / "table_summary.csv")
    print("[Table] attribute_types.csv & table_summary.csv tersimpan")


def network_dan_hierarki(nodes, edges):
    valid = set(nodes["node_id"])
    tak_valid = edges[~(edges["source_node"].isin(valid) &
                        edges["target_node"].isin(valid))]
    print(f"[Network] edge dengan node tidak dikenal: {len(tak_valid)}")

    G = nx.DiGraph()
    for _, r in nodes.iterrows():
        G.add_node(r["node_id"], cluster=str(r["cluster_group"]))
    for _, r in edges.iterrows():
        G.add_edge(r["source_node"], r["target_node"],
                   latency_ms=float(r["latency_ms"]),
                   packet_loss=float(r["packet_loss"]))

    adj_list = {n: [{"to": v, **d} for v, d in G[n].items()] for n in G.nodes}
    (OUT / "adjacency_list.json").write_text(
        json.dumps(adj_list, indent=2), encoding="utf-8")
    nx.to_pandas_adjacency(G, weight="latency_ms").to_csv(OUT / "adjacency_matrix.csv")
    print(f"[Network] {G.number_of_nodes()} node, {G.number_of_edges()} edge, "
          f"memiliki siklus: {not nx.is_directed_acyclic_graph(G)}")

    tree = {"name": "Jaringan", "children": [
        {"name": str(c), "children": [{"name": n} for n in g["node_id"]]}
        for c, g in nodes.groupby("cluster_group", observed=True)]}
    (OUT / "hierarchy.json").write_text(json.dumps(tree, indent=2), encoding="utf-8")
    print("[Hierarchy] hierarchy.json tersimpan")


def validasi_spasial(nodes):
    lat_ok = nodes["latitude"].between(-90, 90)
    lon_ok = nodes["longitude"].between(-180, 180)
    nodes["wgs84_valid"] = lat_ok & lon_ok
    nodes.to_csv(OUT / "spatial_validated.csv", index=False)
    print(f"[Spatial] valid WGS84: {int(nodes['wgs84_valid'].sum())}/{len(nodes)}")


def format_temporal(logs):
    logs["timestamp"] = pd.to_datetime(logs["timestamp"])
    logs = logs.sort_values("timestamp").set_index("timestamp")
    out = logs.copy()
    out.index = out.index.strftime("%Y-%m-%dT%H:%M:%S")
    out.index.name = "timestamp_iso8601"
    out.to_csv(OUT / "temporal_iso8601.csv")
    print(f"[Temporal] {logs.index.min()} s/d {logs.index.max()}, "
          f"{len(logs)} baris, index terurut: {logs.index.is_monotonic_increasing}")


if __name__ == "__main__":
    logs = ingest_access_data()
    nodes = ingest_sqlite_data()
    edges = ingest_postgres_data()

    tabel_dan_atribut(logs, nodes, edges)
    network_dan_hierarki(nodes, edges)
    validasi_spasial(nodes)
    format_temporal(logs)
    print("\nSelesai. Cek folder output/")
