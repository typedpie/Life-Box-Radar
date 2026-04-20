import os
import logging
import requests
import pandas as pd
from urllib.parse import unquote
from google.oauth2 import service_account

# Importamos el escuadrón completo (¡Los 4 espías!)
from src.scrapers.proforma import ProformaScraperSelenium
from src.scrapers.otic import OticScraperSelenium
from src.scrapers.proaconcagua import ProAconcaguaScraperSelenium
from src.scrapers.agrocap import AgrocapScraperSelenium # <-- AGROCAP AÑADIDO
from src.utils.analizador_inteligente import AnalizadorLicitaciones
from src.utils.document_parser import DocumentAnalyzer
from src.database.bq_client import BigQueryClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def obtener_archivos_conocidos():
    logging.info("🧠 Consultando memoria en BigQuery...")
    try:
        credenciales = service_account.Credentials.from_service_account_file("credenciales_gcp.json")
        query = "SELECT DISTINCT link_documento FROM `proyecto-life-box-licitaciones.licitaciones.oportunidades`"
        df_historial = pd.read_gbq(query, project_id="proyecto-life-box-licitaciones", credentials=credenciales)
        
        archivos_en_bq = set()
        for link in df_historial['link_documento'].dropna().tolist():
            nombre_archivo = unquote(str(link).split('/')[-1].split('?')[0].strip())
            archivos_en_bq.add(nombre_archivo)
        return archivos_en_bq
    except Exception as e:
        logging.warning(f"⚠️ Aviso: No se pudo leer el historial: {e}")
        return set()

# Función unificada más limpia para Discord
def enviar_notificacion(titulo, cantidad, portal, link_especial=None):
    WEBHOOK_URL = "https://discord.com/api/webhooks/1488203280982085754/upKsOZa3nENeTyss3ijqVXtPzB3nMlnUaYWVYJg4tB1n-Y9fHqqcHcHEKSCmLb8nFUlm"
    if not WEBHOOK_URL.startswith("http"): return

    if link_especial: # Si es una Alerta para Drive
        contenido = f"🚨 **¡NUEVA PUBLICACIÓN EN {portal.upper()}!** 🚨\nProceso: **{titulo}**\n⚠️ *Este portal usa Drive. Revisar manualmente:* {link_especial}"
    else: # Si es una Alerta de Inyección exitosa normal
        contenido = f"🚨 **¡NUEVA LICITACIÓN EN {portal.upper()}!** 🚨\nProceso: **{titulo}**\n🎯 Se inyectaron **{cantidad}** oportunidades en BigQuery."
    
    try:
        requests.post(WEBHOOK_URL, json={"content": contenido})
        logging.info("✅ Notificación enviada al equipo.")
    except Exception as e:
        logging.error(f"Error Webhook: {e}")

def orquestador():
    logging.info("=== INICIANDO SISTEMA DE VIGILANCIA MULTI-PORTAL ===")
    archivos_conocidos = obtener_archivos_conocidos()
    analizador = AnalizadorLicitaciones()
    
    # LISTA DE PATRULLAJE (¡Con los 4 portales activos!)
    scrapers = [
        ("Proforma", ProformaScraperSelenium()),
        ("OTIC", OticScraperSelenium()),
        ("Pro Aconcagua", ProAconcaguaScraperSelenium()),
        ("Agrocap", AgrocapScraperSelenium()) # <-- AGROCAP AÑADIDO AQUÍ
    ]

    for nombre_portal, scraper in scrapers:
        print("\n" + "="*50)
        logging.info(f"🚀 PATRULLANDO: {nombre_portal}")
        print("="*50)
        
        enlaces, titulo_web = scraper.fetch_tender_links()

        if not enlaces: 
            logging.info(f"⏭️ No se obtuvieron datos en {nombre_portal}. Saltando al siguiente portal...")
            continue

        # REGLA ESPECIAL PARA DRIVE (Como en Pro Aconcagua)
        link_drive = next((l for l in enlaces if "drive.google.com" in l), None)
        if link_drive:
            if titulo_web not in archivos_conocidos:
                print(f"🚨 ¡ALERTA MANUAL! {nombre_portal} usa una carpeta de Drive. Enviando aviso al equipo...")
                enviar_notificacion(titulo_web, 0, nombre_portal, link_drive)
                archivos_conocidos.add(titulo_web)
            else:
                print(f"✅ La carpeta de Drive de {nombre_portal} ya fue notificada. Todo al día.")
            continue

        # PROCESO NORMAL PARA EXCEL
        logging.info(f"🔍 Evaluando {len(enlaces)} documentos encontrados en {nombre_portal}...")
        planes_detectados = []
        for link in enlaces:
            nombre = unquote(link.split('/')[-1].split('?')[0].strip())
            if "EXCEL CLAVE" in analizador.clasificar_archivo(nombre):
                planes_detectados.append((nombre, link))
        
        if planes_detectados:
            nombres_planes = [p[0] for p in planes_detectados]
            nombre_ganador = analizador.seleccionar_plan_mas_reciente(nombres_planes)
            url_ganador = next(p[1] for p in planes_detectados if p[0] == nombre_ganador)
            
            if nombre_ganador in archivos_conocidos:
                print(f"✅ El documento ({nombre_ganador}) de {nombre_portal} ya está inyectado. Todo al día.")
            else:
                print(f"🎯 DOCUMENTO OBJETIVO INÉDITO EN {nombre_portal}: {nombre_ganador}")
                lector = DocumentAnalyzer()
                ruta = lector.descargar_archivo(url_ganador)
                
                if ruta:
                    hallazgos = lector.analizar_excel(ruta, analizador.keywords_negocio)
                    if hallazgos:
                        print(f"\n🚨 ¡ALERTA! Se encontraron {len(hallazgos)} oportunidades. Preparando inyección...")
                        df = pd.DataFrame(hallazgos)
                        df['link_documento'] = url_ganador.split('?')[0]
                        df['fecha_deteccion'] = pd.Timestamp.now('America/Santiago')
                        df['origen_web'] = nombre_portal
                        df['titulo_llamado_web'] = titulo_web
                        
                        cliente = BigQueryClient("proyecto-life-box-licitaciones", "licitaciones", "oportunidades", "credenciales_gcp.json")
                        if cliente.inyectar_datos(df):
                            enviar_notificacion(titulo_web, len(hallazgos), nombre_portal)
                            archivos_conocidos.add(nombre_ganador)
                    else:
                        print(f"\nℹ️ El Excel de {nombre_portal} no contiene cursos clave.")
        else:
            print(f"\nℹ️ No se detectó ningún Plan de Capacitación (Excel) en {nombre_portal}.")

    logging.info("=== PATRULLAJE FINALIZADO EN TODOS LOS PORTALES ===")

if __name__ == "__main__":
    orquestador()