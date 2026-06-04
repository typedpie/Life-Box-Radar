"""
Analysis service: AI classification and tender validation.
"""
import logging
import pandas as pd
from utils.analizador_inteligente import AnalizadorLicitaciones
from utils.document_parser import DocumentAnalyzer
from core.config import TIMEZONE

logger = logging.getLogger(__name__)


class AnalysisService:
    """AI-powered tender analysis and classification."""
    
    def __init__(self):
        """Initialize AI analyzers."""
        self.analizador = AnalizadorLicitaciones()
        self.parser = DocumentAnalyzer()
    
    def clasificar_archivo(self, nombre_archivo):
        """Classify document type by filename."""
        return self.analizador.clasificar_archivo(nombre_archivo)
    
    def seleccionar_plan_mas_reciente(self, nombres_planes):
        """Select most recent training plan from list."""
        return self.analizador.seleccionar_plan_mas_reciente(nombres_planes)
    
    def validar_vigencia_licitacion(self, fecha_cierre):
        """Check if tender deadline has passed."""
        if fecha_cierre == "No especificada":
            logger.warning("⚠️ No deadline specified")
            return True, "Activo"
        
        try:
            fecha_limite_dt = pd.to_datetime(fecha_cierre, format='%Y-%m-%d')
            fecha_hoy_dt = pd.Timestamp.now(TIMEZONE).normalize().tz_localize(None)
            
            if fecha_limite_dt < fecha_hoy_dt:
                logger.info(f"⚠️ Tender expired: {fecha_cierre}")
                return False, "Vencido"
            else:
                logger.info(f"✅ Tender active until: {fecha_cierre}")
                return True, "Activo"
        
        except Exception as e:
            logger.warning(f"⚠️ Cannot validate date: {fecha_cierre} - {e}")
            return True, "Activo"
    
    def extraer_fecha_de_pdf(self, url_pdf):
        """Extract deadline from PDF document."""
        try:
            ruta_pdf = self.parser.descargar_archivo(url_pdf)
            if not ruta_pdf:
                logger.warning("⚠️ Cannot download PDF")
                return "No especificada"
            
            fecha = self.parser.extraer_fecha_pdf(ruta_pdf)
            logger.info(f"✅ Date extracted: {fecha}")
            return fecha
        
        except Exception as e:
            logger.error(f"❌ PDF extraction error: {e}")
            return "No especificada"
    
    def analizar_excel_con_ia(self, url_excel):
        """Analyze Excel and extract key training courses using AI."""
        try:
            ruta = self.parser.descargar_archivo(url_excel)
            if not ruta:
                logger.warning("⚠️ Cannot download Excel")
                return []
            
            hallazgos = self.parser.analizar_excel(ruta, self.analizador.keywords_negocio)
            logger.info(f"✅ Found {len(hallazgos)} opportunities")
            return hallazgos
        
        except Exception as e:
            logger.error(f"❌ Excel analysis error: {e}")
            return []
    
    def procesar_documentos(self, enlaces, titulo_web):
        """Process list of document links and categorize them."""
        resultado = {
            "link_drive": None,
            "planes_detectados": [],
            "links_pdfs": [],
            "fecha_cierre": "No especificada",
            "vigente": True
        }
        
        for link in enlaces:
            nombre = link.split('/')[-1].split('?')[0].strip()
            
            if "drive.google.com" in link:
                resultado["link_drive"] = link
            elif link.lower().endswith('.pdf') or '.pdf?' in link.lower():
                resultado["links_pdfs"].append((nombre, link))
            else:
                if "EXCEL CLAVE" in self.clasificar_archivo(nombre):
                    resultado["planes_detectados"].append((nombre, link))
        
        return resultado
