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

# Cấu hình trang
st.set_page_config(
    page_title="PVI-GSM Reconciliation Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    color: #1f77b4;
    text-align: center;
    margin: 0;
    padding: 0.5rem 0;
    background: linear-gradient(90deg, #1f77b4, #17a2b8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Compact metric cards */
.metric-card {
    background: white;
    padding: 0.8rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border-left: 4px solid #1f77b4;
    margin-bottom: 0.5rem;
}

/* Status cards colors */
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

div[data-testid="metric-container"] > div {
    width: fit-content;
    flex: none;
}

div[data-testid="metric-container"] label {
    font-size: 0.875rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

class DashboardApp:
    def __init__(self):
        self.reader = CSVDataReader()
        self.init_session_state()
    
    def init_session_state(self):
        """Khởi tạo session state"""
        if 'current_data' not in st.session_state:
            st.session_state.current_data = None
        if 'file_info' not in st.session_state:
            st.session_state.file_info = None
        if 'selected_date' not in st.session_state:
            st.session_state.selected_date = None
    
    def render_header(self):
        """Render header của dashboard"""
        st.markdown('<h1 class="main-header" style="color: #11111; font-size: 2rem; font-weight: 700;">📊 PVI-GSM Reconciliation Dashboard</h1>', 
                   unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render sidebar với các option"""
        st.sidebar.markdown("## ⚙️ Cài đặt")
        
        # Chọn đường dẫn base
        base_path = st.sidebar.text_input(
            "📁 Đường dẫn dữ liệu:",
            value="F:/powerbi/gsm_data/out",
            help="Đường dẫn đến thư mục chứa dữ liệu CSV"
        )
        
        self.reader.base_path = base_path
        
        # Chọn năm
        year = st.sidebar.selectbox(
            "📅 Năm:",
            options=[2024, 2025, 2026],
            index=1,
            key="year_selector"
        )
        
        # Chọn tháng
        month = st.sidebar.selectbox(
            "📅 Tháng:",
            options=list(range(1, 13)),
            index=6,  # Default tháng 7
            format_func=lambda x: f"{x:02d}",
            key="month_selector"
        )
        
        # Load và hiển thị ngày có sẵn
        if st.sidebar.button("🔄 Tải danh sách ngày", key="load_dates_btn"):
            self.load_available_days(year, month)
        
        # Hiển thị grid các ngày có sẵn
        # Check both class attribute and session state
        available_days = getattr(self, 'available_days', None) or st.session_state.get('available_days', {})
        
        if available_days:
            st.sidebar.markdown(f"### 📂 Các ngày có sẵn ({year}/{month:02d})")
            
            # Show selected date info
            if st.session_state.get('selected_date'):
                selected_date_display = st.session_state.selected_date
                formatted_date = f"{selected_date_display[:4]}/{selected_date_display[4:6]}/{selected_date_display[6:8]}"
                st.sidebar.info(f"📅 **Đang xem:** {formatted_date}")
            
            # Tạo grid buttons cho các ngày
            cols_per_row = 3
            days_list = sorted(available_days.keys())
            
            for i in range(0, len(days_list), cols_per_row):
                cols = st.sidebar.columns(cols_per_row)
                
                for j, day in enumerate(days_list[i:i+cols_per_row]):
                    with cols[j]:
                        day_info = available_days[day]
                        
                        # Button text with file info
                        btn_text = f"{day:02d}"
                        if day_info['has_version_2']:
                            btn_text += " ⭐"  # Star for version 2
                        
                        # Check if this is the selected day
                        is_selected = (st.session_state.get('selected_date') == day_info['date_str'])
                        
                        # Color coding based on selection and file size
                        btn_kwargs = {
                            'key': f"day_btn_{day}",
                            'help': f"Ngày {day}: {day_info['size_mb']:.1f}MB"
                        }
                        
                        if is_selected:
                            btn_kwargs['type'] = "primary"  # Always primary for selected
                            btn_text = f"➤ {btn_text}"  # Add arrow for selected
                        elif day_info['size_mb'] > 40:
                            btn_kwargs['type'] = "secondary"  # Secondary for large files
                        # Default for small files
                        
                        if st.button(btn_text, **btn_kwargs):
                            # Load data for selected day
                            self.load_day_data(year, month, day)
            
            # Update available_days in class if loaded from session state
            if not hasattr(self, 'available_days'):
                self.available_days = available_days
            
            # Legend
            st.sidebar.markdown("""
            **Chú thích:**
            - ➤ = Ngày đang xem
            - ⭐ = Có file version 2
            - 🔵 = File lớn (>40MB)  
            - ⚪ = File nhỏ (<40MB)
            """)
            
            # Load status message area - AFTER the grid
            if st.session_state.get('load_message'):
                message_type = st.session_state.get('load_message_type', 'info')
                message_text = st.session_state.load_message
                
                if message_type == 'success':
                    st.sidebar.success(message_text)
                elif message_type == 'error':
                    st.sidebar.error(message_text)
                else:
                    st.sidebar.info(message_text)
                
                # Clear message after displaying
                del st.session_state.load_message
                if 'load_message_type' in st.session_state:
                    del st.session_state.load_message_type
        
        # Debug section
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🐛 Debug Tools")
        
        if st.sidebar.button("🗑️ Clear Cache"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.sidebar.success("✅ Cache cleared!")
            st.rerun()
        
        # Hiển thị thông tin hệ thống
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Thông tin hệ thống")
        st.sidebar.info(f"""
        **Phiên bản:** 1.0.0  
        **Cập nhật:** {datetime.now().strftime('%Y-%m-%d')}  
        **Tối ưu:** Polars + Streamlit
        """)
    
    def _test_load_folder(self, test_folder):
        """Helper function để  một folder cụ thể"""
        try:
            # Test direct load
            from csv_reader import CSVDataReader
            reader = CSVDataReader()
            
            date_str = reader.extract_date_from_path(test_folder)
            st.sidebar.write(f"Date extracted: {date_str}")
            
            file_info = reader.get_file_info(test_folder, date_str)
            st.sidebar.write(f"File info: {file_info}")
            
            if file_info['reconciled_file']:
                df = reader.read_csv_polars(file_info['reconciled_file'])
                st.sidebar.write(f"DataFrame: {df.height} x {df.width}")
                
                # Manually set session state
                st.session_state.current_data = df
                st.session_state.file_info = file_info
                st.session_state.selected_date = date_str
                
                st.sidebar.success("✅ Manual load successful!")
                st.rerun()
            else:
                st.sidebar.error("❌ No file found")
                
        except Exception as e:
            st.sidebar.error(f"❌ Test failed: {e}")
            st.sidebar.code(str(e))
        
        # Old test function continues below
        if False:  # Disable old test
            test_folder_old = "F:/powerbi/gsm_data/out/2025/07/01"
            st.sidebar.write(f"Testing with: {test_folder_old}")
            
            try:
                # Test direct load
                from csv_reader import CSVDataReader
                reader = CSVDataReader()
                
                date_str = reader.extract_date_from_path(test_folder)
                st.sidebar.write(f"Date extracted: {date_str}")
                
                file_info = reader.get_file_info(test_folder, date_str)
                st.sidebar.write(f"File info: {file_info}")
                
                if file_info['reconciled_file']:
                    df = reader.read_csv_polars(file_info['reconciled_file'])
                    st.sidebar.write(f"DataFrame: {df.height} x {df.width}")
                    
                    # Manually set session state
                    st.session_state.current_data = df
                    st.session_state.file_info = file_info
                    st.session_state.selected_date = date_str
                    
                    st.sidebar.success("✅ Manual load successful!")
                    st.rerun()
                else:
                    st.sidebar.error("❌ No file found")
                    
            except Exception as e:
                st.sidebar.error(f"❌ Test failed: {e}")
                st.sidebar.code(str(e))
        
    def load_available_days(self, year: int, month: int):
        """Tải danh sách ngày có sẵn trong tháng"""
        try:
            month_path = os.path.join(self.reader.base_path, str(year), f"{month:02d}")
            
            if not os.path.exists(month_path):
                st.sidebar.warning(f"⚠️ Không tìm thấy dữ liệu tháng {month}/{year}")
                return
            
            available_days = {}
            
            # Scan các ngày trong tháng
            for day_name in os.listdir(month_path):
                day_path = os.path.join(month_path, day_name)
                
                if os.path.isdir(day_path) and day_name.isdigit():
                    day = int(day_name)
                    date_str = f"{year}{month:02d}{day:02d}"
                    
                    # Get file info for this day
                    file_info = self.reader.get_file_info(day_path, date_str)
                    
                    if file_info['reconciled_file']:
                        available_days[day] = {
                            'path': day_path,
                            'date_str': date_str,
                            'size_mb': file_info['reconciled_size_mb'],
                            'has_version_2': file_info['has_version_2'],
                            'file_path': file_info['reconciled_file']
                        }
            
            # Store in session state để persistent
            st.session_state.available_days = available_days
            self.available_days = available_days  # Also store in class
            
            if available_days:
                st.sidebar.success(f"✅ Tìm thấy {len(available_days)} ngày có dữ liệu")
            else:
                st.sidebar.warning(f"⚠️ Không tìm thấy dữ liệu nào trong {month}/{year}")
                
        except Exception as e:
            st.sidebar.error(f"❌ Lỗi khi tải danh sách ngày: {e}")
    
    def load_day_data(self, year: int, month: int, day: int):
        """Load dữ liệu cho ngày được chọn"""
        try:
            # Check available_days từ session state hoặc class attribute
            available_days = getattr(self, 'available_days', None) or st.session_state.get('available_days', {})
            
            if not available_days or day not in available_days:
                # Try to reload available days
                self.load_available_days(year, month)
                available_days = getattr(self, 'available_days', {})
                
                if not available_days or day not in available_days:
                    st.session_state.load_message = f"❌ Không tìm thấy dữ liệu ngày {day}"
                    st.session_state.load_message_type = 'error'
                    return
            
            day_info = available_days[day]
            
            # Clear previous data
            st.session_state.current_data = None
            st.session_state.file_info = None
            st.session_state.selected_date = None
            
            # Show loading message
            with st.spinner(f"🔄 Đang tải dữ liệu ngày {day:02d}/{month:02d}/{year}..."):
                # Load data using existing logic
                df = self.reader.read_csv_polars(day_info['file_path'])
            
            if df is not None and not df.is_empty():
                # Create complete file info object
                original_file_info = self.reader.get_file_info(day_info['path'], day_info['date_str'])
                
                file_info = {
                    'folder': day_info['path'],
                    'date': day_info['date_str'],
                    'reconciled_file': day_info['file_path'],
                    'reconciled_size_mb': day_info['size_mb'],
                    'has_version_2': day_info['has_version_2'],
                    # Add missing fields from original file info
                    'taixe_file': original_file_info.get('taixe_file'),
                    'taixe_size_mb': original_file_info.get('taixe_size_mb', 0)
                }
                
                # Set session state
                st.session_state.current_data = df
                st.session_state.file_info = file_info
                st.session_state.selected_date = day_info['date_str']
                
                # Store success message to display later
                st.session_state.load_message = f"✅ Đã tải thành công {df.height:,} bản ghi cho ngày {day:02d}/{month:02d}/{year}"
                st.session_state.load_message_type = 'success'
            else:
                # Store error message to display later
                st.session_state.load_message = f"❌ Không thể đọc dữ liệu ngày {day}"
                st.session_state.load_message_type = 'error'
                
        except Exception as e:
            # Store error message to display later
            st.session_state.load_message = f"❌ Lỗi khi tải dữ liệu ngày {day}: {e}"
            st.session_state.load_message_type = 'error'
    
    def load_daily_data(self, folder_path: str):
        """Tải và phân tích dữ liệu theo ngày"""
        try:
            # Clear và prominent display của ngày đang load
            st.markdown("---")
            st.markdown(f"## 🔄 Đang tải dữ liệu từ: {folder_path}")
            
            date_str = self.reader.extract_date_from_path(folder_path)
            st.markdown(f"### 📅 Ngày: {date_str}")
            
            # Lấy thông tin file với debug chi tiết
            st.write(f"🔍 Checking if folder exists: {os.path.exists(folder_path)}")
            
            if os.path.exists(folder_path):
                files = os.listdir(folder_path)
                st.write(f"📂 Files in folder: {files}")
                csv_files = [f for f in files if f.endswith('.csv')]
                st.write(f"📄 CSV files: {csv_files}")
            
            file_info = self.reader.get_file_info(folder_path, date_str)
            st.write(f"📁 Debug: File info result:")
            for key, value in file_info.items():
                st.write(f"   {key}: {value}")
            st.session_state.file_info = file_info
            
            # Đọc dữ liệu chính
            if file_info['reconciled_file']:
                st.write(f"📄 Debug: Đang đọc file: {file_info['reconciled_file']}")
                df = self.reader.read_csv_polars(file_info['reconciled_file'])
                
                if df is not None and not df.is_empty():
                    st.write(f"📊 Debug: Đã đọc được {df.height} rows, {df.width} columns")
                    st.write(f"🏷️ Debug: Columns: {df.columns}")
                    
                    # Hiển thị sample data
                    st.write("📋 Debug: Sample data (5 rows đầu):")
                    sample_df = df.head(5).to_pandas()
                    st.dataframe(sample_df)
                    
                    st.session_state.current_data = df
                    st.session_state.selected_date = date_str
                    st.success(f"✅ Đã tải dữ liệu ngày {date_str}")
                else:
                    st.error("❌ File rỗng hoặc không đọc được")
            else:
                st.error(f"❌ Không tìm thấy file dữ liệu trong {folder_path}")
                # Hiển thị các file có sẵn
                import os
                if os.path.exists(folder_path):
                    files = os.listdir(folder_path)
                    st.write(f"📂 Debug: Files có sẵn: {files}")
                
        except Exception as e:
            st.error(f"❌ Lỗi khi tải dữ liệu: {e}")
            st.write(f"🐛 Debug: Exception details: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    def render_file_info(self):
        """Hiển thị thông tin file"""
        if st.session_state.file_info:
            info = st.session_state.file_info
            
            # Format ngày đẹp hơn
            date_formatted = f"{info['date'][:4]}/{info['date'][4:6]}/{info['date'][6:8]}"
            
            # Hiển thị thông tin file trong một dòng compact
            col1, col2, col3, col4, col5 = st.columns([1.5, 1.5, 1.5, 1, 2])
            
            with col1:
                st.metric("📅 Ngày", date_formatted)
            
            with col2:
                reconciled_size = f"{info['reconciled_size_mb']:.1f}MB" if info.get('reconciled_file') else "N/A"
                st.metric("📄 Reconciled", reconciled_size)
            
            with col3:
                taixe_size = info.get('taixe_size_mb', 0)
                taixe_text = f"{taixe_size:.1f}MB" if info.get('taixe_file') else "N/A"
                st.metric("🚗 Taixe", taixe_text)
            
            with col4:
                version_text = "V2" if info.get('has_version_2', False) else "V1"
                st.metric("🔢 Ver", version_text)
            
            with col5:
                # File path rút gọn
                if info.get('reconciled_file'):
                    filename = info['reconciled_file'].split('\\')[-1]
                    st.metric("📂 File", filename[:25] + "..." if len(filename) > 25 else filename)
    
    def render_summary_stats(self):
        """Hiển thị thống kê tổng quan"""
        if st.session_state.current_data is not None and not st.session_state.current_data.is_empty():
            df = st.session_state.current_data
            stats = self.reader.get_summary_stats(df)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📝 Records", f"{stats.get('total_records', 0):,}")
            
            with col2:
                st.metric("🆔 Unique Orders", f"{stats.get('unique_orders', 0):,}")
            
            with col3:
                st.metric("🏪 Merchants", f"{stats.get('unique_merchants', 0):,}")
            
            with col4:
                duplicate_rate = ((stats.get('total_records', 0) - stats.get('unique_orders', 0)) / 
                                max(stats.get('total_records', 1), 1) * 100)
                st.metric("📊 Duplicate %", f"{duplicate_rate:.1f}%")
    
    def render_reconcile_analysis(self):
        """Phân tích RECONCILE_STATUS"""
        if st.session_state.current_data is not None and not st.session_state.current_data.is_empty():
            st.markdown("### 🔄 Phân tích Đối soát")
            
            df = st.session_state.current_data
            reconcile_stats = self.reader.analyze_reconcile_status(df)
            
            if reconcile_stats:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("#### 📊 Số liệu thống kê")
                    
                    # Hiển thị các status với buttons để drill down
                    for status, count in reconcile_stats.items():
                        total_records = df.height
                        percentage = (count / total_records * 100) if total_records > 0 else 0
                        
                        # Màu sắc theo trạng thái
                        if status == 'match':
                            status_class = "status-match"
                            icon = "✅"
                            button_type = "secondary"
                        elif 'not_found_in_m' in status:
                            status_class = "status-not-found-m"
                            icon = "❌"
                            button_type = "primary"
                        elif 'not_found_in_external' in status:
                            status_class = "status-not-found-external"
                            icon = "⚠️"
                            button_type = "primary"
                        else:
                            status_class = ""
                            icon = "📊"
                            button_type = "primary"
                        
                        # Card với button để drill down
                        with st.container():
                            col_btn, col_info = st.columns([3, 1])
                            
                            with col_btn:
                                st.markdown(f"""
                                <div class="metric-card {status_class}">
                                    <strong>{icon} {status}</strong><br>
                                    {count:,} records ({percentage:.1f}%)
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col_info:
                                # Chỉ hiển thị button drill-down cho non-match status có ít records
                                if status != 'match' and count < 10000:  # Chỉ cho phép drill-down nếu < 10k records
                                    if st.button(f"🔍 Chi tiết", key=f"drill_{status}", type=button_type, help=f"Xem chi tiết {count} records"):
                                        # Store drill-down data in session state
                                        filtered_df = df.filter(pl.col('RECONCILE_STATUS') == status)
                                        st.session_state.drill_down_data = filtered_df
                                        st.session_state.drill_down_status = status
                                        st.session_state.drill_down_count = count
                                        st.rerun()
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                
                with col2:
                    # Biểu đồ pie chart
                    fig = px.pie(
                        values=list(reconcile_stats.values()),
                        names=list(reconcile_stats.keys()),
                        title="Phân bố Trạng thái Đối soát",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
        # Hiển thị drill-down data nếu có
        if st.session_state.get('drill_down_data') is not None:
            self.render_drill_down_analysis()
        
        # Thêm phân tích amount theo service type
        self.render_amount_analysis_by_service_type()
    
    def render_amount_analysis_by_service_type(self):
        """Phân tích amount theo service type"""
        if st.session_state.current_data is not None and not st.session_state.current_data.is_empty():
            df = st.session_state.current_data
            
            if 'SERVICE_TYPE' in df.columns:
                st.markdown("### 💰 Phân tích Phí theo Service Type")
                
                amount_analysis = self.reader.analyze_amount_by_service_type(df)
                
                if amount_analysis:
                    # Tìm các cột amount có sẵn
                    available_amount_cols = [col for col in amount_analysis.keys() if amount_analysis[col]]
                    
                    if available_amount_cols:
                        # Tạo tabs cho các loại amount khác nhau
                        amount_tabs = st.tabs([f"📊 {col.replace('_', ' ').title()}" for col in available_amount_cols])
                        
                        for i, amount_col in enumerate(available_amount_cols):
                            with amount_tabs[i]:
                                col1, col2 = st.columns([1, 1])
                                
                                with col1:
                                    # Bar chart cho tổng amount
                                    service_types = list(amount_analysis[amount_col].keys())
                                    total_amounts = [amount_analysis[amount_col][st]['total'] for st in service_types]
                                    
                                    fig_total = px.bar(
                                        x=service_types,
                                        y=total_amounts,
                                        title=f"Tổng {amount_col.replace('_', ' ').title()} theo Service Type",
                                        labels={'x': 'Service Type', 'y': 'Tổng Amount (VND)'},
                                        color=total_amounts,
                                        color_continuous_scale='viridis'
                                    )
                                    fig_total.update_layout(
                                        height=400,
                                        xaxis_tickangle=45,
                                        yaxis_tickformat=',.0f'
                                    )
                                    st.plotly_chart(fig_total, use_container_width=True)
                                
                                with col2:
                                    # Bar chart cho average amount
                                    avg_amounts = [amount_analysis[amount_col][st]['average'] for st in service_types]
                                    
                                    fig_avg = px.bar(
                                        x=service_types,
                                        y=avg_amounts,
                                        title=f"Trung bình {amount_col.replace('_', ' ').title()} theo Service Type",
                                        labels={'x': 'Service Type', 'y': 'Trung bình Amount (VND)'},
                                        color=avg_amounts,
                                        color_continuous_scale='plasma'
                                    )
                                    fig_avg.update_layout(
                                        height=400,
                                        xaxis_tickangle=45,
                                        yaxis_tickformat=',.0f'
                                    )
                                    st.plotly_chart(fig_avg, use_container_width=True)
                                
                                # Bảng summary
                                st.markdown(f"#### 📋 Chi tiết {amount_col.replace('_', ' ').title()}")
                                
                                summary_data = []
                                for service_type in service_types:
                                    data = amount_analysis[amount_col][service_type]
                                    summary_data.append({
                                        'Service Type': service_type,
                                        'Tổng Amount': f"{data['total']:,.0f}",
                                        'Số lượng': f"{data['count']:,}",
                                        'Trung bình': f"{data['average']:,.0f}",
                                        'Tỷ lệ tổng': f"{(data['total'] / sum(total_amounts) * 100):.1f}%" if sum(total_amounts) > 0 else "0%"
                                    })
                                
                                summary_df = pd.DataFrame(summary_data)
                                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                                
                                # Overall summary metrics
                                col_m1, col_m2, col_m3 = st.columns(3)
                                
                                with col_m1:
                                    total_all = sum(total_amounts)
                                    st.metric("💰 Tổng cộng", f"{total_all:,.0f} VND")
                                
                                with col_m2:
                                    avg_all = total_all / sum([amount_analysis[amount_col][st]['count'] for st in service_types]) if sum([amount_analysis[amount_col][st]['count'] for st in service_types]) > 0 else 0
                                    st.metric("📊 Trung bình chung", f"{avg_all:,.0f} VND")
                                
                                with col_m3:
                                    total_count = sum([amount_analysis[amount_col][st]['count'] for st in service_types])
                                    st.metric("📝 Tổng giao dịch", f"{total_count:,}")
                        
                        # So sánh tổng quan giữa các loại amount
                        if len(available_amount_cols) > 1:
                            st.markdown("### 🔍 So sánh tổng quan giữa các loại Amount")
                            
                            # Tạo dữ liệu so sánh
                            comparison_data = []
                            service_types_all = set()
                            
                            # Collect all service types
                            for amount_col in available_amount_cols:
                                service_types_all.update(amount_analysis[amount_col].keys())
                            
                            service_types_all = list(service_types_all)
                            
                            for service_type in service_types_all:
                                row = {'Service Type': service_type}
                                for amount_col in available_amount_cols:
                                    if service_type in amount_analysis[amount_col]:
                                        row[f'{amount_col.replace("_", " ").title()}'] = amount_analysis[amount_col][service_type]['total']
                                    else:
                                        row[f'{amount_col.replace("_", " ").title()}'] = 0
                                comparison_data.append(row)
                            
                            # Create grouped bar chart
                            comparison_df = pd.DataFrame(comparison_data)
                            
                            if not comparison_df.empty:
                                fig_comparison = px.bar(
                                    comparison_df,
                                    x='Service Type',
                                    y=[col for col in comparison_df.columns if col != 'Service Type'],
                                    title="So sánh tổng Amount giữa các loại theo Service Type",
                                    barmode='group',
                                    labels={'value': 'Amount (VND)', 'variable': 'Amount Type'}
                                )
                                fig_comparison.update_layout(
                                    height=500,
                                    xaxis_tickangle=45,
                                    yaxis_tickformat=',.0f'
                                )
                                st.plotly_chart(fig_comparison, use_container_width=True)
                    
                    else:
                        st.info("ℹ️ Không tìm thấy dữ liệu amount để phân tích")
                else:
                    st.warning("⚠️ Không thể phân tích amount theo service type")
            else:
                st.info("ℹ️ Không có cột SERVICE_TYPE để phân tích")

    def render_drill_down_analysis(self):
        """Hiển thị phân tích chi tiết cho status được chọn"""
        if st.session_state.get('drill_down_data') is None:
            return
            
        drill_df = st.session_state.drill_down_data
        status = st.session_state.get('drill_down_status', 'Unknown')
        count = st.session_state.get('drill_down_count', 0)
        
        st.markdown("---")
        st.markdown(f"### 🔍 Chi tiết: {status}")
        st.markdown(f"**📊 Tổng số records:** {count:,}")
        
        # Header với buttons
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"#### Danh sách Order IDs và thông tin chi tiết")
        with col2:
            if st.button("🔙 Quay lại", key="back_to_overview"):
                # Clear drill-down data
                del st.session_state.drill_down_data
                del st.session_state.drill_down_status  
                del st.session_state.drill_down_count
                st.rerun()
        with col3:
            # Export button
            if not drill_df.is_empty():
                export_df = drill_df.to_pandas()
                csv_data = export_df.to_csv(index=False)
                st.download_button(
                    label="📥 Export CSV",
                    data=csv_data,
                    file_name=f"{status}_details_{st.session_state.selected_date}.csv",
                    mime="text/csv",
                    key="export_drill_down"
                )
        
        if not drill_df.is_empty():
            # Quick stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                unique_orders = drill_df.select('ORDER_ID').n_unique() if 'ORDER_ID' in drill_df.columns else 0
                st.metric("🆔 Unique Orders", f"{unique_orders:,}")
            
            with col2:
                unique_merchants = drill_df.select('MERCHANT').n_unique() if 'MERCHANT' in drill_df.columns else 0
                st.metric("🏪 Merchants", f"{unique_merchants:,}")
            
            with col3:
                if 'AMOUNT' in drill_df.columns:
                    total_amount = drill_df.select(pl.col('AMOUNT').sum()).item()
                    st.metric("💰 Total Amount", f"{total_amount:,.0f}")
                else:
                    st.metric("💰 Amount", "N/A")
            
            with col4:
                if 'SERVICE_TYPE' in drill_df.columns:
                    service_counts = drill_df.group_by('SERVICE_TYPE').agg(pl.count()).height
                    st.metric("🚗 Service Types", f"{service_counts}")
                else:
                    st.metric("🚗 Service Types", "N/A")
            
            # Filters
            st.markdown("#### 🔧 Bộ lọc")
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            # Initialize filter variables
            selected_merchants = ['All']
            selected_services = ['All']
            
            with filter_col1:
                # Merchant filter
                if 'MERCHANT' in drill_df.columns:
                    merchants = drill_df.select('MERCHANT').unique().to_pandas()['MERCHANT'].tolist()
                    selected_merchants = st.multiselect(
                        "🏪 Merchant:",
                        options=['All'] + merchants,
                        default=['All'],
                        key="merchant_filter"
                    )
            
            with filter_col2:
                # Service type filter
                if 'SERVICE_TYPE' in drill_df.columns:
                    service_types = drill_df.select('SERVICE_TYPE').unique().to_pandas()['SERVICE_TYPE'].tolist()
                    selected_services = st.multiselect(
                        "🚗 Service Type:",
                        options=['All'] + service_types,
                        default=['All'],
                        key="service_filter"
                    )
            
            with filter_col3:
                # Show top N records
                max_records = min(1000, drill_df.height)
                show_records = st.number_input(
                    "📊 Hiển thị records:",
                    min_value=10,
                    max_value=max_records,
                    value=min(100, max_records),
                    step=10,
                    key="show_records_filter"
                )
            
            # Apply filters
            filtered_df = drill_df
            
            if 'MERCHANT' in drill_df.columns and 'All' not in selected_merchants:
                filtered_df = filtered_df.filter(pl.col('MERCHANT').is_in(selected_merchants))
            
            if 'SERVICE_TYPE' in drill_df.columns and 'All' not in selected_services:
                filtered_df = filtered_df.filter(pl.col('SERVICE_TYPE').is_in(selected_services))
            
            # Display filtered data
            if not filtered_df.is_empty():
                st.markdown(f"#### 📋 Dữ liệu chi tiết ({filtered_df.height:,} records)")
                
                # Convert to pandas for display
                display_df = filtered_df.head(show_records).to_pandas()
                
                # Select important columns for display
                important_cols = []
                available_cols = display_df.columns.tolist()
                
                # Priority columns
                priority_cols = ['ORDER_ID', 'MERCHANT', 'AMOUNT', 'SERVICE_TYPE', 'RECONCILE_STATUS', 
                               'INSURANCE_STATUS', 'IS_BUSINESS_ORDER', 'ORDER_TIME', 'CREATED_TIME']
                
                for col in priority_cols:
                    if col in available_cols:
                        important_cols.append(col)
                
                # Add remaining columns
                for col in available_cols:
                    if col not in important_cols:
                        important_cols.append(col)
                
                # Reorder dataframe
                display_df = display_df[important_cols]
                
                # Display with pagination-like behavior
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=400,
                    column_config={
                        "ORDER_ID": st.column_config.TextColumn("Order ID", width="medium"),
                        "AMOUNT": st.column_config.NumberColumn("Amount", format="%.0f"),
                        "ORDER_TIME": st.column_config.DatetimeColumn("Order Time"),
                        "CREATED_TIME": st.column_config.DatetimeColumn("Created Time"),
                    }
                )
                
                # Summary info
                st.info(f"📝 Hiển thị {len(display_df):,} trong tổng số {filtered_df.height:,} records (sau khi lọc)")
                
            else:
                st.warning("⚠️ Không có dữ liệu sau khi áp dụng bộ lọc")
        else:
            st.warning("⚠️ Không có dữ liệu để hiển thị")
    
    def render_insurance_analysis(self):
        """Phân tích INSURANCE_STATUS"""
        if st.session_state.current_data is not None and not st.session_state.current_data.is_empty():
            df = st.session_state.current_data
            
            if 'INSURANCE_STATUS' in df.columns:
                st.markdown("## 🛡️ Phân tích Bảo hiểm (INSURANCE_STATUS)")
                
                insurance_stats = self.reader.analyze_insurance_status(df)
                
                if insurance_stats:
                    # Biểu đồ bar chart
                    fig = px.bar(
                        x=list(insurance_stats.keys()),
                        y=list(insurance_stats.values()),
                        title="Phân bố Trạng thái Bảo hiểm",
                        labels={'x': 'Insurance Status', 'y': 'Số lượng'},
                        color=list(insurance_stats.values()),
                        color_continuous_scale='viridis'
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Bảng thống kê
                    col1, col2 = st.columns(2)
                    with col1:
                        insurance_df = pd.DataFrame(
                            list(insurance_stats.items()),
                            columns=['Trạng thái', 'Số lượng']
                        )
                        insurance_df['Tỷ lệ %'] = (insurance_df['Số lượng'] / insurance_df['Số lượng'].sum() * 100).round(2)
                        st.dataframe(insurance_df, use_container_width=True)
    
    def render_business_analysis(self):
        """Phân tích Business Orders"""
        if st.session_state.current_data is not None and not st.session_state.current_data.is_empty():
            df = st.session_state.current_data
            
            if 'IS_BUSINESS_ORDER' in df.columns:
                st.markdown("### 🏢 Phân tích Business Orders")
                
                business_stats = self.reader.analyze_business_orders(df)
                
                if business_stats:
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        # Pie chart cho business orders
                        # Clean up labels for better display
                        clean_labels = []
                        clean_values = []
                        for label, value in business_stats.items():
                            if str(label).lower() in ['true', '1', 'yes']:
                                clean_labels.append('Business Orders')
                            elif str(label).lower() in ['false', '0', 'no']:
                                clean_labels.append('Non-Business Orders')
                            else:
                                clean_labels.append(f'Unknown ({label})')
                            clean_values.append(value)
                        
                        fig = px.pie(
                            values=clean_values,
                            names=clean_labels,
                            title="Phân bố Business vs Non-Business",
                            color_discrete_sequence=['#FF9999', '#66B2FF', '#99FF99']
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        fig.update_layout(height=350)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Bảng thống kê chi tiết
                        business_df = pd.DataFrame(
                            list(zip(clean_labels, clean_values)),
                            columns=['Loại đơn hàng', 'Số lượng']
                        )
                        business_df['Tỷ lệ %'] = (business_df['Số lượng'] / business_df['Số lượng'].sum() * 100).round(2)
                        
                        st.markdown("**📊 Thống kê chi tiết:**")
                        st.dataframe(business_df, use_container_width=True, hide_index=True)
                        
                        # Summary metrics
                        total_orders = sum(clean_values)
                        business_count = next((v for l, v in zip(clean_labels, clean_values) if 'Business' in l and 'Non-' not in l), 0)
                        business_rate = (business_count / total_orders * 100) if total_orders > 0 else 0
                        
                        st.metric("📈 Tỷ lệ Business", f"{business_rate:.1f}%")
                        st.metric("📝 Tổng đơn hàng", f"{total_orders:,}")
    
    def render_service_type_analysis(self):
        """Phân tích Service Type (Ride/Express)"""
        if st.session_state.current_data is not None and not st.session_state.current_data.is_empty():
            df = st.session_state.current_data
            
            if 'SERVICE_TYPE' in df.columns:
                st.markdown("### 🚗 Phân tích Service Type")
                
                service_stats = self.reader.analyze_service_type(df)
                
                if service_stats:
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        # Bar chart cho service types
                        fig = px.bar(
                            x=list(service_stats.keys()),
                            y=list(service_stats.values()),
                            title="Phân bố theo Service Type",
                            labels={'x': 'Service Type', 'y': 'Số lượng'},
                            color=list(service_stats.values()),
                            color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
                        )
                        fig.update_layout(
                            height=350,
                            xaxis_tickangle=45
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Bảng thống kê chi tiết
                        service_df = pd.DataFrame(
                            list(service_stats.items()),
                            columns=['Service Type', 'Số lượng']
                        )
                        service_df['Tỷ lệ %'] = (service_df['Số lượng'] / service_df['Số lượng'].sum() * 100).round(2)
                        
                        st.markdown("**📊 Thống kê chi tiết:**")
                        st.dataframe(service_df, use_container_width=True, hide_index=True)
                        
                        # Summary metrics
                        total_orders = sum(service_stats.values())
                        ride_count = service_stats.get('Ride (Normal)', 0)
                        express_count = service_stats.get('Express', 0)
                        unknown_count = service_stats.get('Không xác định', 0)
                        
                        st.metric("🚗 Ride Orders", f"{ride_count:,}")
                        st.metric("⚡ Express Orders", f"{express_count:,}")
                        if unknown_count > 0:
                            st.metric("❓ Không xác định", f"{unknown_count:,}")

    def render_order_search(self):
        """Tìm kiếm Order ID đặc biệt"""
        st.markdown("## 🔍 Tìm kiếm Order ID đặc biệt")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            order_ids_input = st.text_area(
                "Nhập Order IDs (mỗi ID một dòng):",
                placeholder="01Z1ABCD123\n01Z2EFGH456\n01Z3IJKL789",
                height=100
            )
        
        with col2:
            search_button = st.button("🔍 Tìm kiếm", type="primary")
        
        if search_button and order_ids_input and st.session_state.current_data is not None:
            order_ids = [id.strip() for id in order_ids_input.split('\n') if id.strip()]
            
            if order_ids:
                with st.spinner("Đang tìm kiếm..."):
                    results = self.reader.find_special_orders(st.session_state.current_data, order_ids)
                    
                    if not results.is_empty():
                        st.success(f"✅ Tìm thấy {results.height} bản ghi")
                        
                        # Chuyển đổi sang pandas để hiển thị
                        results_pd = results.to_pandas()
                        
                        # Hiển thị kết quả
                        st.dataframe(results_pd, use_container_width=True)
                        
                        # Download CSV
                        csv = results_pd.to_csv(index=False)
                        st.download_button(
                            label="📥 Tải xuống CSV",
                            data=csv,
                            file_name=f"special_orders_{st.session_state.selected_date}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("⚠️ Không tìm thấy Order ID nào")
    
    def render_data_viewer(self):
        """Hiển thị dữ liệu thô"""
        if st.session_state.current_data is not None and not st.session_state.current_data.is_empty():
            st.markdown("## 👁️ Xem dữ liệu thô")
            
            df = st.session_state.current_data
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                show_rows = st.number_input("Số dòng hiển thị:", min_value=10, max_value=1000, value=100)
            
            with col2:
                if st.button("🔄 Làm mới"):
                    st.rerun()
            
            # Hiển thị sample data
            sample_data = df.head(show_rows).to_pandas()
            st.dataframe(sample_data, use_container_width=True, height=400)
            
            # Thông tin cột
            with st.expander("📋 Thông tin các cột"):
                cols_info = []
                for col in df.columns:
                    null_count = df.select(pl.col(col).is_null().sum()).item()
                    data_type = str(df.select(pl.col(col)).dtypes[0])
                    cols_info.append({
                        'Cột': col,
                        'Kiểu dữ liệu': data_type,
                        'Giá trị null': null_count,
                        'Tỷ lệ null %': f"{(null_count/df.height*100):.2f}%"
                    })
                
                cols_df = pd.DataFrame(cols_info)
                st.dataframe(cols_df, use_container_width=True)
    
    def run(self):
        """Chạy dashboard"""
        self.render_header()
        self.render_sidebar()
        
        # Main content
        if st.session_state.current_data is not None:
            self.render_file_info()
            self.render_summary_stats()
            
            # Tabs cho các phân tích khác nhau
            tab1, tab2, tab3, tab4 = st.tabs([
                "🔄 Đối soát", 
                "🛡️ Bảo hiểm", 
                "🔍 Tìm kiếm", 
                "👁️ Dữ liệu thô"
            ])
            
            with tab1:
                self.render_reconcile_analysis()
            
            with tab2:
                self.render_insurance_analysis()
                self.render_business_analysis()
                self.render_service_type_analysis()
            
            with tab3:
                self.render_order_search()
            
            with tab4:
                self.render_data_viewer()
        
        else:
            # Hướng dẫn sử dụng
            st.markdown("""
            ## 🚀 Hướng dẫn sử dụng
            
            ### 📋 **Các bước thực hiện:**
            1. **Chọn năm**: Mặc định 2025
            2. **Chọn tháng**: Ví dụ 07 (tháng 7)
            3. **Tải danh sách**: Click "🔄 Tải danh sách ngày"
            4. **Chọn ngày**: Click vào ngày muốn phân tích
            5. **Xem kết quả**: Scroll xuống để xem analysis
            
            ### 📊 **Tính năng chính:**
            
            #### 🔄 **Phân tích Đối soát**
            - **✅ Match**: Giao dịch khớp hoàn toàn (GSM + PVI)
            - **❌ not_found_in_m**: Chỉ có ở PVI, không có ở GSM
            - **⚠️ not_found_in_external**: Chỉ có ở GSM, không có ở PVI
            - Biểu đồ phân bố và thống kê chi tiết
            
            #### 🛡️ **Phân tích Bảo hiểm**
            - Thống kê INSURANCE_STATUS
            - Phân bố: completed, cancelled, pending, failed
            - Biểu đồ bar chart trực quan
            
            #### 🔍 **Tìm kiếm Order ID**
            - Nhập nhiều Order ID (mỗi dòng một ID)
            - Tìm kiếm nhanh trong dữ liệu
            - Export kết quả ra CSV
            
            #### 👁️ **Xem dữ liệu thô**
            - Browse toàn bộ dữ liệu
            - Thông tin chi tiết các cột
            - Sample data với pagination
            
            ### 🎯 **Chú thích Grid Ngày:**
            - **➤ 05**: Ngày đang được chọn
            - **⭐**: Có file version 2 (được ưu tiên)
            - **🔵**: File lớn (>40MB) - màu xanh đậm
            - **⚪**: File nhỏ (<40MB) - màu trắng
            
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
                        st.metric("🗃️ Định dạng", "CSV")
                        
                except:
                    pass

if __name__ == "__main__":
    app = DashboardApp()
    app.run() 