# 📊 PVI-GSM Dashboard System

Hệ thống dashboard phân tích và đối soát dữ liệu giao dịch giữa PVI và GSM với khả năng xử lý file CSV lớn (100MB+) hiệu quả.

## 🚀 Tính năng chính

### 🏠 **Dashboard Launcher** (`main_dashboard.py`)
- Giao diện chọn dashboard chính
- 2 dashboard riêng biệt: Reconciliation và Tài Xế
- Thông tin tổng quan về hệ thống

### 🔄 **Reconciliation Dashboard** (`dashboard.py`)
- **Match**: Giao dịch khớp giữa GSM và PVI
- **not_found_in_m**: Chỉ có ở PVI (không có GSM)  
- **not_found_in_external**: Chỉ có ở GSM (không có PVI)
- Thống kê tỷ lệ khớp và phân tích discrepancy
- Phân tích INSURANCE_STATUS
- Phân tích Business vs Non-Business orders
- Phân tích Service Type (Ride vs Express)
- Phân tích Amount theo Service Type
- Drill-down analysis cho các status đặc biệt

### 🚗 **Tài Xế Dashboard** (`taixe_dashboard.py`)
- Phân tích đơn tai nạn tài xế
- Phân tích RECONCILE_STATUS cho tài xế
- Biểu đồ phân bố trạng thái
- Tìm kiếm Order ID tài xế
- Xem dữ liệu thô tài xế
- Thống kê chi tiết

### 📁 Quản lý File thông minh
- **Logic ưu tiên**: Tự động chọn file `_2` nếu có
- **Cấu trúc thư mục**: `F:/powerbi/gsm_data/out/YYYY/MM/DD/`
- **File patterns**:
  - `pvi_transaction_reconciled_YYYYMMDD.csv` (file gốc)
  - `pvi_transaction_reconciled_YYYYMMDD_2.csv` (file được ưu tiên)
  - `pvi_transaction_reconciled_taixe_YYYYMMDD.csv` (file tài xế)

### ⚡ Hiệu suất cao
- **Polars** cho xử lý file CSV lớn (>100MB)
- **Streaming processing** để tránh out-of-memory
- **Lazy evaluation** để tối ưu truy vấn

## 🛠️ Cài đặt

### 1. Clone project
```bash
git clone https://github.com/vanh1011/dashboard_GSM_out.git
cd dashboard_GSM_out
```

### 2. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 3. Chạy dashboard
```bash
# Chạy launcher chính
streamlit run main_dashboard.py

# Hoặc chạy trực tiếp từng dashboard
streamlit run dashboard.py          # Reconciliation Dashboard
streamlit run taixe_dashboard.py    # Tài Xế Dashboard
```

Dashboard sẽ chạy tại: `http://localhost:8501`

## 📖 Hướng dẫn sử dụng

### Bước 1: Chọn Dashboard
1. Chạy `main_dashboard.py`
2. Chọn dashboard phù hợp:
   - **🔄 Reconciliation Dashboard**: Phân tích giao dịch chính
   - **🚗 Tài Xế Dashboard**: Phân tích đơn tai nạn tài xế

### Bước 2: Cấu hình đường dẫn
1. Mở sidebar bên trái
2. Chọn năm cần phân tích (mặc định: 2025)
3. Chọn tháng cần phân tích

### Bước 3: Tải dữ liệu
1. Click **"🔄 Tải danh sách ngày"**
2. Chọn ngày cụ thể từ grid
3. Dữ liệu sẽ tự động load

### Bước 4: Phân tích
Mỗi dashboard có các tab chuyên biệt:

#### 🔄 Reconciliation Dashboard Tabs:
- **🔄 Đối soát**: Phân tích RECONCILE_STATUS
- **🛡️ Bảo hiểm**: Phân tích INSURANCE_STATUS, Business orders, Service types
- **🔍 Tìm kiếm**: Tìm kiếm Order ID
- **👁️ Dữ liệu thô**: Browse toàn bộ dữ liệu

#### 🚗 Tài Xế Dashboard Tabs:
- **🚗 Phân tích Tài xế**: Phân tích dữ liệu tài xế
- **🔍 Tìm kiếm**: Tìm kiếm Order ID tài xế
- **👁️ Dữ liệu thô**: Xem dữ liệu thô tài xế

