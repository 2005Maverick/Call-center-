import pandas as pd
from typing import Tuple
import streamlit as st

@st.cache_data
def time_patterns(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return hourly and daily call volume and average talk time DataFrames."""
    answered_df = df[df['call_outcome'] == 'Answered']
    hourly_calls = df.groupby('hour')['call_outcome'].count()
    hourly_avg_talk = answered_df.groupby('hour')['length_in_min'].mean()
    hourly_stats = pd.DataFrame({'total_calls': hourly_calls, 'avg_talk_time_min': hourly_avg_talk}).fillna(0)

    daily_calls = df.groupby('day_of_week')['call_outcome'].count()
    daily_avg_talk = answered_df.groupby('day_of_week')['length_in_min'].mean()
    daily_stats = pd.DataFrame({'total_calls': daily_calls, 'avg_talk_time_min': daily_avg_talk}).fillna(0)
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_stats = daily_stats.reindex([day for day in day_order if day in daily_stats.index])
    return hourly_stats, daily_stats 