# Data Abstraction & Multi-DBMS Ingestion

Mata Kuliah: Visualisasi Data dan Informasi
Nama: Anita Yulia Sanjaya | NIM: 230660121155

## Deskripsi
Pipeline Python yang membaca data dari tiga DBMS (Microsoft Access, SQLite,
PostgreSQL) dan mengubahnya ke abstraksi data kerangka Munzner
(Table/Attribute, Network, Hierarchy, Spatial, Temporal).

## Prasyarat
- Windows, Python 3.9+ (64-bit)
- Microsoft Access Database Engine (64-bit)
- PostgreSQL berjalan di localhost:5432, database `viz_abstraction`

## Instalasi
    pip install -r requirements.txt

## Cara Menjalankan
    python src\buat_data.py     # membuat data dummy SQLite & Access
    python src\ingest.py        # tes ETL tiga DBMS
    cd src
    python abstraction.py       # menghasilkan artefak di output/

Tabel `topology_edges` di PostgreSQL dibuat manual lewat psql.
Password dibaca dari variabel lingkungan PGPASSWORD (kosong jika tidak ada).

## Struktur
    src/buat_data.py     data dummy SQLite & Access
    src/ingest.py        ETL 3 DBMS
    src/abstraction.py   konversi ke abstraksi data
    data/                network.db, monitoring.accdb
    output/              hasil artefak

## Sumber Data
| DBMS | Tabel | Baris | Abstraksi |
|---|---|---|---|
| MS Access | system_logs | 576 | Temporal + Attribute |
| SQLite | network_nodes | 6 | Spatial + Categorical |
| PostgreSQL | topology_edges | 8 | Network |

## Pemetaan Tipe Atribut
Lengkapnya ada di `output/attribute_types.csv`.

| Kolom | Tipe | Visual channel |
|---|---|---|
| timestamp | Temporal | Position X |
| node_id, cluster_group | Nominal | Hue |
| severity_level | Ordinal (Low<Medium<High<Critical) | Luminance |
| metric_value, latency_ms, packet_loss | Quantitative | Position / Length |
| latitude, longitude | Quantitative (spatial) | Position X/Y |

## Artefak Output
| File | Isi |
|---|---|
| attribute_types.csv | Pemetaan kolom ke tipe atribut dan visual channel |
| table_summary.csv | Ringkasan statistik tiap tabel |
| adjacency_list.json | Graf berarah dalam bentuk adjacency list |
| adjacency_matrix.csv | Adjacency matrix berbobot latency_ms |
| hierarchy.json | Pohon root -> cluster_group -> node |
| spatial_validated.csv | Node dengan flag validitas WGS84 |
| temporal_iso8601.csv | Log terurut, index format ISO-8601 |

## Pertimbangan Teknis
- **Network vs Hierarchy:** edge N06 -> N01 membuat graf bersiklus, jadi
  topologi dimodelkan sebagai Network (DiGraph), bukan pohon. Hierarki dibuat
  terpisah dari cluster_group, tiap node hanya punya satu induk.
- **Adjacency list** dipilih sebagai format utama karena graf jarang (sparse);
  adjacency matrix disediakan sebagai pembanding.
- **Ordinal:** severity_level memakai pd.Categorical(ordered=True) agar urutan
  terjaga dan tidak diperlakukan sebagai kategori biasa.
- **Validasi spasial:** latitude [-90, 90], longitude [-180, 180] (WGS84).
- **Validasi relasi:** setiap source_node/target_node harus ada di
  network_nodes.node_id (hasil: 0 edge tidak valid).
- **Temporal:** timestamp dikonversi ke datetime, diurutkan, di-index, lalu
  diekspor ISO-8601 (YYYY-MM-DDTHH:MM:SS).
- **PostgreSQL via psycopg2 langsung** karena SQLAlchemy 1.4 tidak kompatibel
  dengan pandas 2.x.