## 🏗️ Kiến trúc hệ thống

```
dashboard-GSM/
├── main_dashboard.py     # Dashboard launcher
├── dashboard.py          # Reconciliation Dashboard
├── taixe_dashboard.py    # Tài Xế Dashboard
├── csv_reader.py         # CSV reading & file management
├── data_analyzer.py      # Advanced data analysis
├── requirements.txt      # Python dependencies
└── README.md            # Documentation
```

### Modules chính:

#### `CSVDataReader`
- Quản lý file CSV với logic ưu tiên
- Xử lý dữ liệu lớn với Polars
- Extract metadata từ file
- Hỗ trợ cả file reconciled và taixe

#### `DataAnalyzer` 
- Phân tích reconcile patterns
- Tìm kiếm discrepancy
- Generate recommendations
- Export báo cáo Excel

#### `DashboardApp` & `TaixeDashboardApp`
- Giao diện Streamlit cho từng loại dashboard
- Interactive widgets
- Real-time visualization

## 🔧 Cấu hình nâng cao

### Environment Variables
```bash
export GSM_DATA_PATH="F:/powerbi/gsm_data/out"
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_HEADLESS=true
```

### Memory optimization cho file lớn
```python
# Trong csv_reader.py
def read_csv_polars(self, file_path: str, chunk_size: int = 50000):
    # Tăng chunk_size cho máy có RAM lớn
    # Giảm chunk_size cho máy hạn chế memory
```

## 📊 Ví dụ dữ liệu

### Sample CSV structure (Reconciliation):
```csv
ORDER_ID,MERCHANT,TOTAL_AMOUNT,ORDER_TIME,RECONCILE_STATUS,INSURANCE_STATUS,IS_BUSINESS_ORDER,SERVICE_TYPE
01Z1ABCD123,MERCHANT_A,1000,2025-07-01 10:30:00,match,completed,true,normal
01Z2EFGH456,MERCHANT_B,2000,2025-07-01 11:45:00,not_found_in_m,cancelled,false,express
01Z3IJKL789,MERCHANT_C,1500,2025-07-01 14:20:00,not_found_in_external,pending,true,normal
```

### Sample CSV structure (Tài Xế):
```csv
ORDER_ID,RECONCILE_STATUS,GSM_AMOUNT,MERCHANT_AMOUNT,RECONCILE_AMOUNT,GSM_STATUS,MERCHANT_STATUS
01JZ2SWN3GYQQP8PH8ZT5GFEZ7,match,100,100,0,COMPLETED,COMPLETED
01JZ2KBJRN9B8MJY2XT6A25NJ8,match,100,100,0,COMPLETED,COMPLETED
```

### Reconcile Status meanings:
- `match`: ✅ Giao dịch khớp hoàn toàn
- `not_found_in_m`: ❌ Chỉ có ở PVI, không có ở GSM
- `not_found_in_external`: ⚠️ Chỉ có ở GSM, không có ở PVI

## 🚨 Troubleshooting

### Lỗi thường gặp:

#### 1. File không tìm thấy
```
❌ Không tìm thấy file dữ liệu
```
**Giải pháp**: Kiểm tra đường dẫn và đảm bảo file tồn tại

#### 2. Memory error với file lớn
```
Error: Out of memory
```
**Giải pháp**: 
- Giảm `chunk_size` trong `csv_reader.py`
- Upgrade RAM hoặc sử dụng máy mạnh hơn
- Xử lý file từng phần

#### 3. Polars parsing error
```
Error reading CSV: Invalid UTF-8
```
**Giải pháp**:
- Kiểm tra encoding của file CSV
- Thử với pandas reader làm fallback

### Performance tips:
- **File lớn**: Sử dụng SSD để đọc nhanh hơn
- **RAM**: Tối thiểu 8GB cho file 100MB+
- **CPU**: Multi-core sẽ tăng tốc Polars processing

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

## 📝 License

MIT License - xem file LICENSE để biết thêm chi tiết.

## 📞 Liên hệ

- **Repository**: https://github.com/vanh1011/dashboard_GSM_out.git
- **Project**: PVI-GSM Dashboard System
