#!/usr/bin/env python3
"""
Test file để debug dashboard errors
"""

try:
    print("Testing imports...")
    import streamlit as st
    print("✅ Streamlit OK")
    
    import pandas as pd
    print("✅ Pandas OK")
    
    import polars as pl
    print("✅ Polars OK")
    
    import plotly.express as px
    print("✅ Plotly OK")
    
    from csv_reader import CSVDataReader
    print("✅ CSVDataReader OK")
    
    print("\nTesting CSVDataReader...")
    reader = CSVDataReader()
    print(f"✅ Base path: {reader.base_path}")
    
    print("\nTesting dashboard import...")
    from dashboard import DashboardApp
    print("✅ DashboardApp import OK")
    
    print("\nTesting dashboard init...")
    app = DashboardApp()
    print("✅ DashboardApp init OK")
    
    print("\n🎉 All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 