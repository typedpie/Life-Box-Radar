import streamlit as st
import pandas as pd
import os
from google.oauth2 import service_account
from google.cloud import bigquery

ID_PROYECTO = "proyecto-life-box-licitaciones" 
RUTA_CREDENCIALES = "credenciales_gcp.json"

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Radar de Licitaciones - LifeBox UDD", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. INYECCIÓN DE CSS (Adaptable a Modo Claro y Oscuro)
st.markdown("""
<style>
    /* Tarjetas (Cards) que leen el color de fondo secundario del tema actual de Streamlit */
    .dashboard-card {
        background-color: var(--secondary-background-color);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid rgba(150, 150, 150, 0.15);
        transition: all 0.3s ease; 
    }
    
    /* Textos dentro de las tarjetas que leen el color de texto oficial del tema */
    .card-title {
        color: var(--text-color);
        opacity: 0.75; 
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }
    
    .card-value {
        font-size: 36px !important;
        font-weight: 700 !important;
        margin: 0;
    }
    
    /* Colores de acento */
    .val-blue { color: #4A90E2 !important; }
    .val-orange { color: #F5A623 !important; }
    .val-green { color: #2ecc71 !important; }
    .val-purple { color: #9b59b6 !important; }

    /* --- NUEVO: ESCUDO PROTECTOR PARA LOS LOGOS --- */
    [data-testid="stSidebar"] img {
        background-color: #ffffff; /* Obliga un fondo blanco puro */
        padding: 8px; /* Le da aire al logo para que no choque con los bordes */
        border-radius: 10px; /* Bordes suaves */
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); /* Sombra muy sutil */
    }
</style>
""", unsafe_allow_html=True)

# 3. VALIDACIÓN DE CREDENCIALES
if not os.path.exists(RUTA_CREDENCIALES):
    st.error("🚨 ¡ALERTA CRÍTICA! Python no encuentra tu llave maestra.")
    st.warning(f"Asegúrate de que el archivo se llame EXACTAMENTE '{RUTA_CREDENCIALES}' y esté guardado en la misma carpeta que este dashboard.")
    st.stop()

credenciales = service_account.Credentials.from_service_account_file(RUTA_CREDENCIALES)

# 4. EXTRACCIÓN DE DATOS DESDE BIGQUERY
@st.cache_data(ttl=600)
def cargar_oportunidades_bq():
    try:
        query = f"""
            SELECT fecha_deteccion, titulo_llamado_web, origen_web, palabra_clave, curso, region, comuna, modalidad, link_documento
            FROM `{ID_PROYECTO}.licitaciones.oportunidades`
            WHERE estado = 'Activo' OR estado IS NULL
            ORDER BY fecha_deteccion DESC
        """
        df = pd.read_gbq(query, project_id=ID_PROYECTO, credentials=credenciales)
        
        # Renombramos las columnas inmediatamente para que sea más fácil trabajar con ellas
        if not df.empty:
            df.columns = ['Detectado el', 'Llamado', 'OTIC', 'Gatillo', 'Curso', 'Región', 'Comuna', 'Modalidad', 'Alumnos', 'Horas', 'Link Excel']
            df['Detectado el'] = pd.to_datetime(df['Detectado el']).dt.strftime('%d-%m-%Y %H:%M')
            # Limpiamos posibles valores nulos en los textos para los filtros
            for col in ['OTIC', 'Región', 'Comuna', 'Gatillo']:
                df[col] = df[col].fillna('No especificado').astype(str)
        return df
    except Exception as e:
        st.error(f"Error conectando a la base de datos: {e}")
        return pd.DataFrame()

df_base = cargar_oportunidades_bq()

