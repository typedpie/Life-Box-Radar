"""
Styles loader: Load CSS styles to Streamlit.
"""
import streamlit as st


def cargar_estilos_css():
    """Load all CSS styles to dashboard."""
    
    # Colors and variables
    colores_css = """<style>:root {
        --primary-color: #4A90E2;
        --accent-color: #F5A623;
        --success-color: #28a745;
        --error-color: #dc3545;
    }</style>"""
    
    # Component styles
    componentes_css = """<style>
        .dashboard-card {
            background-color: var(--secondary-background-color);
            border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            text-align: center; margin-bottom: 20px;
            border: 1px solid rgba(150, 150, 150, 0.15);
        }
        .card-title { color: var(--text-color); opacity: 0.75; font-size: 14px; font-weight: 600; }
        .card-value { font-size: 36px !important; font-weight: 700 !important; }
        .val-blue { color: #4A90E2 !important; }
        .val-orange { color: #F5A623 !important; }
        
        .health-card {
            border-radius: 10px; padding: 15px; margin-bottom: 15px;
            background-color: var(--secondary-background-color);
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .health-ok { border-left: 8px solid #28a745; }
        .health-error { border-left: 8px solid #dc3545; }
        .health-status-ok { color: #28a745; font-weight: bold; }
        .health-status-error { color: #dc3545; font-weight: bold; }
        
        [data-testid="stSidebar"] img {
            background-color: #ffffff; padding: 8px; border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
    </style>"""
    
    # Load styles
    st.markdown(colores_css, unsafe_allow_html=True)
    st.markdown(componentes_css, unsafe_allow_html=True)


def cargar_estilos_personalizados(css_personalizado=""):
    """Load custom CSS styles."""
    if css_personalizado:
        st.markdown(f"<style>{css_personalizado}</style>", unsafe_allow_html=True)
