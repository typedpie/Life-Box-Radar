"""
Frontend dashboard: Modular Streamlit application.
"""
import sys
import os
from pathlib import Path

import streamlit as st
import pandas as pd

# Add paths
sys.path.insert(0, str(Path(__file__).parent / 'utils'))
sys.path.insert(0, str(Path(__file__).parent / 'components'))

from utils.config import (
    STREAMLIT_TITLE, STREAMLIT_ICON, STREAMLIT_LAYOUT,
    GCP_PROJECT_ID, GCP_CREDENTIALS_PATH,
    FUENTES_LICITACIONES
)
from utils.styles_loader import cargar_estilos_css
from utils.data_loader import DataLoader
from components.kpi_cards import render_kpi_cards
from components.health_cards import render_health_grid
from components.data_table import render_data_table
from components.source_list import render_source_list


# Configure Streamlit
st.set_page_config(
    page_title=STREAMLIT_TITLE,
    page_icon=STREAMLIT_ICON,
    layout=STREAMLIT_LAYOUT,
    initial_sidebar_state="expanded"
)

# Load styles
cargar_estilos_css()

# Initialize data loader
@st.cache_resource
def get_data_loader():
    """Get cached data loader instance."""
    loader = DataLoader(GCP_PROJECT_ID, GCP_CREDENTIALS_PATH)
    loader.conectar()
    return loader


def main():
    """Main dashboard application."""
    
    # Load header
    st.title("📊 " + STREAMLIT_TITLE)
    st.markdown("---")
    
    # Sidebar filters
    with st.sidebar:
        st.header("🔧 Filters & Settings")
        
        refresh_interval = st.slider(
            "Data refresh interval (seconds)",
            min_value=60, max_value=3600, value=300
        )
        
        vista = st.radio(
            "Select view",
            ["Overview", "Active", "Expired", "Scrapers", "Sources"]
        )
    
    # Load data
    loader = get_data_loader()
    
    if vista == "Overview":
        render_overview(loader)
    elif vista == "Active":
        render_active(loader)
    elif vista == "Expired":
        render_expired(loader)
    elif vista == "Scrapers":
        render_scrapers(loader)
    elif vista == "Sources":
        render_sources(loader)


def render_overview(loader):
    """Display overview dashboard."""
    st.header("📈 Overview")
    
    df_vigentes, df_vencidos = loader.cargar_oportunidades()
    
    # KPI cards
    render_kpi_cards(df_vigentes, df_vencidos)
    
    # Active opportunities sample
    if not df_vigentes.empty:
        st.subheader("📋 Latest Active Opportunities")
        render_data_table(df_vigentes.head(10), "Active")


def render_active(loader):
    """Display active opportunities."""
    st.header("✅ Active Opportunities")
    
    df_vigentes, _ = loader.cargar_oportunidades()
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        portales = st.multiselect(
            "Filter by Portal",
            df_vigentes['origen_web'].unique() if not df_vigentes.empty else []
        )
    
    with col2:
        regiones = st.multiselect(
            "Filter by Region",
            df_vigentes['region'].unique() if not df_vigentes.empty else []
        )
    
    # Apply filters
    df_filtrada = df_vigentes.copy()
    if portales:
        df_filtrada = df_filtrada[df_filtrada['origen_web'].isin(portales)]
    if regiones:
        df_filtrada = df_filtrada[df_filtrada['region'].isin(regiones)]
    
    # Display
    st.metric("Records", len(df_filtrada))
    render_data_table(df_filtrada, "Active")


def render_expired(loader):
    """Display expired opportunities."""
    st.header("❌ Expired Opportunities")
    
    _, df_vencidos = loader.cargar_oportunidades()
    
    if df_vencidos.empty:
        st.info("ℹ️ No expired records")
        return
    
    st.metric("Expired Records", len(df_vencidos))
    render_data_table(df_vencidos.head(50), "Expired")


def render_scrapers(loader):
    """Display scraper health status."""
    st.header("🔍 Scraper Status")
    
    df_estado = loader.cargar_estado_scrapers()
    
    if df_estado.empty:
        st.warning("⚠️ No scraper status data")
        return
    
    # Stats
    col1, col2, col3 = st.columns(3)
    
    df_latest = df_estado.sort_values('fecha_ejecucion', ascending=False).drop_duplicates('portal')
    
    with col1:
        ok_count = (df_latest['estado'] == 'OK').sum()
        st.metric("Healthy Portals", ok_count)
    
    with col2:
        error_count = (df_latest['estado'] != 'OK').sum()
        st.metric("Failed Portals", error_count)
    
    with col3:
        st.metric("Total Portals", len(df_latest))
    
    st.markdown("---")
    
    # Health grid
    st.subheader("Portal Health")
    render_health_grid(df_latest)


def render_sources(loader):
    """Display sources and data storage information."""
    st.header("📌 Fuentes de licitaciones")
    
    df_stats = loader.cargar_estadisticas()
    if df_stats:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Oportunidades activas", df_stats.get('total_oportunidades', 0))
        col2.metric("Licitaciones únicas", df_stats.get('total_licitaciones', 0))
        col3.metric("Portales", df_stats.get('total_portales', 0))
        col4.metric("Regiones", df_stats.get('total_regiones', 0))
    else:
        st.info("No se pudieron cargar estadísticas de la base de datos.")
    
    st.markdown("---")
    st.markdown(
        "Estas son las páginas desde donde se deben extraer las licitaciones en la siguiente fase de scrapers."
    )
    render_source_list(FUENTES_LICITACIONES)
    
    st.markdown("---")
    st.subheader("Sugerencia de almacenamiento")
    st.markdown(
        "- Actualmente el proyecto ya usa BigQuery como almacén principal de licitaciones.\n"
        "- Si no tienes acceso a BigQuery, una alternativa simple es usar SQLite local (`data/licitaciones.db`) o PostgreSQL para producción.\n"
        "- La tabla principal debería tener campos como `fecha_deteccion`, `titulo_llamado_web`, `origen_web`, `curso`, `region`, `comuna`, `cupos`, `horas`, `fecha_cierre`, `estado`, `link_documento`."
    )
    st.markdown(
        "- También puedes usar Google Sheets o un CSV temporal mientras desarrollas los scrapers, pero para escalabilidad recomiendo BigQuery o PostgreSQL."
    )


if __name__ == "__main__":
    main()
