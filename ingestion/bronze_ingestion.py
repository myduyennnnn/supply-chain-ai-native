import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import boto3
import hashlib
import psycopg2
import os
from datetime import datetime
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

# ── Kết nối MinIO ──────────────────────────────────────────────
s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="admin",
    aws_secret_access_key="password123",
)

# ── Kết nối PostgreSQL ─────────────────────────────────────────
conn = psycopg2.connect(
    host="localhost",
    port=5433,
    dbname="metadata_db",
    user="admin",
    password="admin123"
)
cursor = conn.cursor()

BRONZE_BUCKET = "bronze"

# ── Hàm tính checksum ──────────────────────────────────────────
def compute_checksum(filepath: str) -> str:
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ── Hàm ghi log vào PostgreSQL ─────────────────────────────────
def log_ingestion(source_file, layer, row_count, file_size, checksum, status="success", notes=""):
    cursor.execute("""
        INSERT INTO ingestion_log
            (source_file, layer, row_count, file_size_bytes, checksum, status, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (source_file, layer, row_count, file_size, checksum, status, notes))
    conn.commit()

# ── Hàm upload CSV → Parquet → MinIO ──────────────────────────
def ingest_csv_to_bronze(csv_path: str, minio_key: str, encoding="utf-8"):
    filename = os.path.basename(csv_path)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Bắt đầu ingest: {filename}")

    try:
        # 1. Đọc CSV
        print(f"  Đọc CSV...")
        df = pd.read_csv(csv_path, encoding=encoding, low_memory=False)
        row_count = len(df)
        file_size = os.path.getsize(csv_path)
        checksum  = compute_checksum(csv_path)
        print(f"  Số dòng: {row_count:,} | Size: {file_size/1024/1024:.1f} MB")

        # 2. Convert sang Parquet (in-memory)
        print(f"  Convert sang Parquet...")
        table  = pa.Table.from_pandas(df)
        buffer = BytesIO()
        pq.write_table(table, buffer, compression="snappy")
        buffer.seek(0)

        # 3. Upload lên MinIO Bronze bucket
        print(f"  Upload lên MinIO: bronze/{minio_key}")
        s3.put_object(
            Bucket=BRONZE_BUCKET,
            Key=minio_key,
            Body=buffer.getvalue(),
        )

        # 4. Ghi log
        log_ingestion(filename, "bronze", row_count, file_size, checksum)
        print(f"  Done!")

    except Exception as e:
        log_ingestion(filename, "bronze", 0, 0, "", status="failed", notes=str(e))
        print(f"  FAILED: {e}")
        raise


# ── Chạy ingestion ─────────────────────────────────────────────
if __name__ == "__main__":

    ingest_csv_to_bronze(
        csv_path  = "data/DataCoSupplyChainDataset.csv",
        minio_key = "supply_chain/DataCoSupplyChainDataset.parquet",
        encoding  = "latin-1",  
    )

    ingest_csv_to_bronze(
        csv_path  = "data/DescriptionDataCoSupplyChain.csv",
        minio_key = "supply_chain/DescriptionDataCoSupplyChain.parquet",
        encoding  = "utf-8",
    )

    ingest_csv_to_bronze(
        csv_path  = "data/tokenized_access_logs.csv",
        minio_key = "clickstream/tokenized_access_logs.parquet",
        encoding  = "utf-8",
    )

    print("\nTất cả file đã ingest xong!")
    cursor.close()
    conn.close()