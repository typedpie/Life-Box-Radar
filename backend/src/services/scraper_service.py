"""
Scraper orchestrator: Main service coordinating all scraping operations.
"""
import logging
import os
from urllib.parse import unquote
import pandas as pd

from core.config import TIMEZONE
from database.bq_client import BigQueryClient
from services.notification_service import NotificationService
from services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)


class ScraperService:
    """Orchestrates scraping, analysis, and data injection workflow."""
    
    def __init__(self, scrapers_config):
        """Initialize service with list of scrapers."""
        self.scrapers_config = scrapers_config
        self.notification_service = NotificationService()
        self.analysis_service = AnalysisService()
        self.archivos_conocidos = set()
    
    def cargar_historial(self):
        """Load known documents from BigQuery to prevent duplicates."""
        logger.info("🧠 Loading history...")
        try:
            from google.oauth2 import service_account
            
            credenciales = service_account.Credentials.from_service_account_file(
                "credenciales_gcp.json"
            )
            query = (
                "SELECT DISTINCT link_documento, titulo_llamado_web "
                "FROM `proyecto-life-box-licitaciones.licitaciones.oportunidades`"
            )
            df_historial = pd.read_gbq(
                query,
                project_id="proyecto-life-box-licitaciones",
                credentials=credenciales
            )
            
            for _, fila in df_historial.iterrows():
                link = fila['link_documento']
                if pd.notna(link):
                    nombre_archivo = unquote(str(link).split('/')[-1].split('?')[0].strip())
                    self.archivos_conocidos.add(nombre_archivo)
                
                titulo = fila['titulo_llamado_web']
                if pd.notna(titulo):
                    self.archivos_conocidos.add(str(titulo).strip())
            
            logger.info(f"✅ History loaded: {len(self.archivos_conocidos)} items")
            return True
        
        except Exception as e:
            logger.warning(f"⚠️ Cannot read history: {e}")
            return False
    
    def procesar_portal(self, nombre_portal, scraper):
        """Process single portal and extract opportunities."""
        logger.info(f"🚀 Scanning: {nombre_portal}")
        print("=" * 50)
        
        try:
            # Fetch links
            enlaces, titulo_web = scraper.fetch_tender_links()
            
            if not enlaces:
                logger.info(f"⏭️ No data in {nombre_portal}")
                self.notification_service.registrar_estado_scraper(
                    nombre_portal, "OK", "No new data"
                )
                return
            
            # Process documents
            docs_info = self.analysis_service.procesar_documentos(enlaces, titulo_web)
            
            # Handle Drive links
            if docs_info["link_drive"]:
                if titulo_web not in self.archivos_conocidos:
                    logger.info(f"🚨 {nombre_portal} uses Drive. Alerting...")
                    self.notification_service.enviar_notificacion_licitacion(
                        titulo_web, 0, nombre_portal, docs_info["link_drive"]
                    )
                    self._guardar_fila_fantasma(
                        titulo_web, docs_info["link_drive"], nombre_portal,
                        "Revisión Manual", "N/A"
                    )
                    self.archivos_conocidos.add(titulo_web)
                
                self.notification_service.registrar_estado_scraper(
                    nombre_portal, "OK", "Uses Drive"
                )
                return
            
            # Process training plans
            if docs_info["planes_detectados"]:
                self._procesar_planes(
                    docs_info,
                    nombre_portal,
                    titulo_web
                )
            else:
                logger.info(f"ℹ️ No plans in {nombre_portal}")
            
            self.notification_service.registrar_estado_scraper(nombre_portal, "OK")
        
        except Exception as e:
            logger.error(f"❌ Error in {nombre_portal}: {e}")
            self.notification_service.enviar_alerta_error(nombre_portal, e)
            self.notification_service.registrar_estado_scraper(
                nombre_portal, "ERROR", str(e)
            )
    
    def _procesar_planes(self, docs_info, nombre_portal, titulo_web):
        """Process and analyze training plans."""
        nombres_planes = [p[0] for p in docs_info["planes_detectados"]]
        nombre_ganador = self.analysis_service.seleccionar_plan_mas_reciente(nombres_planes)
        url_ganador = next(
            (p[1] for p in docs_info["planes_detectados"] if p[0] == nombre_ganador),
            None
        )
        
        if nombre_ganador in self.archivos_conocidos:
            logger.info(f"✅ Already processed: {nombre_ganador}")
            return
        
        logger.info(f"🎯 New document: {nombre_ganador}")
        
        # Extract deadline from PDFs
        fecha_cierre = "No especificada"
        if docs_info["links_pdfs"]:
            url_pdf = self._seleccionar_pdf_prioritario(docs_info["links_pdfs"])
            if url_pdf:
                fecha_cierre = self.analysis_service.extraer_fecha_de_pdf(url_pdf)
        
        # Check if tender is active
        vigente, estado = self.analysis_service.validar_vigencia_licitacion(fecha_cierre)
        
        if not vigente:
            logger.info(f"⏭️ Tender expired: {fecha_cierre}")
            self._guardar_fila_fantasma(
                "Licitación Vencida",
                url_ganador.split('?')[0],
                nombre_portal,
                "Vencido",
                fecha_cierre
            )
            self.archivos_conocidos.add(nombre_ganador)
            return
        
        # Analyze Excel with AI
        hallazgos = self.analysis_service.analizar_excel_con_ia(url_ganador)
        
        if hallazgos:
            logger.info(f"🚨 Found {len(hallazgos)} opportunities")
            self._inyectar_datos(
                hallazgos,
                url_ganador,
                nombre_portal,
                titulo_web,
                fecha_cierre,
                estado
            )
            self.notification_service.enviar_notificacion_licitacion(
                titulo_web, len(hallazgos), nombre_portal
            )
            self.archivos_conocidos.add(nombre_ganador)
        else:
            logger.info(f"ℹ️ No key courses in {nombre_portal}")
    
    def _seleccionar_pdf_prioritario(self, links_pdfs):
        """Select most relevant PDF by priority."""
        # High priority
        for nombre, link in links_pdfs:
            nom_bajo = nombre.lower()
            if any(x in nom_bajo for x in ['cronograma', 'anexo 1', 'calendario']):
                return link
        
        # Medium priority
        for nombre, link in links_pdfs:
            nom_bajo = nombre.lower()
            if any(x in nom_bajo for x in ['base', 'anexo']):
                if not any(x in nom_bajo for x in ['modifica', 'resolucion']):
                    return link
        
        return links_pdfs[0][1] if links_pdfs else None
    
    def _inyectar_datos(self, hallazgos, url_ganador, nombre_portal, titulo_web,
                       fecha_cierre, estado):
        """Inject extracted data to BigQuery."""
        try:
            df = pd.DataFrame(hallazgos)
            df['link_documento'] = url_ganador.split('?')[0]
            df['fecha_deteccion'] = pd.Timestamp.now(TIMEZONE)
            df['origen_web'] = nombre_portal
            df['titulo_llamado_web'] = titulo_web
            df['fecha_cierre'] = fecha_cierre
            df['estado'] = estado
            
            cliente = BigQueryClient(
                "proyecto-life-box-licitaciones",
                "licitaciones",
                "oportunidades",
                "credenciales_gcp.json"
            )
            cliente.inyectar_datos(df)
            logger.info(f"✅ {len(hallazgos)} records injected")
        
        except Exception as e:
            logger.error(f"❌ Injection error: {e}")
    
    def _guardar_fila_fantasma(self, titulo, link, portal, estado, fecha):
        """Save placeholder row in BigQuery for memory."""
        try:
            df = pd.DataFrame([{
                "palabra_clave": "N/A",
                "curso": titulo,
                "region": "N/A",
                "comuna": "N/A",
                "cupos": "0",
                "horas": "0",
                "modalidad": "N/A",
                "fila": 0
            }])
            df['link_documento'] = link
            df['fecha_deteccion'] = pd.Timestamp.now(TIMEZONE)
            df['origen_web'] = portal
            df['titulo_llamado_web'] = titulo
            df['fecha_cierre'] = fecha
            df['estado'] = estado
            
            cliente = BigQueryClient(
                "proyecto-life-box-licitaciones",
                "licitaciones",
                "oportunidades",
                "credenciales_gcp.json"
            )
            cliente.inyectar_datos(df)
            logger.info(f"✅ Reference row saved")
        
        except Exception as e:
            logger.error(f"❌ Reference row error: {e}")
    
    def ejecutar(self):
        """Execute complete scraping workflow."""
        logger.info("=== STARTING MULTI-PORTAL SURVEILLANCE ===")
        self.cargar_historial()
        
        for nombre_portal, scraper in self.scrapers_config:
            print("\n" + "=" * 50)
            self.procesar_portal(nombre_portal, scraper)
        
        logger.info("=== SURVEILLANCE COMPLETE ===")
