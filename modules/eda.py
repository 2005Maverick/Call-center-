import pandas as pd
from typing import Dict, Any
import streamlit as st

@st.cache_data
def overview_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute detailed overview statistics and call outcome distribution."""
    answered_df = df[df['call_outcome'] == 'Answered']
    total_calls = len(df)
    avg_talk_time = answered_df['length_in_min'].mean()
    total_talk_time = answered_df['length_in_min'].sum()
    unique_agents = df['full_name'].nunique()
    date_range = (df['date'].min(), df['date'].max())
    outcome_dist = df['call_outcome'].value_counts(normalize=True) * 100
    outcome_counts = df['call_outcome'].value_counts()
    min_talk_time = answered_df['length_in_min'].min() if not answered_df.empty else 0
    max_talk_time = answered_df['length_in_min'].max() if not answered_df.empty else 0
    median_talk_time = answered_df['length_in_min'].median() if not answered_df.empty else 0
    answered_count = outcome_counts.get('Answered', 0)
    dropped_count = outcome_counts.get('Dropped', 0)
    answered_rate = outcome_dist.get('Answered', 0)
    dropped_rate = outcome_dist.get('Dropped', 0)
    # Busiest hour and day
    busiest_hour = df['hour'].mode()[0] if 'hour' in df.columns and not df['hour'].isnull().all() else None
    busiest_day = df['day_of_week'].mode()[0] if 'day_of_week' in df.columns and not df['day_of_week'].isnull().all() else None
    # Summary string
    summary = f"Total Calls: {total_calls:,}\n" \
              f"Answered: {answered_count:,} ({answered_rate:.1f}%) | Dropped: {dropped_count:,} ({dropped_rate:.1f}%)\n" \
              f"Unique Agents: {unique_agents}\n" \
              f"Date Range: {date_range[0]} to {date_range[1]}\n" \
              f"Avg Talk Time: {avg_talk_time:.2f} min | Median: {median_talk_time:.2f} min | Min: {min_talk_time:.2f} min | Max: {max_talk_time:.2f} min\n" \
              f"Total Talk Time: {total_talk_time:.2f} min ({total_talk_time/60:.2f} hrs)\n" \
              f"Busiest Hour: {busiest_hour if busiest_hour is not None else '-'} | Busiest Day: {busiest_day if busiest_day is not None else '-'}"
    return {
        'total_calls': total_calls,
        'avg_talk_time': avg_talk_time,
        'total_talk_time': total_talk_time,
        'unique_agents': unique_agents,
        'date_range': date_range,
        'outcome_dist': outcome_dist,
        'outcome_counts': outcome_counts,
        'min_talk_time': min_talk_time,
        'max_talk_time': max_talk_time,
        'median_talk_time': median_talk_time,
        'answered_count': answered_count,
        'dropped_count': dropped_count,
        'answered_rate': answered_rate,
        'dropped_rate': dropped_rate,
        'busiest_hour': busiest_hour,
        'busiest_day': busiest_day,
        'summary': summary
    } 