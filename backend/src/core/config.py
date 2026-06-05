"""
Centralized backend configuration.
All environment variables and constants in one place.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# GOOGLE CLOUD / BIGQUERY
# ============================================
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "proyecto-life-box-licitaciones")
GCP_CREDENTIALS_PATH = os.getenv("GCP_CREDENTIALS_PATH", "credenciales_gcp.json")
BQ_DATASET = "licitaciones"
BQ_TABLE_OPORTUNIDADES = "oportunidades"
BQ_TABLE_ESTADO_SCRAPERS = "estado_scrapers"

# ============================================
# TELEGRAM
# ============================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ============================================
# TIMEZONE
# ============================================
TIMEZONE = "America/Santiago"

# ============================================
# SCRAPERS
# ============================================
PORTALES = [
    "Proforma",
    "OTIC",
    "Pro Aconcagua",
    "Agrocap",
    "Banotic",
    "Alianza Pyme",
    "OTIC Sofofa"
]

# ============================================
# LOGGING
# ============================================
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'

# ============================================
# VALIDATION
# ============================================
def validar_config():
    """Validates all required configurations are present and valid."""
    if not os.path.exists(GCP_CREDENTIALS_PATH):
        raise FileNotFoundError(f"❌ {GCP_CREDENTIALS_PATH} not found")
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("❌ Missing Telegram credentials in .env")
    
    return True
