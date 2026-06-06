"""
KPI Cards component: Display key metrics in card format.
"""
import streamlit as st
import pandas as pd


def render_kpi_cards(df_oportunidades, df_vencidas):
    
     
    """Display main KPI metrics in four columns."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(
            f"""<div class="dashboard-card">
                <div class="card-title">Active Tenders</div>
                <div class="card-value val-blue">{len(df_oportunidades)}</div>
            </div>""",
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f"""<div class="dashboard-card">
                <div class="card-title">Expired Tenders</div>
                <div class="card-value val-orange">{len(df_vencidas)}</div>
            </div>""",
            unsafe_allow_html=True
        )
    
    with col3:
        total_cupos = df_oportunidades['cupos'].sum() if not df_oportunidades.empty else 0
        st.markdown(
            f"""<div class="dashboard-card">
                <div class="card-title">Available Spots</div>
                <div class="card-value val-blue">{int(total_cupos)}</div>
            </div>""",
            unsafe_allow_html=True
        )
    
    with col4:
        portales = df_oportunidades['origen_web'].nunique() if not df_oportunidades.empty else 0
        st.markdown(
            f"""<div class="dashboard-card">
                <div class="card-title">Active Portals</div>
                <div class="card-value val-orange">{int(portales)}</div>
            </div>""",
            unsafe_allow_html=True
        )


def render_kpi_row(label, value, color="blue"):
    """Display single KPI card."""
    color_class = f"val-{color}"
    st.markdown(
        f"""<div class="dashboard-card">
            <div class="card-title">{label}</div>
            <div class="card-value {color_class}">{value}</div>
        </div>""",
        unsafe_allow_html=True
    )
