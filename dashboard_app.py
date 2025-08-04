import streamlit as st
import pandas as pd
import polars as pl
import plotly.express as px
from datetime import datetime
import os
from csv_reader import CSVDataReader

# Cấu hình trang
st.set_page_config(
    page_title="PVI-GSM Dashboard System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 100%;
}

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

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

class DashboardApp:
    def __init__(self):
        self.reader = CSVDataReader()
        self.init_session_state()
    
    def init_session_state(self):
        if 'current_data' not in st.session_state:
            st.session_state.current_data = None
        if 'taixe_data' not in st.session_state:
            st.session_state.taixe_data = None
        if 'file_info' not in st.session_state:
            st.session_state.file_info = None
        if 'taixe_file_info' not in st.session_state:
            st.session_state.taixe_file_info = None
        if 'selected_date' not in st.session_state:
            st.session_state.selected_date = None
        if 'available_days' not in st.session_state:
            st.session_state.available_days = {}
        if 'load_message' not in st.session_state:
            st.session_state.load_message = ""
        if 'current_tab' not in st.session_state:
            st.session_state.current_tab = "launcher"
    
    def render_header(self):
        st.markdown('<h1 class="main-header">📊 PVI-GSM Dashboard System</h1>', unsafe_allow_html=True)
        
        # Debug info cho navigation
        print(f"DEBUG: render_header - current_tab: {st.session_state.current_tab}")
        
        # Navigation buttons thay vì tabs
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏠 Launcher", key="nav_launcher", use_container_width=True):
                print(f"DEBUG: Launcher nav button clicked")
                st.session_state.current_tab = "launcher"
                st.rerun()
        
        with col2:
            if st.button("🔄 Reconciliation", key="nav_reconciliation", use_container_width=True):
                print(f"DEBUG: Reconciliation nav button clicked")
                st.session_state.current_tab = "reconciliation"
                st.rerun()
        
        with col3:
            if st.button("🚗 Tài Xế", key="nav_taixe", use_container_width=True):
                print(f"DEBUG: Taixe nav button clicked")
                st.session_state.current_tab = "taixe"
                st.rerun()
        
        # Hiển thị current tab
        st.markdown(f"### 📍 **Đang xem: {st.session_state.current_tab.upper()}**")
    
    def render_sidebar(self):
        with st.sidebar:
            st.markdown("## ⚙️ Cài đặt")
            
            # Chọn năm
            year = st.selectbox(
                "📅 Năm:",
                [2025, 2024, 2023],
                index=0,
                key="app_year_selector"
            )
            
            # Chọn tháng
            month = st.selectbox(
                "📅 Tháng:",
                list(range(1, 13)),
                index=6,
                format_func=lambda x: f"{x:02d}",
                key="app_month_selector"
            )
            
            # Button tải danh sách ngày
            if st.button("🔄 Tải danh sách ngày", key="app_load_days_btn"):
                self.load_available_days(year, month)
                st.rerun()
            
            # Hiển thị grid ngày nếu có
            if st.session_state.available_days:
                st.markdown(f"### 📂 Các ngày có sẵn ({year}/{month:02d})")
                
                # Tạo grid buttons
                cols_per_row = 3
                days_list = sorted(st.session_state.available_days.keys())
                
                for i in range(0, len(days_list), cols_per_row):
                    cols = st.sidebar.columns(cols_per_row)
                    
                    for j, day in enumerate(days_list[i:i+cols_per_row]):
                        with cols[j]:
                            day_info = st.session_state.available_days[day]
                            
                            btn_text = f"{day:02d}"
                            if day_info['has_version_2']:
                                btn_text += " ⭐"
                            
                            is_selected = (st.session_state.selected_date == day_info['date_str'])
                            if is_selected:
                                btn_text = f"➤ {btn_text}"
                            
                            if st.button(btn_text, key=f"app_day_btn_{day}"):
                                self.load_day_data(year, month, day)
                                st.rerun()
                
                # Legend
                st.sidebar.markdown("""
                **Chú thích:**
                - ➤ = Ngày đang xem
                - ⭐ = Có file version 2
                """)
            
            # Message area
            if st.session_state.load_message:
                st.sidebar.info(st.session_state.load_message)
                st.session_state.load_message = ""
    
    def load_available_days(self, year: int, month: int):
        try:
            month_path = os.path.join(self.reader.base_path, str(year), f"{month:02d}")
            
            if not os.path.exists(month_path):
                st.session_state.load_message = f"⚠️ Không tìm thấy dữ liệu tháng {month}/{year}"
                return
            
            available_days = {}
            
            for day_name in os.listdir(month_path):
                day_path = os.path.join(month_path, day_name)
                
                if os.path.isdir(day_path) and day_name.isdigit():
                    day = int(day_name)
                    date_str = f"{year}{month:02d}{day:02d}"
                    
                    # Get file info
                    file_info = self.reader.get_file_info(day_path, date_str)
                    
                    if file_info['reconciled_file'] or file_info['taixe_file']:
                        available_days[day] = {
                            'path': day_path,
                            'date_str': date_str,
                            'has_version_2': file_info['has_version_2'],
                            'reconciled_file': file_info['reconciled_file'],
                            'taixe_file': file_info['taixe_file']
                        }
            
            st.session_state.available_days = available_days
            
            if available_days:
                st.session_state.load_message = f"✅ Tìm thấy {len(available_days)} ngày có dữ liệu"
            else:
                st.session_state.load_message = f"⚠️ Không tìm thấy dữ liệu nào trong {month}/{year}"
                
        except Exception as e:
            st.session_state.load_message = f"❌ Lỗi khi tải danh sách ngày: {e}"
    
    def load_day_data(self, year: int, month: int, day: int):
        try:
            available_days = st.session_state.available_days
            
            if not available_days or day not in available_days:
                st.session_state.load_message = f"❌ Không tìm thấy dữ liệu ngày {day}"
                return
            
            day_info = available_days[day]
            
            # Debug info
            print(f"DEBUG: Loading data for day {day}")
            print(f"DEBUG: Day info: {day_info}")
            
            # Clear previous data
            st.session_state.current_data = None
            st.session_state.taixe_data = None
            st.session_state.file_info = None
            st.session_state.taixe_file_info = None
            st.session_state.selected_date = None
            
            # Load reconciliation data
            if day_info['reconciled_file']:
                print(f"DEBUG: Loading reconciled file: {day_info['reconciled_file']}")
                df = self.reader.read_csv_polars(day_info['reconciled_file'])
                if df is not None and not df.is_empty():
                    print(f"DEBUG: Loaded reconciled data: {df.height} rows")
                    st.session_state.current_data = df
                    st.session_state.file_info = {
                        'date': day_info['date_str'],
                        'reconciled_file': day_info['reconciled_file'],
                        'reconciled_size_mb': os.path.getsize(day_info['reconciled_file']) / (1024 * 1024)
                    }
                else:
                    print(f"DEBUG: Failed to load reconciled data")
            else:
                print(f"DEBUG: No reconciled file found")
            
            # Load taixe data
            if day_info['taixe_file']:
                print(f"DEBUG: Loading taixe file: {day_info['taixe_file']}")
                taixe_df = self.reader.read_csv_polars(day_info['taixe_file'])
                if taixe_df is not None and not taixe_df.is_empty():
                    print(f"DEBUG: Loaded taixe data: {taixe_df.height} rows")
                    st.session_state.taixe_data = taixe_df
                    st.session_state.taixe_file_info = {
                        'date': day_info['date_str'],
                        'taixe_file': day_info['taixe_file'],
                        'taixe_size_mb': os.path.getsize(day_info['taixe_file']) / (1024 * 1024)
                    }
                else:
                    print(f"DEBUG: Failed to load taixe data")
            else:
                print(f"DEBUG: No taixe file found")
            
            st.session_state.selected_date = day_info['date_str']
            st.session_state.load_message = f"✅ Đã tải dữ liệu ngày {day:02d}/{month:02d}/{year}"
            
            print(f"DEBUG: Final session state:")
            print(f"  - current_data: {st.session_state.current_data is not None}")
            print(f"  - taixe_data: {st.session_state.taixe_data is not None}")
            print(f"  - selected_date: {st.session_state.selected_date}")
            
        except Exception as e:
            print(f"DEBUG: Error loading data: {e}")
            st.session_state.load_message = f"❌ Lỗi khi tải dữ liệu: {e}"
    
    def render_launcher(self):
        st.markdown("### 🎯 Chọn dashboard để phân tích dữ liệu PVI-GSM")
        
        # Hướng dẫn sử dụng
        st.info("""
        **📋 Hướng dẫn sử dụng:**
        1. **Chọn năm/tháng** từ sidebar bên trái
        2. **Click "🔄 Tải danh sách ngày"** để load danh sách ngày có sẵn
        3. **Chọn ngày** từ grid hiển thị
        4. **Chọn tab** Reconciliation hoặc Tài Xế để xem data
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: white; padding: 2rem; border-radius: 12px; border-left: 6px solid #28a745;">
                <h2>🔄 Reconciliation Dashboard</h2>
                <p><strong>Phân tích đối soát giao dịch chính</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚀 Mở Reconciliation Dashboard", key="btn_reconciled", use_container_width=True):
                print(f"DEBUG: Reconciliation button clicked")
                st.session_state.current_tab = "reconciliation"
                print(f"DEBUG: Set current_tab to: {st.session_state.current_tab}")
                st.rerun()
        
        with col2:
            st.markdown("""
            <div style="background: white; padding: 2rem; border-radius: 12px; border-left: 6px solid #e74c3c;">
                <h2>🚗 Tài Xế Dashboard</h2>
                <p><strong>Phân tích đơn tai nạn tài xế</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚀 Mở Tài Xế Dashboard", key="btn_taixe", use_container_width=True):
                print(f"DEBUG: Taixe button clicked")
                st.session_state.current_tab = "taixe"
                print(f"DEBUG: Set current_tab to: {st.session_state.current_tab}")
                st.rerun()
        
        # Debug info
        st.markdown("### 🐛 Debug Info")
        col_debug1, col_debug2, col_debug3 = st.columns(3)
        
        with col_debug1:
            st.write("**Session State:**")
            st.write(f"- Current Tab: {st.session_state.current_tab}")
            st.write(f"- Selected Date: {st.session_state.selected_date}")
            st.write(f"- Available Days: {len(st.session_state.available_days)}")
        
        with col_debug2:
            st.write("**Data Status:**")
            st.write(f"- Reconciliation Data: {'✅' if st.session_state.current_data is not None else '❌'}")
            st.write(f"- Taixe Data: {'✅' if st.session_state.taixe_data is not None else '❌'}")
            st.write(f"- File Info: {'✅' if st.session_state.file_info is not None else '❌'}")
        
        with col_debug3:
            st.write("**Path Info:**")
            st.write(f"- Base Path: {self.reader.base_path}")
            st.write(f"- Path Exists: {'✅' if os.path.exists(self.reader.base_path) else '❌'}")
            if os.path.exists(self.reader.base_path):
                try:
                    year_folders = os.listdir(self.reader.base_path)
                    st.write(f"- Years: {year_folders}")
                except:
                    st.write("- Years: Error reading")
        
        # Thông tin chung
        st.markdown("---")
        st.markdown("### 📋 Thông tin chung")
        
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            st.markdown("""
            **📁 Cấu trúc thư mục:**
            ```
            F:/powerbi/gsm_data/out/
            ├── 2025/07/01/
            │   ├── pvi_transaction_reconciled_20250701.csv
            │   ├── pvi_transaction_reconciled_20250701_2.csv
            │   └── pvi_transaction_reconciled_taixe_20250701.csv
            ```
            """)
        
        with col_info2:
            st.markdown("""
            **📊 Loại file:**
            
            **🔄 Reconciliation:**
            - `pvi_transaction_reconciled_YYYYMMDD.csv`
            - `pvi_transaction_reconciled_YYYYMMDD_2.csv` (ưu tiên)
            
            **🚗 Tài xế:**
            - `pvi_transaction_reconciled_taixe_YYYYMMDD.csv`
            """)
        
        with col_info3:
            st.markdown("""
            **⚡ Công nghệ:**
            
            - **🐍 Python**: Streamlit, Polars, Pandas
            - **📊 Visualization**: Plotly Express
            - **🚀 Performance**: Polars cho file lớn
            - **💾 Data**: CSV files (100MB+)
            """)
    
    def render_reconciliation_dashboard(self):
        print(f"DEBUG: render_reconciliation_dashboard called")
        print(f"DEBUG: current_data is None: {st.session_state.current_data is None}")
        print(f"DEBUG: selected_date: {st.session_state.selected_date}")
        
        if st.session_state.current_data is None:
            st.warning("⚠️ **Chưa có dữ liệu!** Vui lòng:")
            st.markdown("""
            1. **Chọn năm/tháng** từ sidebar bên trái
            2. **Click "🔄 Tải danh sách ngày"** 
            3. **Chọn ngày** từ grid hiển thị
            4. **Quay lại tab này** để xem data
            """)
            
            # Debug info
            st.markdown("### 🐛 Debug Info")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Current Data:** {st.session_state.current_data}")
                st.write(f"**Selected Date:** {st.session_state.selected_date}")
                st.write(f"**Available Days:** {len(st.session_state.available_days)}")
            with col2:
                st.write(f"**File Info:** {st.session_state.file_info}")
                st.write(f"**Base Path:** {self.reader.base_path}")
                st.write(f"**Path Exists:** {os.path.exists(self.reader.base_path)}")
            return
        
        df = st.session_state.current_data
        print(f"DEBUG: Data loaded successfully: {df.height} rows, {df.width} columns")
        
        # File info
        if st.session_state.file_info:
            info = st.session_state.file_info
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📅 Ngày", info['date'])
            with col2:
                st.metric("📄 File", os.path.basename(info['reconciled_file']))
            with col3:
                st.metric("📊 Size", f"{info['reconciled_size_mb']:.1f} MB")
            with col4:
                st.metric("📝 Records", f"{df.height:,}")
        
        # Summary stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📝 Records", f"{df.height:,}")
        with col2:
            if 'ORDER_ID' in df.columns:
                unique_orders = df.select(pl.col('ORDER_ID').n_unique()).item()
                st.metric("🆔 Orders", f"{unique_orders:,}")
            else:
                st.metric("🆔 Orders", "N/A")
        with col3:
            if 'MERCHANT' in df.columns:
                unique_merchants = df.select(pl.col('MERCHANT').n_unique()).item()
                st.metric("🏪 Merchants", f"{unique_merchants:,}")
            else:
                st.metric("🏪 Merchants", "N/A")
        with col4:
            if 'AMOUNT' in df.columns:
                total_amount = df.select(pl.col('AMOUNT').sum()).item()
                st.metric("💰 Total", f"{total_amount:,.0f}")
            else:
                st.metric("💰 Total", "N/A")
        
        # Analysis tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🔄 Đối soát", "🛡️ Bảo hiểm", "🏢 Business", "🚗 Service Type", "🔍 Tìm kiếm", "👁️ Dữ liệu"])
        
        with tab1:
            self.render_reconcile_analysis(df)
        
        with tab2:
            self.render_insurance_analysis(df)
        
        with tab3:
            self.render_business_analysis(df)
        
        with tab4:
            self.render_service_type_analysis(df)
        
        with tab5:
            self.render_search_orders(df)
        
        with tab6:
            self.render_data_viewer(df)
    
    def render_taixe_dashboard(self):
        if st.session_state.taixe_data is None:
            st.warning("⚠️ **Chưa có dữ liệu tài xế!** Vui lòng:")
            st.markdown("""
            1. **Chọn năm/tháng** từ sidebar bên trái
            2. **Click "🔄 Tải danh sách ngày"** 
            3. **Chọn ngày** từ grid hiển thị
            4. **Quay lại tab này** để xem data
            """)
            
            # Debug info
            st.markdown("### 🐛 Debug Info")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Taixe Data:** {st.session_state.taixe_data}")
                st.write(f"**Selected Date:** {st.session_state.selected_date}")
                st.write(f"**Available Days:** {len(st.session_state.available_days)}")
            with col2:
                st.write(f"**Taixe File Info:** {st.session_state.taixe_file_info}")
                st.write(f"**Base Path:** {self.reader.base_path}")
                st.write(f"**Path Exists:** {os.path.exists(self.reader.base_path)}")
            return
        
        df = st.session_state.taixe_data
        
        # File info
        if st.session_state.taixe_file_info:
            info = st.session_state.taixe_file_info
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📅 Ngày", info['date'])
            with col2:
                st.metric("📄 File", os.path.basename(info['taixe_file']))
            with col3:
                st.metric("📊 Size", f"{info['taixe_size_mb']:.1f} MB")
            with col4:
                st.metric("📝 Records", f"{df.height:,}")
        
        # Summary stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📝 Records", f"{df.height:,}")
        with col2:
            st.metric("📋 Columns", f"{df.width}")
        with col3:
            if 'AMOUNT' in df.columns:
                total_amount = df.select(pl.col('AMOUNT').sum()).item()
                st.metric("💰 Total", f"{total_amount:,.0f}")
            else:
                st.metric("💰 Total", "N/A")
        with col4:
            if 'ORDER_ID' in df.columns:
                unique_orders = df.select(pl.col('ORDER_ID').n_unique()).item()
                st.metric("🆔 Orders", f"{unique_orders:,}")
            else:
                st.metric("🆔 Orders", "N/A")
        
        # Analysis tabs
        tab1, tab2, tab3 = st.tabs(["🚗 Phân tích", "🔍 Tìm kiếm", "👁️ Dữ liệu"])
        
        with tab1:
            self.render_taixe_analysis(df)
        
        with tab2:
            self.render_taixe_search(df)
        
        with tab3:
            self.render_taixe_data_viewer(df)
    
    def render_reconcile_analysis(self, df):
        # Tìm cột RECONCILE_STATUS với các tên có thể có
        reconcile_col = None
        possible_reconcile_cols = ['RECONCILE_STATUS', 'Reconcile Status', 'RECONCILE STATUS', 'RECONCILE', 'GSM_ORDER_RECONCILE', 'GSM_ORDE_RECONCILE', 'RECONCILE_STAT']
        
        for col in possible_reconcile_cols:
            if col in df.columns:
                reconcile_col = col
                break
        
        if reconcile_col:
            st.success(f"✅ Tìm thấy cột: **{reconcile_col}**")
            
            reconcile_stats = df.group_by(reconcile_col).agg(
                pl.count().alias('count')
            ).sort('count', descending=True)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("#### 📊 Số liệu thống kê")
                
                # Hiển thị các status với buttons để drill down
                for row in reconcile_stats.iter_rows(named=True):
                    status = row[reconcile_col]
                    count = row['count']
                    percentage = (count / df.height) * 100
                    
                    # Màu sắc theo trạng thái
                    if status == 'match':
                        icon = "✅"
                        button_type = "secondary"
                    elif 'not_found_in_m' in status:
                        icon = "❌"
                        button_type = "primary"
                    elif 'not_found_in_external' in status:
                        icon = "⚠️"
                        button_type = "primary"
                    else:
                        icon = "📊"
                        button_type = "primary"
                    
                    # Card với button để drill down
                    with st.container():
                        col_btn, col_info = st.columns([3, 1])
                        
                        with col_btn:
                            st.markdown(f"""
                            <div class="metric-card">
                                <strong>{icon} {status}</strong><br>
                                {count:,} records ({percentage:.1f}%)
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_info:
                            # Chỉ hiển thị button drill-down cho non-match status có ít records
                            if status != 'match' and count < 10000:  # Chỉ cho phép drill-down nếu < 10k records
                                if st.button(f"🔍 Chi tiết", key=f"drill_{status}", type=button_type, help=f"Xem chi tiết {count} records"):
                                    # Store drill-down data in session state
                                    filtered_df = df.filter(pl.col(reconcile_col) == status)
                                    st.session_state.drill_down_data = filtered_df
                                    st.session_state.drill_down_status = status
                                    st.session_state.drill_down_count = count
                                    st.rerun()
                    
                    st.markdown("<br>", unsafe_allow_html=True)
            
            with col2:
                # Biểu đồ pie chart
                fig = px.pie(
                    reconcile_stats.to_pandas(),
                    values='count',
                    names=reconcile_col,
                    title=f"Phân bố {reconcile_col}",
                    color_discrete_map={
                        'match': '#28a745',
                        'not_found_in_m': '#dc3545',
                        'not_found_in_external': '#ffc107'
                    }
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Hiển thị drill-down data nếu có
        if st.session_state.get('drill_down_data') is not None:
            self.render_drill_down_analysis()
        
        # Thêm phân tích amount theo service type
        self.render_amount_analysis_by_service_type(df)
        
    def render_insurance_analysis(self, df):
        if 'INSURANCE_STATUS' in df.columns:
            insurance_stats = df.group_by('INSURANCE_STATUS').agg(
                pl.count().alias('count')
            ).sort('count', descending=True)

            fig = px.bar(
                insurance_stats.to_pandas(),
                x='INSURANCE_STATUS',
                y='count',
                title="Phân bố INSURANCE_STATUS"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render_search_orders(self, df):
        order_ids_input = st.text_area(
            "Nhập Order IDs (mỗi dòng một ID):",
            height=100
        )
        
        if st.button("🔍 Tìm kiếm"):
            if order_ids_input and 'ORDER_ID' in df.columns:
                order_ids = [id.strip() for id in order_ids_input.split('\n') if id.strip()]
                results = df.filter(pl.col('ORDER_ID').is_in(order_ids))
                
                if not results.is_empty():
                    st.success(f"✅ Tìm thấy {results.height} bản ghi")
                    st.dataframe(results.to_pandas(), use_container_width=True)
                else:
                    st.warning("⚠️ Không tìm thấy Order ID nào")
    
    def render_data_viewer(self, df):
        show_rows = st.number_input("Số dòng hiển thị:", min_value=10, max_value=1000, value=100)
        st.dataframe(df.head(show_rows).to_pandas(), use_container_width=True)
    
    def render_taixe_analysis(self, df):
        # Debug: Hiển thị tên cột thực tế
        st.markdown("### 🔍 Debug: Tên cột thực tế")
        st.write(f"**Tổng số cột:** {df.width}")
        st.write(f"**Tên các cột:** {list(df.columns)}")
        
        # Phân tích Bike vs Car dựa trên GSM_AMOUNT
        st.markdown("### 🚗 Phân tích Bike vs Car (dựa trên GSM_AMOUNT)")
        
        # Tìm cột GSM_AMOUNT với các tên có thể có
        gsm_amount_col = None
        possible_gsm_cols = ['GSM Amount', 'GSM_AMOUNT', 'GSM_AMO', 'GSM_AMOUNT_MERCHANT', 'GSM_AMO_MERCHANT', 'GSM_AMOUNT_MERCH', 'GSM_AMO_MERCH']
        
        for col in possible_gsm_cols:
            if col in df.columns:
                gsm_amount_col = col
                break
        
        if gsm_amount_col:
            st.success(f"✅ Tìm thấy cột: **{gsm_amount_col}**")
            
            # Phân tích theo GSM_AMOUNT: 100 = Bike, 200 = Car
            bike_df = df.filter(pl.col(gsm_amount_col) == 100)
            car_df = df.filter(pl.col(gsm_amount_col) == 200)
            other_df = df.filter(~pl.col(gsm_amount_col).is_in([100, 200]))
            
            bike_count = bike_df.height
            car_count = car_df.height
            other_count = other_df.height
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("#### 📊 Thống kê Bike vs Car")
                
                total = df.height
                bike_percentage = (bike_count / total * 100) if total > 0 else 0
                car_percentage = (car_count / total * 100) if total > 0 else 0
                other_percentage = (other_count / total * 100) if total > 0 else 0
                
                st.markdown(f"**🛵 Bike ({gsm_amount_col} = 100)**: {bike_count:,} ({bike_percentage:.1f}%)")
                st.markdown(f"**🚗 Car ({gsm_amount_col} = 200)**: {car_count:,} ({car_percentage:.1f}%)")
                if other_count > 0:
                    st.markdown(f"**🚙 Khác**: {other_count:,} ({other_percentage:.1f}%)")
                
                # Summary metrics
                st.markdown("---")
                col_bike, col_car = st.columns(2)
                with col_bike:
                    st.metric("🛵 Bike Orders", f"{bike_count:,}")
                with col_car:
                    st.metric("🚗 Car Orders", f"{car_count:,}")
            
            with col2:
                # Pie chart cho Bike vs Car
                vehicle_data = {
                    'Loại xe': ['Bike', 'Car', 'Khác'],
                    'Số lượng': [bike_count, car_count, other_count]
                }
                vehicle_df = pd.DataFrame(vehicle_data)
                
                fig_vehicle = px.pie(
                    vehicle_df,
                    values='Số lượng',
                    names='Loại xe',
                    title="Phân bố Bike vs Car",
                    color_discrete_sequence=['#FF9999', '#66B2FF', '#99FF99']
                )
                fig_vehicle.update_traces(textposition='inside', textinfo='percent+label')
                fig_vehicle.update_layout(height=400)
                st.plotly_chart(fig_vehicle, use_container_width=True)
        else:
            st.warning(f"⚠️ Không tìm thấy cột GSM_AMOUNT. Đã tìm kiếm: {possible_gsm_cols}")
            st.info("💡 Dựa vào hình ảnh, có thể tên cột là 'GSM Amo Merchant' hoặc tương tự")
        
        # Phân tích RECONCILE_STATUS
        st.markdown("### 🔄 Phân tích RECONCILE_STATUS")
        
        # Tìm cột RECONCILE_STATUS với các tên có thể có
        reconcile_col = None
        possible_reconcile_cols = ['Reconcile Status', 'RECONCILE STATUS', 'RECONCILE_STATUS', 'RECONCILE', 'GSM_ORDER_RECONCILE', 'GSM_ORDE_RECONCILE', 'RECONCILE_STAT']
        
        for col in possible_reconcile_cols:
            if col in df.columns:
                reconcile_col = col
                break
        
        if reconcile_col:
            st.success(f"✅ Tìm thấy cột: **{reconcile_col}**")
            
            reconcile_stats = df.group_by(reconcile_col).agg(
                pl.count().alias('count')
            ).sort('count', descending=True)

            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("#### 📊 Thống kê RECONCILE_STATUS")
                
                # Hiển thị các status với buttons để drill down
                for row in reconcile_stats.iter_rows(named=True):
                    status = row[reconcile_col]
                    count = row['count']
                    percentage = (count / df.height) * 100
                    
                    # Màu sắc theo trạng thái
                    if status == 'match':
                        icon = "✅"
                        button_type = "secondary"
                    elif 'not_found_in_m' in status:
                        icon = "❌"
                        button_type = "primary"
                    elif 'not_found_in_external' in status:
                        icon = "⚠️"
                        button_type = "primary"
                    else:
                        icon = "📊"
                        button_type = "primary"
                    
                    # Card với button để drill down
                    with st.container():
                        col_btn, col_info = st.columns([3, 1])
                        
                        with col_btn:
                            st.markdown(f"""
                            <div class="metric-card">
                                <strong>{icon} {status}</strong><br>
                                {count:,} records ({percentage:.1f}%)
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_info:
                            # Chỉ hiển thị button drill-down cho non-match status có ít records
                            if status != 'match' and count < 10000:  # Chỉ cho phép drill-down nếu < 10k records
                                if st.button(f"🔍 Chi tiết", key=f"taixe_drill_{status}", type=button_type, help=f"Xem chi tiết {count} records"):
                                    # Store drill-down data in session state
                                    filtered_df = df.filter(pl.col(reconcile_col) == status)
                                    st.session_state.drill_down_data = filtered_df
                                    st.session_state.drill_down_status = status
                                    st.session_state.drill_down_count = count
                                    st.rerun()
                    
                    st.markdown("<br>", unsafe_allow_html=True)
            
            with col2:
                # Pie chart cho RECONCILE_STATUS
                fig = px.pie(
                    reconcile_stats.to_pandas(),
                    values='count',
                    names=reconcile_col,
                    title=f"Phân bố {reconcile_col} - Tài xế",
                    color_discrete_map={
                        'match': '#28a745',
                        'not_found_in_m': '#dc3545',
                        'not_found_in_external': '#ffc107'
                    }
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Hiển thị drill-down data nếu có
        if st.session_state.get('drill_down_data') is not None:
            self.render_drill_down_analysis()
        
        # Phân tích MERCHANT_STATUS
        st.markdown("### 🏪 Phân tích MERCHANT_STATUS")
        
        # Tìm cột MERCHANT_STATUS với các tên có thể có
        merchant_status_col = None
        possible_merchant_cols = ['Merchant Status', 'MERCHANT_STATUS', 'GSM_STATUS_MERCHANT', 'GSM_STATU_MERCHANT', 'MERCHANT_STAT', 'MERCH_STATUS']
        
        for col in possible_merchant_cols:
            if col in df.columns:
                merchant_status_col = col
                break
        
        if merchant_status_col:
            st.success(f"✅ Tìm thấy cột: **{merchant_status_col}**")
            
            merchant_status_stats = df.group_by(merchant_status_col).agg(
                pl.count().alias('count')
            ).sort('count', descending=True)
            
            st.markdown("#### 📊 Số liệu thống kê")
            
            # Hiển thị các status với buttons để drill down
            for row in merchant_status_stats.iter_rows(named=True):
                status = row[merchant_status_col]
                count = row['count']
                percentage = (count / df.height) * 100
                
                # Xác định màu và button type dựa trên status
                if 'fail' in str(status).lower() or 'error' in str(status).lower():
                    color = "🔴"
                    button_type = "secondary"
                elif 'success' in str(status).lower() or 'match' in str(status).lower():
                    color = "🟢"
                    button_type = "primary"
                else:
                    color = "🟡"
                    button_type = "secondary"
                
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"{color} **{status}**: {count:,} records ({percentage:.1f}%)")
                
                with col2:
                    st.metric("Số lượng", f"{count:,}")
                
                with col3:
                    # Hiển thị button drill-down cho tất cả status, đặc biệt là failed
                    if count < 10000:  # Chỉ cho phép drill-down nếu < 10k records
                        if st.button(f"🔍 Chi tiết", key=f"merchant_drill_{status}", type=button_type, help=f"Xem chi tiết {count} records"):
                            # Store drill-down data in session state
                            filtered_df = df.filter(pl.col(merchant_status_col) == status)
                            st.session_state.drill_down_data = filtered_df
                            st.session_state.drill_down_status = f"Merchant Status: {status}"
                            st.session_state.show_drill_down = True
                            st.rerun()
                
                st.divider()
            
            # Hiển thị riêng các đơn failed
            st.markdown("#### 🔴 Các đơn Failed/Error")
            
            failed_statuses = []
            for row in merchant_status_stats.iter_rows(named=True):
                status = row[merchant_status_col]
                if 'fail' in str(status).lower() or 'error' in str(status).lower():
                    failed_statuses.append(row)
            
            if failed_statuses:
                for row in failed_statuses:
                    status = row[merchant_status_col]
                    count = row['count']
                    percentage = (count / df.height) * 100
                    
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        st.markdown(f"🔴 **{status}**")
                    
                    with col2:
                        st.metric("Số đơn", f"{count:,}")
                    
                    with col3:
                        st.metric("Tỷ lệ", f"{percentage:.1f}%")
                    
                    with col4:
                        if st.button(f"📋 Xem chi tiết", key=f"failed_detail_{status}", type="secondary"):
                            # Store drill-down data in session state
                            filtered_df = df.filter(pl.col(merchant_status_col) == status)
                            st.session_state.drill_down_data = filtered_df
                            st.session_state.drill_down_status = f"Failed Merchant Status: {status}"
                            st.session_state.show_drill_down = True
                            st.rerun()
                    
                    st.divider()
                
                # Tổng kết failed
                total_failed = sum(row['count'] for row in failed_statuses)
                total_failed_percentage = (total_failed / df.height) * 100
                
                st.markdown("#### 📊 Tổng kết Failed")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🔴 Tổng đơn Failed", f"{total_failed:,}")
                with col2:
                    st.metric("📊 Tỷ lệ Failed", f"{total_failed_percentage:.1f}%")
                with col3:
                    st.metric("✅ Đơn thành công", f"{df.height - total_failed:,}")
                
            else:
                st.success("✅ Không có đơn nào bị failed/error!")
            
            # Pie chart
            fig_merchant = px.pie(
                merchant_status_stats.to_pandas(),
                values='count',
                names=merchant_status_col,
                title=f"Phân bố {merchant_status_col} - Tài xế",
                color_discrete_map={
                    'success': '#28a745',
                    'failed': '#dc3545',
                    'error': '#dc3545',
                    'match': '#28a745',
                    'not_found': '#ffc107'
                }
            )
            fig_merchant.update_traces(textposition='inside', textinfo='percent+label')
            fig_merchant.update_layout(height=400)
            st.plotly_chart(fig_merchant, use_container_width=True)
        else:
            st.info("ℹ️ Không có cột MERCHANT_STATUS để phân tích")
        
        # Phân tích Amount theo loại xe
        st.markdown("### 💰 Phân tích Amount theo loại xe (Bike vs Car)")
        
        if 'GSM Amount' in df.columns and 'Merchant Amount' in df.columns:
            # Phân tích GSM Amount theo loại xe
            gsm_bike_df = df.filter(pl.col('GSM Amount') == 100)
            gsm_car_df = df.filter(pl.col('GSM Amount') == 200)
            
            # Phân tích Merchant Amount theo loại xe
            merchant_bike_df = df.filter(pl.col('Merchant Amount') == 100)
            merchant_car_df = df.filter(pl.col('Merchant Amount') == 200)
            
            # Tính tổng tiền
            gsm_bike_total = gsm_bike_df.select(pl.col('GSM Amount').sum()).item() if not gsm_bike_df.is_empty() else 0
            gsm_car_total = gsm_car_df.select(pl.col('GSM Amount').sum()).item() if not gsm_car_df.is_empty() else 0
            merchant_bike_total = merchant_bike_df.select(pl.col('Merchant Amount').sum()).item() if not merchant_bike_df.is_empty() else 0
            merchant_car_total = merchant_car_df.select(pl.col('Merchant Amount').sum()).item() if not merchant_car_df.is_empty() else 0
            
            # Số lượng đơn hàng
            gsm_bike_count = gsm_bike_df.height
            gsm_car_count = gsm_car_df.height
            merchant_bike_count = merchant_bike_df.height
            merchant_car_count = merchant_car_df.height
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("#### 📊 GSM Amount theo loại xe")
                
                # Tạo dữ liệu cho chart
                gsm_data = {
                    'Loại xe': ['Bike (100)', 'Car (200)'],
                    'Tổng tiền': [gsm_bike_total, gsm_car_total],
                    'Số đơn': [gsm_bike_count, gsm_car_count]
                }
                gsm_df = pd.DataFrame(gsm_data)
                
                # Bar chart cho GSM Amount
                fig_gsm = px.bar(
                    gsm_df,
                    x='Loại xe',
                    y='Tổng tiền',
                    title="GSM Amount theo loại xe",
                    labels={'Tổng tiền': 'Tổng GSM Amount (VND)', 'Loại xe': 'Loại xe'},
                    color='Tổng tiền',
                    color_continuous_scale='viridis'
                )
                fig_gsm.update_layout(height=400)
                st.plotly_chart(fig_gsm, use_container_width=True)
                
                # Metrics
                col_gsm1, col_gsm2 = st.columns(2)
                with col_gsm1:
                    st.metric("🛵 Bike GSM", f"{gsm_bike_total:,.0f} VND", f"{gsm_bike_count:,} đơn")
                with col_gsm2:
                    st.metric("🚗 Car GSM", f"{gsm_car_total:,.0f} VND", f"{gsm_car_count:,} đơn")
            
            with col2:
                st.markdown("#### 📊 Merchant Amount theo loại xe")
                
                # Tạo dữ liệu cho chart
                merchant_data = {
                    'Loại xe': ['Bike (100)', 'Car (200)'],
                    'Tổng tiền': [merchant_bike_total, merchant_car_total],
                    'Số đơn': [merchant_bike_count, merchant_car_count]
                }
                merchant_df = pd.DataFrame(merchant_data)
                
                # Bar chart cho Merchant Amount
                fig_merchant = px.bar(
                    merchant_df,
                    x='Loại xe',
                    y='Tổng tiền',
                    title="Merchant Amount theo loại xe",
                    labels={'Tổng tiền': 'Tổng Merchant Amount (VND)', 'Loại xe': 'Loại xe'},
                    color='Tổng tiền',
                    color_continuous_scale='plasma'
                )
                fig_merchant.update_layout(height=400)
                st.plotly_chart(fig_merchant, use_container_width=True)
                
                # Metrics
                col_merch1, col_merch2 = st.columns(2)
                with col_merch1:
                    st.metric("🛵 Bike Merchant", f"{merchant_bike_total:,.0f} VND", f"{merchant_bike_count:,} đơn")
                with col_merch2:
                    st.metric("🚗 Car Merchant", f"{merchant_car_total:,.0f} VND", f"{merchant_car_count:,} đơn")
            
            # Tổng kết
            st.markdown("### 📈 Tổng kết Amount theo loại xe")
            
            col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
            
            with col_sum1:
                total_gsm = gsm_bike_total + gsm_car_total
                st.metric("💰 Tổng GSM", f"{total_gsm:,.0f} VND")
            
            with col_sum2:
                total_merchant = merchant_bike_total + merchant_car_total
                st.metric("💰 Tổng Merchant", f"{total_merchant:,.0f} VND")
            
            with col_sum3:
                total_bike = gsm_bike_total + merchant_bike_total
                st.metric("🛵 Tổng Bike", f"{total_bike:,.0f} VND")
            
            with col_sum4:
                total_car = gsm_car_total + merchant_car_total
                st.metric("🚗 Tổng Car", f"{total_car:,.0f} VND")
            
            # Bảng so sánh
            st.markdown("#### 📋 Bảng so sánh chi tiết")
            
            comparison_data = {
                'Loại xe': ['Bike', 'Car', 'Tổng cộng'],
                'GSM Amount': [gsm_bike_total, gsm_car_total, total_gsm],
                'Merchant Amount': [merchant_bike_total, merchant_car_total, total_merchant],
                'Tổng Amount': [total_bike, total_car, total_gsm + total_merchant],
                'Số đơn GSM': [gsm_bike_count, gsm_car_count, gsm_bike_count + gsm_car_count],
                'Số đơn Merchant': [merchant_bike_count, merchant_car_count, merchant_bike_count + merchant_car_count]
            }
            
            comparison_df = pd.DataFrame(comparison_data)
            
            # Format số tiền
            comparison_df['GSM Amount'] = comparison_df['GSM Amount'].apply(lambda x: f"{x:,.0f}")
            comparison_df['Merchant Amount'] = comparison_df['Merchant Amount'].apply(lambda x: f"{x:,.0f}")
            comparison_df['Tổng Amount'] = comparison_df['Tổng Amount'].apply(lambda x: f"{x:,.0f}")
            
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
            
        else:
            st.warning("⚠️ Không tìm thấy cột 'GSM Amount' hoặc 'Merchant Amount' để phân tích")
        
        # Sample data
        st.markdown("### 👁️ Sample Data (10 records đầu)")
        st.dataframe(df.head(10).to_pandas(), use_container_width=True)
    
    def render_taixe_search(self, df):
        order_ids_input = st.text_area(
            "Nhập Order IDs (mỗi dòng một ID):",
            height=100,
            key="taixe_search"
        )
        
        if st.button("🔍 Tìm kiếm", key="taixe_search_btn"):
            if order_ids_input and 'ORDER_ID' in df.columns:
                order_ids = [id.strip() for id in order_ids_input.split('\n') if id.strip()]
                results = df.filter(pl.col('ORDER_ID').is_in(order_ids))
                
                if not results.is_empty():
                    st.success(f"✅ Tìm thấy {results.height} bản ghi")
                    st.dataframe(results.to_pandas(), use_container_width=True)
                else:
                    st.warning("⚠️ Không tìm thấy Order ID nào")
    
    def render_taixe_data_viewer(self, df):
        show_rows = st.number_input("Số dòng hiển thị:", min_value=10, max_value=1000, value=100, key="taixe_rows")
        st.dataframe(df.head(show_rows).to_pandas(), use_container_width=True)
    
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
            
            # Display filtered data
            if not drill_df.is_empty():
                st.markdown(f"#### 📋 Dữ liệu chi tiết ({drill_df.height:,} records)")
                
                # Convert to pandas for display
                display_df = drill_df.head(100).to_pandas()
                
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
                st.info(f"📝 Hiển thị {len(display_df):,} trong tổng số {drill_df.height:,} records")
                
            else:
                st.warning("⚠️ Không có dữ liệu để hiển thị")
        else:
            st.warning("⚠️ Không có dữ liệu để hiển thị")
    
    def render_amount_analysis_by_service_type(self, df):
        """Phân tích amount theo service type"""
        if 'SERVICE_TYPE' in df.columns:
            st.markdown("### 💰 Phân tích Phí theo Service Type")
            
            # Tạo tabs cho các loại amount khác nhau
            amount_cols = ['AMOUNT', 'GSM_AMOUNT', 'MERCHANT_AMOUNT', 'RECONCILED_AMOUNT']
            available_amount_cols = [col for col in amount_cols if col in df.columns]
            
            if available_amount_cols:
                amount_tabs = st.tabs([f"📊 {col.replace('_', ' ').title()}" for col in available_amount_cols])
                
                for i, amount_col in enumerate(available_amount_cols):
                    with amount_tabs[i]:
                        # Phân tích theo service type
                        service_analysis = df.group_by('SERVICE_TYPE').agg([
                            pl.col(amount_col).sum().alias('total'),
                            pl.col(amount_col).mean().alias('average'),
                            pl.count().alias('count')
                        ]).sort('total', descending=True)
                        
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            # Bar chart cho tổng amount
                            fig_total = px.bar(
                                service_analysis.to_pandas(),
                                x='SERVICE_TYPE',
                                y='total',
                                title=f"Tổng {amount_col.replace('_', ' ').title()} theo Service Type",
                                labels={'total': 'Tổng Amount (VND)', 'SERVICE_TYPE': 'Service Type'},
                                color='total',
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
                            fig_avg = px.bar(
                                service_analysis.to_pandas(),
                                x='SERVICE_TYPE',
                                y='average',
                                title=f"Trung bình {amount_col.replace('_', ' ').title()} theo Service Type",
                                labels={'average': 'Trung bình Amount (VND)', 'SERVICE_TYPE': 'Service Type'},
                                color='average',
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
                        total_all = service_analysis.select(pl.col('total').sum()).item()
                        
                        for row in service_analysis.iter_rows(named=True):
                            # Handle None values for average
                            avg_value = row['average'] if row['average'] is not None else 0
                            summary_data.append({
                                'Service Type': row['SERVICE_TYPE'],
                                'Tổng Amount': f"{row['total']:,.0f}",
                                'Số lượng': f"{row['count']:,}",
                                'Trung bình': f"{avg_value:,.0f}",
                                'Tỷ lệ tổng': f"{(row['total'] / total_all * 100):.1f}%" if total_all > 0 else "0%"
                            })
                        
                        summary_df = pd.DataFrame(summary_data)
                        st.dataframe(summary_df, use_container_width=True, hide_index=True)
                        
                        # Overall summary metrics
                        col_m1, col_m2, col_m3 = st.columns(3)
                        
                        with col_m1:
                            st.metric("💰 Tổng cộng", f"{total_all:,.0f} VND")
                        
                        with col_m2:
                            total_count = service_analysis.select(pl.col('count').sum()).item()
                            avg_all = total_all / total_count if total_count > 0 else 0
                            st.metric("📊 Trung bình chung", f"{avg_all:,.0f} VND")
                        
                        with col_m3:
                            st.metric("📝 Tổng giao dịch", f"{total_count:,}")
            else:
                st.info("ℹ️ Không tìm thấy cột amount để phân tích")
        else:
            st.info("ℹ️ Không có cột SERVICE_TYPE để phân tích")
    
    def render_business_analysis(self, df):
        """Phân tích Business Orders"""
        if 'IS_BUSINESS_ORDER' in df.columns:
            st.markdown("### 🏢 Phân tích Business Orders")
            
            business_stats = df.group_by('IS_BUSINESS_ORDER').agg(
                pl.count().alias('count')
            ).sort('count', descending=True)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Pie chart cho business orders
                # Clean up labels for better display
                clean_labels = []
                clean_values = []
                for row in business_stats.iter_rows(named=True):
                    label = row['IS_BUSINESS_ORDER']
                    value = row['count']
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
        else:
            st.info("ℹ️ Không có cột IS_BUSINESS_ORDER để phân tích")
    
    def render_service_type_analysis(self, df):
        """Phân tích Service Type (Ride/Express)"""
        if 'SERVICE_TYPE' in df.columns:
            st.markdown("### 🚗 Phân tích Service Type")
            
            service_stats = df.group_by('SERVICE_TYPE').agg(
                pl.count().alias('count')
            ).sort('count', descending=True)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Bar chart cho service types
                fig = px.bar(
                    service_stats.to_pandas(),
                    x='SERVICE_TYPE',
                    y='count',
                    title="Phân bố theo Service Type",
                    labels={'count': 'Số lượng', 'SERVICE_TYPE': 'Service Type'},
                    color='count',
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
                    list(service_stats.iter_rows(named=True)),
                    columns=['Service Type', 'Số lượng']
                )
                service_df['Tỷ lệ %'] = (service_df['Số lượng'] / service_df['Số lượng'].sum() * 100).round(2)
                
                st.markdown("**📊 Thống kê chi tiết:**")
                st.dataframe(service_df, use_container_width=True, hide_index=True)
                
                # Summary metrics
                total_orders = sum(service_df['Số lượng'])
                # Convert to string before using .str accessor
                service_df['Service Type'] = service_df['Service Type'].astype(str)
                ride_count = service_df[service_df['Service Type'].str.contains('Ride', case=False, na=False)]['Số lượng'].sum()
                express_count = service_df[service_df['Service Type'].str.contains('Express', case=False, na=False)]['Số lượng'].sum()
                
                st.metric("🚗 Ride Orders", f"{ride_count:,}")
                st.metric("⚡ Express Orders", f"{express_count:,}")
        else:
            st.info("ℹ️ Không có cột SERVICE_TYPE để phân tích")
    
    def run(self):
        print(f"DEBUG: run() called - current_tab: {st.session_state.current_tab}")
        self.render_header()
        self.render_sidebar()
        
        # Render content based on current tab
        print(f"DEBUG: About to render content for tab: {st.session_state.current_tab}")
        
        if st.session_state.current_tab == "launcher":
            print(f"DEBUG: Rendering launcher")
            self.render_launcher()
        elif st.session_state.current_tab == "reconciliation":
            print(f"DEBUG: Rendering reconciliation dashboard")
            self.render_reconciliation_dashboard()
        elif st.session_state.current_tab == "taixe":
            print(f"DEBUG: Rendering taixe dashboard")
            self.render_taixe_dashboard()
        else:
            print(f"DEBUG: Unknown tab: {st.session_state.current_tab}, defaulting to launcher")
            self.render_launcher()

if __name__ == "__main__":
    app = DashboardApp()
    app.run() 