import os
import logging
import requests
import pandas as pd
from urllib.parse import unquote
from google.oauth2 import service_account

# Importe de scrappers
from src.utils.sec import verificar_lic
from src.scrapers.proforma import ProformaScraperSelenium 
from src.scrapers.otic import OticScraperSelenium 
from src.scrapers.proaconcagua import ProAconcaguaScraperSelenium 
from src.scrapers.agrocap import AgrocapScraperSelenium 
from src.scrapers.banotic import BanoticScraperSelenium 
from src.scrapers.alianzapyme import AlianzaPymeScraperSelenium 
from src.scrapers.oticsosofa import OticSofofaScraperSelenium 
from src.scrapers.francochileno import FrancoChilenoScraperSelenium
from src.scrapers.winesofchile import ChileVinosScraperSelenium
from src.scrapers.ccc import CccScraperSelenium
from src.utils.analizador_inteligente import AnalizadorLicitaciones
from src.utils.document_parser import DocumentAnalyzer
from src.database.bq_client import BigQueryClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def obtener_archivos_conocidos():
    logging.info("🧠 Consultando memoria en BigQuery...")
    try:
        credenciales = service_account.Credentials.from_service_account_file("credenciales_gcp.json")
        
        query = "SELECT DISTINCT link_documento, titulo_llamado_web FROM `proyecto-life-box-licitaciones.licitaciones.oportunidades`"
        df_historial = pd.read_gbq(query, project_id="proyecto-life-box-licitaciones", credentials=credenciales)
        
        archivos_en_bq = set()
        for _, fila in df_historial.iterrows():
            link = fila['link_documento']
            if pd.notna(link):
                nombre_archivo = unquote(str(link).split('/')[-1].split('?')[0].strip())
                archivos_en_bq.add(nombre_archivo)
            
            titulo = fila['titulo_llamado_web']
            if pd.notna(titulo):
                archivos_en_bq.add(str(titulo).strip())
                
        return archivos_en_bq
    except Exception as e:
        logging.warning(f"⚠️ Aviso: No se pudo leer el historial: {e}")
        return set()

def enviar_notificacion(titulo, cantidad, portal, link_especial=None):
    # --- CONFIGURACIÓN TELEGRAM ---
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    if not TELEGRAM_TOKEN or not CHAT_ID:
        logging.error("⚠️ Faltan las credenciales de Telegram en las variables de entorno.")
        return


    # Esto evita que los guiones bajos en los links o títulos rompan Telegram
    if link_especial: 
        contenido = f"🚨 <b>¡NUEVA PUBLICACIÓN EN {portal.upper()}!</b> 🚨\nProceso: <b>{titulo}</b>\n⚠️ <i>Este portal usa Drive. Revisar manualmente:</i> {link_especial}"
    else: 
        contenido = f"🚨 <b>¡NUEVA LICITACIÓN EN {portal.upper()}!</b> 🚨\nProceso: <b>{titulo}</b>\n🎯 Se inyectaron <b>{cantidad}</b> oportunidades en BigQuery."
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": contenido,
        "parse_mode": "HTML"  
    }
    
    try:
        respuesta = requests.post(url, json=payload)
        if respuesta.status_code == 200:
            logging.info("✅ Notificación enviada a Telegram directo a tu teléfono.")
        else:
            logging.error(f"Telegram rechazó el envío: {respuesta.text}")
    except Exception as e:
        logging.error(f"Error conectando con la API de Telegram: {e}")

