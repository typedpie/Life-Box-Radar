import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Configuración básica de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProformaScraperSelenium:
    def __init__(self):
        self.url = "https://proforma.cl/becas-laborales-2/"
        self.driver = self._init_driver()

    def _init_driver(self):
        logging.info("Inicializando el navegador automatizado (Selenium)...")
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless") # Descomentar para modo invisible
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    def fetch_tender_links(self):
        logging.info(f"Iniciando navegación en: {self.url}")
        
        anio_actual = str(datetime.now().year)
        logging.info(f"Filtro temporal activado: Buscando exclusivamente licitaciones del año {anio_actual}")
        
        # Variable por defecto en caso de que la página cambie su estructura de repente
        titulo_acordeon_encontrado = f"Llamado Licitación {anio_actual}" 
        
        try:
            self.driver.get(self.url)
            time.sleep(5) 

            logging.info("Buscando acordeones en la página...")
            selector_acordeones = "details.e-n-accordion-item"
            acordeones = self.driver.find_elements(By.CSS_SELECTOR, selector_acordeones)
            
            # PASO 1: ABRIR SOLO LOS ACORDEONES DEL AÑO ACTUAL
            for acordeon in acordeones:
                texto_acordeon = acordeon.text
                if anio_actual in texto_acordeon:
                    logging.info(f"Acordeón del año {anio_actual} detectado. Desplegando...")
                    if not acordeon.get_attribute("open"):
                        self.driver.execute_script("arguments[0].setAttribute('open', '')", acordeon)
                        time.sleep(0.5)

            logging.info("Extrayendo HTML final...")
            html_final = self.driver.page_source
            soup = BeautifulSoup(html_final, 'html.parser')
            
            enlaces_encontrados = set()
            acordeones_html = soup.find_all('details', class_='e-n-accordion-item')
            
            # PASO 2: EXTRAER ENLACES Y EL TÍTULO EXACTO DEL ACORDEÓN
            if acordeones_html:
                for acordeon in acordeones_html:
                    texto_resumen = acordeon.get_text()
                    
                    if anio_actual in texto_resumen:
                        
                        # --- MAGIA AÑADIDA AQUÍ ---
                        # Buscamos la etiqueta <summary> que es la que tiene el título visible
                        etiqueta_titulo = acordeon.find('summary')
                        if etiqueta_titulo:
                            # get_text(strip=True) limpia los espacios en blanco y saltos de línea basura
                            titulo_acordeon_encontrado = etiqueta_titulo.get_text(strip=True)
                            logging.info(f"Título exacto capturado: {titulo_acordeon_encontrado}")
                        # --------------------------

                        for enlace in acordeon.find_all('a', href=True):
                            href = enlace['href']
                            if any(ext in href.lower() for ext in ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.zip']):
                                enlaces_encontrados.add(href)
            else:
                logging.warning("No se encontraron elementos <details> en el HTML extraído.")
                
            logging.info(f"Extracción completada. Se encontraron {len(enlaces_encontrados)} documentos vigentes.")
            
            # MODIFICACIÓN CRÍTICA: Ahora devolvemos la lista de links Y el título capturado
            return enlaces_encontrados, titulo_acordeon_encontrado

        except Exception as e:
            logging.error(f"Error durante la automatización: {e}")
            return set(), titulo_acordeon_encontrado

        finally:
            logging.info("Cerrando el navegador automatizado.")
            self.driver.quit()

# Bloque de prueba local actualizado para soportar el nuevo formato
if __name__ == "__main__":
    scraper = ProformaScraperSelenium()
    # Ahora desempaquetamos las dos variables que devuelve la función
    links, titulo = scraper.fetch_tender_links()
    
    print(f"\n--- TÍTULO DEL LLAMADO ---")
    print(f"📌 {titulo}")
    
    print(f"\n--- Documentos Vigentes ({datetime.now().year}) ---")
    if links:
        for link in links:
            print(f"- {link}")
    else:
        print("No se encontraron enlaces para el año en curso.")