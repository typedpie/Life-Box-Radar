import sys
from pathlib import Path

def find_src_dir(start: Path) -> Path:
    """Busca upward un directorio 'src' desde start hasta la raíz."""
    cur = start.resolve()
    for parent in [cur] + list(cur.parents):
        candidate = parent / "src"
        if candidate.is_dir():
            return candidate
    return None

src_dir = find_src_dir(Path(__file__).parent)
if not src_dir:
    raise RuntimeError("No se encontró el directorio 'src' en la jerarquía de carpetas.")
sys.path.insert(0, str(src_dir))

from core.config import validar_config
from services.scraper_service import ScraperService

# Import scrapers
from scrapers.proforma import ProformaScraperSelenium
from scrapers.otic import OticScraperSelenium
from scrapers.proaconcagua import ProAconcaguaScraperSelenium
from scrapers.agrocap import AgrocapScraperSelenium
from scrapers.banotic import BanoticScraperSelenium
from scrapers.alianzapyme import AlianzaPymeScraperSelenium
from scrapers.oticsosofa import OticSofofaScraperSelenium


def get_scrapers():
    """Initialize all portal scrapers."""
    return [
        ("Proforma", ProformaScraperSelenium()),
        ("OTIC", OticScraperSelenium()),
        ("Pro Aconcagua", ProAconcaguaScraperSelenium()),
        ("Agrocap", AgrocapScraperSelenium()),
        ("Banotic", BanoticScraperSelenium()),
        ("Alianza Pyme", AlianzaPymeScraperSelenium()),
        ("OTIC Sofofa", OticSofofaScraperSelenium())
    ]


def main():
    """Execute complete scraping workflow."""
    
    # Validate configuration
    try:
        validar_config()
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Initialize scraper service with scrapers
    scrapers = get_scrapers()
    scraper_service = ScraperService(scrapers)
    
    # Execute scraping
    try:
        print("🚀 Starting scraping process...")
        scraper_service.ejecutar()
        print("✅ Scraping completed successfully")
        return True
    
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
