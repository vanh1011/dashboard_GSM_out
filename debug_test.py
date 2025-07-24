#!/usr/bin/env python3
"""
Script debug để test các function trong csv_reader
"""

import os
from csv_reader import CSVDataReader
import polars as pl

def test_basic_functions():
    """Test các function cơ bản"""
    print("🔧 Testing CSVDataReader...")
    
    reader = CSVDataReader()
    print(f"📁 Base path: {reader.base_path}")
    
    # Test 1: Kiểm tra base path có tồn tại không
    if os.path.exists(reader.base_path):
        print(f"✅ Base path exists: {reader.base_path}")
    else:
        print(f"❌ Base path NOT exists: {reader.base_path}")
        return False
    
    # Test 2: Lấy danh sách thư mục
    print("\n📂 Testing get_date_folders...")
    folders = reader.get_date_folders(2025)
    print(f"Found {len(folders)} folders:")
    for i, folder in enumerate(folders[:5]):  # Chỉ hiển thị 5 đầu
        print(f"  {i+1}. {folder}")
    
    if not folders:
        print("❌ No folders found!")
        return False
    
    # Test 3: Test extract_date_from_path
    print("\n📅 Testing extract_date_from_path...")
    test_folder = folders[0] if folders else "F:/powerbi/gsm_data/out/2025/07/01"
    date_str = reader.extract_date_from_path(test_folder)
    print(f"Folder: {test_folder}")
    print(f"Date string: {date_str}")
    
    # Test 4: Test get_file_info
    print(f"\n📄 Testing get_file_info for {date_str}...")
    file_info = reader.get_file_info(test_folder, date_str)
    print("File info:")
    for key, value in file_info.items():
        print(f"  {key}: {value}")
    
    # Test 5: Kiểm tra file có tồn tại không
    if file_info['reconciled_file']:
        reconciled_file = file_info['reconciled_file']
        print(f"\n📋 Testing file existence...")
        print(f"Reconciled file: {reconciled_file}")
        
        if os.path.exists(reconciled_file):
            print(f"✅ File exists")
            file_size = os.path.getsize(reconciled_file) / (1024 * 1024)
            print(f"📊 File size: {file_size:.2f} MB")
            
            # Test 6: Thử đọc file
            print(f"\n📖 Testing read_csv_polars...")
            try:
                df = reader.read_csv_polars(reconciled_file)
                if df is not None and not df.is_empty():
                    print(f"✅ Successfully read CSV")
                    print(f"📊 Shape: {df.height} rows x {df.width} columns")
                    print(f"🏷️ Columns: {df.columns}")
                    
                    # Hiển thị sample
                    print(f"\n📋 Sample data (first 3 rows):")
                    sample = df.head(3).to_pandas()
                    print(sample.to_string())
                    
                    return True
                else:
                    print(f"❌ DataFrame is empty or None")
                    return False
                    
            except Exception as e:
                print(f"❌ Error reading CSV: {e}")
                
                # Thử với pandas
                print(f"\n🔄 Trying with pandas...")
                try:
                    df_pandas = reader.read_csv_pandas(reconciled_file)
                    if not df_pandas.empty:
                        print(f"✅ Pandas read successfully")
                        print(f"📊 Shape: {df_pandas.shape}")
                        print(f"🏷️ Columns: {list(df_pandas.columns)}")
                        return True
                    else:
                        print(f"❌ Pandas DataFrame is empty")
                        return False
                except Exception as e2:
                    print(f"❌ Pandas also failed: {e2}")
                    return False
        else:
            print(f"❌ File does not exist: {reconciled_file}")
            return False
    else:
        print(f"❌ No reconciled file found")
        return False

def test_manual_file_check():
    """Test manual - kiểm tra thư mục cụ thể"""
    print("\n" + "="*50)
    print("🔍 MANUAL FILE CHECK")
    print("="*50)
    
    # Kiểm tra thư mục cụ thể
    test_path = "F:/powerbi/gsm_data/out/2025/07/01"
    print(f"📂 Checking: {test_path}")
    
    if os.path.exists(test_path):
        print(f"✅ Directory exists")
        files = os.listdir(test_path)
        print(f"📋 Files in directory ({len(files)} total):")
        
        csv_files = [f for f in files if f.endswith('.csv')]
        for file in csv_files:
            full_path = os.path.join(test_path, file)
            size_mb = os.path.getsize(full_path) / (1024 * 1024)
            print(f"  📄 {file} ({size_mb:.2f} MB)")
        
        # Tìm file reconciled
        reconciled_files = [f for f in csv_files if 'reconciled' in f and 'taixe' not in f]
        print(f"\n🎯 Reconciled files found: {len(reconciled_files)}")
        for file in reconciled_files:
            print(f"  📄 {file}")
            
        if reconciled_files:
            # Thử đọc file đầu tiên
            test_file = os.path.join(test_path, reconciled_files[0])
            print(f"\n📖 Testing read: {reconciled_files[0]}")
            
            try:
                # Thử đọc 10 dòng đầu với pandas
                import pandas as pd
                sample_df = pd.read_csv(test_file, nrows=10)
                print(f"✅ Sample read successful")
                print(f"📊 Sample shape: {sample_df.shape}")
                print(f"🏷️ Columns: {list(sample_df.columns)}")
                print("\n📋 First 3 rows:")
                print(sample_df.head(3).to_string())
                
            except Exception as e:
                print(f"❌ Error reading sample: {e}")
                
                # Thử đọc raw text
                try:
                    with open(test_file, 'r', encoding='utf-8') as f:
                        first_lines = [f.readline().strip() for _ in range(3)]
                    print(f"📝 Raw first 3 lines:")
                    for i, line in enumerate(first_lines):
                        print(f"  {i+1}: {line[:100]}...")
                except Exception as e2:
                    print(f"❌ Even raw read failed: {e2}")
        
    else:
        print(f"❌ Directory does not exist")

if __name__ == "__main__":
    print("🚀 Starting CSV Reader Debug Test")
    print("="*60)
    
    success = test_basic_functions()
    
    if not success:
        test_manual_file_check()
    
    print("\n" + "="*60)
    print("✅ Debug test completed") 