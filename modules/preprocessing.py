import pandas as pd
from typing import Optional
import streamlit as st

@st.cache_data
def preprocess_data(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Clean and preprocess the call center data."""
    try:
        # Standardize column names for sample data
        rename_map = {
            'Date': 'date',
            'Agent': 'full_name',
            'Call Type': 'call_type',
            'Outcome': 'call_outcome',
            'Talk Time (min)': 'length_in_min'
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

        # Handle date and time columns
        if 'call_date' in df.columns and 'Time' in df.columns:
            df['call_dateTime'] = pd.to_datetime(
                df['call_date'].astype(str) + ' ' + df['Time'].astype(str), errors='coerce')
        elif 'call_dateTime' in df.columns:
            df['call_dateTime'] = pd.to_datetime(df['call_dateTime'])
        else:
            df['call_dateTime'] = pd.date_range(start='2024-01-01', periods=len(df), freq='H')

        df['date'] = df['call_dateTime'].dt.date
        df['hour'] = df['call_dateTime'].dt.hour
        df['day_of_week'] = df['call_dateTime'].dt.day_name()
        df['day_of_month'] = df['call_dateTime'].dt.day

        # Clean status column and create call outcome
        if 'status' in df.columns:
            df['status'] = df['status'].astype(str).str.upper().str.strip()
        else:
            if 'length_in_sec' in df.columns:
                df['status'] = (pd.to_numeric(df['length_in_sec'], errors='coerce') > 0).map({True: 'ANSWERED', False: 'DROPPED'})
            else:
                df['status'] = 'ANSWERED'

        def categorize_call_outcome(status):
            if pd.isna(status): return 'Unknown'
            status_str = str(status)
            if 'ANSWER' in status_str: return 'Answered'
            if 'DROP' in status_str: return 'Dropped'
            if 'BUSY' in status_str: return 'Busy'
            if 'NO ANSWER' in status_str: return 'No Answer'
            return 'Other'
        df['call_outcome'] = df['status'].apply(categorize_call_outcome)

        # Handle call duration
        if 'length_in_sec' in df.columns:
            df['length_in_sec'] = pd.to_numeric(df['length_in_sec'], errors='coerce').fillna(0)
        else:
            df['length_in_sec'] = 0
        df['length_in_min'] = df['length_in_sec'] / 60

        # Handle agent names
        if 'full_name' not in df.columns:
            df['full_name'] = df.get('user', 'Agent_' + (df.index % 10 + 1).astype(str))
        df['full_name'] = df['full_name'].fillna('Unknown Agent')

        return df
    except Exception as e:
        print(f"❌ Error during preprocessing: {e}")
        return None 