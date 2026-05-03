import streamlit as st
import pandas as pd
import os
from google.oauth2 import service_account
from google.cloud import bigquery
from streamlit_autorefresh import st_autorefresh # <--- NUEVO MOTOR DE LIVE VIEW

ID_PROYECTO = "proyecto-life-box-licitaciones" 
RUTA_CREDENCIALES = "credenciales_gcp.json"

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Radar de Licitaciones - LifeBox UDD", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ACTIVAR EL "LIVE VIEW" ---
# Refresca el dashboard automáticamente cada 5 minutos (300,000 milisegundos).
st_autorefresh(interval=300000, limit=None, key="autorefresh_dashboard")

# 2. INYECCIÓN DE CSS
st.markdown("""
<style>
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
    .val-blue { color: #4A90E2 !important; }
    .val-orange { color: #F5A623 !important; }

    [data-testid="stSidebar"] img {
        background-color: #ffffff; 
        padding: 8px; 
        border-radius: 10px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); 
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
# Ajustamos la caché a 300 segundos (5 mins) para que coincida con la recarga automática
@st.cache_data(ttl=300) 
def cargar_oportunidades_bq():
    try:
        query = f"""
            SELECT fecha_deteccion, titulo_llamado_web, origen_web, palabra_clave, curso, region, comuna, modalidad, cupos, horas, link_documento
            FROM `{ID_PROYECTO}.licitaciones.oportunidades`
            WHERE estado = 'Activo' OR estado IS NULL
            ORDER BY fecha_deteccion DESC
        """
        df = pd.read_gbq(query, project_id=ID_PROYECTO, credentials=credenciales)
        
        if not df.empty:
            df.columns = ['Detectado el', 'Llamado', 'OTIC', 'Gatillo', 'Curso', 'Región', 'Comuna', 'Modalidad', 'Alumnos', 'Horas', 'Link Excel']
            df['Detectado el'] = pd.to_datetime(df['Detectado el']).dt.strftime('%d-%m-%Y %H:%M')
            
            for col in ['OTIC', 'Región', 'Comuna', 'Gatillo']:
                df[col] = df[col].fillna('No especificado').astype(str)
        return df
    except Exception as e:
        st.error(f"Error conectando a la base de datos: {e}")
        return pd.DataFrame()

df_base = cargar_oportunidades_bq()

# 5. SIDEBAR: BRANDING Y FILTROS MINIMALISTAS
with st.sidebar:
    st.markdown("---")
    col_udd, col_lifebox = st.columns(2)
    with col_udd:
        if os.path.exists("logo_udd.png"): st.image("logo_udd.png", use_container_width=True) 
    with col_lifebox:
        if os.path.exists("logo_lifebox.png"): st.image("logo_lifebox.png", use_container_width=True) 
    st.markdown("<h5 style='text-align: center; color: #4F8BF9; margin-top: 10px;'>Colaboración Estratégica</h5>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### 🔍 Filtros de Búsqueda")
    
    if not df_base.empty:
        fechas_unicas = sorted(list(set([d.split(" ")[0] for d in df_base['Detectado el']])), reverse=True)
        
        lista_otics = ["Todas"] + sorted(df_base['OTIC'].unique().tolist())
        lista_gatillos = ["Todos"] + sorted(df_base['Gatillo'].unique().tolist())
        lista_fechas = ["Todas"] + fechas_unicas
        
        filtro_fecha = st.selectbox("📅 Fecha de Detección", lista_fechas)
        filtro_otic = st.selectbox("📌 OTIC", lista_otics)
        filtro_gatillo = st.selectbox("🎯 Gatillo (Palabra Clave)", lista_gatillos)
    else:
        st.info("Filtros no disponibles (Base de datos vacía)")
        filtro_otic = filtro_gatillo = filtro_fecha = "Todos"
        
    st.markdown("---")
    st.markdown("### ⚙️ Estado del Sistema")
    st.success("🟢 Live View: Activo (Auto-refresco cada 5 min)")
    if st.button("🔄 Actualizar Manualmente", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# 6. LÓGICA DE APLICACIÓN DE FILTROS
df_filtrado = df_base.copy()
if not df_filtrado.empty:
    if filtro_fecha != "Todas": 
        df_filtrado = df_filtrado[df_filtrado['Detectado el'].str.startswith(filtro_fecha)]
    if filtro_otic != "Todas": 
        df_filtrado = df_filtrado[df_filtrado['OTIC'] == filtro_otic]
    if filtro_gatillo != "Todos": 
        df_filtrado = df_filtrado[df_filtrado['Gatillo'] == filtro_gatillo]

# 7. CABECERA PRINCIPAL
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
    st.info("No hay oportunidades activas en la base de datos en este momento.")
else:
    kpi1, kpi2 = st.columns(2)
    
    total_ops = len(df_filtrado)
    total_otics = df_filtrado['OTIC'].nunique() if total_ops > 0 else 0
    
    with kpi1:
        st.markdown(f"""<div class="dashboard-card"><div class="card-title">Oportunidades</div><p class="card-value val-blue">{total_ops}</p></div>""", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""<div class="dashboard-card"><div class="card-title">OTICs Activas</div><p class="card-value val-orange">{total_otics}</p></div>""", unsafe_allow_html=True)

    st.markdown("### 📋 Repositorio de Licitaciones")
    if total_ops == 0:
        st.warning("No hay resultados que coincidan con los filtros seleccionados.")
    else:
        df_interactivo = df_filtrado.copy()
        df_interactivo.insert(0, '🗑️ Descartar', False)

        df_editado = st.data_editor(
            df_interactivo,
            column_config={
                "🗑️ Descartar": st.column_config.CheckboxColumn("Descartar", help="Marca esta casilla para enviar a la lista negra"),
                "Link Excel": st.column_config.LinkColumn("Descargar Base")
            },
            disabled=['Detectado el', 'Llamado', 'OTIC', 'Gatillo', 'Curso', 'Región', 'Comuna', 'Modalidad', 'Link Excel'],
            use_container_width=True,
            hide_index=True,
            height=400
        )

        filas_a_descartar = df_editado[df_editado['🗑️ Descartar'] == True]

        if not filas_a_descartar.empty:
            st.warning(f"Estás a punto de ocultar {len(filas_a_descartar)} documentos de la vista principal.")
            if st.button("⚠️ Confirmar y Ocultar Selección", type="primary"):
                
                cliente_bq = bigquery.Client(project=ID_PROYECTO, credentials=credenciales)
                
                condiciones_ocultar = []
                for _, fila in filas_a_descartar.iterrows():
                    link_safe = str(fila['Link Excel']).replace("'", "\\'")
                    curso_safe = str(fila['Curso']).replace("'", "\\'")
                    region_safe = str(fila['Región']).replace("'", "\\'")
                    comuna_safe = str(fila['Comuna']).replace("'", "\\'")
                    
                    condiciones_ocultar.append(
                        f"(link_documento = '{link_safe}' "
                        f"AND curso = '{curso_safe}' "
                        f"AND COALESCE(region, 'No especificado') = '{region_safe}' "
                        f"AND COALESCE(comuna, 'No especificado') = '{comuna_safe}')"
                    )
                
                where_sql = " OR ".join(condiciones_ocultar)
                
                query_update = f"""
                    UPDATE `{ID_PROYECTO}.licitaciones.oportunidades`
                    SET estado = 'Descartado'
                    WHERE {where_sql}
                """
                
                with st.spinner("Enviando a la lista negra..."):
                    cliente_bq.query(query_update).result() 
                    st.cache_data.clear()
                    st.rerun()

