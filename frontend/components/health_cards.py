"""
Health Cards component: Display scraper status and health.
"""
import streamlit as st
import pandas as pd


def render_health_card(portal, estado, mensaje, fecha):
    """Display health status card for single portal."""
    if estado == "OK":
        st.markdown(
            f"""<div class="health-card health-ok">
                <div class="health-title">{portal}</div>
                <div class="health-status-ok">✅ {estado}</div>
                <div class="health-msg">{mensaje}</div>
                <div class="health-date">{fecha}</div>
            </div>""",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""<div class="health-card health-error">
                <div class="health-title">{portal}</div>
                <div class="health-status-error">❌ {estado}</div>
                <div class="health-msg">{mensaje}</div>
                <div class="health-date">{fecha}</div>
            </div>""",
            unsafe_allow_html=True
        )


def render_health_grid(df_estado):
    """Display health grid for all portals."""
    if df_estado.empty:
        st.warning("⚠️ No health data available")
        return
    
    # Get latest status per portal
    df_latest = df_estado.sort_values('fecha_ejecucion', ascending=False).drop_duplicates('portal')
    
    for _, row in df_latest.iterrows():
        render_health_card(
            row['portal'],
            row['estado'],
            row['mensaje'],
            row['fecha_ejecucion'].strftime('%Y-%m-%d %H:%M:%S')
        )
