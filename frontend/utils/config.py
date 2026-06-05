"""
Frontend configuration: Settings and constants.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Google Cloud
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "proyecto-life-box-licitaciones")
GCP_CREDENTIALS_PATH = os.getenv("GCP_CREDENTIALS_PATH", "credenciales_gcp.json")

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

# Defaults
DEFAULT_LIMIT_ROWS = 100
DEFAULT_CACHE_TTL = 300
