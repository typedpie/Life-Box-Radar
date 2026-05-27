import os
import logging
import requests
import pandas as pd
from urllib.parse import unquote
from google.oauth2 import service_account

# Importe de scrappers
from src.scrapers.proforma import ProformaScraperSelenium 
from src.scrapers.otic import OticScraperSelenium 
from src.scrapers.proaconcagua import ProAconcaguaScraperSelenium 
from src.scrapers.agrocap import AgrocapScraperSelenium 
from src.scrapers.banotic import BanoticScraperSelenium 
from src.scrapers.alianzapyme import AlianzaPymeScraperSelenium 
from src.scrapers.oticsosofa import OticSofofaScraperSelenium 
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

def enviar_notificacion(titulo, cantidad, portal, link_especial=None):
    WEBHOOK_URL = "https://discord.com/api/webhooks/1488203280982085754/upKsOZa3nENeTyss3ijqVXtPzB3nMlnUaYWVYJg4tB1n-Y9fHqqcHcHEKSCmLb8nFUlm"
    if not WEBHOOK_URL.startswith("http"): return

    if link_especial: 
        contenido = f"🚨 **¡NUEVA PUBLICACIÓN EN {portal.upper()}!** 🚨\nProceso: **{titulo}**\n⚠️ *Este portal usa Drive. Revisar manualmente:* {link_especial}"
    else: 
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
    
    scrapers = [
        ("Proforma", ProformaScraperSelenium()),
        ("OTIC", OticScraperSelenium()),
        ("Pro Aconcagua", ProAconcaguaScraperSelenium()),
        ("Agrocap", AgrocapScraperSelenium()), 
        ("Banotic", BanoticScraperSelenium()),
        ("Alianza Pyme", AlianzaPymeScraperSelenium()),
        ("OTIC Sofofa", OticSofofaScraperSelenium())
    ]

    for nombre_portal, scraper in scrapers:
        print("\n" + "="*50)
        logging.info(f"🚀 PATRULLANDO: {nombre_portal}")
        print("="*50)
        
        enlaces, titulo_web = scraper.fetch_tender_links()

        if not enlaces: 
            logging.info(f"⏭️ No se obtuvieron datos en {nombre_portal}. Saltando al siguiente portal...")
            continue

        link_drive = next((l for l in enlaces if "drive.google.com" in l), None)
        if link_drive:
            if titulo_web not in archivos_conocidos:
                print(f"🚨 ¡ALERTA MANUAL! {nombre_portal} usa una carpeta de Drive. Enviando aviso al equipo...")
                enviar_notificacion(titulo_web, 0, nombre_portal, link_drive)
                archivos_conocidos.add(titulo_web)
            else:
                print(f"✅ La carpeta de Drive de {nombre_portal} ya fue notificada. Todo al día.")
            continue

        logging.info(f"🔍 Evaluando {len(enlaces)} documentos encontrados en {nombre_portal}...")
        planes_detectados = []
        links_pdfs = [] # <--- NUEVA LISTA PARA PDFs
        
        for link in enlaces:
            nombre = unquote(link.split('/')[-1].split('?')[0].strip())
            # Clasificar Excels
            if "EXCEL CLAVE" in analizador.clasificar_archivo(nombre):
                planes_detectados.append((nombre, link))
            # Clasificar PDFs
            elif link.lower().endswith('.pdf') or '.pdf?' in link.lower():
                links_pdfs.append((nombre, link))
        
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
                # NUEVO: EXTRACCIÓN DE FECHA DESDE EL PDF
                # ==========================================
                fecha_cierre = "No especificada"
                estado_licitacion = "Activo"
                url_pdf_fecha = None
                
                # Buscar un PDF prioritario (Bases, Anexos, Cronogramas)
                for nombre_pdf, link_pdf in links_pdfs:
                    if any(x in nombre_pdf.lower() for x in ['base', 'anexo', 'cronograma']):
                        url_pdf_fecha = link_pdf
                        break
                
                # Si no hay uno prioritario, tomamos el primer PDF que encontremos
                if not url_pdf_fecha and links_pdfs:
                    url_pdf_fecha = links_pdfs[0][1]
                    
                if url_pdf_fecha:
                    print(f"📄 Descargando PDF para extraer fecha: {unquote(url_pdf_fecha.split('/')[-1])}")
                    ruta_pdf = lector.descargar_archivo(url_pdf_fecha)
                    if ruta_pdf:
                        fecha_cierre = lector.extraer_fecha_pdf(ruta_pdf)
                        os.remove(ruta_pdf) 
                        
                        # LOGICA DE VENCIMIENTO
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
                        df['fecha_cierre'] = fecha_cierre      # <--- Inyectamos la fecha
                        df['estado'] = estado_licitacion       # <--- Inyectamos si está Activo o Vencido
                        
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