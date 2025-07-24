import polars as pl
import pandas as pd
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
import numpy as np

class DataAnalyzer:
    """
    Class phân tích dữ liệu nâng cao cho đối soát PVI-GSM
    Hỗ trợ các chức năng:
    - Phân tích chi tiết reconcile status
    - Tìm kiếm order patterns
    - Phân tích merchant và business patterns
    - Báo cáo discrepancy
    """
    
    def __init__(self):
        self.reconcile_mappings = {
            'match': 'Khớp (GSM + PVI)',
            'not_found_in_m': 'Chỉ có PVI (không có GSM)',
            'not_found_in_external': 'Chỉ có GSM (không có PVI)',
            'completed': 'Hoàn thành',
            'cancelled': 'Đã hủy',
            'pending': 'Đang chờ'
        }
        
        self.insurance_mappings = {
            'completed': 'Bảo hiểm thành công',
            'cancelled': 'Bảo hiểm bị hủy',
            'pending': 'Đang xử lý bảo hiểm',
            'failed': 'Bảo hiểm thất bại'
        }
    
    def get_reconcile_summary(self, df: pl.DataFrame) -> Dict:
        """Tóm tắt chi tiết về reconcile status"""
        if df.is_empty() or 'RECONCILE_STATUS' not in df.columns:
            return {}
        
        # Đếm theo status
        status_counts = df.group_by('RECONCILE_STATUS').agg([
            pl.count().alias('count'),
            pl.col('TOTAL_AMOUNT').sum().alias('total_amount'),
            pl.col('TOTAL_AMOUNT').mean().alias('avg_amount')
        ]).sort('count', descending=True)
        
        # Chuyển đổi sang dict
        result = {}
        for row in status_counts.iter_rows(named=True):
            status = row['RECONCILE_STATUS']
            result[status] = {
                'count': row['count'],
                'total_amount': row['total_amount'] or 0,
                'avg_amount': row['avg_amount'] or 0,
                'description': self.reconcile_mappings.get(status, status)
            }
        
        # Tính tỷ lệ
        total_records = df.height
        for status_data in result.values():
            status_data['percentage'] = (status_data['count'] / total_records * 100) if total_records > 0 else 0
        
        return result
    
    def analyze_discrepancies(self, df: pl.DataFrame) -> Dict:
        """Phân tích chi tiết các trường hợp không khớp"""
        discrepancies = {
            'pvi_only': [],  # not_found_in_m
            'gsm_only': [],  # not_found_in_external
            'amount_mismatch': [],
            'time_discrepancy': []
        }
        
        if df.is_empty():
            return discrepancies
        
        # PVI only (có PVI nhưng không có GSM)
        if 'RECONCILE_STATUS' in df.columns:
            pvi_only = df.filter(pl.col('RECONCILE_STATUS').str.contains('not_found_in_m'))
            if not pvi_only.is_empty():
                discrepancies['pvi_only'] = self._format_discrepancy_records(pvi_only)
            
            # GSM only (có GSM nhưng không có PVI)
            gsm_only = df.filter(pl.col('RECONCILE_STATUS').str.contains('not_found_in_external'))
            if not gsm_only.is_empty():
                discrepancies['gsm_only'] = self._format_discrepancy_records(gsm_only)
        
        # Amount mismatch analysis
        if all(col in df.columns for col in ['GSM_AMOUNT', 'PVI_AMOUNT']):
            amount_diff = df.filter(
                (pl.col('GSM_AMOUNT').is_not_null()) & 
                (pl.col('PVI_AMOUNT').is_not_null()) &
                (pl.col('GSM_AMOUNT') != pl.col('PVI_AMOUNT'))
            )
            if not amount_diff.is_empty():
                discrepancies['amount_mismatch'] = self._format_amount_mismatch(amount_diff)
        
        return discrepancies
    
    def _format_discrepancy_records(self, df: pl.DataFrame, limit: int = 100) -> List[Dict]:
        """Format discrepancy records cho hiển thị"""
        if df.is_empty():
            return []
        
        # Lấy các cột quan trọng
        important_cols = ['ORDER_ID', 'MERCHANT', 'TOTAL_AMOUNT', 'ORDER_TIME', 'RECONCILE_STATUS']
        available_cols = [col for col in important_cols if col in df.columns]
        
        # Giới hạn số lượng để tránh quá tải
        sample_df = df.select(available_cols).head(limit)
        
        return sample_df.to_dicts()
    
    def _format_amount_mismatch(self, df: pl.DataFrame, limit: int = 100) -> List[Dict]:
        """Format amount mismatch records"""
        if df.is_empty():
            return []
        
        # Tính difference và percentage difference
        df_with_diff = df.with_columns([
            (pl.col('GSM_AMOUNT') - pl.col('PVI_AMOUNT')).alias('amount_diff'),
            ((pl.col('GSM_AMOUNT') - pl.col('PVI_AMOUNT')) / pl.col('PVI_AMOUNT') * 100).alias('diff_percentage')
        ])
        
        # Lấy các cột quan trọng
        cols = ['ORDER_ID', 'MERCHANT', 'GSM_AMOUNT', 'PVI_AMOUNT', 'amount_diff', 'diff_percentage']
        available_cols = [col for col in cols if col in df_with_diff.columns]
        
        sample_df = df_with_diff.select(available_cols).head(limit)
        return sample_df.to_dicts()
    
    def analyze_merchant_patterns(self, df: pl.DataFrame) -> Dict:
        """Phân tích patterns theo merchant"""
        if df.is_empty() or 'MERCHANT' not in df.columns:
            return {}
        
        merchant_analysis = df.group_by('MERCHANT').agg([
            pl.count().alias('total_transactions'),
            pl.col('TOTAL_AMOUNT').sum().alias('total_amount'),
            pl.col('TOTAL_AMOUNT').mean().alias('avg_amount'),
            pl.col('RECONCILE_STATUS').filter(pl.col('RECONCILE_STATUS') == 'match').count().alias('match_count'),
            pl.col('RECONCILE_STATUS').filter(pl.col('RECONCILE_STATUS').str.contains('not_found')).count().alias('discrepancy_count')
        ]).with_columns([
            (pl.col('match_count') / pl.col('total_transactions') * 100).alias('match_rate'),
            (pl.col('discrepancy_count') / pl.col('total_transactions') * 100).alias('discrepancy_rate')
        ]).sort('total_transactions', descending=True)
        
        return merchant_analysis.to_dicts()
    
    def analyze_time_patterns(self, df: pl.DataFrame) -> Dict:
        """Phân tích patterns theo thời gian"""
        if df.is_empty() or 'ORDER_TIME' not in df.columns:
            return {}
        
        try:
            # Parse datetime if it's string
            df_time = df.with_columns([
                pl.col('ORDER_TIME').str.strptime(pl.Datetime, format='%Y-%m-%d %H:%M:%S').alias('order_datetime')
            ])
            
            # Phân tích theo giờ
            hourly_analysis = df_time.with_columns([
                pl.col('order_datetime').dt.hour().alias('hour')
            ]).group_by('hour').agg([
                pl.count().alias('transaction_count'),
                pl.col('RECONCILE_STATUS').filter(pl.col('RECONCILE_STATUS') == 'match').count().alias('match_count')
            ]).with_columns([
                (pl.col('match_count') / pl.col('transaction_count') * 100).alias('match_rate')
            ]).sort('hour')
            
            return {
                'hourly': hourly_analysis.to_dicts(),
                'peak_hour': hourly_analysis.sort('transaction_count', descending=True).head(1).to_dicts()[0] if not hourly_analysis.is_empty() else None
            }
            
        except Exception as e:
            print(f"Error in time analysis: {e}")
            return {}
    
    def find_suspicious_patterns(self, df: pl.DataFrame) -> Dict:
        """Tìm các patterns đáng ngờ"""
        suspicious = {
            'duplicate_orders': [],
            'high_amount_discrepancy': [],
            'unusual_merchants': [],
            'time_anomalies': []
        }
        
        if df.is_empty():
            return suspicious
        
        # Duplicate orders
        if 'ORDER_ID' in df.columns:
            duplicate_orders = df.group_by('ORDER_ID').agg(pl.count().alias('count')).filter(pl.col('count') > 1)
            if not duplicate_orders.is_empty():
                suspicious['duplicate_orders'] = duplicate_orders.to_dicts()
        
        # High amount discrepancy (> 10%)
        if all(col in df.columns for col in ['GSM_AMOUNT', 'PVI_AMOUNT']):
            high_discrepancy = df.filter(
                (pl.col('GSM_AMOUNT').is_not_null()) & 
                (pl.col('PVI_AMOUNT').is_not_null()) &
                (pl.col('PVI_AMOUNT') > 0) &
                ((pl.col('GSM_AMOUNT') - pl.col('PVI_AMOUNT')).abs() / pl.col('PVI_AMOUNT') > 0.1)
            )
            if not high_discrepancy.is_empty():
                suspicious['high_amount_discrepancy'] = self._format_amount_mismatch(high_discrepancy, 50)
        
        # Unusual merchants (có tỷ lệ lỗi cao)
        merchant_patterns = self.analyze_merchant_patterns(df)
        unusual_merchants = [m for m in merchant_patterns if m.get('discrepancy_rate', 0) > 20]
        suspicious['unusual_merchants'] = unusual_merchants
        
        return suspicious
    
    def generate_reconciliation_report(self, df: pl.DataFrame) -> Dict:
        """Tạo báo cáo đối soát toàn diện"""
        if df.is_empty():
            return {}
        
        report = {
            'summary': self.get_reconcile_summary(df),
            'discrepancies': self.analyze_discrepancies(df),
            'merchant_analysis': self.analyze_merchant_patterns(df),
            'time_analysis': self.analyze_time_patterns(df),
            'suspicious_patterns': self.find_suspicious_patterns(df),
            'recommendations': self.generate_recommendations(df)
        }
        
        return report
    
    def generate_recommendations(self, df: pl.DataFrame) -> List[str]:
        """Tạo các khuyến nghị dựa trên phân tích"""
        recommendations = []
        
        if df.is_empty():
            return recommendations
        
        # Phân tích reconcile status
        reconcile_summary = self.get_reconcile_summary(df)
        
        if reconcile_summary:
            total_records = sum(data['count'] for data in reconcile_summary.values())
            match_count = reconcile_summary.get('match', {}).get('count', 0)
            match_rate = (match_count / total_records * 100) if total_records > 0 else 0
            
            if match_rate < 80:
                recommendations.append(f"⚠️ Tỷ lệ khớp thấp ({match_rate:.1f}%). Cần kiểm tra quy trình đồng bộ dữ liệu.")
            
            # Kiểm tra PVI only
            pvi_only_count = sum(data['count'] for key, data in reconcile_summary.items() if 'not_found_in_m' in key)
            if pvi_only_count > total_records * 0.05:  # > 5%
                recommendations.append(f"🔍 Có {pvi_only_count} giao dịch chỉ có ở PVI. Kiểm tra kết nối GSM.")
            
            # Kiểm tra GSM only
            gsm_only_count = sum(data['count'] for key, data in reconcile_summary.items() if 'not_found_in_external' in key)
            if gsm_only_count > total_records * 0.05:  # > 5%
                recommendations.append(f"📊 Có {gsm_only_count} giao dịch chỉ có ở GSM. Kiểm tra API callback PVI.")
        
        # Phân tích merchant
        merchant_patterns = self.analyze_merchant_patterns(df)
        if merchant_patterns:
            high_discrepancy_merchants = [m for m in merchant_patterns if m.get('discrepancy_rate', 0) > 15]
            if high_discrepancy_merchants:
                recommendations.append(f"🏪 {len(high_discrepancy_merchants)} merchant có tỷ lệ lỗi cao. Cần review configuration.")
        
        # Phân tích suspicious patterns
        suspicious = self.find_suspicious_patterns(df)
        if suspicious['duplicate_orders']:
            recommendations.append(f"🔄 Phát hiện {len(suspicious['duplicate_orders'])} Order ID trùng lặp. Kiểm tra idempotency.")
        
        if suspicious['high_amount_discrepancy']:
            recommendations.append(f"💰 Có {len(suspicious['high_amount_discrepancy'])} giao dịch lệch số tiền lớn. Review pricing logic.")
        
        if not recommendations:
            recommendations.append("✅ Dữ liệu trông ổn định. Tiếp tục monitor theo chu kỳ.")
        
        return recommendations
    
    def export_discrepancy_report(self, df: pl.DataFrame, file_path: str) -> bool:
        """Export báo cáo discrepancy ra Excel"""
        try:
            discrepancies = self.analyze_discrepancies(df)
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # PVI Only sheet
                if discrepancies['pvi_only']:
                    pvi_df = pd.DataFrame(discrepancies['pvi_only'])
                    pvi_df.to_excel(writer, sheet_name='PVI Only', index=False)
                
                # GSM Only sheet
                if discrepancies['gsm_only']:
                    gsm_df = pd.DataFrame(discrepancies['gsm_only'])
                    gsm_df.to_excel(writer, sheet_name='GSM Only', index=False)
                
                # Amount Mismatch sheet
                if discrepancies['amount_mismatch']:
                    amount_df = pd.DataFrame(discrepancies['amount_mismatch'])
                    amount_df.to_excel(writer, sheet_name='Amount Mismatch', index=False)
                
                # Summary sheet
                summary = self.get_reconcile_summary(df)
                if summary:
                    summary_df = pd.DataFrame([
                        {
                            'Status': status,
                            'Count': data['count'],
                            'Percentage': f"{data['percentage']:.2f}%",
                            'Total Amount': data['total_amount'],
                            'Avg Amount': data['avg_amount'],
                            'Description': data['description']
                        }
                        for status, data in summary.items()
                    ])
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            return True
            
        except Exception as e:
            print(f"Error exporting report: {e}")
            return False 