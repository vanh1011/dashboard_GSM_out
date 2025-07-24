import os
import pandas as pd
import polars as pl
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import glob
import re

class CSVDataReader:
    """
    Class để đọc và xử lý file CSV theo logic ưu tiên:
    - Nếu có file _2 thì đọc file _2
    - Nếu không có thì đọc file gốc
    - Hỗ trợ xử lý dữ liệu lớn với Polars
    """
    
    def __init__(self, base_path: str = "F:/powerbi/gsm_data/out"):
        self.base_path = base_path
        self.file_types = {
            'reconciled': 'pvi_transaction_reconciled_',
            'taixe': 'pvi_transaction_reconciled_taixe_'
        }
        
    def get_date_folders(self, year: int = 2025) -> List[str]:
        """Lấy danh sách các thư mục theo ngày"""
        folders = []
        year_path = os.path.join(self.base_path, str(year))
        
        if os.path.exists(year_path):
            for month in os.listdir(year_path):
                month_path = os.path.join(year_path, month)
                if os.path.isdir(month_path):
                    for day in os.listdir(month_path):
                        day_path = os.path.join(month_path, day)
                        if os.path.isdir(day_path):
                            folders.append(day_path)
        
        return sorted(folders)
    
    def find_best_file(self, folder_path: str, date_str: str, file_type: str = 'reconciled') -> Optional[str]:
        """
        Tìm file tốt nhất theo logic:
        1. Ưu tiên file có _2
        2. Nếu không có thì lấy file gốc
        """
        base_name = self.file_types.get(file_type, 'pvi_transaction_reconciled_')
        
        # Tìm file có _2
        file_pattern_2 = f"{base_name}{date_str}_2.csv"
        file_path_2 = os.path.join(folder_path, file_pattern_2)
        
        if os.path.exists(file_path_2):
            return file_path_2
        
        # Tìm file gốc
        file_pattern = f"{base_name}{date_str}.csv"
        file_path = os.path.join(folder_path, file_pattern)
        
        if os.path.exists(file_path):
            return file_path
            
        return None
    
    def read_csv_polars(self, file_path: str, chunk_size: int = 50000) -> pl.DataFrame:
        """Đọc CSV sử dụng Polars để xử lý hiệu quả dữ liệu lớn"""
        try:
            # Đọc với Polars - nhanh hơn pandas cho file lớn
            df = pl.read_csv(
                file_path,
                separator=',',
                quote_char='"',
                null_values=['', 'NULL', 'null'],
                ignore_errors=True
            )
            return df
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return pl.DataFrame()
    
    def read_csv_pandas(self, file_path: str, chunk_size: int = 10000) -> pd.DataFrame:
        """Đọc CSV với pandas (fallback option)"""
        try:
            chunks = []
            for chunk in pd.read_csv(file_path, chunksize=chunk_size, low_memory=False):
                chunks.append(chunk)
            return pd.concat(chunks, ignore_index=True)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return pd.DataFrame()
    
    def extract_date_from_path(self, folder_path: str) -> str:
        """Trích xuất ngày từ đường dẫn thư mục"""
        # Ví dụ: F:/powerbi/gsm_data/out/2025/07/01 -> 20250701
        # Hoặc: F:\powerbi\gsm_data\out\2025\07\01 -> 20250701
        
        # Chuẩn hóa đường dẫn (thay \ thành /)
        folder_path = folder_path.replace('\\', '/')
        parts = folder_path.split('/')
        
        if len(parts) >= 3:
            year = parts[-3]
            month = parts[-2]
            day = parts[-1]
            return f"{year}{month.zfill(2)}{day.zfill(2)}"
        return ""
    
    def get_file_info(self, folder_path: str, date_str: str) -> Dict:
        """Lấy thông tin về các file trong thư mục"""
        info = {
            'folder': folder_path,
            'date': date_str,
            'reconciled_file': None,
            'taixe_file': None,
            'reconciled_size_mb': 0,
            'taixe_size_mb': 0,
            'has_version_2': False
        }
        
        # Kiểm tra file reconciled
        reconciled_file = self.find_best_file(folder_path, date_str, 'reconciled')
        if reconciled_file:
            info['reconciled_file'] = reconciled_file
            info['reconciled_size_mb'] = os.path.getsize(reconciled_file) / (1024 * 1024)
            info['has_version_2'] = '_2.csv' in reconciled_file
        
        # Kiểm tra file taixe
        taixe_file = self.find_best_file(folder_path, date_str, 'taixe')
        if taixe_file:
            info['taixe_file'] = taixe_file
            info['taixe_size_mb'] = os.path.getsize(taixe_file) / (1024 * 1024)
        
        return info
    
    def analyze_reconcile_status(self, df: pl.DataFrame) -> Dict:
        """Phân tích RECONCILE_STATUS"""
        if df.is_empty() or 'RECONCILE_STATUS' not in df.columns:
            return {}
        
        status_counts = df.group_by('RECONCILE_STATUS').agg(pl.count()).to_dict(as_series=False)
        
        analysis = {}
        for status, count in zip(status_counts['RECONCILE_STATUS'], status_counts['count']):
            analysis[status] = count[0] if isinstance(count, list) else count
        
        return analysis
    
    def analyze_insurance_status(self, df: pl.DataFrame) -> Dict:
        """Phân tích INSURANCE_STATUS"""
        if df.is_empty() or 'INSURANCE_STATUS' not in df.columns:
            return {}
        
        status_counts = df.group_by('INSURANCE_STATUS').agg(pl.count()).to_dict(as_series=False)
        
        analysis = {}
        for status, count in zip(status_counts['INSURANCE_STATUS'], status_counts['count']):
            analysis[status] = count[0] if isinstance(count, list) else count
        
        return analysis
    
    def find_special_orders(self, df: pl.DataFrame, order_ids: List[str]) -> pl.DataFrame:
        """Tìm các order ID đặc biệt"""
        if df.is_empty() or 'ORDER_ID' not in df.columns:
            return pl.DataFrame()
        
        return df.filter(pl.col('ORDER_ID').is_in(order_ids))
    
    def analyze_business_orders(self, df: pl.DataFrame) -> Dict:
        """Phân tích IS_BUSINESS_ORDER"""
        if df.is_empty() or 'IS_BUSINESS_ORDER' not in df.columns:
            return {}
        
        # Count business vs non-business orders
        business_counts = df.group_by('IS_BUSINESS_ORDER').agg(pl.count()).to_dict(as_series=False)
        
        analysis = {}
        for status, count in zip(business_counts['IS_BUSINESS_ORDER'], business_counts['count']):
            status_str = str(status) if status is not None else 'Unknown'
            analysis[status_str] = count[0] if isinstance(count, list) else count
        
        return analysis
    
    def analyze_service_type(self, df: pl.DataFrame) -> Dict:
        """Phân tích SERVICE_TYPE"""
        if df.is_empty() or 'SERVICE_TYPE' not in df.columns:
            return {}
        
        # Count service types với handling null values
        service_counts = df.group_by('SERVICE_TYPE').agg(pl.count()).to_dict(as_series=False)
        
        analysis = {}
        for service_type, count in zip(service_counts['SERVICE_TYPE'], service_counts['count']):
            if service_type is None or service_type == '':
                service_name = 'Không xác định'
            elif str(service_type).lower() == 'normal':
                service_name = 'Ride (Normal)'
            elif str(service_type).lower() == 'express':
                service_name = 'Express'
            else:
                service_name = str(service_type)
            
            analysis[service_name] = count[0] if isinstance(count, list) else count
        
        return analysis
    
    def analyze_amount_by_service_type(self, df: pl.DataFrame) -> Dict:
        """Phân tích amount theo service type cho GSM, Merchant và Reconciled amount"""
        if df.is_empty() or 'SERVICE_TYPE' not in df.columns:
            return {}
        
        # Mapping service types
        def map_service_type(service_type):
            if service_type is None or service_type == '':
                return 'Không xác định'
            elif str(service_type).lower() == 'normal':
                return 'Ride (Normal)'
            elif str(service_type).lower() == 'express':
                return 'Express'
            else:
                return str(service_type)
        
        # Tạo mapped service type column
        df_with_mapped = df.with_columns([
            pl.col('SERVICE_TYPE').map_elements(map_service_type, return_dtype=pl.Utf8).alias('SERVICE_TYPE_MAPPED')
        ])
        
        analysis = {}
        
        # Define amount columns to analyze
        amount_columns = ['GSM_AMOUNT', 'MERCHANT_AMOUNT', 'RECONCILED_AMOUNT', 'AMOUNT']
        
        for amount_col in amount_columns:
            if amount_col in df_with_mapped.columns:
                try:
                    # Group by service type and sum amounts
                    amount_by_service = df_with_mapped.group_by('SERVICE_TYPE_MAPPED').agg([
                        pl.col(amount_col).sum().alias('total_amount'),
                        pl.col(amount_col).count().alias('count'),
                        pl.col(amount_col).mean().alias('avg_amount')
                    ]).to_dict(as_series=False)
                    
                    analysis[amount_col] = {}
                    for i, service_type in enumerate(amount_by_service['SERVICE_TYPE_MAPPED']):
                        analysis[amount_col][service_type] = {
                            'total': amount_by_service['total_amount'][i] if amount_by_service['total_amount'][i] is not None else 0,
                            'count': amount_by_service['count'][i] if amount_by_service['count'][i] is not None else 0,
                            'average': amount_by_service['avg_amount'][i] if amount_by_service['avg_amount'][i] is not None else 0
                        }
                except Exception as e:
                    print(f"Error analyzing {amount_col}: {e}")
                    analysis[amount_col] = {}
        
        return analysis

    def get_summary_stats(self, df: pl.DataFrame) -> Dict:
        """Lấy thống kê tổng quan"""
        if df.is_empty():
            return {}
        
        stats = {
            'total_records': df.height,
            'unique_orders': df.select('ORDER_ID').n_unique() if 'ORDER_ID' in df.columns else 0,
            'unique_merchants': df.select('MERCHANT').n_unique() if 'MERCHANT' in df.columns else 0,
            'date_range': {
                'min': None,
                'max': None
            }
        }
        
        # Phân tích theo ngày nếu có cột ORDER_TIME
        if 'ORDER_TIME' in df.columns:
            try:
                date_stats = df.select([
                    pl.col('ORDER_TIME').min().alias('min_date'),
                    pl.col('ORDER_TIME').max().alias('max_date')
                ]).to_dict(as_series=False)
                
                stats['date_range']['min'] = date_stats['min_date'][0]
                stats['date_range']['max'] = date_stats['max_date'][0]
            except:
                pass
        
        return stats 