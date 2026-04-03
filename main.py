import json
import os
import logging
import time
import requests
import pandas as pd

from src.scrapers.proforma import ProformaScraperSelenium
from src.utils.analizador_inteligente import AnalizadorLicitaciones
from src.utils.document_parser import DocumentAnalyzer
from src.database.bq_client import BigQueryClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ARCHIVO_ESTADO = "estado_proforma.json"

def cargar_estado_anterior():
    if os.path.exists(ARCHIVO_ESTADO):
        if os.path.getsize(ARCHIVO_ESTADO) > 0:
            try:
                with open(ARCHIVO_ESTADO, 'r') as f:
                    return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def guardar_estado_actual(enlaces):
    with open(ARCHIVO_ESTADO, 'w') as f:
        json.dump(list(enlaces), f, indent=4)

def enviar_notificacion_equipo(titulo_llamado, cantidad_oportunidades):
    """Envía un mensaje automático al canal del equipo (Slack/Discord/Teams)."""
    # 🔴 PEGA AQUÍ LA URL DEL WEBHOOK QUE TE DEN LOS DE LIFEBOX 🔴
    WEBHOOK_URL = "https://discord.com/api/webhooks/1488203280982085754/upKsOZa3nENeTyss3ijqVXtPzB3nMlnUaYWVYJg4tB1n-Y9fHqqcHcHEKSCmLb8nFUlm" 
    
    if WEBHOOK_URL == "https://discord.com/api/webhooks/1488203280982085754/upKsOZa3nENeTyss3ijqVXtPzB3nMlnUaYWVYJg4tB1n-Y9fHqqcHcHEKSCmLb8nFUlm" or not WEBHOOK_URL.startswith("http"):
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
    
    enlaces_conocidos = cargar_estado_anterior()
    scraper = ProformaScraperSelenium()
    
    # 1. RECIBIMOS LOS ENLACES Y EL TÍTULO EXACTO DE LA WEB
    enlaces_actuales, titulo_acordeon = scraper.fetch_tender_links()

    if not enlaces_actuales:
        logging.warning("No se obtuvieron datos. Abortando.")
        return

    licitaciones_nuevas = enlaces_actuales - enlaces_conocidos

    if licitaciones_nuevas:
        logging.info(f"¡ALERTA NIVEL 1! Proforma ha subido {len(licitaciones_nuevas)} nuevos documentos.")
        
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
            print(f"🎯 DOCUMENTO OBJETIVO: {nombre_ganador}")
            
            lector = DocumentAnalyzer()
            ruta_temporal = lector.descargar_archivo(url_ganador)
            
            if ruta_temporal:
                hallazgos = lector.analizar_excel(ruta_temporal, analizador.keywords_negocio)
                
                if hallazgos:
                    print(f"\n🚨 ¡ALERTA! Se encontraron {len(hallazgos)} oportunidades. Preparando inyección a BigQuery...")
                    
                    # 2. ARMAMOS LA TABLA CON LOS DATOS DE LA IA Y DEL SCRAPER
                    df_nuevos = pd.DataFrame(hallazgos)
                    df_nuevos['link_documento'] = url_ganador
                    df_nuevos['fecha_deteccion'] = pd.Timestamp.now('America/Santiago')
                    
                    # Estampamos la verdad absoluta leída de la página web
                    df_nuevos['origen_web'] = "Proforma"
                    df_nuevos['titulo_llamado_web'] = titulo_acordeon
                    
                    # 3. CONEXIÓN A LA NUBE
                    cliente_bq = BigQueryClient(
                        project_id="proyecto-life-box-licitaciones", # 🔴 CAMBIAR POR TU ID REAL 🔴
                        dataset_id="licitaciones",            
                        table_id="oportunidades",             
                        credentials_path="credenciales_gcp.json" 
                    )
                    
                    if cliente_bq.inyectar_datos(df_nuevos):
                        # 4. DISPARO DE LA NOTIFICACIÓN
                        enviar_notificacion_equipo(titulo_acordeon, len(hallazgos))
                        
                else:
                    print(f"\nℹ️ El Excel no contiene cursos que coincidan con tus palabras clave.")
        
        guardar_estado_actual(enlaces_actuales)
        logging.info("Memoria actualizada.")
        
    else:
        logging.info("Sin novedades desde la última revisión.")

if __name__ == "__main__":
    orquestador()