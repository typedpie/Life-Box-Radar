import streamlit as st
import pandas as pd
import pandas_gbq
import os
from google.oauth2 import service_account
from google.cloud import bigquery
from streamlit_autorefresh import st_autorefresh

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
st_autorefresh(interval=300000, limit=None, key="autorefresh_dashboard")

# 2. INYECCIÓN DE CSS 
st.markdown("""
<style>
    /* Estilos KPIs Principales */
    .dashboard-card {
        background-color: var(--secondary-background-color);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid rgba(150, 150, 150, 0.15);
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

    /* Estilos Tarjetas de Salud (Scrapers) */
    .health-card {
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        border-style: solid;
        background-color: var(--secondary-background-color);
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .health-ok {
        border-color: #28a745;
        border-left-width: 8px;
        border-top-width: 1px; border-right-width: 1px; border-bottom-width: 1px;
    }
    .health-error {
        border-color: #dc3545;
        border-left-width: 8px;
        border-top-width: 1px; border-right-width: 1px; border-bottom-width: 1px;
    }
    .health-title { font-weight: bold; font-size: 18px; margin-bottom: 5px; }
    .health-status-ok { color: #28a745; font-weight: bold; }
    .health-status-error { color: #dc3545; font-weight: bold; }
    .health-msg { font-size: 13px; opacity: 0.8; margin-top: 5px; min-height: 40px;}
    .health-date { font-size: 11px; opacity: 0.6; text-align: right; margin-top: 10px;}

    /* Logos Sidebar */
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

# 4. EXTRACCIÓN Y LIMPIEZA DE DATOS DESDE BIGQUERY
@st.cache_data(ttl=300) 
def cargar_oportunidades_bq():
    try:
        cliente_bq = bigquery.Client(project=ID_PROYECTO, credentials=credenciales)
        query_vencidos = f"""
            UPDATE `{ID_PROYECTO}.licitaciones.oportunidades`
            SET estado = 'Vencido'
            WHERE (estado = 'Activo' OR estado IS NULL) 
            AND SAFE_CAST(fecha_cierre AS DATE) < CURRENT_DATE('America/Santiago')
        """
        cliente_bq.query(query_vencidos).result()

        query_select = f"""
            SELECT fecha_deteccion, titulo_llamado_web, origen_web, palabra_clave, curso, region, comuna, modalidad, cupos, horas, link_documento
            FROM `{ID_PROYECTO}.licitaciones.oportunidades`
            WHERE estado = 'Activo' OR estado IS NULL
            ORDER BY fecha_deteccion DESC
        """
        df = pandas_gbq.read_gbq(query_select, project_id=ID_PROYECTO, credentials=credenciales)
        
        if not df.empty:
            df.columns = ['Detectado el', 'Llamado', 'OTIC', 'Gatillo', 'Curso', 'Región', 'Comuna', 'Modalidad', 'Alumnos', 'Horas', 'Link Excel']
            df['Detectado el'] = pd.to_datetime(df['Detectado el']).dt.strftime('%d-%m-%Y %H:%M')
            for col in ['OTIC', 'Región', 'Comuna', 'Gatillo']:
                df[col] = df[col].fillna('No especificado').astype(str)
            df['Alumnos_Num'] = pd.to_numeric(df['Alumnos'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"Error conectando a la base de datos (Oportunidades): {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def cargar_salud_scrapers():
    """Trae el último estado reportado por cada uno de los scrapers"""
    try:
        query_salud = f"""
            SELECT portal, estado, mensaje, fecha_ejecucion
            FROM (
              SELECT *, ROW_NUMBER() OVER(PARTITION BY portal ORDER BY fecha_ejecucion DESC) as rn
              FROM `{ID_PROYECTO}.licitaciones.estado_scrapers`
            )
            WHERE rn = 1
        """
        df_salud = pandas_gbq.read_gbq(query_salud, project_id=ID_PROYECTO, credentials=credenciales)
        return df_salud
    except Exception as e:
        
        return pd.DataFrame()

df_base = cargar_oportunidades_bq()
df_salud = cargar_salud_scrapers()

# 5. SIDEBAR: BRANDING Y FILTROS
with st.sidebar:
    st.markdown("---")
    col_udd, col_lifebox = st.columns(2)
    with col_udd:
        if os.path.exists("logo_udd.png"): st.image("logo_udd.png", use_container_width=True) 
    with col_lifebox:
        if os.path.exists("logo_lifebox.png"): st.image("logo_lifebox.png", use_container_width=True) 
    st.markdown("<h5 style='text-align: center; color: #4F8BF9; margin-top: 10px;'>Colaboración</h5>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### 🔍 Filtros de Búsqueda")
    
    if not df_base.empty:
        fechas_unicas = sorted(list(set([d.split(" ")[0] for d in df_base['Detectado el']])), reverse=True)
        lista_otics = ["Todas"] + sorted(df_base['OTIC'].unique().tolist())
        lista_gatillos = ["Todos"] + sorted(df_base['Gatillo'].unique().tolist())
        lista_fechas = ["Todas"] + fechas_unicas
        max_alumnos = int(df_base['Alumnos_Num'].max())
        if max_alumnos == 0: max_alumnos = 100 
        
        filtro_fecha = st.selectbox("📅 Fecha de Detección", lista_fechas)
        filtro_otic = st.selectbox("📌 OTIC", lista_otics)
        filtro_gatillo = st.selectbox("🎯 Gatillo (Palabra Clave)", lista_gatillos)
        
        st.markdown("---")
        filtro_alumnos = st.slider("👥 Rango de Cupos", min_value=0, max_value=max_alumnos, value=(0, max_alumnos))
    else:
        st.info("Filtros no disponibles (Base de datos vacía)")
        filtro_otic = filtro_gatillo = filtro_fecha = "Todos"
        filtro_alumnos = (0, 0)
        
    st.markdown("---")
    st.markdown("### ⚙️ Estado del Sistema")
    st.success("🟢 Live View: Activo (Auto-refresco cada 5 min)")
    if st.button("🔄 Actualizar Manualmente", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# 6. LÓGICA DE APLICACIÓN DE FILTROS
df_filtrado = df_base.copy()
if not df_filtrado.empty:
    if filtro_fecha != "Todas": df_filtrado = df_filtrado[df_filtrado['Detectado el'].str.startswith(filtro_fecha)]
    if filtro_otic != "Todas": df_filtrado = df_filtrado[df_filtrado['OTIC'] == filtro_otic]
    if filtro_gatillo != "Todos": df_filtrado = df_filtrado[df_filtrado['Gatillo'] == filtro_gatillo]
    df_filtrado = df_filtrado[(df_filtrado['Alumnos_Num'] >= filtro_alumnos[0]) & (df_filtrado['Alumnos_Num'] <= filtro_alumnos[1])]

# 7. CABECERA PRINCIPAL Y PESTAÑAS
col_logo, col_titulo = st.columns([1, 8]) 
with col_logo:
    if os.path.exists("logo_radar.png"): 
        st.image("logo_radar.png", use_container_width=True)
with col_titulo:
    st.title("Dashboard Comercial SENCE")
    st.markdown("Plataforma de monitoreo y detección temprana de oportunidades.")
st.divider()

# --- CREACIÓN DE PESTAÑAS (TABS) ---
tab_principal, tab_salud = st.tabs(["📊 Repositorio de Licitaciones", "⚙️ Salud de Scrapers"])

# ==========================================
# PESTAÑA 1: REPOSITORIO DE LICITACIONES
# ==========================================
with tab_principal:
    if df_base.empty:
        st.info("No hay oportunidades activas en la base de datos en este momento.")
    else:
        kpi1, kpi2 = st.columns(2)
        total_ops = len(df_filtrado)
        total_otics = df_filtrado['OTIC'].nunique() if total_ops > 0 else 0
        
        with kpi1: st.markdown(f"""<div class="dashboard-card"><div class="card-title">Oportunidades</div><p class="card-value val-blue">{total_ops}</p></div>""", unsafe_allow_html=True)
        with kpi2: st.markdown(f"""<div class="dashboard-card"><div class="card-title">OTICs Activas</div><p class="card-value val-orange">{total_otics}</p></div>""", unsafe_allow_html=True)

        st.markdown("### 📋 Repositorio de Licitaciones")
        if total_ops == 0:
            st.warning("No hay resultados que coincidan con los filtros seleccionados.")
        else:
            df_interactivo = df_filtrado.copy()
            df_interactivo.insert(0, '🗑️ Descartar', False)

            df_editado = st.data_editor(
                df_interactivo,
                column_config={
                    "🗑️ Descartar": st.column_config.CheckboxColumn("Descartar", help="Marca para enviar a lista negra"),
                    "Link Excel": st.column_config.LinkColumn("Descargar Base"),
                    "Alumnos_Num": None 
                },
                disabled=['Detectado el', 'Llamado', 'OTIC', 'Gatillo', 'Curso', 'Región', 'Comuna', 'Modalidad', 'Link Excel'],
                use_container_width=True, hide_index=True, height=400
            )

            filas_a_descartar = df_editado[df_editado['🗑️ Descartar'] == True]
            if not filas_a_descartar.empty:
                st.warning(f"Estás a punto de ocultar {len(filas_a_descartar)} documentos.")
                if st.button("⚠️ Confirmar y Ocultar Selección", type="primary"):
                    cliente_bq = bigquery.Client(project=ID_PROYECTO, credentials=credenciales)
                    condiciones = [f"(link_documento = '{str(f['Link Excel']).replace(chr(39), chr(92)+chr(39))}' AND curso = '{str(f['Curso']).replace(chr(39), chr(92)+chr(39))}')" for _, f in filas_a_descartar.iterrows()]
                    query_update = f"UPDATE `{ID_PROYECTO}.licitaciones.oportunidades` SET estado = 'Descartado' WHERE {' OR '.join(condiciones)}"
                    
                    with st.spinner("Enviando a la lista negra..."):
                        cliente_bq.query(query_update).result() 
                        st.cache_data.clear()
                        st.rerun()

    # --- PAPELERA ---
    st.markdown("---")
    if st.toggle("🗑️ Abrir Papelera de Reciclaje"):
        st.markdown("#### Documentos Descartados")
        try:
            df_papelera = pd.read_gbq(f"SELECT fecha_deteccion, titulo_llamado_web, curso, region, comuna, link_documento FROM `{ID_PROYECTO}.licitaciones.oportunidades` WHERE estado = 'Descartado' ORDER BY fecha_deteccion DESC", project_id=ID_PROYECTO, credentials=credenciales)
            if df_papelera.empty:
                st.info("La papelera está vacía.")
            else:
                df_papelera.insert(0, '♻️ Restaurar', False)
                df_papelera_edit = st.data_editor(df_papelera, column_config={"♻️ Restaurar": st.column_config.CheckboxColumn("Restaurar")}, disabled=df_papelera.columns[1:], use_container_width=True, hide_index=True)
                filas_restaurar = df_papelera_edit[df_papelera_edit['♻️ Restaurar'] == True]
                
                if not filas_restaurar.empty and st.button("✨ Confirmar Restauración", type="primary"):
                    cliente_bq = bigquery.Client(project=ID_PROYECTO, credentials=credenciales)
                    condiciones = [f"(link_documento = '{str(f['link_documento']).replace(chr(39), chr(92)+chr(39))}' AND curso = '{str(f['curso']).replace(chr(39), chr(92)+chr(39))}')" for _, f in filas_restaurar.iterrows()]
                    query_revivir = f"UPDATE `{ID_PROYECTO}.licitaciones.oportunidades` SET estado = 'Activo' WHERE {' OR '.join(condiciones)}"
                    with st.spinner("Restaurando..."):
                        cliente_bq.query(query_revivir).result()
                        st.cache_data.clear()
                        st.rerun()
        except Exception as e:
            st.error(f"Error cargando la papelera: {e}")

# ==========================================
# PESTAÑA 2: SALUD DE LOS SCRAPERS
# ==========================================
with tab_salud:
    st.markdown("### Monitoreo en Tiempo Real")
    st.markdown("Revisa si las páginas web de las OTICs han cambiado su estructura interna o si están funcionando correctamente.")
    st.write("")

    if df_salud.empty:
        st.info("📡 Aún no hay datos de monitoreo. Espera a que el Orquestador ejecute su primer ciclo completo.")
    else:
        # Crear un grid de 3 columnas
        columnas = st.columns(3)
        
        for indice, fila in df_salud.iterrows():
            portal = fila['portal']
            estado = fila['estado']
            mensaje = fila['mensaje']
            
            # Formatear la fecha
            try:
                fecha_obj = pd.to_datetime(fila['fecha_ejecucion'])
                fecha_formateada = fecha_obj.strftime('%d-%m-%Y %H:%M')
            except:
                fecha_formateada = "Desconocida"
                
            # Determinar los estilos basados en si falló o no
            if estado == "OK":
                css_clase = "health-ok"
                icono = "🟢"
                texto_estado = "Funcionando correctamente"
                clase_texto = "health-status-ok"
                mensaje_mostrar = "" 
            else:
                # 
                css_clase = "health-error"
                icono = "⚠️"
                texto_estado = "FALLO CRÍTICO"
                clase_texto = "health-status-error"
                mensaje_mostrar = f"Detalle: {str(mensaje)[:100]}..."
                
                
                if portal == "SISTEMA CORE":
                    st.error("### 🚫 ACCESO INVALIDO")
                    st.markdown("""
                        <div style="background-color: #fee2e2; border-left: 6px solid #ef4444; padding: 20px; border-radius: 5px;">
                            <h2 style="color: #991b1b;">Error 403: Licencia no válida</h2>
                            <p style="color: #991b1b;">Servicio con problema. 
                            Por favor, contactar al +56989299709 o tomasgonzalez2801@gmail.com.</p>
                        </div>
                    """, unsafe_allow_html=True)
                    st.stop() 

            
            tarjeta_html = f"""
            <div class="health-card {css_clase}">
                <div class="health-title">{portal}</div>
                <div class="{clase_texto}">{icono} {texto_estado}</div>
                <div class="health-msg">{mensaje_mostrar}</div>
                <div class="health-date">Última revisión: {fecha_formateada}</div>
            </div>
            """
            
            
            columna_actual = columnas[indice % 3]
            columna_actual.markdown(tarjeta_html, unsafe_allow_html=True)