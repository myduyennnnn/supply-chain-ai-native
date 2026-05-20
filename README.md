# Supply Chain AI-Native

Hệ thống phân tích chuỗi cung ứng theo kiến trúc Medallion (Bronze → Silver → Gold)

## Setup

### 1. Clone repo
git clone https://github.com/myduyennnnn/supply-chain-ai-native.git
cd supply-chain-ai-native

### 2. Tải data
Tải 3 file CSV từ Google Drive: [(https://data.mendeley.com/datasets/8gx2fvg2k6/5)]
Đặt vào thư mục `data/`:
- DataCoSupplyChainDataset.csv
- tokenized_access_logs.csv  
- DescriptionDataCoSupplyChain.csv

### 3. Khởi động Docker
docker-compose up -d

### 4. Cài thư viện Python
pip install -r ingestion/requirements.txt

### 5. Chạy Bronze ingestion
python ingestion/bronze_ingestion.py

## Services
| Service  | URL                   | Login         |
|----------|-----------------------|---------------|
| MinIO    | http://localhost:9001 | admin/password123 |
| MLflow   | http://localhost:5001 | không cần     |
| Prefect  | http://localhost:4200 | không cần     |
| Metabase | http://localhost:3000 | setup lần đầu |

## Lưu ý
- PostgreSQL chạy ở port **5433** (không phải 5432 mặc định)
- Sau khi chạy bronze_ingestion.py, vào MinIO kiểm tra bucket `bronze` có 2 folder: `supply_chain/` và `clickstream/`