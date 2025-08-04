import streamlit as st
import pandas as pd
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date, timedelta
import os
from csv_reader import CSVDataReader
from typing import Dict, List

# Cấu hình trang - chỉ set nếu chưa được set
if 'page_config_set' not in st.session_state:
    st.set_page_config(
        page_title="PVI-GSM Tài Xế Dashboard",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.session_state.page_config_set = True

# CSS cho giao diện đẹp hơn
st.markdown("""
<style>
/* Loại bỏ padding và margin thừa */
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 100%;
}

/* Header compact */
.main-header {
    font-size: 2rem;
    font-weight: 700;
    color: #e74c3c;
    text-align: center;
    margin: 0;
    padding: 0.5rem 0;
    background: linear-gradient(90deg, #e74c3c, #c0392b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Compact metric cards */
.metric-card {
    background: white;
    padding: 0.8rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border-left: 4px solid #e74c3c;
    margin-bottom: 0.5rem;
}

/* Status cards colors cho tài xế */
.status-match {
    background-color: #d4edda;
    border-color: #28a745;
    color: #155724;
}

.status-not-found-m {
    background-color: #f8d7da;
    border-color: #dc3545;
    color: #721c24;
}

.status-not-found-external {
    background-color: #fff3cd;
    border-color: #ffc107;
    color: #856404;
}

/* Compact tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    height: 3rem;
    padding: 0.5rem 1rem;
}

/* Compact sidebar */
.css-1d391kg {
    padding-top: 1rem;
}

/* Hide streamlit menu and footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Compact file info section */
div[data-testid="metric-container"] {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    padding: 0.5rem;
    border-radius: 0.375rem;
    margin: 0.25rem 0;
}

/* Day grid styling */
.day-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
    gap: 8px;
    margin: 1rem 0;
}

.day-button {
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    text-align: center;
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.2s;
}

.day-button:hover {
    background-color: #f0f0f0;
}

.day-button.selected {
    background-color: #e74c3c;
    color: white;
    border-color: #e74c3c;
}

.day-button.has-v2 {
    background-color: #f39c12;
    color: white;
    border-color: #f39c12;
}

.day-button.large-file {
    background-color: #3498db;
    color: white;
    border-color: #3498db;
}

/* Message area */
.message-area {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 0.375rem;
    padding: 1rem;
    margin: 1rem 0;
    min-height: 60px;
}

/* Compact tables */
.dataframe {
    font-size: 0.85rem;
}

/* Compact charts */
.plotly-graph-div {
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

class TaixeDashboardApp:
    def __init__(self):
        """Khởi tạo dashboard cho tài xế"""
        self.reader = CSVDataReader()
        self.init_session_state()
    
    def init_session_state(self):
        """Khởi tạo session state"""
        if 'taixe_current_data' not in st.session_state:
            st.session_state.taixe_current_data = None
        if 'taixe_file_info' not in st.session_state:
            st.session_state.taixe_file_info = {}
        if 'taixe_available_days' not in st.session_state:
            st.session_state.taixe_available_days = []
        if 'taixe_load_message' not in st.session_state:
            st.session_state.taixe_load_message = ""
        if 'taixe_selected_year' not in st.session_state:
            st.session_state.taixe_selected_year = 2025
        if 'taixe_selected_month' not in st.session_state:
            st.session_state.taixe_selected_month = 7
        if 'taixe_selected_day' not in st.session_state:
            st.session_state.taixe_selected_day = None
    
    def render_header(self):
        """Render header cho trang tài xế"""
        # Nút quay lại launcher
        if st.button("🏠 Quay lại Launcher", key="taixe_back_to_launcher"):
            if 'selected_dashboard' in st.session_state:
                del st.session_state.selected_dashboard
            st.rerun()
        
        st.markdown('<h1 class="main-header">🚗 PVI-GSM Tài Xế Dashboard</h1>', unsafe_allow_html=True)
        st.markdown("### 📊 Phân tích đơn tai nạn tài xế - Dữ liệu từ file `pvi_transaction_reconciled_taixe_YYYYMMDD.csv`")
    
    def render_sidebar(self):
        """Render sidebar cho chọn ngày"""
        with st.sidebar:
            st.markdown("### 📅 Chọn ngày phân tích")
            
            # Chọn năm
            year = st.selectbox(
                "Năm:",
                [2025, 2024, 2023],
                index=0,
                key="taixe_year_selector"
            )
            
            # Chọn tháng
            month = st.selectbox(
                "Tháng:",
                list(range(1, 13)),
                index=6,  # Mặc định tháng 7
                format_func=lambda x: f"{x:02d}",
                key="taixe_month_selector"
            )
            
            # Button tải danh sách ngày
            if st.button("🔄 Tải danh sách ngày", key="taixe_load_days"):
                self.load_available_days(year, month)
                st.rerun()
            
            # Hiển thị grid ngày nếu có
            if st.session_state.taixe_available_days:
                st.markdown("### 📋 Chọn ngày:")
                
                # Tạo grid ngày
                cols = st.columns(7)
                for i, day_info in enumerate(st.session_state.taixe_available_days):
                    col_idx = i % 7
                    with cols[col_idx]:
                        day_num = day_info['day']
                        file_size = day_info['file_size']
                        has_v2 = day_info['has_v2']
                        is_selected = st.session_state.taixe_selected_day == day_num
                        
                        # Tạo button style
                        button_text = f"{day_num:02d}"
                        if has_v2:
                            button_text += " ⭐"
                        if is_selected:
                            button_text += " ➤"
                        
                        # Button color logic
                        if is_selected:
                            button_style = "selected"
                        elif has_v2:
                            button_style = "has-v2"
                        elif file_size > 40:
                            button_style = "large-file"
                        else:
                            button_style = "normal"
                        
                        if st.button(
                            button_text,
                            key=f"taixe_day_{day_num}",
                            help=f"Ngày {day_num:02d} - {file_size:.1f}MB"
                        ):
                            self.load_day_data(year, month, day_num)
                            st.rerun()
            
            # Hiển thị message area
            if st.session_state.taixe_load_message:
                st.markdown("### 📢 Thông báo:")
                st.info(st.session_state.taixe_load_message)
                # Clear message after display
                st.session_state.taixe_load_message = ""
    
    def load_available_days(self, year: int, month: int):
        """Tải danh sách ngày có sẵn trong tháng"""
        try:
            month_path = os.path.join(self.reader.base_path, str(year), f"{month:02d}")
            if not os.path.exists(month_path):
                st.session_state.taixe_load_message = f"❌ Không tìm thấy thư mục tháng {month:02d}/{year}"
                return
            
            available_days = []
            for day_folder in os.listdir(month_path):
                day_path = os.path.join(month_path, day_folder)
                if os.path.isdir(day_path):
                    day_num = int(day_folder)
                    date_str = f"{year}{month:02d}{day_num:02d}"
                    
                    # Tìm file tài xế
                    taixe_file = self.reader.find_best_file(day_path, date_str, 'taixe')
                    
                    if taixe_file and os.path.exists(taixe_file):
                        file_size = os.path.getsize(taixe_file) / (1024 * 1024)  # MB
                        
                        # Check if has version 2
                        has_v2 = os.path.exists(taixe_file.replace('.csv', '_2.csv'))
                        
                        available_days.append({
                            'day': day_num,
                            'file_size': file_size,
                            'has_v2': has_v2,
                            'path': day_path
                        })
            
            st.session_state.taixe_available_days = sorted(available_days, key=lambda x: x['day'])
            st.session_state.taixe_load_message = f"✅ Tìm thấy {len(available_days)} ngày có dữ liệu tài xế"
            
        except Exception as e:
            st.session_state.taixe_load_message = f"❌ Lỗi khi tải danh sách ngày: {str(e)}"
    
    def load_day_data(self, year: int, month: int, day: int):
        """Tải dữ liệu cho ngày được chọn"""
        try:
            date_str = f"{year}{month:02d}{day:02d}"
            folder_path = os.path.join(self.reader.base_path, str(year), f"{month:02d}", f"{day:02d}")
            
            if not os.path.exists(folder_path):
                st.session_state.taixe_load_message = f"❌ Không tìm thấy thư mục ngày {day:02d}/{month:02d}/{year}"
                return
            
            # Tìm file tài xế
            taixe_file = self.reader.find_best_file(folder_path, date_str, 'taixe')
            
            if not taixe_file or not os.path.exists(taixe_file):
                st.session_state.taixe_load_message = f"❌ Không tìm thấy file tài xế cho ngày {day:02d}/{month:02d}/{year}"
                return
            
            # Đọc dữ liệu
            df = self.reader.read_csv_polars(taixe_file)
            
            if df is None or df.is_empty():
                st.session_state.taixe_load_message = f"❌ File tài xế rỗng hoặc lỗi: {os.path.basename(taixe_file)}"
                return
            
            # Lưu dữ liệu vào session state
            st.session_state.taixe_current_data = df
            st.session_state.taixe_selected_day = day
            
            # Lấy thông tin file
            file_info = self.reader.get_file_info(folder_path, date_str)
            st.session_state.taixe_file_info = {
                'taixe_file': os.path.basename(taixe_file),
                'taixe_size': os.path.getsize(taixe_file) / (1024 * 1024),
                'taixe_path': taixe_file,
                'date': date_str,
                'folder': folder_path
            }
            
            st.session_state.taixe_load_message = f"✅ Đã tải dữ liệu tài xế: {df.height:,} records từ {os.path.basename(taixe_file)}"
            
        except Exception as e:
            st.session_state.taixe_load_message = f"❌ Lỗi khi tải dữ liệu: {str(e)}"
    
    def render_file_info(self):
        """Hiển thị thông tin file"""
        if not st.session_state.taixe_file_info:
            return
        
        info = st.session_state.taixe_file_info
        
        st.markdown("### 📁 Thông tin file")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📅 Ngày", info.get('date', 'N/A'))
        with col2:
            st.metric("📄 File tài xế", info.get('taixe_file', 'N/A'))
        with col3:
            st.metric("📊 Kích thước", f"{info.get('taixe_size', 0):.1f} MB")
        with col4:
            st.metric("📂 Thư mục", os.path.basename(info.get('folder', 'N/A')))
        with col5:
            st.metric("🔍 Loại", "Tài xế")
    
    def render_summary_stats(self):
        """Hiển thị thống kê tổng quan"""
        if st.session_state.taixe_current_data is None:
            return
        
        df = st.session_state.taixe_current_data
        
        st.markdown("### 📈 Thống kê tổng quan")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Records", f"{df.height:,}")
        with col2:
            st.metric("📋 Columns", f"{df.width}")
        with col3:
            # Tính tổng amount nếu có cột AMOUNT
            if 'AMOUNT' in df.columns:
                total_amount = df.select(pl.col('AMOUNT').sum()).item()
                st.metric("💰 Tổng tiền", f"{total_amount:,.0f}")
            else:
                st.metric("💰 Tổng tiền", "N/A")
        with col4:
            # Đếm unique order IDs
            if 'ORDER_ID' in df.columns:
                unique_orders = df.select(pl.col('ORDER_ID').n_unique()).item()
                st.metric("🆔 Đơn hàng", f"{unique_orders:,}")
            else:
                st.metric("🆔 Đơn hàng", "N/A")
    
    def render_taixe_analysis(self):
        """Phân tích dữ liệu tài xế"""
        if st.session_state.taixe_current_data is None:
            return
        
        df = st.session_state.taixe_current_data
        
        st.markdown("### 🚗 Phân tích đơn tai nạn tài xế")
        
        # Phân tích RECONCILE_STATUS nếu có
        if 'RECONCILE_STATUS' in df.columns:
            reconcile_stats = df.group_by('RECONCILE_STATUS').agg(
                pl.count().alias('count')
            ).sort('count', descending=True)
            
            # Hiển thị thống kê
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Biểu đồ pie chart
                fig = px.pie(
                    reconcile_stats.to_pandas(),
                    values='count',
                    names='RECONCILE_STATUS',
                    title='Phân bố RECONCILE_STATUS',
                    color_discrete_map={
                        'match': '#28a745',
                        'not_found_in_m': '#dc3545',
                        'not_found_in_external': '#ffc107'
                    }
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Bảng thống kê
                st.markdown("#### 📊 Thống kê chi tiết")
                for _, row in reconcile_stats.iter_rows(named=True):
                    percentage = (row['count'] / df.height) * 100
                    status_icon = {
                        'match': '✅',
                        'not_found_in_m': '❌',
                        'not_found_in_external': '⚠️'
                    }.get(row['RECONCILE_STATUS'], '📊')
                    
                    st.markdown(f"""
                    **{status_icon} {row['RECONCILE_STATUS']}**
                    - Số lượng: {row['count']:,} records ({percentage:.1f}%)
                    """)
        
        # Phân tích các cột khác nếu có
        st.markdown("### 📋 Thông tin chi tiết")
        
        # Hiển thị sample data
        st.markdown("#### 👁️ Sample Data (10 records đầu)")
        sample_df = df.head(10).to_pandas()
        st.dataframe(sample_df, use_container_width=True)
        
        # Hiển thị thông tin cột
        st.markdown("#### 📊 Thông tin cột")
        col_info = []
        for col in df.columns:
            col_type = str(df.schema[col])
            null_count = df.select(pl.col(col).null_count()).item()
            null_percentage = (null_count / df.height) * 100
            
            col_info.append({
                'Column': col,
                'Type': col_type,
                'Null Count': null_count,
                'Null %': f"{null_percentage:.1f}%"
            })
        
        col_info_df = pd.DataFrame(col_info)
        st.dataframe(col_info_df, use_container_width=True)
    
    def render_search_orders(self):
        """Tìm kiếm order ID"""
        if st.session_state.taixe_current_data is None:
            return
        
        df = st.session_state.taixe_current_data
        
        st.markdown("### 🔍 Tìm kiếm Order ID")
        
        # Input area
        order_ids_text = st.text_area(
            "Nhập Order IDs (mỗi dòng một ID):",
            height=100,
            placeholder="01JZ2SWN3GYQQP8PH8ZT5GFEZ7\n01JZ2KBJRN9B8MJY2XT6A25NJ8\n..."
        )
        
        if st.button("🔍 Tìm kiếm", key="taixe_search"):
            if order_ids_text.strip():
                order_ids = [id.strip() for id in order_ids_text.split('\n') if id.strip()]
                
                if 'ORDER_ID' in df.columns:
                    # Tìm kiếm
                    found_orders = df.filter(pl.col('ORDER_ID').is_in(order_ids))
                    
                    if not found_orders.is_empty():
                        st.success(f"✅ Tìm thấy {found_orders.height} orders")
                        
                        # Export button
                        csv = found_orders.to_pandas().to_csv(index=False)
                        st.download_button(
                            "📥 Download CSV",
                            csv,
                            "taixe_found_orders.csv",
                            "text/csv",
                            key="taixe_download"
                        )
                        
                        # Hiển thị kết quả
                        st.dataframe(found_orders.to_pandas(), use_container_width=True)
                    else:
                        st.warning("⚠️ Không tìm thấy order nào trong dữ liệu")
                else:
                    st.error("❌ Không có cột ORDER_ID trong dữ liệu")
            else:
                st.warning("⚠️ Vui lòng nhập ít nhất một Order ID")
    
    def render_data_viewer(self):
        """Xem dữ liệu thô"""
        if st.session_state.taixe_current_data is None:
            return
        
        df = st.session_state.taixe_current_data
        
        st.markdown("### 👁️ Xem dữ liệu thô")
        
        # Pagination
        total_rows = df.height
        page_size = st.selectbox("Số records mỗi trang:", [100, 500, 1000, 5000], key="taixe_page_size")
        
        if 'taixe_current_page' not in st.session_state:
            st.session_state.taixe_current_page = 0
        
        total_pages = (total_rows + page_size - 1) // page_size
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ Trước", disabled=st.session_state.taixe_current_page == 0):
                st.session_state.taixe_current_page = max(0, st.session_state.taixe_current_page - 1)
                st.rerun()
        
        with col2:
            st.markdown(f"**Trang {st.session_state.taixe_current_page + 1}/{total_pages}**")
        
        with col3:
            if st.button("Tiếp ➡️", disabled=st.session_state.taixe_current_page >= total_pages - 1):
                st.session_state.taixe_current_page = min(total_pages - 1, st.session_state.taixe_current_page + 1)
                st.rerun()
        
        # Hiển thị data
        start_idx = st.session_state.taixe_current_page * page_size
        end_idx = min(start_idx + page_size, total_rows)
        
        page_data = df.slice(start_idx, end_idx - start_idx)
        st.dataframe(page_data.to_pandas(), use_container_width=True)
        
        st.markdown(f"**Hiển thị records {start_idx + 1}-{end_idx} trong tổng số {total_rows:,} records**")
    
    def run(self):
        """Chạy dashboard tài xế"""
        self.render_header()
        self.render_sidebar()
        
        # Main content
        if st.session_state.taixe_current_data is not None:
            self.render_file_info()
            self.render_summary_stats()
            
            # Tabs cho các phân tích khác nhau
            tab1, tab2, tab3 = st.tabs([
                "🚗 Phân tích Tài xế", 
                "🔍 Tìm kiếm", 
                "👁️ Dữ liệu thô"
            ])
            
            with tab1:
                self.render_taixe_analysis()
            
            with tab2:
                self.render_search_orders()
            
            with tab3:
                self.render_data_viewer()
        
        else:
            # Hướng dẫn sử dụng
            st.markdown("""
            ## 🚗 Hướng dẫn sử dụng Dashboard Tài Xế
            
            ### 📋 **Các bước thực hiện:**
            1. **Chọn năm**: Mặc định 2025
            2. **Chọn tháng**: Ví dụ 07 (tháng 7)
            3. **Tải danh sách**: Click "🔄 Tải danh sách ngày"
            4. **Chọn ngày**: Click vào ngày muốn phân tích
            5. **Xem kết quả**: Scroll xuống để xem analysis
            
            ### 📊 **Tính năng chính:**
            
            #### 🚗 **Phân tích Tài Xế**
            - **📊 RECONCILE_STATUS**: Phân tích trạng thái đối soát
            - **📈 Biểu đồ**: Pie chart phân bố status
            - **📋 Thống kê**: Chi tiết từng loại status
            - **📊 Sample Data**: Xem 10 records đầu tiên
            - **📋 Column Info**: Thông tin chi tiết các cột
            
            #### 🔍 **Tìm kiếm Order ID**
            - Nhập nhiều Order ID (mỗi dòng một ID)
            - Tìm kiếm nhanh trong dữ liệu tài xế
            - Export kết quả ra CSV
            
            #### 👁️ **Xem dữ liệu thô**
            - Browse toàn bộ dữ liệu tài xế
            - Pagination để xem từng phần
            - Thông tin chi tiết các cột
            
            ### 🎯 **Chú thích Grid Ngày:**
            - **➤ 05**: Ngày đang được chọn
            - **⭐**: Có file version 2 (được ưu tiên)
            - **🔵**: File lớn (>40MB) - màu xanh đậm
            - **⚪**: File nhỏ (<40MB) - màu trắng
            
            ### 📁 **File được đọc:**
            - **Ưu tiên**: `pvi_transaction_reconciled_taixe_YYYYMMDD_2.csv`
            - **Fallback**: `pvi_transaction_reconciled_taixe_YYYYMMDD.csv`
            
            ### ⚡ **Tối ưu hiệu suất:**
            - Sử dụng **Polars** cho file CSV lớn (100MB+)
            - **Lazy loading** chỉ tải khi cần
            - **Smart caching** tránh load lại dữ liệu
            """)
            
            # Thống kê quick stats nếu có data path
            if os.path.exists("F:/powerbi/gsm_data/out"):
                st.markdown("### 📈 **Quick Stats**")
                try:
                    total_folders = len([d for d in os.listdir("F:/powerbi/gsm_data/out/2025/07") 
                                       if os.path.isdir(os.path.join("F:/powerbi/gsm_data/out/2025/07", d))])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📂 Tổng số ngày", total_folders)
                    with col2:
                        st.metric("📅 Tháng hiện tại", "07/2025")
                    with col3:
                        st.metric("🚗 Loại dữ liệu", "Tài xế")
                        
                except:
                    pass

if __name__ == "__main__":
    app = TaixeDashboardApp()
    app.run() 