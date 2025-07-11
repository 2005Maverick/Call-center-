import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional

def agent_activity_heatmap(df: pd.DataFrame) -> Optional[px.imshow]:
    """Create an interactive heatmap of agent activity by hour using Plotly."""
    if 'full_name' not in df.columns or 'hour' not in df.columns:
        return None
    activity = df.pivot_table(index='full_name', columns='hour', values='call_outcome', aggfunc='count', fill_value=0)
    fig = px.imshow(
        activity,
        labels=dict(x="Hour of Day", y="Agent", color="Call Count"),
        aspect="auto",
        color_continuous_scale="Blues",
        title="Agent Activity Heatmap (Calls per Hour)"
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig

def animated_agent_bar_chart(df: pd.DataFrame, top_n: int = 10) -> Optional[px.bar]:
    """Create an animated bar chart race of top agents by call volume over days."""
    if 'full_name' not in df.columns or 'date' not in df.columns:
        return None
    daily_agent = df.groupby(['date', 'full_name']).size().reset_index(name='call_count')
    # Only keep top N agents overall
    top_agents = daily_agent.groupby('full_name')['call_count'].sum().nlargest(top_n).index
    daily_agent = daily_agent[daily_agent['full_name'].isin(top_agents)]
    fig = px.bar(
        daily_agent,
        x='call_count',
        y='full_name',
        color='full_name',
        animation_frame=daily_agent['date'].astype(str),
        orientation='h',
        range_x=[0, daily_agent['call_count'].max() * 1.1],
        title=f"Top {top_n} Agents by Call Volume (Animated by Day)",
        labels={"call_count": "Calls", "full_name": "Agent", "date": "Date"},
        height=600
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    return fig

def call_flow_sankey(df: pd.DataFrame) -> Optional[go.Figure]:
    """Create a Sankey diagram of call flow and outcomes using Plotly."""
    if 'full_name' not in df.columns or 'call_outcome' not in df.columns:
        return None
    # Group by agent and outcome
    flow = df.groupby(['full_name', 'call_outcome']).size().reset_index(name='count')
    agents = flow['full_name'].unique().tolist()
    outcomes = flow['call_outcome'].unique().tolist()
    labels = agents + outcomes
    source = flow['full_name'].apply(lambda x: labels.index(x)).tolist()
    target = flow['call_outcome'].apply(lambda x: labels.index(x)).tolist()
    value = flow['count'].tolist()
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=["#4a90e2"]*len(agents) + ["#7ed957"]*len(outcomes)
        ),
        link=dict(
            source=source,
            target=target,
            value=value
        ))])
    fig.update_layout(title_text="Call Flow and Outcome Sankey Diagram", font_size=12)
    return fig 