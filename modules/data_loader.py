import pandas as pd
import streamlit as st
from typing import Optional

@st.cache_data
def load_data(uploaded_file) -> Optional[pd.DataFrame]:
    """Load CSV or Excel file from Streamlit uploader with error handling and caching. Always load 'Sheet1' for Excel files."""
    try:
        if uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file, sheet_name='Sheet1')
        else:
            df = pd.read_csv(uploaded_file)
        return df
    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
        return None 