# 5. SIDEBAR: BRANDING Y FILTROS
with st.sidebar:
    # Branding
    st.markdown("---")
    col_udd, col_lifebox = st.columns(2)
    with col_udd:
        if os.path.exists("logo_udd.png"): st.image("logo_udd.png", use_container_width=True) 
    with col_lifebox:
        if os.path.exists("logo_lifebox.png"): st.image("logo_lifebox.png", use_container_width=True) 
    st.markdown("<h5 style='text-align: center; color: #4F8BF9; margin-top: 10px;'>Colaboración Estratégica</h5>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Filtros Interactivos
    st.markdown("### 🔍 Filtros de Búsqueda")
    
    if not df_base.empty:
        # Obtenemos listas únicas y agregamos "Todos" al principio
        lista_otics = ["Todos"] + sorted(df_base['OTIC'].unique().tolist())
        lista_regiones = ["Todas"] + sorted(df_base['Región'].unique().tolist())
        lista_comunas = ["Todas"] + sorted(df_base['Comuna'].unique().tolist())
        lista_gatillos = ["Todos"] + sorted(df_base['Gatillo'].unique().tolist())
        
        filtro_otic = st.selectbox("📌 OTIC", lista_otics)
        filtro_region = st.selectbox("🌎 Región", lista_regiones)
        filtro_comuna = st.selectbox("📍 Comuna", lista_comunas)
        filtro_gatillo = st.selectbox("🎯 Gatillo (Palabra Clave)", lista_gatillos)
    else:
        st.info("Filtros no disponibles (Base de datos vacía)")
        filtro_otic = filtro_region = filtro_comuna = filtro_gatillo = "Todos"
        
    st.markdown("---")
    st.markdown("### ⚙️ Estado del Sistema")
    st.success("Base de Datos: Conectada")
    if st.button("🔄 Forzar Actualización Ahora", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# 6. LÓGICA DE APLICACIÓN DE FILTROS
df_filtrado = df_base.copy()
if not df_filtrado.empty:
    if filtro_otic != "Todos": df_filtrado = df_filtrado[df_filtrado['OTIC'] == filtro_otic]
    if filtro_region != "Todas": df_filtrado = df_filtrado[df_filtrado['Región'] == filtro_region]
    if filtro_comuna != "Todas": df_filtrado = df_filtrado[df_filtrado['Comuna'] == filtro_comuna]
    if filtro_gatillo != "Todos": df_filtrado = df_filtrado[df_filtrado['Gatillo'] == filtro_gatillo]

# 7. CABECERA PRINCIPAL (MAIN BODY)
col_logo, col_titulo = st.columns([1, 8]) 
with col_logo:
    if os.path.exists("logo_radar.png"): 
        st.image("logo_radar.png", use_container_width=True)
with col_titulo:
    st.title("Dashboard Comercial SENCE")
    st.markdown("Plataforma de monitoreo y detección temprana de oportunidades.")
st.divider()

# 8. DIBUJAR PANTALLA PRINCIPAL
if df_base.empty:
    st.info("No hay oportunidades en la base de datos o el motor aún no ha inyectado datos.")
else:
    # --- BLOQUE DE TARJETAS (KPIs) ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    # Cálculos para las tarjetas
    total_ops = len(df_filtrado)
    total_regiones = df_filtrado['Región'].nunique() if total_ops > 0 else 0
    total_comunas = df_filtrado['Comuna'].nunique() if total_ops > 0 else 0
    total_alumnos = pd.to_numeric(df_filtrado['Alumnos'], errors='coerce').fillna(0).sum() if total_ops > 0 else 0
    
    # Dibujamos las tarjetas usando HTML y nuestras clases de CSS
    with kpi1:
        st.markdown(f"""
            <div class="dashboard-card">
                <div class="card-title">Oportunidades</div>
                <p class="card-value val-blue">{total_ops}</p>
            </div>
        """, unsafe_allow_html=True)
        
    with kpi2:
        st.markdown(f"""
            <div class="dashboard-card">
                <div class="card-title">Regiones Activas</div>
                <p class="card-value val-orange">{total_regiones}</p>
            </div>
        """, unsafe_allow_html=True)
        
    with kpi3:
        st.markdown(f"""
            <div class="dashboard-card">
                <div class="card-title">Comunas / Localidades</div>
                <p class="card-value val-green">{total_comunas}</p>
            </div>
        """, unsafe_allow_html=True)
        
    with kpi4:
        st.markdown(f"""
            <div class="dashboard-card">
                <div class="card-title">Cupos (Aprox)</div>
                <p class="card-value val-purple">{int(total_alumnos)}</p>
            </div>
        """, unsafe_allow_html=True)

    # --- TABLA DE DATOS INTERACTIVA ---
    st.markdown("### 📋 Repositorio de Licitaciones")
    if total_ops == 0:
        st.warning("No hay resultados que coincidan con los filtros seleccionados.")
    else:
        # Agregamos una columna falsa de casillas de verificación al principio
        df_interactivo = df_filtrado.copy()
        df_interactivo.insert(0, '🗑️ Descartar', False)

        # Usamos data_editor en vez de dataframe para que el usuario pueda hacer clic
        df_editado = st.data_editor(
            df_interactivo,
            column_config={
                "🗑️ Descartar": st.column_config.CheckboxColumn("Descartar", help="Marca esta casilla para enviar a la lista negra"),
                "Link Excel": st.column_config.LinkColumn("Descargar Base")
            },
            # Bloqueamos el resto de las columnas para que no editen los nombres por error
            disabled=['Detectado el', 'Llamado', 'OTIC', 'Gatillo', 'Curso', 'Región', 'Comuna', 'Modalidad', 'Link Excel'],
            use_container_width=True,
            hide_index=True,
            height=400
        )

        # Filtramos para ver si el usuario marcó alguna casilla
        filas_a_descartar = df_editado[df_editado['🗑️ Descartar'] == True]

        # Si hay casillas marcadas, mostramos el botón de acción
        if not filas_a_descartar.empty:
            st.warning(f"Estás a punto de ocultar {len(filas_a_descartar)} documentos de la vista principal.")
            if st.button("⚠️ Confirmar y Ocultar Selección", type="primary"):
                
                # Preparamos la conexión directa a BigQuery para enviar la actualización
                cliente_bq = bigquery.Client(project=ID_PROYECTO, credentials=credenciales)
                links_a_ocultar = filas_a_descartar['Link Excel'].tolist()
                
                # Formateamos los links para la consulta SQL
                links_format = "','".join(links_a_ocultar)
                
                query_update = f"""
                    UPDATE `{ID_PROYECTO}.licitaciones.oportunidades`
                    SET estado = 'Descartado'
                    WHERE link_documento IN ('{links_format}')
                """
                
                with st.spinner("Enviando a la lista negra..."):
                    # Ejecutamos la actualización
                    query_job = cliente_bq.query(query_update)
                    query_job.result() # Esperamos a que termine
                    
                    # Limpiamos la caché y recargamos la página
                    st.cache_data.clear()
                    st.rerun()