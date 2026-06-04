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
        options.page_load_strategy = 'eager'
        options.add_argument("--no-sandbox")#permiso para correr en linux
        options.add_argument("--disable-dev-shm-usage")#evitar quedarse sin ram 
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        options.add_argument("--headless=new") #invisible
        

        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(30)
        return driver

    def fetch_tender_links(self):
        logging.info(f"Iniciando navegación en: {self.url}")
        
        # 🎯 ambos años
        anio_actual = str(datetime.now().year)
        anio_anterior = str(datetime.now().year - 1)
        
        titulo_acordeon_encontrado = f"Llamado Licitación Proforma {anio_actual}" 
        enlaces_encontrados = set()
        
        try:
            self.driver.get(self.url)
            time.sleep(5) 

            logging.info("Buscando acordeones en la página...")
            selector_acordeones = "details.e-n-accordion-item"
            acordeones = self.driver.find_elements(By.CSS_SELECTOR, selector_acordeones)
            
            anios_a_buscar = [anio_actual, anio_anterior]
            
            for anio_objetivo in anios_a_buscar:
                logging.info(f"Buscando acordeones correspondientes al año {anio_objetivo}...")
                hubo_exito = False
                
                # PASO 1: ABRIR SOLO LOS ACORDEONES DEL AÑO OBJETIVO
                for acordeon in acordeones:
                    texto_acordeon = acordeon.text
                    if anio_objetivo in texto_acordeon:
                        logging.info(f"Acordeón del año {anio_objetivo} detectado. Desplegando...")
                        if not acordeon.get_attribute("open"):
                            self.driver.execute_script("arguments[0].setAttribute('open', '')", acordeon)
                            time.sleep(0.5)
                        hubo_exito = True

                # PASO 2: SI ENCuentro ALGO, EXTRAEMOS EL HTML Y SACAMOS LOS LINKS
                if hubo_exito:
                    logging.info("Extrayendo HTML final...")
                    html_final = self.driver.page_source
                    soup = BeautifulSoup(html_final, 'html.parser')
                    
                    acordeones_html = soup.find_all('details', class_='e-n-accordion-item')
                    
                    if acordeones_html:
                        for acordeon in acordeones_html:
                            texto_resumen = acordeon.get_text()
                            
                            if anio_objetivo in texto_resumen:
                                etiqueta_titulo = acordeon.find('summary')
                                if etiqueta_titulo:
                                    # Le sumamos "Proforma" al título para mayor claridad en el dashboard
                                    titulo_acordeon_encontrado = f"Proforma - {etiqueta_titulo.get_text(strip=True)}"
                                    logging.info(f"Título exacto capturado: {titulo_acordeon_encontrado}")

                                for enlace in acordeon.find_all('a', href=True):
                                    href = enlace['href']
                                    if any(ext in href.lower() for ext in ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.zip']):
                                        enlaces_encontrados.add(href)
                    else:
                        logging.warning("No se encontraron elementos <details> en el HTML extraído.")
                        
                    logging.info(f"Extracción completada. Se encontraron {len(enlaces_encontrados)} documentos vigentes para {anio_objetivo}.")
                    break # 🎯 se rompe el ciclo por data encontrada
                else:
                    logging.info(f"No se encontraron acordeones para el año {anio_objetivo}.")

            return enlaces_encontrados, titulo_acordeon_encontrado

        except Exception as e:
            logging.error(f"Error durante la automatización: {e}")
            return set(), titulo_acordeon_encontrado

        finally:
            logging.info("Cerrando el navegador automatizado.")
            self.driver.quit()

# Bloque de prueba local
if __name__ == "__main__":
    scraper = ProformaScraperSelenium()
    
    links, titulo = scraper.fetch_tender_links()
    
    print(f"\n--- TÍTULO DEL LLAMADO ---")
    print(f"📌 {titulo}")
    
    print(f"\n--- Documentos Vigentes ---")
    if links:
        for link in links:
            print(f"- {link}")
    else:
        print("No se encontraron enlaces.")