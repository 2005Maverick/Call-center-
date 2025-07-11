import streamlit as st
from modules import data_loader, preprocessing, eda, agent_analysis, time_analysis, anomaly, visualizations, business_intel
import plotly.graph_objects as go
import plotly.express as px
import os
import pandas as pd

st.set_page_config(page_title="Call Center Analytics Dashboard", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for advanced styling (placeholder)
if os.path.exists("assets/custom.css"):
    with open("assets/custom.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="header">
        <h1>📞 Call Center Analytics Dashboard</h1>
        <div style='float:right;'>
            <button onclick="window.location.reload()">🔄 Refresh</button>
        </div>
    </div>
""", unsafe_allow_html=True)

# Sidebar: Filters, quick insights, alerts
with st.sidebar:
    st.title("Filters & Insights")
    # --- Quick Stats (if data loaded) ---
    if 'preprocessed' in locals() and preprocessed is not None:
        stats = eda.overview_stats(preprocessed)
        st.markdown(f"""
        <div class='metric-card' style='margin-bottom:1em;'>
            <div class='metric-icon'>📞</div>
            <div class='metric-number'>{stats['total_calls']:,}</div>
            <div class='metric-label'>Total Calls</div>
        </div>
        <div class='metric-card' style='margin-bottom:1em;'>
            <div class='metric-icon'>👥</div>
            <div class='metric-number'>{stats['unique_agents']}</div>
            <div class='metric-label'>Agents</div>
        </div>
        <div class='metric-card' style='margin-bottom:1em;'>
            <div class='metric-icon'>🚨</div>
            <div class='metric-number'>{stats['dropped_rate']:.1f}%</div>
            <div class='metric-label'>Drop Rate</div>
        </div>
        """, unsafe_allow_html=True)
    # --- Filters ---
    st.markdown("<div class='section'></div>", unsafe_allow_html=True)
    st.subheader("Filter Data")
    date_range = st.date_input("Date Range", [])
    agent_filter = st.text_input("Agent Name (optional)")
    call_type = st.selectbox("Call Type", ["All", "Inbound", "Outbound"])
    st.markdown("<div class='section'></div>", unsafe_allow_html=True)
    # --- Sample Data Download ---
    st.subheader("Sample Data")
    with open(os.path.join(os.path.dirname(__file__), "sample_data.csv"), "rb") as f:
        st.download_button("Download Sample CSV", f, file_name="sample_call_data.csv", mime="text/csv")
    # --- Help & Support ---
    st.markdown("<div class='section'></div>", unsafe_allow_html=True)
    with st.expander("❓ Help & Support"):
        st.markdown("""
        - **How to use:** Upload your call data (CSV/XLSX) or load the sample data.
        - **Filters:** Use the sidebar to filter by date, agent, or call type.
        - **Support:** For help, contact [support@yourcompany.com](mailto:support@yourcompany.com)
        """)
    st.markdown("<div class='section'></div>", unsafe_allow_html=True)
    st.info("Upload your call center data to get started or use the sample data.")

# File upload and sample data logic
uploaded_file = st.file_uploader("Upload Call Data", type=["csv", "xlsx"], help="Drag and drop your call center data file here.")
load_sample = False
if not uploaded_file:
    # Show Load Sample Data button on landing page
    if st.button("✨ Load Sample Data", key="load_sample_btn"):
        load_sample = True

# --- Session state for mapping and data ---
if 'mapping_confirmed' not in st.session_state:
    st.session_state['mapping_confirmed'] = False
if 'preprocessed' not in st.session_state:
    st.session_state['preprocessed'] = None
if 'last_uploaded_file' not in st.session_state:
    st.session_state['last_uploaded_file'] = None

# Reset mapping if a new file is uploaded
if uploaded_file and uploaded_file != st.session_state['last_uploaded_file']:
    st.session_state['mapping_confirmed'] = False
    st.session_state['preprocessed'] = None
    st.session_state['last_uploaded_file'] = uploaded_file

preprocessed = None
if uploaded_file or load_sample:
    with st.spinner("Processing data..."):
        if uploaded_file:
            df = data_loader.load_data(uploaded_file)
            if df is not None:
                if not st.session_state['mapping_confirmed']:
                    # --- Strict User-Driven Column Mapping ---
                    st.markdown("## Map Your Columns to Required Features")
                    st.info("Please map each required feature to a column in your file. No defaults are used. All mappings are mandatory.")
                    columns = list(df.columns)
                    # Date mapping: single or split
                    date_mapping_type = st.radio("How is the date/time stored in your file?", ["Single column", "Two columns (date + time)"])
                    date_col = None
                    time_col = None
                    if date_mapping_type == "Single column":
                        date_col = st.selectbox("Select the column for Date/DateTime", ["-- Select --"] + columns, index=0)
                    else:
                        date_col = st.selectbox("Select the column for Date", ["-- Select --"] + columns, index=0)
                        time_col = st.selectbox("Select the column for Time", ["-- Select --"] + columns, index=0)
                    agent_col = st.selectbox("Select the column for Agent", ["-- Select --"] + columns, index=0)
                    outcome_col = st.selectbox("Select the column for Outcome", ["-- Select --"] + columns, index=0)
                    talk_time_col = st.selectbox("Select the column for Talk Time (min)", ["-- Select --"] + columns, index=0)
                    # Confirm mapping
                    mapping_confirmed = st.button("Confirm Mapping")
                    mapping_valid = False
                    if mapping_confirmed:
                        # Validate all mappings
                        if date_mapping_type == "Single column":
                            mapping_valid = (date_col and date_col != "-- Select --")
                        else:
                            mapping_valid = (date_col and date_col != "-- Select --" and time_col and time_col != "-- Select --")
                        mapping_valid = mapping_valid and all(x and x != "-- Select --" for x in [agent_col, outcome_col, talk_time_col])
                        if not mapping_valid:
                            st.error("All mappings are required. Please select a column for every feature.")
                        else:
                            # Apply mapping
                            if date_mapping_type == "Single column":
                                df['call_dateTime'] = pd.to_datetime(df[date_col], errors='coerce')
                            else:
                                df['call_dateTime'] = pd.to_datetime(df[date_col].astype(str) + ' ' + df[time_col].astype(str), errors='coerce')
                            df['date'] = df['call_dateTime'].dt.date
                            df['full_name'] = df[agent_col]
                            df['call_outcome'] = df[outcome_col]
                            df['length_in_min'] = pd.to_numeric(df[talk_time_col], errors='coerce')
                            # Continue with preprocessing and analysis
                            preprocessed = preprocessing.preprocess_data(df)
                            st.session_state['preprocessed'] = preprocessed
                            st.session_state['mapping_confirmed'] = True
                            st.success("Column mapping applied. Proceeding with analysis.")
                            st.rerun()
                    if not mapping_confirmed or not mapping_valid:
                        st.warning("Please complete the column mapping above to proceed with analysis.")
                        st.stop()
                else:
                    preprocessed = st.session_state['preprocessed']
            else:
                st.error("Failed to load data.")
        elif load_sample:
            sample_path = os.path.join(os.path.dirname(__file__), "sample_data.csv")
            with open(sample_path, "rb") as f:
                df = data_loader.load_data(f)
            if df is not None:
                preprocessed = preprocessing.preprocess_data(df)
            else:
                st.error("Failed to load sample data.")

# Main content: Tabs for EDA, Agent Analysis, Time Patterns, Anomalies, BI
if preprocessed is not None:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Agent Analysis", "Time Patterns", "Anomalies", "Business Intelligence"])
    with tab1:
        stats = eda.overview_stats(preprocessed)
        # Hero section
        st.markdown("""
        <div class='hero-section'>
            <div class='hero-icon'>📊</div>
            <div class='hero-content'>
                <h1>Call Center Analytics Dashboard</h1>
                <p>Modern, interactive analytics for actionable business insights.<br><span style='font-size:1.1em;color:#fff;'>Transform your call data into decisions.</span></p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        # Metric cards with animation and icons
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-icon'>📞</div>
                <div class='metric-number'>{stats['total_calls']:,}</div>
                <div class='metric-label'>Total Calls</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-icon'>👥</div>
                <div class='metric-number'>{stats['unique_agents']}</div>
                <div class='metric-label'>Unique Agents</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-icon'>⏱️</div>
                <div class='metric-number'>{stats['avg_talk_time']:.2f}</div>
                <div class='metric-label'>Avg Talk Time (min)</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-icon'>🕒</div>
                <div class='metric-number'>{stats['total_talk_time']/60:.2f}</div>
                <div class='metric-label'>Total Talk Time (hrs)</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("<div class='section'></div>", unsafe_allow_html=True)
        # Donut chart for call outcome
        st.subheader("Call Outcome Distribution")
        if not stats['outcome_counts'].empty:
            donut_fig = px.pie(
                names=stats['outcome_counts'].index,
                values=stats['outcome_counts'].values,
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel,
                title="Call Outcomes"
            )
            donut_fig.update_traces(textinfo='percent+label', pull=[0.05]*len(stats['outcome_counts']))
            st.plotly_chart(donut_fig, use_container_width=True)
        else:
            st.info("No call outcome data available for chart.")
        st.markdown("<div class='section'></div>", unsafe_allow_html=True)
        # Progress bars for answered/dropped rates
        st.write("**Answered Rate**")
        st.progress(min(int(stats['answered_rate']), 100))
        st.write("**Dropped Rate**")
        st.progress(min(int(stats['dropped_rate']), 100))
        st.markdown("<div class='section'></div>", unsafe_allow_html=True)
        # Executive summary with badges
        drop_badge = "<span class='badge badge-good'>Good</span>" if stats['dropped_rate'] < 5 else ("<span class='badge badge-alert'>High</span>" if stats['dropped_rate'] > 15 else "<span class='badge badge-warning'>Moderate</span>")
        st.markdown(f"""
        <div class='summary-card'>
        <b>Executive Summary</b><br>
        <ul style='margin-top:0.5em;'>
        <li><b>Date Range:</b> {stats['date_range'][0]} to {stats['date_range'][1]}</li>
        <li><b>Answered:</b> {stats['answered_count']:,} ({stats['answered_rate']:.1f}%) | <b>Dropped:</b> {stats['dropped_count']:,} ({stats['dropped_rate']:.1f}%) {drop_badge}</li>
        <li><b>Median Talk Time:</b> {stats['median_talk_time']:.2f} min | <b>Min:</b> {stats['min_talk_time']:.2f} min | <b>Max:</b> {stats['max_talk_time']:.2f} min</li>
        <li><b>Busiest Hour:</b> {stats['busiest_hour']} | <b>Busiest Day:</b> {stats['busiest_day']}</li>
        </ul>
        <span style='color:#4f8cff;font-weight:bold;'>
        {"Drop rate is excellent!" if stats['dropped_rate'] < 5 else ("Warning: Drop rate is high!" if stats['dropped_rate'] > 15 else "Drop rate is moderate.")}
        </span>
        </div>
        """, unsafe_allow_html=True)
    with tab2:
        st.markdown("""
        <h2 style='margin-bottom:0.5em;'>Agent Performance Benchmarking</h2>
        <div style='margin-bottom:1.5em;'>Compare agent AHT (Average Handle Time) to the team. Click an agent for call history and trend.</div>
        """, unsafe_allow_html=True)
        agent_stats = agent_analysis.agent_performance(preprocessed)
        leaderboard_cols = ['full_name', 'avg_talk_time_min', 'median_talk_time_min', 'total_calls', 'rank_by_avg_talk_time']
        leaderboard = agent_stats[leaderboard_cols].copy()
        leaderboard = leaderboard.sort_values('avg_talk_time_min')
        team_avg = leaderboard['avg_talk_time_min'].mean()
        def badge(rank):
            if rank == 1:
                return "<span class='badge badge-good'>Top Performer</span>"
            elif rank == leaderboard['rank_by_avg_talk_time'].max():
                return "<span class='badge badge-alert'>Needs Coaching</span>"
            else:
                return "<span class='badge badge-warning'>Team</span>"
        leaderboard['Badge'] = leaderboard['rank_by_avg_talk_time'].apply(badge)
        def aht_sparkline(agent):
            df_agent = preprocessed[(preprocessed['full_name'] == agent) & (preprocessed['call_outcome'] == 'Answered')]
            if df_agent.shape[0] < 3:
                return ""
            df_agent = df_agent.sort_values('date')
            fig = go.Figure(go.Scatter(y=df_agent['length_in_min'], mode='lines', line=dict(color='#ff9800', width=2)))
            fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=32, width=90, xaxis=dict(visible=False), yaxis=dict(visible=False), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            return st.plotly_chart(fig, use_container_width=False, height=32)
        # --- Agent search/filter ---
        agent_search = st.text_input("Search Agent Name", "", placeholder="Type agent name...")
        if agent_search:
            leaderboard = leaderboard[leaderboard['full_name'].str.contains(agent_search, case=False, na=False)]
        st.markdown("<div class='feature-card' style='padding:1.5em;'>", unsafe_allow_html=True)
        st.markdown("<b>Leaderboard (by AHT)</b>", unsafe_allow_html=True)
        st.download_button("Download Leaderboard CSV", leaderboard.to_csv(index=False).encode('utf-8'), file_name="agent_aht_leaderboard.csv", mime="text/csv")
        if leaderboard.empty:
            st.info("No agents match your search.")
        else:
            for idx, row in leaderboard.iterrows():
                col1, col2, col3, col4, col5 = st.columns([2,2,2,2,2])
                with col1:
                    st.markdown(f"<b>{row['full_name']}</b> {row['Badge']}", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"AHT: <span style='color:#ff9800;font-weight:700'>{row['avg_talk_time_min']:.2f} min</span>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"Median: {row['median_talk_time_min']:.2f} min", unsafe_allow_html=True)
                with col4:
                    st.markdown(f"Calls: {int(row['total_calls'])}", unsafe_allow_html=True)
                with col5:
                    aht_sparkline(row['full_name'])
                with st.expander(f"Show {row['full_name']}'s Call History"):
                    agent_calls = preprocessed[(preprocessed['full_name'] == row['full_name'])][['date','call_outcome','length_in_min']]
                    st.dataframe(agent_calls.rename(columns={'date':'Date','call_outcome':'Outcome','length_in_min':'Talk Time (min)'}), use_container_width=True)
                    st.download_button(f"Download {row['full_name']} Call History CSV", agent_calls.to_csv(index=False).encode('utf-8'), file_name=f"{row['full_name']}_call_history.csv", mime="text/csv")
        st.markdown("</div>", unsafe_allow_html=True)
        # Agent Activity Heatmap
        st.subheader("Agent Activity Heatmap (Calls per Hour)")
        if 'hour' in preprocessed.columns and preprocessed['hour'].notnull().any():
            heatmap_fig = visualizations.agent_activity_heatmap(preprocessed)
            if heatmap_fig is not None:
                st.plotly_chart(heatmap_fig, use_container_width=True)
                heatmap_data = preprocessed.pivot_table(index='full_name', columns='hour', values='call_outcome', aggfunc='count', fill_value=0)
                st.download_button("Download Heatmap Data CSV", heatmap_data.to_csv().encode('utf-8'), file_name="agent_activity_heatmap.csv", mime="text/csv")
            else:
                st.info("Not enough data for heatmap.")
        else:
            st.info("No hour data available for heatmap.")
        # Animated Bar Chart Race
        st.subheader("Animated Bar Chart Race: Top Agents by Call Volume")
        if 'date' in preprocessed.columns and 'full_name' in preprocessed.columns and not preprocessed.empty:
            bar_race_fig = visualizations.animated_agent_bar_chart(preprocessed, top_n=10)
            if bar_race_fig is not None:
                st.plotly_chart(bar_race_fig, use_container_width=True)
                bar_race_data = preprocessed.groupby(['date', 'full_name']).size().reset_index(name='call_count')
                st.download_button("Download Bar Race Data CSV", bar_race_data.to_csv(index=False).encode('utf-8'), file_name="agent_bar_race.csv", mime="text/csv")
            else:
                st.info("Not enough data for animated bar chart race.")
        else:
            st.info("No date or agent data available for bar chart race.")
        # (Optional) Sankey Diagram (commented)
        # st.subheader("Call Flow and Outcome Sankey Diagram")
        # sankey_fig = visualizations.call_flow_sankey(preprocessed)
        # if sankey_fig is not None:
        #     st.plotly_chart(sankey_fig, use_container_width=True)
        # else:
        #     st.info("Not enough data for Sankey diagram.")
    with tab3:
        # --- Agent search/filter for Time Patterns ---
        agent_search_tp = st.text_input("Filter by Agent Name (optional)", "", placeholder="Type agent name...")
        filtered_preprocessed = preprocessed.copy()
        if agent_search_tp:
            filtered_preprocessed = filtered_preprocessed[filtered_preprocessed['full_name'].str.contains(agent_search_tp, case=False, na=False)]
        if filtered_preprocessed.empty:
            st.info("No agents match your search. Please try another name.")
        else:
            # Hero/intro section and all stats/charts below should use filtered_preprocessed instead of preprocessed
            st.markdown("""
            <div class='hero-section' style='margin-bottom:2em;'>
                <div class='hero-icon'>⏰</div>
                <div class='hero-content'>
                    <h1>Time Patterns & Workload Insights</h1>
                    <p>Discover when your call center is busiest and how talk times change by hour and day. Use these insights to optimize staffing, scheduling, and performance.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            # Compute stats for cards
            hourly_stats, daily_stats = time_analysis.time_patterns(filtered_preprocessed)
            busiest_hour = hourly_stats['total_calls'].idxmax() if not hourly_stats.empty and 'total_calls' in hourly_stats else '--'
            busiest_day = daily_stats['total_calls'].idxmax() if not daily_stats.empty and 'total_calls' in daily_stats else '--'
            peak_volume = int(hourly_stats['total_calls'].max()) if not hourly_stats.empty and 'total_calls' in hourly_stats else '--'
            shortest_talk = hourly_stats['avg_talk_time_min'].min() if not hourly_stats.empty and 'avg_talk_time_min' in hourly_stats else '--'
            shortest_talk_display = f"{shortest_talk:.2f}" if shortest_talk != '--' else '--'
            # --- Textual summary row ---
            total_calls = int(filtered_preprocessed.shape[0])
            if 'call_outcome' in filtered_preprocessed and 'length_in_min' in filtered_preprocessed:
                answered_calls = filtered_preprocessed[filtered_preprocessed['call_outcome'] == 'Answered']
                avg_talk_time = answered_calls['length_in_min'].mean()
            else:
                avg_talk_time = None
            avg_talk_time_display = f"{avg_talk_time:.2f} min" if avg_talk_time is not None else '--'
            date_min = filtered_preprocessed['date'].min() if 'date' in filtered_preprocessed else '--'
            date_max = filtered_preprocessed['date'].max() if 'date' in filtered_preprocessed else '--'
            st.markdown(f"""
            <div style='margin-bottom:1.5em;font-size:1.15em;'>
                <b>Total Calls:</b> {total_calls} &nbsp;|&nbsp; <b>Avg Talk Time:</b> {avg_talk_time_display} &nbsp;|&nbsp; <b>Date Range:</b> {date_min} to {date_max}
            </div>
            """, unsafe_allow_html=True)
            # Glassy cards
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-icon'>🕒</div>
                    <div class='metric-number'>{busiest_hour}</div>
                    <div class='metric-label'>Busiest Hour</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-icon'>📅</div>
                    <div class='metric-number'>{busiest_day}</div>
                    <div class='metric-label'>Busiest Day</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-icon'>📈</div>
                    <div class='metric-number'>{peak_volume}</div>
                    <div class='metric-label'>Peak Call Volume (hr)</div>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-icon'>⏱️</div>
                    <div class='metric-number'>{shortest_talk_display}</div>
                    <div class='metric-label'>Shortest Avg Talk Time (min)</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("<div class='section'></div>", unsafe_allow_html=True)
            # Hourly Call Volume
            st.markdown("<div class='feature-card' style='margin-bottom:1.5em;'>", unsafe_allow_html=True)
            st.subheader("Hourly Call Volume")
            if not hourly_stats.empty and 'total_calls' in hourly_stats and hourly_stats['total_calls'].notnull().any():
                fig = px.area(hourly_stats, x=hourly_stats.index, y='total_calls', title='Hourly Call Volume', labels={'x':'Hour of Day','total_calls':'Calls'}, color_discrete_sequence=['#ff9800'])
                fig.update_layout(plot_bgcolor='rgba(255,255,255,0.25)', paper_bgcolor='rgba(255,255,255,0.25)')
                st.plotly_chart(fig, use_container_width=True)
                peak_hr = hourly_stats['total_calls'].idxmax()
                peak_hr_val = int(hourly_stats['total_calls'].max())
                st.caption(f"Peak call volume was at {peak_hr}h with {peak_hr_val} calls.")
            else:
                st.info("No hourly call data available for chart.")
            st.markdown("</div>", unsafe_allow_html=True)
            # Hourly Avg Talk Time
            st.markdown("<div class='feature-card' style='margin-bottom:1.5em;'>", unsafe_allow_html=True)
            st.subheader("Hourly Average Talk Time")
            if not hourly_stats.empty and 'avg_talk_time_min' in hourly_stats and hourly_stats['avg_talk_time_min'].notnull().any():
                fig = px.line(hourly_stats, x=hourly_stats.index, y='avg_talk_time_min', title='Hourly Avg Talk Time', labels={'x':'Hour of Day','avg_talk_time_min':'Avg Talk Time (min)'}, color_discrete_sequence=['#ff9800'])
                fig.update_layout(plot_bgcolor='rgba(255,255,255,0.25)', paper_bgcolor='rgba(255,255,255,0.25)')
                st.plotly_chart(fig, use_container_width=True)
                peak_hr_talk = hourly_stats['avg_talk_time_min'].idxmax()
                peak_hr_talk_val = hourly_stats['avg_talk_time_min'].max()
                st.caption(f"Average talk time was highest at {peak_hr_talk}h ({peak_hr_talk_val:.2f} min).")
            else:
                st.info("No hourly talk time data available for chart.")
            st.markdown("</div>", unsafe_allow_html=True)
            # Daily Call Volume
            st.markdown("<div class='feature-card' style='margin-bottom:1.5em;'>", unsafe_allow_html=True)
            st.subheader("Daily Call Volume")
            if not daily_stats.empty and 'total_calls' in daily_stats and daily_stats['total_calls'].notnull().any():
                fig = px.bar(daily_stats, x=daily_stats.index, y='total_calls', title='Daily Call Volume', labels={'x':'Day','total_calls':'Calls'}, color_discrete_sequence=['#ff9800'])
                fig.update_layout(plot_bgcolor='rgba(255,255,255,0.25)', paper_bgcolor='rgba(255,255,255,0.25)')
                st.plotly_chart(fig, use_container_width=True)
                peak_day = daily_stats['total_calls'].idxmax()
                peak_day_val = int(daily_stats['total_calls'].max())
                st.caption(f"{peak_day} had the highest call volume with {peak_day_val} calls.")
            else:
                st.info("No daily call data available for chart.")
            st.markdown("</div>", unsafe_allow_html=True)
            # Daily Avg Talk Time
            st.markdown("<div class='feature-card' style='margin-bottom:1.5em;'>", unsafe_allow_html=True)
            st.subheader("Daily Average Talk Time")
            if not daily_stats.empty and 'avg_talk_time_min' in daily_stats and daily_stats['avg_talk_time_min'].notnull().any():
                fig = px.line(daily_stats, x=daily_stats.index, y='avg_talk_time_min', title='Daily Avg Talk Time', labels={'x':'Day','avg_talk_time_min':'Avg Talk Time (min)'}, color_discrete_sequence=['#ff9800'])
                fig.update_layout(plot_bgcolor='rgba(255,255,255,0.25)', paper_bgcolor='rgba(255,255,255,0.25)')
                st.plotly_chart(fig, use_container_width=True)
                peak_day_talk = daily_stats['avg_talk_time_min'].idxmax()
                peak_day_talk_val = daily_stats['avg_talk_time_min'].max()
                st.caption(f"Average talk time was highest on {peak_day_talk} ({peak_day_talk_val:.2f} min).")
            else:
                st.info("No daily talk time data available for chart.")
            st.markdown("</div>", unsafe_allow_html=True)
            # --- Data Table Expander ---
            with st.expander("Show Hourly & Daily Data Table"):
                st.write("**Hourly Stats**")
                st.dataframe(hourly_stats, use_container_width=True)
                st.download_button("Download Hourly Stats CSV", hourly_stats.to_csv().encode('utf-8'), file_name="hourly_stats.csv", mime="text/csv")
                st.write("**Daily Stats**")
                st.dataframe(daily_stats, use_container_width=True)
                st.download_button("Download Daily Stats CSV", daily_stats.to_csv().encode('utf-8'), file_name="daily_stats.csv", mime="text/csv")
            # --- Executive Summary ---
            st.markdown("<div class='summary-card' style='margin-top:2em;'>", unsafe_allow_html=True)
            summary_lines = []
            if busiest_hour != '--':
                summary_lines.append(f"Your busiest hour is <b>{busiest_hour}</b>.")
            if busiest_day != '--':
                summary_lines.append(f"<b>{busiest_day}</b> has the highest call volume.")
            if shortest_talk != '--':
                summary_lines.append(f"Shortest average talk time is <b>{shortest_talk_display} min</b>.")
            if peak_volume != '--':
                summary_lines.append(f"Peak call volume in an hour: <b>{peak_volume}</b>.")
            st.markdown("<b>Executive Summary:</b> " + " ".join(summary_lines), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    with tab4:
        # Hero/intro section
        st.markdown("""
        <div class='hero-section' style='margin-bottom:2em;'>
            <div class='hero-icon'>🚨</div>
            <div class='hero-content'>
                <h1>Anomalous Calls & Outliers</h1>
                <p>Spot unusually long or short calls that may indicate issues, training opportunities, or exceptional service. Anomalies are detected using statistical outlier analysis on talk times.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.spinner('Detecting anomalies and rendering visuals...'):
            anomalies = anomaly.detect_anomalies(preprocessed, n=10)
            # Glassy cards for key outliers
            if anomalies is not None and not anomalies.empty:
                longest = anomalies.iloc[0]
                shortest = anomalies.iloc[-1]
                num_anom = anomalies.shape[0]
                # Robust date extraction
                def get_date(row):
                    if 'date' in row.index:
                        return row['date']
                    date_cols = [col for col in row.index if 'date' in col.lower()]
                    if date_cols:
                        return row[date_cols[0]]
                    return 'N/A'
                longest_date = get_date(longest)
                shortest_date = get_date(shortest)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-icon'>⏱️</div>
                        <div class='metric-number'>{longest['length_in_min']:.2f} min</div>
                        <div class='metric-label'>Longest Call</div>
                        <div style='font-size:0.95em;color:#888;'>{longest['full_name']}<br>{longest_date}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-icon'>⚡</div>
                        <div class='metric-number'>{shortest['length_in_min']:.2f} min</div>
                        <div class='metric-label'>Shortest Call</div>
                        <div style='font-size:0.95em;color:#888;'>{shortest['full_name']}<br>{shortest_date}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-icon'>🔎</div>
                        <div class='metric-number'>{num_anom}</div>
                        <div class='metric-label'># of Anomalies</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("<div class='section'></div>", unsafe_allow_html=True)
                # Lollipop Timeline Chart for Anomalies
                st.subheader("Anomalous Calls Timeline (Lollipop Chart)")
                # Ensure call_dateTime is present
                if 'call_dateTime' in preprocessed.columns:
                    all_calls = preprocessed[['call_dateTime', 'length_in_min']].copy()
                    all_calls['Anomaly'] = False
                    if 'call_dateTime' in anomalies.columns:
                        anomaly_keys = set(anomalies['call_dateTime'])
                        all_calls['Anomaly'] = all_calls['call_dateTime'].isin(anomaly_keys)
                    # Sort by time
                    all_calls = all_calls.sort_values('call_dateTime')
                    # Build lollipop chart
                    fig = go.Figure()
                    # Stems (vertical lines)
                    fig.add_trace(go.Scatter(
                        x=all_calls['call_dateTime'],
                        y=all_calls['length_in_min'],
                        mode='lines',
                        line=dict(color='rgba(180,180,180,0.3)', width=2),
                        showlegend=False,
                        hovertemplate='Time: %{x}<br>Talk Time: %{y:.2f} min'
                    ))
                    # Dots: normal
                    normal = all_calls[~all_calls['Anomaly']]
                    fig.add_trace(go.Scatter(
                        x=normal['call_dateTime'],
                        y=normal['length_in_min'],
                        mode='markers',
                        marker=dict(color='#888', size=8),
                        name='Normal Call',
                        hovertemplate='Time: %{x}<br>Talk Time: %{y:.2f} min'
                    ))
                    # Dots: anomalies
                    anom = all_calls[all_calls['Anomaly']]
                    fig.add_trace(go.Scatter(
                        x=anom['call_dateTime'],
                        y=anom['length_in_min'],
                        mode='markers',
                        marker=dict(color='#ff9800', size=12, line=dict(width=2, color='#d35400')),
                        name='Anomaly',
                        hovertemplate='Time: %{x}<br>Talk Time: %{y:.2f} min'
                    ))
                    fig.update_layout(
                        title='Anomalous Calls Timeline',
                        xaxis_title='Call Date/Time',
                        yaxis_title='Talk Time (min)',
                        plot_bgcolor='rgba(255,255,255,0.25)',
                        paper_bgcolor='rgba(255,255,255,0.25)',
                        legend_title_text='',
                        showlegend=True,
                        height=420
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption("""
                    <b>How to read this chart:</b> Each dot is a call (orange = anomaly, gray = normal). Vertical lines show talk time for each call. This timeline makes it easy to spot when anomalies occur and how extreme they are.
                    """, unsafe_allow_html=True)
                else:
                    st.info("No call_dateTime column available for timeline chart.")
                # Narrative summary
                st.markdown("<div class='feature-card' style='margin-bottom:1.5em;'>", unsafe_allow_html=True)
                st.markdown(f"""
                <b>Summary:</b> {num_anom} calls were flagged as anomalies. The longest call was <b>{longest['length_in_min']:.2f} min</b> by <b>{longest['full_name']}</b> on <b>{longest_date}</b>. The shortest was <b>{shortest['length_in_min']:.2f} min</b> by <b>{shortest['full_name']}</b> on <b>{shortest_date}</b>.
                """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                # Interactive table with pagination
                st.markdown("<div class='feature-card' style='margin-bottom:1.5em;'>", unsafe_allow_html=True)
                st.markdown("<b>Anomalous Calls Table</b>", unsafe_allow_html=True)
                show_all_rows = st.checkbox(f"Show all {len(anomalies)} anomalies in table", value=False)
                table_rows = anomalies if show_all_rows else anomalies.head(10)
                st.dataframe(table_rows, use_container_width=True)
                st.download_button("Download Anomalies CSV", anomalies.to_csv(index=False).encode('utf-8'), file_name="anomalies.csv", mime="text/csv")
                # Expander for each anomaly: show agent's call history around that time (limit to top 5 by default)
                show_all_expanders = st.checkbox(f"Show all {len(anomalies)} anomaly details", value=False)
                expander_rows = anomalies if show_all_expanders else anomalies.head(5)
                for idx, row in expander_rows.iterrows():
                    expander_date = get_date(row)
                    with st.expander(f"Show {row['full_name']}'s Call History for {expander_date} ({row['length_in_min']:.2f} min)"):
                        date_col = 'date'
                        if 'date' not in preprocessed.columns:
                            date_cols = [col for col in preprocessed.columns if 'date' in col.lower()]
                            date_col = date_cols[0] if date_cols else None
                        cols_to_show = [c for c in [date_col, 'call_outcome', 'length_in_min'] if c in preprocessed.columns]
                        agent_calls = preprocessed[(preprocessed['full_name'] == row['full_name'])][cols_to_show] if cols_to_show else preprocessed[(preprocessed['full_name'] == row['full_name'])]
                        rename_map = {}
                        if date_col: rename_map[date_col] = 'Date'
                        if 'call_outcome' in agent_calls.columns: rename_map['call_outcome'] = 'Outcome'
                        if 'length_in_min' in agent_calls.columns: rename_map['length_in_min'] = 'Talk Time (min)'
                        st.dataframe(agent_calls.rename(columns=rename_map), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
    with tab5:
        st.markdown("""
        <div class='hero-section' style='margin-bottom:2em;'>
            <div class='hero-icon'>💡</div>
            <div class='hero-content'>
                <h1>Business Intelligence & Executive Insights</h1>
                <p>Simulate, explore, and act on the most impactful levers in your call center. This is where data becomes business value.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        # 1. What-If Scenario Simulator
        st.markdown("<div class='feature-card' style='margin-bottom:2em;'>", unsafe_allow_html=True)
        st.subheader("What-If Scenario Simulator 🧮")
        st.write("Adjust the levers below to see real-time impact on key business metrics.")
        # Sliders for scenario
        drop_rate = st.slider("Drop Rate (%)", min_value=0.0, max_value=30.0, value=float(stats['dropped_rate']), step=0.1)
        agent_count = st.slider("Agent Count", min_value=1, max_value=stats['unique_agents']*2, value=stats['unique_agents'])
        avg_talk_time = st.slider("Avg Talk Time (min)", min_value=1.0, max_value=20.0, value=float(stats['avg_talk_time']), step=0.1)
        hold_time = st.slider("Hold Time per Call (min)", min_value=0.0, max_value=10.0, value=0.0, step=0.1)
        acw_time = st.slider("After-Call Work (min)", min_value=0.0, max_value=10.0, value=1.0, step=0.1)
        utilization = st.slider("Agent Utilization (%)", min_value=60, max_value=100, value=85, step=1)
        peak_load = st.slider("Peak Load Factor", min_value=1.0, max_value=2.0, value=1.0, step=0.01, help="Multiplier for call volume during peak hours.")
        # Realistic calculations
        minutes_per_shift = 8 * 60
        effective_minutes = minutes_per_shift * (utilization / 100)
        calls_per_agent = effective_minutes / (avg_talk_time + hold_time + acw_time)
        total_calls = int(agent_count * calls_per_agent * peak_load)
        projected_dropped = int(total_calls * drop_rate / 100)
        # Customer satisfaction logic
        base_satisfaction = 100
        satisfaction_penalty = drop_rate * 1.5 + hold_time * 2 + acw_time * 1
        if utilization < 80:
            satisfaction_penalty += 2
        projected_satisfaction = max(60, base_satisfaction - satisfaction_penalty)
        st.markdown(f"""
        <div class='kpi-row'>
            <div class='kpi-card'><div class='kpi-label'>Projected Calls Handled</div><div class='kpi-value'>{total_calls:,}</div></div>
            <div class='kpi-card'><div class='kpi-label'>Projected Dropped</div><div class='kpi-value'>{projected_dropped:,}</div></div>
            <div class='kpi-card'><div class='kpi-label'>Customer Satisfaction</div><div class='kpi-value'>{projected_satisfaction:.1f}%</div></div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Tweak the sliders to simulate operational changes and see their business impact instantly. Now includes hold time, after-call work, agent utilization, and peak load for more realistic predictions.")
        st.markdown("</div>", unsafe_allow_html=True)
        # 2. Root Cause Explorer (AHT Heatmap)
        st.markdown("<div class='feature-card' style='margin-bottom:2em;'>", unsafe_allow_html=True)
        st.subheader("Root Cause Explorer: High AHT 🔍")
        st.markdown("""
        <div style='background:#fffbe6;border-radius:8px;padding:0.8em 1em;margin-bottom:1em;border:1px solid #ffe082;'>
        <b>How to read this:</b> <br>
        <ul style='margin:0 0 0 1.2em;padding:0;'>
        <li><b>X-axis:</b> Agent name</li>
        <li><b>Y-axis:</b> Day of week</li>
        <li><b>Color:</b> Average talk time (AHT, min) — darker = higher</li>
        </ul>
        <span style='color:#e67e22;'>Focus on the darkest cells: these agent-day pairs are driving high AHT.</span>
        </div>
        """, unsafe_allow_html=True)
        st.write("See which agents, days, and times are driving high average handle time (AHT > 3 min).")
        if 'full_name' in preprocessed.columns and 'date' in preprocessed.columns and 'length_in_min' in preprocessed.columns:
            aht_df = preprocessed[preprocessed['call_outcome']=='Answered'].copy()
            aht_df['Day'] = pd.to_datetime(aht_df['date']).dt.day_name()
            aht_df['Agent'] = aht_df['full_name'].apply(lambda x: x.split()[0] if isinstance(x,str) else x)
            pivot = aht_df.groupby(['Agent','Day'])['length_in_min'].mean().reset_index()
            heatmap = pivot.pivot(index='Day', columns='Agent', values='length_in_min')
            # Reorder days for clarity
            days_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
            heatmap = heatmap.reindex(days_order)
            fig = px.imshow(
                heatmap,
                color_continuous_scale='YlOrRd',
                aspect='auto',
                labels=dict(x="Agent", y="Day", color="Avg Talk Time (min)")
            )
            fig.update_layout(title='AHT (Avg Talk Time) by Agent & Day', height=420)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Darker = higher AHT. Focus on these agent-day pairs to reduce average handle time.")
            # Top 3 root causes summary
            high_aht = pivot[pivot['length_in_min'] > 3].sort_values('length_in_min', ascending=False).head(3)
            if not high_aht.empty:
                st.markdown("<div class='summary-card' style='background:#fffbe6;border-radius:8px;padding:1em 1.2em;margin-top:1em;border:1px solid #ffe082;'>", unsafe_allow_html=True)
                st.markdown("<b>Top 3 Root Causes for High AHT:</b>", unsafe_allow_html=True)
                for _, row in high_aht.iterrows():
                    st.markdown(f"- <b>{row['Agent']}</b> on <b>{row['Day']}</b> — <span style='color:#e67e22;font-weight:bold;'>{row['length_in_min']:.2f} min avg talk time</span>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Not enough data for AHT root cause explorer.")
        st.markdown("</div>", unsafe_allow_html=True)
        # 3. Executive Alerts & Recommendations
        st.markdown("<div class='feature-card' style='margin-bottom:2em;'>", unsafe_allow_html=True)
        st.subheader("Executive Alerts & Recommendations 🚨")
        # Compute team averages
        recs = []
        if 'full_name' in preprocessed.columns and 'date' in preprocessed.columns and 'length_in_min' in preprocessed.columns:
            df = preprocessed.copy()
            df['Agent'] = df['full_name'].apply(lambda x: x.split()[0] if isinstance(x,str) else x)
            df['Day'] = pd.to_datetime(df['date']).dt.day_name()
            df['Hour'] = pd.to_datetime(df['date']).dt.hour
            # Team averages
            team_aht = df[df['call_outcome']=='Answered']['length_in_min'].mean()
            team_drop = (df['call_outcome']=='Dropped').mean()*100
            # Agent AHT alerts
            agent_aht = df[df['call_outcome']=='Answered'].groupby('Agent')['length_in_min'].mean()
            for agent, aht in agent_aht.items():
                if aht > team_aht:
                    # Find worst hour/day for this agent
                    agent_df = df[(df['Agent']==agent) & (df['call_outcome']=='Answered')]
                    if not agent_df.empty:
                        worst = agent_df.groupby(['Day','Hour'])['length_in_min'].mean().sort_values(ascending=False).head(1)
                        worst_day, worst_hour = worst.index[0]
                        worst_val = worst.values[0]
                        recs.append((
                            f"⏱️ High AHT: <b>{agent}</b>",
                            f"AHT: <b>{aht:.2f} min</b> (team avg: {team_aht:.2f} min). Worst: <b>{worst_day} at {int(worst_hour):02d}:00</b> ({worst_val:.2f} min)",
                            f"Coach {agent} for efficiency, especially on {worst_day} at {int(worst_hour):02d}:00."
                        ))
            # Hourly team AHT alerts
            hour_aht = df[df['call_outcome']=='Answered'].groupby(['Day','Hour'])['length_in_min'].mean()
            for (day, hour), val in hour_aht.items():
                if val > team_aht + 0.5:
                    recs.append((
                        f"⏱️ Abnormal Team AHT: <b>{day} {int(hour):02d}:00</b>",
                        f"Team AHT: <b>{val:.2f} min</b> (avg: {team_aht:.2f} min)",
                        f"Review call routing, staffing, or process for this slot."
                    ))
            # Agent drop rate alerts
            agent_drop = df.groupby('Agent').apply(lambda x: (x['call_outcome']=='Dropped').mean()*100)
            for agent, dr in agent_drop.items():
                if dr > team_drop + 5:
                    recs.append((
                        f"🚨 High Drop Rate: <b>{agent}</b>",
                        f"Drop Rate: <b>{dr:.1f}%</b> (team avg: {team_drop:.1f}%)",
                        f"Review call handling and support for {agent}."
                    ))
        # Visual summary
        num_critical = len(recs)
        st.markdown(f"<div style='font-size:1.1em;font-weight:600;margin-bottom:1em;'>Detected <span style='color:#e74c3c;font-weight:bold;'>{num_critical} critical issue{'s' if num_critical!=1 else ''}</span> this week.</div>", unsafe_allow_html=True)
        for title, desc, action in recs:
            st.markdown(f"""
            <div style='background:#fffbe6;border-left:6px solid #ff9800;border-radius:8px;padding:1em 1.2em;margin-bottom:1em;box-shadow:0 2px 8px #0001;'>
                <div style='font-size:1.15em;font-weight:700;margin-bottom:0.2em;'>{title}</div>
                <div style='margin-bottom:0.5em;'>{desc}</div>
                <div style='font-size:1.05em;font-weight:600;color:#ff9800;'>What to do next: {action}</div>
            </div>
            """, unsafe_allow_html=True)
        if not recs:
            st.markdown("<div style='background:#e8f5e9;border-left:6px solid #4caf50;border-radius:8px;padding:1em 1.2em;margin-bottom:1em;box-shadow:0 2px 8px #0001;'><b>✅ All Good!</b> No critical issues detected. Keep up the great work!</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        # 4. Actionable Insights Matrix (improved)
        st.markdown("<div class='feature-card' style='margin-bottom:2em;'>", unsafe_allow_html=True)
        st.subheader("Actionable Insights Matrix 🧭")
        st.write("All agents across key metrics. Focus on red cells for biggest wins. Hover for action tips.")
        if 'full_name' in preprocessed.columns and 'call_outcome' in preprocessed.columns and 'length_in_min' in preprocessed.columns:
            matrix_df = preprocessed.copy()
            matrix_df['Agent'] = matrix_df['full_name'].apply(lambda x: x.split()[0] if isinstance(x,str) else x)
            # Metrics
            aht = matrix_df[matrix_df['call_outcome']=='Answered'].groupby('Agent')['length_in_min'].mean()
            drop_rate = matrix_df.groupby('Agent').apply(lambda x: (x['call_outcome']=='Dropped').mean()*100)
            call_vol = matrix_df.groupby('Agent').size()
            # Team averages
            team_aht = aht.mean()
            team_drop = drop_rate.mean()
            team_vol = call_vol.mean()
            # Build matrix
            import numpy as np
            import pandas as pd
            matrix = pd.DataFrame({
                'AHT (min)': aht,
                'Drop Rate (%)': drop_rate,
                'Call Volume': call_vol
            })
            matrix.loc['Team Avg'] = [team_aht, team_drop, team_vol]
            # Color coding by deviation from average
            def color_cell(val, col, idx):
                if idx == 'Team Avg':
                    return 'background:#e3f2fd;color:#1976d2;font-weight:700;'
                if col == 'AHT (min)':
                    if val > team_aht + 0.5: return 'background:#ffebee;color:#c62828;font-weight:700;'  # red
                    elif val > team_aht: return 'background:#fff8e1;color:#ff9800;font-weight:600;'  # orange
                    else: return 'background:#e8f5e9;color:#388e3c;font-weight:600;'  # green
                if col == 'Drop Rate (%)':
                    if val > team_drop + 5: return 'background:#ffebee;color:#c62828;font-weight:700;'
                    elif val > team_drop: return 'background:#fff8e1;color:#ff9800;font-weight:600;'
                    else: return 'background:#e8f5e9;color:#388e3c;font-weight:600;'
                if col == 'Call Volume':
                    if val > team_vol * 1.2: return 'background:#e3f2fd;color:#1976d2;font-weight:600;'
                    else: return ''
                return ''
            styled = matrix.style.apply(lambda s: [color_cell(v, s.name, idx) for idx, v in zip(matrix.index, s)], axis=0)
            st.dataframe(styled, use_container_width=True, height=380)
            # Action tips summary
            st.caption("Red/orange = above average. Green = best-in-class. Team Avg row for comparison. Focus on red cells for biggest wins. Hover for action tips.")
        else:
            st.info("Not enough data for actionable insights matrix.")
        st.markdown("</div>", unsafe_allow_html=True)
else:
    # Mesmerizing dark-themed landing page
    st.markdown("""
    <div class='hero-section'>
        <div class='hero-icon'>📊</div>
        <div class='hero-content'>
            <h1>Call Center Analytics Dashboard</h1>
            <p>Modern, interactive analytics for actionable business insights.<br><span style='font-size:1.1em;color:#fff;'>Transform your call data into decisions.</span></p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class='upload-card'>
        <div class='upload-anim-icon'>⬆️</div>
        <div style='font-size:1.25em;font-weight:600;margin-bottom:0.5em;'>Upload Call Data</div>
        <div style='color:#b0b8c9;font-size:1em;margin-bottom:1.2em;'>Drag and drop your CSV or Excel file here to get started.<br>We support large files and multiple sheets.</div>
        <form>
            <input type='file' style='display:none;'>
        </form>
        <button class='upload-btn' onclick='document.querySelector("input[type=file]").click();return false;'>Get Started</button>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class='features-row'>
        <div class='feature-card'>
            <div class='feature-icon'>📈</div>
            <div class='feature-title'>Instant Insights</div>
            <div class='feature-desc'>Upload your data and get executive-ready analytics in seconds.</div>
        </div>
        <div class='feature-card'>
            <div class='feature-icon'>🧑‍💼</div>
            <div class='feature-title'>Agent Benchmarking</div>
            <div class='feature-desc'>See who's performing best and where to coach for improvement.</div>
        </div>
        <div class='feature-card'>
            <div class='feature-icon'>⚡</div>
            <div class='feature-title'>Anomaly Detection</div>
            <div class='feature-desc'>Spot outliers and root causes with advanced ML-powered analytics.</div>
        </div>
        <div class='feature-card'>
            <div class='feature-icon'>📊</div>
            <div class='feature-title'>Stunning Visuals</div>
            <div class='feature-desc'>Modern charts, heatmaps, and dashboards for every business user.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center;color:#b0b8c9;font-size:1.1em;margin-top:2em;'>
        Data source: [Your Source] | Last updated: --
    </div>
    """, unsafe_allow_html=True) 