import os
import logging
import time
import requests
import pandas as pd
from google.oauth2 import service_account

from src.scrapers.proforma import ProformaScraperSelenium
from src.utils.analizador_inteligente import AnalizadorLicitaciones
from src.utils.document_parser import DocumentAnalyzer
from src.database.bq_client import BigQueryClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def obtener_historial_bigquery():
    """Lee BigQuery y devuelve un 'Set' con los links ya procesados para evitar duplicados."""
    logging.info("🧠 Consultando memoria en BigQuery...")
    try:
        # Usamos las credenciales que GitHub inyecta mágicamente
        credenciales = service_account.Credentials.from_service_account_file("credenciales_gcp.json")
        query = "SELECT DISTINCT link_documento FROM `proyecto-life-box-licitaciones.licitaciones.oportunidades`"
        
        df_historial = pd.read_gbq(
            query, 
            project_id="proyecto-life-box-licitaciones", 
            credentials=credenciales
        )
        
        enlaces_conocidos = set(df_historial['link_documento'].dropna().tolist())
        logging.info(f"✅ Memoria cargada: {len(enlaces_conocidos)} documentos ya almacenados en BQ.")
        return enlaces_conocidos

    except Exception as e:
        logging.warning(f"⚠️ Aviso: La tabla de historial está vacía o hubo un error al leerla: {e}")
        return set()

def enviar_notificacion_equipo(titulo_llamado, cantidad_oportunidades):
    """Envía un mensaje automático al canal del equipo (Slack/Discord/Teams)."""
    # 🔴 RECORDATORIO DE SEGURIDAD: En el futuro, pasa esto a una variable de entorno 🔴
    WEBHOOK_URL = "https://discord.com/api/webhooks/1488203280982085754/upKsOZa3nENeTyss3ijqVXtPzB3nMlnUaYWVYJg4tB1n-Y9fHqqcHcHEKSCmLb8nFUlm" 
    
    if not WEBHOOK_URL.startswith("http"):
        logging.warning("No hay Webhook configurado. Notificación omitida.")
        return

    mensaje = {
        "content": f"🚨 **¡NUEVA LICITACIÓN DETECTADA!** 🚨\nEl radar automático ha encontrado el siguiente proceso en Proforma:\n**{titulo_llamado}**\n🎯 Se inyectaron **{cantidad_oportunidades}** oportunidades nuevas en BigQuery."
    }
    
    try:
        requests.post(WEBHOOK_URL, json=mensaje)
        logging.info("✅ Notificación enviada al equipo comercial.")
    except Exception as e:
        logging.error(f"❌ Error enviando la notificación: {e}")

def orquestador():
    logging.info("=== INICIANDO SISTEMA DE VIGILANCIA DE LICITACIONES ===")
    
    # 1. CARGAMOS LA MEMORIA DESDE LA NUBE EN VEZ DEL ARCHIVO LOCAL
    enlaces_conocidos = obtener_historial_bigquery()
    scraper = ProformaScraperSelenium()
    
    # 2. RECIBIMOS LOS ENLACES Y EL TÍTULO EXACTO DE LA WEB
    enlaces_actuales, titulo_acordeon = scraper.fetch_tender_links()

    if not enlaces_actuales:
        logging.warning("No se obtuvieron datos. Abortando.")
        return

    # Comparamos lo que hay en la web VS lo que ya está en BigQuery
    licitaciones_nuevas = enlaces_actuales - enlaces_conocidos

    if licitaciones_nuevas:
        logging.info(f"¡ALERTA NIVEL 1! Hay {len(licitaciones_nuevas)} documentos en la web que no están en nuestra base.")
        
        analizador = AnalizadorLicitaciones()
        planes_excel_detectados = []

        print("\n=== CLASIFICACIÓN DE NUEVOS DOCUMENTOS ===")
        for link in licitaciones_nuevas:
            nombre_archivo = link.split('/')[-1].split('?')[0]
            categoria = analizador.clasificar_archivo(nombre_archivo)
            print(f"- {categoria}: {nombre_archivo}")
            if "EXCEL CLAVE" in categoria:
                planes_excel_detectados.append((nombre_archivo, link))
        
        if planes_excel_detectados:
            print("\n=== RESOLUCIÓN DE VERSIONES COMERCIALES ===")
            nombres_planes = [plan[0] for plan in planes_excel_detectados]
            nombre_ganador = analizador.seleccionar_plan_mas_reciente(nombres_planes)
            url_ganador = next(plan[1] for plan in planes_excel_detectados if plan[0] == nombre_ganador)
            
            # EL ESCUDO FINAL: Verificamos que la URL ganadora específica no esté en BigQuery
            if url_ganador in enlaces_conocidos:
                print(f"⏭️ El documento ganador ({nombre_ganador}) ya fue inyectado anteriormente. Saltando...")
            else:
                print(f"🎯 DOCUMENTO OBJETIVO INÉDITO: {nombre_ganador}")
                lector = DocumentAnalyzer()
                ruta_temporal = lector.descargar_archivo(url_ganador)
                
                if ruta_temporal:
                    hallazgos = lector.analizar_excel(ruta_temporal, analizador.keywords_negocio)
                    
                    if hallazgos:
                        print(f"\n🚨 ¡ALERTA! Se encontraron {len(hallazgos)} oportunidades. Preparando inyección a BigQuery...")
                        
                        df_nuevos = pd.DataFrame(hallazgos)
                        df_nuevos['link_documento'] = url_ganador
                        df_nuevos['fecha_deteccion'] = pd.Timestamp.now('America/Santiago')
                        df_nuevos['origen_web'] = "Proforma"
                        df_nuevos['titulo_llamado_web'] = titulo_acordeon
                        
                        cliente_bq = BigQueryClient(
                            project_id="proyecto-life-box-licitaciones", 
                            dataset_id="licitaciones",            
                            table_id="oportunidades",             
                            credentials_path="credenciales_gcp.json" 
                        )
                        
                        if cliente_bq.inyectar_datos(df_nuevos):
                            enviar_notificacion_equipo(titulo_acordeon, len(hallazgos))
                    else:
                        print(f"\nℹ️ El Excel no contiene cursos que coincidan con tus palabras clave.")
        else:
            print("\nℹ️ Ninguno de los documentos nuevos es un Excel relevante.")
    else:
        logging.info("Sin novedades desde la última revisión. Todo al día.")

if __name__ == "__main__":
    orquestador()