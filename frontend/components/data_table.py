"""
Data Table component: Display opportunity data in table format.
"""
import streamlit as st
import pandas as pd


def render_data_table(df, titulo="Opportunities"):
    """Display data table with selected columns."""
    if df.empty:
        st.info(f"ℹ️ No {titulo.lower()}")
        return
    
    # Prepare display columns
    columnas_mostrar = [
        'titulo_llamado_web',
        'curso',
        'region',
        'cupos',
        'horas',
        'fecha_cierre',
        'origen_web',
        'estado'
    ]
    
    df_mostrar = df[columnas_mostrar].copy()
    df_mostrar.columns = [
        'Process',
        'Course',
        'Region',
        'Spots',
        'Hours',
        'Deadline',
        'Portal',
        'Status'
    ]
    
    st.dataframe(
        df_mostrar,
        use_container_width=True,
        height=400,
        hide_index=True
    )


def render_filtered_table(df, columnas_filtro, titulo="Data"):
    """Display table with filter options."""
    if df.empty:
        st.warning(f"⚠️ No data in {titulo}")
        return
    
    df_filtrado = df.copy()
    
    col1, col2 = st.columns(2)
    
    with col1:
        for col, opciones in columnas_filtro.items():
            valores_seleccionados = st.multiselect(
                f"Filter by {col}",
                opciones,
                default=opciones[:5] if len(opciones) > 5 else opciones
            )
            if valores_seleccionados:
                df_filtrado = df_filtrado[df_filtrado[col].isin(valores_seleccionados)]
    
    with col2:
        st.metric("Records shown", len(df_filtrado))
    
    render_data_table(df_filtrado, titulo)