# --- PAPELERA DE RECICLAJE ---
st.markdown("---")
ver_papelera = st.toggle("🗑️ Abrir Papelera de Reciclaje")

if ver_papelera:
    st.markdown("#### Documentos Descartados")
    
    query_papelera = f"""
        SELECT fecha_deteccion, titulo_llamado_web, curso, region, comuna, link_documento
        FROM `{ID_PROYECTO}.licitaciones.oportunidades`
        WHERE estado = 'Descartado'
        ORDER BY fecha_deteccion DESC
    """
    try:
        df_papelera = pd.read_gbq(query_papelera, project_id=ID_PROYECTO, credentials=credenciales)
        
        if df_papelera.empty:
            st.info("La papelera está vacía.")
        else:
            df_papelera['region'] = df_papelera['region'].fillna('No especificado').astype(str)
            df_papelera['comuna'] = df_papelera['comuna'].fillna('No especificado').astype(str)
            
            df_papelera.insert(0, '♻️ Restaurar', False)
            
            df_papelera_edit = st.data_editor(
                df_papelera,
                column_config={
                    "♻️ Restaurar": st.column_config.CheckboxColumn("Restaurar", help="Marca para devolver a la vista principal")
                },
                disabled=['fecha_deteccion', 'titulo_llamado_web', 'curso', 'region', 'comuna', 'link_documento'],
                use_container_width=True,
                hide_index=True
            )
            
            filas_a_restaurar = df_papelera_edit[df_papelera_edit['♻️ Restaurar'] == True]
            
            if not filas_a_restaurar.empty:
                if st.button("✨ Confirmar Restauración", type="primary"):
                    
                    condiciones_restaurar = []
                    for _, fila in filas_a_restaurar.iterrows():
                        link_safe = str(fila['link_documento']).replace("'", "\\'")
                        curso_safe = str(fila['curso']).replace("'", "\\'")
                        region_safe = str(fila['region']).replace("'", "\\'")
                        comuna_safe = str(fila['comuna']).replace("'", "\\'")
                        
                        condiciones_restaurar.append(
                            f"(link_documento = '{link_safe}' "
                            f"AND curso = '{curso_safe}' "
                            f"AND COALESCE(region, 'No especificado') = '{region_safe}' "
                            f"AND COALESCE(comuna, 'No especificado') = '{comuna_safe}')"
                        )
                    
                    where_sql_restaurar = " OR ".join(condiciones_restaurar)
                    
                    query_revivir = f"""
                        UPDATE `{ID_PROYECTO}.licitaciones.oportunidades`
                        SET estado = 'Activo'
                        WHERE {where_sql_restaurar}
                    """
                    
                    with st.spinner("Restaurando documentos..."):
                        cliente_bq = bigquery.Client(project=ID_PROYECTO, credentials=credenciales)
                        cliente_bq.query(query_revivir).result()
                        
                        st.cache_data.clear()
                        st.rerun()
                        
    except Exception as e:
        st.error(f"Error cargando la papelera: {e}")