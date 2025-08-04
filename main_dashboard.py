import streamlit as st
import os
import sys

# Cấu hình trang
st.set_page_config(
    page_title="PVI-GSM Dashboard Launcher",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS cho giao diện đẹp
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
    font-size: 2.5rem;
    font-weight: 700;
    color: #1f77b4;
    text-align: center;
    margin: 0;
    padding: 1rem 0;
    background: linear-gradient(90deg, #1f77b4, #17a2b8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Dashboard cards */
.dashboard-card {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    border: 2px solid #e0e0e0;
    transition: all 0.3s ease;
    cursor: pointer;
    text-align: center;
}

.dashboard-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    border-color: #1f77b4;
}

.dashboard-card.reconciled {
    border-left: 6px solid #28a745;
}

.dashboard-card.taixe {
    border-left: 6px solid #e74c3c;
}

/* Hide streamlit menu and footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Feature list styling */
.feature-list {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
}

.feature-list ul {
    margin: 0;
    padding-left: 1.5rem;
}

.feature-list li {
    margin: 0.5rem 0;
    color: #495057;
}
</style>
""", unsafe_allow_html=True)

def main():
    """Main launcher function"""
    # Kiểm tra nếu đã chọn dashboard
    if 'selected_dashboard' in st.session_state:
        if st.session_state.selected_dashboard == "reconciliation":
            # Import và chạy reconciliation dashboard
            import dashboard
            app = dashboard.DashboardApp()
            app.run()
            return
        elif st.session_state.selected_dashboard == "taixe":
            # Import và chạy taixe dashboard
            import taixe_dashboard
            app = taixe_dashboard.TaixeDashboardApp()
            app.run()
            return
    
    # Hiển thị launcher nếu chưa chọn dashboard
    st.markdown('<h1 class="main-header">🏠 PVI-GSM Dashboard Launcher</h1>', unsafe_allow_html=True)
    st.markdown("### 🎯 Chọn dashboard để phân tích dữ liệu PVI-GSM")
    
    # Tạo 2 cột cho 2 dashboard
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="dashboard-card reconciled">
            <h2>🔄 Reconciliation Dashboard</h2>
            <p><strong>Phân tích đối soát giao dịch chính</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-list">
            <h4>📊 Tính năng chính:</h4>
            <ul>
                <li>🔄 Phân tích RECONCILE_STATUS (match, not_found_in_m, not_found_in_external)</li>
                <li>🛡️ Phân tích INSURANCE_STATUS</li>
                <li>🏢 Phân tích Business vs Non-Business orders</li>
                <li>🚗 Phân tích Service Type (Ride vs Express)</li>
                <li>💰 Phân tích Amount theo Service Type</li>
                <li>🔍 Drill-down analysis cho các status đặc biệt</li>
                <li>📥 Export data ra CSV/Excel</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Mở Reconciliation Dashboard", key="btn_reconciled", use_container_width=True):
            st.session_state.selected_dashboard = "reconciliation"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="dashboard-card taixe">
            <h2>🚗 Tài Xế Dashboard</h2>
            <p><strong>Phân tích đơn tai nạn tài xế</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-list">
            <h4>📊 Tính năng chính:</h4>
            <ul>
                <li>🚗 Phân tích đơn tai nạn tài xế</li>
                <li>📊 Phân tích RECONCILE_STATUS cho tài xế</li>
                <li>📈 Biểu đồ phân bố trạng thái</li>
                <li>🔍 Tìm kiếm Order ID tài xế</li>
                <li>👁️ Xem dữ liệu thô tài xế</li>
                <li>📋 Thống kê chi tiết</li>
                <li>📥 Export data ra CSV</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Mở Tài Xế Dashboard", key="btn_taixe", use_container_width=True):
            st.session_state.selected_dashboard = "taixe"
            st.rerun()
    
    # Thông tin chung
    st.markdown("---")
    st.markdown("### 📋 Thông tin chung")
    
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.markdown("""
        **📁 Cấu trúc thư mục:**
        ```
        F:/powerbi/gsm_data/out/
        ├── 2025/
        │   ├── 07/
        │   │   ├── 01/
        │   │   │   ├── pvi_transaction_reconciled_20250701.csv
        │   │   │   ├── pvi_transaction_reconciled_20250701_2.csv
        │   │   │   └── pvi_transaction_reconciled_taixe_20250701.csv
        │   │   └── 02/
        │   └── 08/
        └── 2024/
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
        - `pvi_transaction_reconciled_taixe_YYYYMMDD_2.csv` (ưu tiên)
        """)
    
    with col_info3:
        st.markdown("""
        **⚡ Công nghệ:**
        
        - **🐍 Python**: Streamlit, Polars, Pandas
        - **📊 Visualization**: Plotly Express
        - **🚀 Performance**: Polars cho file lớn
        - **💾 Data**: CSV files (100MB+)
        - **🎨 UI**: Responsive, modern design
        
        **📈 Tính năng:**
        - Lazy loading
        - Smart caching
        - Interactive charts
        - Export functionality
        """)
    
    # Quick stats
    if os.path.exists("F:/powerbi/gsm_data/out"):
        st.markdown("### 📈 Quick Stats")
        try:
            # Đếm số thư mục ngày trong tháng 7/2025
            month_path = "F:/powerbi/gsm_data/out/2025/07"
            if os.path.exists(month_path):
                total_days = len([d for d in os.listdir(month_path) 
                                if os.path.isdir(os.path.join(month_path, d))])
                
                col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
                
                with col_stats1:
                    st.metric("📂 Tổng số ngày", total_days)
                with col_stats2:
                    st.metric("📅 Tháng hiện tại", "07/2025")
                with col_stats3:
                    st.metric("🗃️ Định dạng", "CSV")
                with col_stats4:
                    st.metric("💾 Kích thước file", "~100MB")
                    
        except Exception as e:
            st.info(f"ℹ️ Không thể đọc thống kê: {str(e)}")

if __name__ == "__main__":
    main() 