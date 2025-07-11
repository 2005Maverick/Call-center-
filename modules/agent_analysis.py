import pandas as pd
from typing import Optional
import streamlit as st

@st.cache_data
def agent_performance(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Return a DataFrame with detailed agent performance metrics and rankings."""
    # Agent call counts and outcome breakdown
    agent_outcomes = df.pivot_table(index='full_name', columns='call_outcome', aggfunc='size', fill_value=0)
    agent_outcomes['total_calls'] = agent_outcomes.sum(axis=1)
    if 'Answered' not in agent_outcomes.columns: agent_outcomes['Answered'] = 0
    if 'Dropped' not in agent_outcomes.columns: agent_outcomes['Dropped'] = 0

    # Agent talk time statistics for answered calls
    answered_df = df[df['call_outcome'] == 'Answered']
    agent_talk_stats = answered_df.groupby('full_name').agg(
        avg_talk_time_min=('length_in_min', 'mean'),
        median_talk_time_min=('length_in_min', 'median'),
        total_talk_time_hours=('length_in_min', lambda x: x.sum() / 60),
        std_talk_time_min=('length_in_min', 'std')
    )

    # Combine all stats
    agent_stats = agent_outcomes.join(agent_talk_stats).fillna(0)
    agent_stats['answer_rate'] = (agent_stats['Answered'] / agent_stats['total_calls'] * 100).replace([float('inf'), float('-inf')], 0).fillna(0)
    agent_stats['talk_time_consistency_cv'] = (agent_stats['std_talk_time_min'] / agent_stats['avg_talk_time_min']).replace([float('inf'), float('-inf')], 0).fillna(0)
    agent_stats['rank_by_avg_talk_time'] = agent_stats['avg_talk_time_min'][agent_stats['Answered'] > 0].rank(method='dense', ascending=True)
    agent_stats['rank_by_total_calls'] = agent_stats['total_calls'].rank(method='dense', ascending=False)
    agent_stats = agent_stats.sort_values('rank_by_avg_talk_time').fillna(0)

    # Reorder columns for display
    report_cols = [
        'total_calls', 'Answered', 'Dropped', 'answer_rate',
        'avg_talk_time_min', 'median_talk_time_min', 'total_talk_time_hours',
        'talk_time_consistency_cv', 'rank_by_avg_talk_time', 'rank_by_total_calls'
    ]
    other_cols = [col for col in agent_stats.columns if col not in report_cols]
    agent_stats_sorted = agent_stats[report_cols + other_cols]
    return agent_stats_sorted.reset_index() 