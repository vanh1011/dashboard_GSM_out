#!/usr/bin/env python3
"""
Debug script để kiểm tra tại sao chỉ ngày 1 load được
"""

import os
from csv_reader import CSVDataReader

def test_multiple_dates():
    """Test multiple dates để tìm pattern"""
    print("🔍 Testing Multiple Dates")
    print("=" * 50)
    
    reader = CSVDataReader()
    folders = reader.get_date_folders(2025)
    
    print(f"Found {len(folders)} folders total")
    print()
    
    # Test first 10 folders
    for i, folder in enumerate(folders[:10]):
        print(f"\n📅 Testing folder {i+1}: {folder}")
        
        # Extract date
        date_str = reader.extract_date_from_path(folder)
        print(f"   📆 Date extracted: {date_str}")
        
        # Check what files exist
        if os.path.exists(folder):
            files = os.listdir(folder)
            csv_files = [f for f in files if f.endswith('.csv')]
            print(f"   📂 CSV files found: {len(csv_files)}")
            
            # Show all CSV files
            for file in csv_files:
                if 'reconciled' in file and 'taixe' not in file:
                    file_path = os.path.join(folder, file)
                    size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    print(f"   📄 {file} ({size_mb:.1f}MB)")
            
            # Test get_file_info
            file_info = reader.get_file_info(folder, date_str)
            print(f"   🔍 Reconciled file found: {file_info['reconciled_file'] is not None}")
            
            if file_info['reconciled_file']:
                print(f"   ✅ Selected: {os.path.basename(file_info['reconciled_file'])}")
                print(f"   📊 Size: {file_info['reconciled_size_mb']:.1f}MB")
                
                # Test if file can be read
                try:
                    df = reader.read_csv_polars(file_info['reconciled_file'])
                    if df is not None and not df.is_empty():
                        print(f"   ✅ Read successful: {df.height} rows")
                    else:
                        print(f"   ❌ Read failed: Empty DataFrame")
                except Exception as e:
                    print(f"   ❌ Read error: {e}")
            else:
                print(f"   ❌ No reconciled file found")
                
                # Show what files are available for debugging
                reconciled_files = [f for f in csv_files if 'reconciled' in f]
                print(f"   🔍 All reconciled files: {reconciled_files}")
        else:
            print(f"   ❌ Folder does not exist")

def test_file_patterns():
    """Test file naming patterns across dates"""
    print("\n" + "=" * 50)
    print("🔍 File Pattern Analysis")
    print("=" * 50)
    
    reader = CSVDataReader()
    folders = reader.get_date_folders(2025)
    
    patterns = {}
    
    for folder in folders[:15]:  # Test first 15 days
        if os.path.exists(folder):
            files = os.listdir(folder)
            csv_files = [f for f in files if f.endswith('.csv')]
            
            date_str = reader.extract_date_from_path(folder)
            day = date_str[-2:]  # Last 2 digits = day
            
            # Find reconciled files (not taixe)
            reconciled_files = [f for f in csv_files if 'reconciled' in f and 'taixe' not in f]
            
            patterns[day] = {
                'date_str': date_str,
                'folder': folder,
                'reconciled_files': reconciled_files,
                'has_version_2': any('_2.csv' in f for f in reconciled_files)
            }
    
    # Print patterns
    for day, info in sorted(patterns.items()):
        print(f"\n📅 Day {day} ({info['date_str']}):")
        print(f"   📂 Folder: {info['folder']}")
        print(f"   📄 Reconciled files: {len(info['reconciled_files'])}")
        for file in info['reconciled_files']:
            print(f"      - {file}")
        print(f"   🔢 Has version 2: {info['has_version_2']}")

def test_specific_problematic_date():
    """Test a specific date that's failing"""
    print("\n" + "=" * 50)
    print("🔍 Testing Specific Problematic Date")
    print("=" * 50)
    
    # Test day 2 specifically
    reader = CSVDataReader()
    test_folder = "F:/powerbi/gsm_data/out/2025/07/02"
    
    print(f"📂 Testing: {test_folder}")
    
    if os.path.exists(test_folder):
        print("✅ Folder exists")
        
        # List all files
        files = os.listdir(test_folder)
        print(f"📋 All files ({len(files)}):")
        for file in files:
            print(f"   - {file}")
        
        # Extract date
        date_str = reader.extract_date_from_path(test_folder)
        print(f"\n📅 Date extracted: {date_str}")
        
        # Test find_best_file manually
        print(f"\n🔍 Testing find_best_file...")
        
        # Check for _2 version
        file_pattern_2 = f"pvi_transaction_reconciled_{date_str}_2.csv"
        file_path_2 = os.path.join(test_folder, file_pattern_2)
        print(f"   Looking for: {file_pattern_2}")
        print(f"   Full path: {file_path_2}")
        print(f"   Exists: {os.path.exists(file_path_2)}")
        
        # Check for regular version
        file_pattern = f"pvi_transaction_reconciled_{date_str}.csv"
        file_path = os.path.join(test_folder, file_pattern)
        print(f"   Looking for: {file_pattern}")
        print(f"   Full path: {file_path}")
        print(f"   Exists: {os.path.exists(file_path)}")
        
        # Test get_file_info
        file_info = reader.get_file_info(test_folder, date_str)
        print(f"\n📄 get_file_info result:")
        for key, value in file_info.items():
            print(f"   {key}: {value}")
            
    else:
        print("❌ Folder does not exist")

if __name__ == "__main__":
    print("🚀 Multiple Dates Debug Test")
    
    test_multiple_dates()
    test_file_patterns()
    test_specific_problematic_date()
    
    print("\n" + "=" * 60)
    print("✅ Multiple dates debug completed") 