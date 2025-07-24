# 📊 PVI-GSM Reconciliation Dashboard

Dashboard phân tích và đối soát dữ liệu giao dịch giữa PVI và GSM với khả năng xử lý file CSV lớn (100MB+) hiệu quả.

## 🚀 Tính năng chính

### 🔄 Phân tích Đối soát
- **Match**: Giao dịch khớp giữa GSM và PVI
- **not_found_in_m**: Chỉ có ở PVI (không có GSM)  
- **not_found_in_external**: Chỉ có ở GSM (không có PVI)
- Thống kê tỷ lệ khớp và phân tích discrepancy

### 🛡️ Phân tích Bảo hiểm
- Thống kê INSURANCE_STATUS
- Phân bố theo trạng thái (completed, cancelled, pending, failed)
- Biểu đồ trực quan

### 🔍 Tìm kiếm Order ID
- Tra cứu nhiều Order ID cùng lúc
- Export kết quả ra CSV
- Hiển thị chi tiết thông tin giao dịch

### 📁 Quản lý File thông minh
- **Logic ưu tiên**: Tự động chọn file `_2` nếu có
- **Cấu trúc thư mục**: `F:/powerbi/gsm_data/out/YYYY/MM/DD/`
- **File patterns**:
  - `pvi_transaction_reconciled_YYYYMMDD.csv` (file gốc)
  - `pvi_transaction_reconciled_YYYYMMDD_2.csv` (file được ưu tiên)
  - `pvi_transaction_reconciled_taixe_YYYYMMDD.csv`

### ⚡ Hiệu suất cao
- **Polars** cho xử lý file CSV lớn (>100MB)
- **Streaming processing** để tránh out-of-memory
- **Lazy evaluation** để tối ưu truy vấn

## 🛠️ Cài đặt

### 1. Clone project
```bash
git clone <repository-url>
cd dashboard-GSM
```

### 2. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 3. Chạy dashboard
```bash
streamlit run dashboard.py
```

Dashboard sẽ chạy tại: `http://localhost:8501`

## 📖 Hướng dẫn sử dụng

### Bước 1: Cấu hình đường dẫn
1. Mở sidebar bên trái
2. Nhập đường dẫn dữ liệu (mặc định: `F:/powerbi/gsm_data/out`)
3. Chọn năm cần phân tích

### Bước 2: Tải dữ liệu
1. Click **"🔄 Tải danh sách ngày"**
2. Chọn ngày cụ thể từ dropdown
3. Click **"📈 Phân tích dữ liệu ngày này"**

### Bước 3: Phân tích
Dashboard sẽ hiển thị 4 tab chính:

#### 🔄 Tab Đối soát
- Thống kê tổng quan về reconcile status
- Biểu đồ pie chart phân bố
- Số liệu chi tiết với tỷ lệ phần trăm

#### 🛡️ Tab Bảo hiểm  
- Phân tích INSURANCE_STATUS
- Biểu đồ bar chart
- Bảng thống kê chi tiết

#### 🔍 Tab Tìm kiếm
- Nhập danh sách Order ID (mỗi ID một dòng)
- Kết quả hiển thị trong bảng
- Download CSV để backup

#### 👁️ Tab Dữ liệu thô
- Browse toàn bộ dữ liệu
- Thông tin về các cột
- Sample data với pagination

## 🏗️ Kiến trúc hệ thống

```
dashboard-GSM/
├── dashboard.py          # Main Streamlit app
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

#### `DataAnalyzer` 
- Phân tích reconcile patterns
- Tìm kiếm discrepancy
- Generate recommendations
- Export báo cáo Excel

#### `DashboardApp`
- Giao diện Streamlit
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

### Sample CSV structure:
```csv
ORDER_ID,MERCHANT,TOTAL_AMOUNT,ORDER_TIME,RECONCILE_STATUS,INSURANCE_STATUS
01Z1ABCD123,MERCHANT_A,1000,2025-07-01 10:30:00,match,completed
01Z2EFGH456,MERCHANT_B,2000,2025-07-01 11:45:00,not_found_in_m,cancelled
01Z3IJKL789,MERCHANT_C,1500,2025-07-01 14:20:00,not_found_in_external,pending
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

- **Developer**: Your Name
- **Email**: your.email@example.com
- **Project**: PVI-GSM Reconciliation Dashboard 