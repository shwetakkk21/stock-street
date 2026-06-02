# src/analytics.py
import streamlit as st
import pandas as pd
import plotly.express as px

def render_temporal_analysis(df):
    """Processes historical window transformations and plots time series projections."""
    st.subheader("Historical Performance Metrics Over Time Windows")
    
    if df['Timestamp'].isna().all():
        st.info("💡 To activate time-series analytics, include a 'Timestamp' column in your sheet.")
        return

    time_window = st.selectbox("Aggregation Interval Lookback", ["All Records", "30 Days", "7 Days"])
    filtered_df = df.copy()
    
    if time_window == "30 Days":
        filtered_df = df[df['Timestamp'] >= (pd.Timestamp.now() - pd.Timedelta(days=30))]
    elif time_window == "7 Days":
        filtered_df = df[df['Timestamp'] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]
        
    fig_timeline = px.line(
        filtered_df.sort_values(by="Timestamp"), 
        x="Timestamp", 
        y="Price", 
        color="Ticker",
        title="Asset Valuation Divergence Timeline"
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

def render_distribution_plots(df):
    """Generates market distribution sector charts."""
    st.markdown("### Fundamental Distribution Profiling")
    c1, c2 = st.columns(2)
    with c1:
        fig_scatter = px.scatter(df, x="PE Ratio", y="Price", color="Status", size="Volume", hover_name="Ticker")
        st.plotly_chart(fig_scatter, use_container_width=True)
    with c2:
        fig_pie = px.pie(df, names="Status", values="Volume", hole=0.4, title="Volume Allocations by Sentiment Status")
        st.plotly_chart(fig_pie, use_container_width=True)