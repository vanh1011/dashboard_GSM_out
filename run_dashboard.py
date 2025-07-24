#!/usr/bin/env python3
"""
Script khởi chạy PVI-GSM Reconciliation Dashboard
Tối ưu cho xử lý file CSV lớn và hiệu suất cao
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_dependencies():
    """Kiểm tra các dependency cần thiết"""
    required_packages = [
        'streamlit',
        'pandas', 
        'polars',
        'plotly',
        'openpyxl'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Thiếu các package: {', '.join(missing_packages)}")
        print("🔧 Cài đặt bằng lệnh: pip install -r requirements.txt")
        return False
    
    print("✅ Tất cả dependencies đã được cài đặt")
    return True

def setup_environment():
    """Cấu hình môi trường cho dashboard"""
    env_vars = {
        # Streamlit config
        'STREAMLIT_SERVER_PORT': '8501',
        'STREAMLIT_SERVER_HEADLESS': 'true',
        'STREAMLIT_BROWSER_GATHER_USAGE_STATS': 'false',
        'STREAMLIT_SERVER_FILE_WATCHER_TYPE': 'poll',
        
        # Memory optimization
        'POLARS_MAX_THREADS': str(os.cpu_count() or 4),
        'PYTHONHASHSEED': '0',
        
        # Default data path
        'GSM_DATA_PATH': 'F:/powerbi/gsm_data/out'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("⚙️ Đã cấu hình môi trường")

def create_streamlit_config():
    """Tạo file cấu hình Streamlit tối ưu"""
    config_dir = Path.home() / '.streamlit'
    config_dir.mkdir(exist_ok=True)
    
    config_path = config_dir / 'config.toml'
    
    config_content = """
[server]
port = 8501
headless = true
fileWatcherType = "poll"
maxUploadSize = 500

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[runner]
magicEnabled = true
fixMatplotlib = true

[client]
showErrorDetails = true
toolbarMode = "viewer"
"""
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"📝 Đã tạo cấu hình Streamlit tại {config_path}")

def get_system_info():
    """Lấy thông tin hệ thống"""
    info = {
        'OS': platform.system(),
        'OS Version': platform.release(),
        'Architecture': platform.machine(),
        'Python': platform.python_version(),
        'CPU Count': os.cpu_count(),
        'Working Directory': os.getcwd()
    }
    
    print("💻 Thông tin hệ thống:")
    for key, value in info.items():
        print(f"   {key}: {value}")

def check_data_path():
    """Kiểm tra đường dẫn dữ liệu"""
    default_path = "F:/powerbi/gsm_data/out"
    
    if os.path.exists(default_path):
        print(f"✅ Tìm thấy thư mục dữ liệu: {default_path}")
        
        # Đếm số file trong thư mục
        total_files = 0
        for root, dirs, files in os.walk(default_path):
            csv_files = [f for f in files if f.endswith('.csv')]
            total_files += len(csv_files)
        
        print(f"📊 Tổng số file CSV: {total_files}")
    else:
        print(f"⚠️ Không tìm thấy thư mục mặc định: {default_path}")
        print("💡 Bạn có thể thay đổi đường dẫn trong dashboard")

def run_dashboard():
    """Chạy dashboard"""
    print("🚀 Đang khởi chạy PVI-GSM Reconciliation Dashboard...")
    print("🌐 Dashboard sẽ mở tại: http://localhost:8501")
    print("⏹️ Nhấn Ctrl+C để dừng")
    
    try:
        # Chạy Streamlit
        cmd = [
            sys.executable, '-m', 'streamlit', 'run', 'dashboard.py',
            '--server.port', '8501',
            '--server.headless', 'true',
            '--browser.gatherUsageStats', 'false'
        ]
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard đã được dừng")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi chạy dashboard: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Không tìm thấy file dashboard.py")
        print("💡 Đảm bảo bạn đang ở đúng thư mục project")
        sys.exit(1)

def main():
    """Main function"""
    print("=" * 60)
    print("📊 PVI-GSM Reconciliation Dashboard")
    print("🔧 Dashboard phân tích và đối soát dữ liệu giao dịch")
    print("=" * 60)
    
    # Kiểm tra hệ thống
    get_system_info()
    print()
    
    # Kiểm tra dependencies
    if not check_dependencies():
        sys.exit(1)
    print()
    
    # Cấu hình môi trường
    setup_environment()
    create_streamlit_config()
    print()
    
    # Kiểm tra dữ liệu
    check_data_path()
    print()
    
    # Chạy dashboard
    run_dashboard()

if __name__ == "__main__":
    main() 