def enviar_alerta_error(portal, mensaje_error):
    """Envía un mensaje de emergencia a Telegram cuando un scraper falla"""
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    if not TELEGRAM_TOKEN or not CHAT_ID: return

    # error corto paara no colapsar telegram
    error_corto = str(mensaje_error)[:200]
    
    contenido = (
        f"🚨 *¡ALERTA CRÍTICA DE SCRAPER!* 🚨\n\n"
        f"🛑 *Portal Caído:* {portal}\n"
        f"⚠️ *Motivo:* `{error_corto}...`\n\n"
        f"🛠️ _Revisa el código, es posible que la página haya cambiado su diseño._"
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": contenido, "parse_mode": "Markdown"}
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        logging.error(f"No se pudo avisar a Telegram del error: {e}")

def registrar_estado_scraper(portal, estado, mensaje="Funcionando correctamente"):
    """Guarda el estado de salud de cada scraper en BigQuery"""
    proyecto_id = "proyecto-life-box-licitaciones"
    
    df_estado = pd.DataFrame([{
        "fecha_ejecucion": pd.Timestamp.now('America/Santiago'),
        "portal": portal,
        "estado": estado,
        "mensaje": str(mensaje)
    }])
    
    try:
        
        pd.io.gbq.to_gbq(
            df_estado, 
            destination_table='licitaciones.estado_scrapers', 
            project_id=proyecto_id, 
            if_exists='append'
        )
    except Exception as e:
        logging.error(f"Error guardando el estado en BigQuery: {e}")

def orquestador():
    verificar_lic()
    logging.info("=== INICIANDO SISTEMA DE VIGILANCIA MULTI-PORTAL ===")
    archivos_conocidos = obtener_archivos_conocidos()
    analizador = AnalizadorLicitaciones()
    
    scrapers = [
        ("Proforma", ProformaScraperSelenium()),
        ("OTIC", OticScraperSelenium()),
        ("Pro Aconcagua", ProAconcaguaScraperSelenium()),
        ("Agrocap", AgrocapScraperSelenium()), 
        ("Banotic", BanoticScraperSelenium()),
        ("Alianza Pyme", AlianzaPymeScraperSelenium()),
        ("OTIC Sofofa", OticSofofaScraperSelenium()),
        ("CCC", CccScraperSelenium()),
        ("Franco Chileno", FrancoChilenoScraperSelenium()),
        ("Wines of Chile", ChileVinosScraperSelenium())
    ]

    for nombre_portal, scraper in scrapers:
        print("\n" + "="*50)
        logging.info(f"🚀 PATRULLANDO: {nombre_portal}")
        print("="*50)
        
        try: 
            enlaces, titulo_web = scraper.fetch_tender_links()

            if not enlaces: 
                logging.info(f"⏭️ No se obtuvieron datos en {nombre_portal}. Saltando al siguiente portal...")
                #  Reportos 
                registrar_estado_scraper(nombre_portal, "OK", "Sin datos nuevos o error interno del scraper") 
                continue

            link_drive = next((l for l in enlaces if "drive.google.com" in l), None)
            if link_drive:
                if titulo_web not in archivos_conocidos:
                    print(f"🚨 ¡ALERTA MANUAL! {nombre_portal} usa una carpeta de Drive. Enviando aviso al equipo...")
                    enviar_notificacion(titulo_web, 0, nombre_portal, link_drive)
                    archivos_conocidos.add(titulo_web)
                    
                    
                    df_drive = pd.DataFrame([{
                        "palabra_clave": "N/A", "curso": "Carpeta de Drive (Aviso ya enviado)", 
                        "region": "N/A", "comuna": "N/A", "cupos": "0", "horas": "0", "modalidad": "N/A", "fila": 0
                    }])
                    df_drive['link_documento'] = link_drive
                    df_drive['fecha_deteccion'] = pd.Timestamp.now('America/Santiago')
                    df_drive['origen_web'] = nombre_portal
                    df_drive['titulo_llamado_web'] = titulo_web
                    df_drive['fecha_cierre'] = "Drive Manual"
                    df_drive['estado'] = "Revisión Manual"

                    cliente = BigQueryClient("proyecto-life-box-licitaciones", "licitaciones", "oportunidades", "credenciales_gcp.json")
                    cliente.inyectar_datos(df_drive)
                    
                    
                else:
                    print(f"✅ La carpeta de Drive de {nombre_portal} ya fue notificada. Todo al día.")
                
                registrar_estado_scraper(nombre_portal, "OK", "Usa carpeta de Drive") 
                continue

            

            logging.info(f"🔍 Evaluando {len(enlaces)} documentos encontrados en {nombre_portal}...")
            planes_detectados = []
            links_pdfs = [] 
            
            for link_original in enlaces:
                # 1. Limpiar link
                link_limpio = link_original.split('#')[0] 
                
                # 2. saca nombre inyectado
                if "#" in link_original:
                    nombre = unquote(link_original.split('#')[-1].strip())
                else:
                    nombre = unquote(link_original.split('/')[-1].split('?')[0].strip())
                
                # 3. Clasifica excel usando nombre
                if "EXCEL CLAVE" in analizador.clasificar_archivo(nombre):
                    planes_detectados.append((nombre, link_limpio))
                
                # 4. ClasificarRRR PDFs
                elif nombre.lower().endswith('.pdf') or '.pdf?' in nombre.lower():
                    links_pdfs.append((nombre, link_limpio))
            
            if planes_detectados:
                nombres_planes = [p[0] for p in planes_detectados]
                nombre_ganador = analizador.seleccionar_plan_mas_reciente(nombres_planes)
                url_ganador = next(p[1] for p in planes_detectados if p[0] == nombre_ganador)
                
                if nombre_ganador in archivos_conocidos:
                    print(f"✅ El documento ({nombre_ganador}) de {nombre_portal} ya está inyectado. Todo al día.")
                else:
                    print(f"🎯 DOCUMENTO OBJETIVO INÉDITO EN {nombre_portal}: {nombre_ganador}")
                    lector = DocumentAnalyzer()
                    
                    # ==========================================
                    # EXTRACCIÓN DE FECHA DESDE EL PDF
                    # ==========================================
                    fecha_cierre = "No especificada"
                    estado_licitacion = "Activo"
                    url_pdf_fecha = None
                    
                    # 1. Búsqued PRIORIDAD
                    for nombre_pdf, link_pdf in links_pdfs:
                        nom_bajo = nombre_pdf.lower()
                        if any(x in nom_bajo for x in ['cronograma', 'anexo 1', 'anexo-1', 'anexo1', 'anexo n°1', 'calendario']):
                            url_pdf_fecha = link_pdf
                            break
                    
                    # 2. Búsqueda PRIORIDAD menor
                    if not url_pdf_fecha:
                        for nombre_pdf, link_pdf in links_pdfs:
                            nom_bajo = nombre_pdf.lower()
                            if any(x in nom_bajo for x in ['base', 'anexo']):
                                if not any(basura in nom_bajo for basura in ['modifica', 'r.e.', 'resolucion', 'ord', 'ordinario']):
                                    url_pdf_fecha = link_pdf
                                    break
                    
                    
                    if not url_pdf_fecha and links_pdfs:
                        url_pdf_fecha = links_pdfs[0][1]
                        
                    if url_pdf_fecha:
                        print(f"📄 Descargando PDF para extraer fecha: {unquote(url_pdf_fecha.split('/')[-1])}")
                        ruta_pdf = lector.descargar_archivo(url_pdf_fecha)
                        if ruta_pdf:
                            fecha_cierre = lector.extraer_fecha_pdf(ruta_pdf)
                            os.remove(ruta_pdf) 
                            
                            if fecha_cierre != "No especificada":
                                try:
                                    fecha_limite_dt = pd.to_datetime(fecha_cierre, format='%Y-%m-%d')
                                    fecha_hoy_dt = pd.Timestamp.now('America/Santiago').normalize().tz_localize(None)
                                    
                                    if fecha_limite_dt < fecha_hoy_dt:
                                        estado_licitacion = "Vencido"
                                        print(f"⚠️ LICITACIÓN EXPIRADA: La fecha de cierre ({fecha_cierre}) ya pasó.")
                                    else:
                                        print(f"✅ LICITACIÓN VIGENTE: Cierra el {fecha_cierre}.")
                                except Exception as e:
                                    logging.warning(f"No se pudo calcular el vencimiento para la fecha: {fecha_cierre}")
                    

                    # ==========================================
                    # DECISIÓN: ¿LEo EL EXCEL?
                    # ==========================================
                    if estado_licitacion == "Vencido":
                        print(f"⏭️ AHORRO DE TOKENS: La licitación está vencida. Se descarta la lectura de cursos del Excel de {nombre_portal}.")
                        
                        #Subo UNA sola fila "fantasma" a BigQuery para que el bot la recuerde mañana
                        df_vencida = pd.DataFrame([{
                            "palabra_clave": "N/A", "curso": "Licitación Vencida (Ignorada para ahorrar proceso)", 
                            "region": "N/A", "comuna": "N/A", "cupos": "0", "horas": "0", "modalidad": "N/A", "fila": 0
                        }])
                        df_vencida['link_documento'] = url_ganador.split('?')[0]
                        df_vencida['fecha_deteccion'] = pd.Timestamp.now('America/Santiago')
                        df_vencida['origen_web'] = nombre_portal
                        df_vencida['titulo_llamado_web'] = titulo_web
                        df_vencida['fecha_cierre'] = fecha_cierre
                        df_vencida['estado'] = "Vencido"

                        cliente = BigQueryClient("proyecto-life-box-licitaciones", "licitaciones", "oportunidades", "credenciales_gcp.json")
                        cliente.inyectar_datos(df_vencida)
                        archivos_conocidos.add(nombre_ganador)
                        
                    else:
                        # ==========================================
                        # LA LICITACIÓN ESTÁ VIGENTE, APLICO LA IA AL EXCEL
                        # ==========================================
                        ruta = lector.descargar_archivo(url_ganador)
                        
                        if ruta:
                            hallazgos = lector.analizar_excel(ruta, analizador.keywords_negocio)
                            if hallazgos:
                                print(f"\n🚨 ¡ALERTA! Se encontraron {len(hallazgos)} oportunidades vigentes. Preparando inyección...")
                                df = pd.DataFrame(hallazgos)
                                df['link_documento'] = url_ganador.split('?')[0]
                                df['fecha_deteccion'] = pd.Timestamp.now('America/Santiago')
                                df['origen_web'] = nombre_portal
                                df['titulo_llamado_web'] = titulo_web
                                df['fecha_cierre'] = fecha_cierre      
                                df['estado'] = estado_licitacion       
                                
                                cliente = BigQueryClient("proyecto-life-box-licitaciones", "licitaciones", "oportunidades", "credenciales_gcp.json")
                                if cliente.inyectar_datos(df):
                                    enviar_notificacion(titulo_web, len(hallazgos), nombre_portal)
                                    archivos_conocidos.add(nombre_ganador)
                            else:
                                print(f"\nℹ️ El Excel de {nombre_portal} no contiene cursos clave.")
            else:
                print(f"\nℹ️ No se detectó ningún Plan de Capacitación (Excel) en {nombre_portal}.")

            registrar_estado_scraper(nombre_portal, "OK")

        except Exception as e:
            
            logging.error(f"❌ Falla crítica ejecutando {nombre_portal}: {e}")
            enviar_alerta_error(nombre_portal, e)
            registrar_estado_scraper(nombre_portal, "ERROR", e)
            continue # pasa al siguiente portal-

    logging.info("=== PATRULLAJE FINALIZADO EN TODOS LOS PORTALES ===")

if __name__ == "__main__":
    orquestador()