-- Database cho MLflow
CREATE DATABASE mlflow_db;

-- Schema ghi lại lịch sử ingest Bronze
\c metadata_db;

CREATE TABLE IF NOT EXISTS ingestion_log (
    id          SERIAL PRIMARY KEY,
    source_file VARCHAR(255) NOT NULL,
    layer       VARCHAR(20)  NOT NULL,
    ingest_time TIMESTAMP    DEFAULT NOW(),
    row_count   INTEGER,
    file_size_bytes BIGINT,
    checksum    VARCHAR(64),
    status      VARCHAR(20)  DEFAULT 'success',
    notes       TEXT
);