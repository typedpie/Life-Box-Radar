import os
import logging
import time
import requests
import pandas as pd
from urllib.parse import unquote
from google.oauth2 import service_account

from src.scrapers.proforma import ProformaScraperSelenium
from src.utils.analizador_inteligente import AnalizadorLicitaciones
from src.utils.document_parser import DocumentAnalyzer
from src.database.bq_client import BigQueryClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def obtener_archivos_conocidos():
    """Lee BigQuery y extrae SOLO los nombres exactos de los archivos para evitar engaños de URLs."""
    logging.info("🧠 Consultando memoria en BigQuery...")
    try:
        credenciales = service_account.Credentials.from_service_account_file("credenciales_gcp.json")
        query = "SELECT DISTINCT link_documento FROM `proyecto-life-box-licitaciones.licitaciones.oportunidades`"
        df_historial = pd.read_gbq(query, project_id="proyecto-life-box-licitaciones", credentials=credenciales)
        
        archivos_en_bq = set()
        for link in df_historial['link_documento'].dropna().tolist():
            # Magia pura: Cortamos la URL y nos quedamos solo con "Nombre-del-Archivo.xlsx"
            nombre_archivo = unquote(str(link).split('/')[-1].split('?')[0].strip())
            archivos_en_bq.add(nombre_archivo)
            
        logging.info(f"✅ Memoria cargada: {len(archivos_en_bq)} documentos Excel ya registrados en la base.")
        return archivos_en_bq

    except Exception as e:
        logging.warning(f"⚠️ Aviso: La tabla de historial está vacía o hubo un error: {e}")
        return set()

def enviar_notificacion_equipo(titulo_llamado, cantidad_oportunidades):
    WEBHOOK_URL = "https://discord.com/api/webhooks/1488203280982085754/upKsOZa3nENeTyss3ijqVXtPzB3nMlnUaYWVYJg4tB1n-Y9fHqqcHcHEKSCmLb8nFUlm" 
    if not WEBHOOK_URL.startswith("http"):
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
    
    # 1. Cargamos los nombres de los archivos que ya procesamos en el pasado
    archivos_conocidos = obtener_archivos_conocidos()
    scraper = ProformaScraperSelenium()
    
    # 2. Obtenemos TODOS los documentos que están vivos en la página ahora mismo
    enlaces_actuales, titulo_acordeon = scraper.fetch_tender_links()

    if not enlaces_actuales:
        logging.warning("No se obtuvieron datos. Abortando.")
        return

    logging.info(f"🔍 Evaluando {len(enlaces_actuales)} documentos encontrados en la web...")
    analizador = AnalizadorLicitaciones()
    planes_excel_detectados = []

    print("\n=== BÚSQUEDA DEL PLAN DE CAPACITACIÓN MÁS RECIENTE ===")
    # 3. Buscamos a los candidatos (todos los Excel)
    for link in enlaces_actuales:
        nombre_archivo = unquote(link.split('/')[-1].split('?')[0].strip())
        categoria = analizador.clasificar_archivo(nombre_archivo)
        
        if "EXCEL CLAVE" in categoria:
            planes_excel_detectados.append((nombre_archivo, link))
    
    if planes_excel_detectados:
        # 4. Elegimos al campeón absoluto entre todos los que están en la web
        nombres_planes = [plan[0] for plan in planes_excel_detectados]
        nombre_ganador = analizador.seleccionar_plan_mas_reciente(nombres_planes)
        url_ganador = next(plan[1] for plan in planes_excel_detectados if plan[0] == nombre_ganador)
        
        # 5. EL ESCUDO INFALIBLE: ¿El campeón ya está en nuestra base de datos?
        if nombre_ganador in archivos_conocidos:
            print(f"⏭️ El documento más reciente ({nombre_ganador}) ya se encuentra inyectado en BigQuery.")
            logging.info("Sin novedades. Todo al día.")
        else:
            print(f"🎯 DOCUMENTO OBJETIVO INÉDITO ENCONTRADO: {nombre_ganador}")
            lector = DocumentAnalyzer()
            ruta_temporal = lector.descargar_archivo(url_ganador)
            
            if ruta_temporal:
                hallazgos = lector.analizar_excel(ruta_temporal, analizador.keywords_negocio)
                
                if hallazgos:
                    print(f"\n🚨 ¡ALERTA! Se encontraron {len(hallazgos)} oportunidades. Preparando inyección a BigQuery...")
                    
                    df_nuevos = pd.DataFrame(hallazgos)
                    # Guardamos la URL base limpia
                    df_nuevos['link_documento'] = url_ganador.split('?')[0]
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
        print("\nℹ️ No se detectó ningún Plan de Capacitación (Excel) en esta página.")

if __name__ == "__main__":
    orquestador()