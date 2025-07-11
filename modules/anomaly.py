import pandas as pd
from typing import Optional
import streamlit as st

@st.cache_data
def detect_anomalies(df: pd.DataFrame, n: int = 10) -> Optional[pd.DataFrame]:
    """Return a DataFrame of anomalous calls based on call duration (IQR method)."""
    answered_df = df[df['call_outcome'] == 'Answered']
    if answered_df.empty:
        return None
    duration_series = answered_df['length_in_min']
    Q1 = duration_series.quantile(0.25)
    Q3 = duration_series.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    anomalous_calls_df = answered_df[(duration_series < lower_bound) | (duration_series > upper_bound)].copy()
    if anomalous_calls_df.empty:
        return None
    anomalous_calls_df['anomaly_score'] = (duration_series - (Q1 + Q3)/2).abs()
    top_anomalies = anomalous_calls_df.sort_values('anomaly_score', ascending=False).head(n)
    return top_anomalies[['call_dateTime', 'full_name', 'status', 'length_in_sec', 'length_in_min', 'anomaly_score']] 