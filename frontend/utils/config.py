"""
Frontend configuration: Settings and constants.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Google Cloud
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "proyecto-life-box-licitaciones")
GCP_CREDENTIALS_PATH = os.getenv("GCP_CREDENTIALS_PATH", "credenciales_gcp.json")

# Local DB
USE_LOCAL_DB = os.getenv("USE_LOCAL_DB", "True").lower() == "true"
LOCAL_DB_PATH = os.getenv("LOCAL_DB_PATH", "data/licitaciones.db")

# Streamlit
STREAMLIT_TITLE = "Radar de Licitaciones - LifeBox UDD"
STREAMLIT_ICON = "⚡"
STREAMLIT_LAYOUT = "wide"
STREAMLIT_SIDEBAR = "expanded"

# Data refresh
DATA_REFRESH_INTERVAL = 300000  # 5 minutes in milliseconds

# Portals
PORTALES_DISPONIBLES = [
    "Proforma",
    "OTIC",
    "Pro Aconcagua",
    "Agrocap",
    "Banotic",
    "Alianza Pyme",
    "OTIC Sofofa"
]

# Sources list for the UI and scraper plan
FUENTES_LICITACIONES = [
    {"name": "CCC Capacitación", "url": "https://www.ccc.cl/capacitacion/"},
    {"name": "SENCE Becas Laborales", "url": "https://sence.gob.cl/organismos/programa-becas-laborales"},
    {"name": "OTIC Asimet", "url": "https://www.oticasimet.cl/becas-laborales-v2/"},
    {"name": "Indupan OTIC", "url": "https://www.indupan.cl/otic"},
    {"name": "Banotic", "url": "https://banotic.cl/becas-laborales/#1620407860219-ff0c9051-357c"},
    {"name": "OTIC", "url": "https://otic.cl/becas-laborales/#licitacion2025"},
    {"name": "OTIC Sofofa", "url": "https://www.oticsofofa.cl/becas-laborales/"},
    {"name": "Pro Aconcagua", "url": "https://www.oticproaconcagua.cl/"},
    {"name": "Agrocap", "url": "https://www.agrocap.cl/webid/?page_id=2922"},
    {"name": "OTIC Alianza Pyme", "url": "https://www.oticalianzapyme.cl/becas/"},
    {"name": "CGCI", "url": "https://www.cgci.cl/"},
    {"name": "ProMaule", "url": "https://www.promaule.cl/"},
    {"name": "Wines of Chile", "url": "https://www.winesofchile.org/capital-humano/otic-chile-vinos/"},
    {"name": "OTIC del Comercio", "url": "https://oticdelcomercio.cl/becas-laborales/"},
    {"name": "Corficap", "url": "https://www.corficap.cl/primer-llamado-licitacion-publica-programa-becas-laborales-2024-otic-corficap-sence/"},
    {"name": "OTIC Franco Chileno", "url": "https://www.oticfrancochileno.cl/2024becas-laborales/"},
    {"name": "Proforma", "url": "https://www.proforma.cl/"},
    {"name": "OTIC Camacoes", "url": "https://otic-camacoes.cl/noticias/segundo_llamado_becas_laborales_2024"}
]

# Defaults
DEFAULT_LIMIT_ROWS = 100
DEFAULT_CACHE_TTL = 300
