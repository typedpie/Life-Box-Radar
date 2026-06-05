import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException 

class ProAconcaguaScraperSelenium:
    def __init__(self):
        self.url = "https://www.oticproaconcagua.cl/becas-laborales/"
        
        self.opciones = Options()
        self.opciones.page_load_strategy = 'eager'
        self.opciones.add_argument("--disable-gpu")
        self.opciones.add_argument("--headless=new")
        self.opciones.add_argument("--no-sandbox")
        self.opciones.add_argument("--disable-dev-shm-usage")
        self.opciones.add_argument("--window-size=1920,1080")

    def fetch_tender_links(self):
        # 🎯 
        anio_actual = str(datetime.now().year)
        anio_anterior = str(datetime.now().year - 1)
        
        logging.info(f"Iniciando exploración en Pro Aconcagua: {self.url}")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.opciones)
        driver.set_page_load_timeout(30)
        enlaces = set()
        titulo_encontrado = f"Llamado Licitación Pro Aconcagua {anio_actual}"

        try:
            driver.get(self.url)
            
            # Esperar a que cargue el bloque principal
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "elementor-text-editor"))
            )
            time.sleep(2)

            anios_a_buscar = [anio_actual, anio_anterior]

            for anio_objetivo in anios_a_buscar:
                logging.info(f"Buscando el título para el año {anio_objetivo}...")
                xpath_titulo = f"//h2[contains(., '{anio_objetivo}')]"
                titulos = driver.find_elements(By.XPATH, xpath_titulo)

                if titulos:
                    titulo_elemento = titulos[0]
                    texto_titulo = titulo_elemento.text.strip()
                    titulo_encontrado = f"Pro Aconcagua - {texto_titulo}"
                    logging.info(f"¡Título detectado!: '{texto_titulo}'")

                    # Busco el botón de descarga o link al Drive que esté justo después del título
                    xpath_boton = "./following::a[contains(@class, 'elementor-button-link')][1]"
                    try:
                        boton = titulo_elemento.find_element(By.XPATH, xpath_boton)
                        href = boton.get_attribute("href")
                        if href:
                            enlaces.add(href)
                            logging.info(f"Link a la carpeta capturado: {href}")
                            break # 🎯 Rompemos el ciclo porque encontramos el año 
                    except Exception:
                        logging.warning("Se encontró el título pero no el botón de descarga.")
                else:
                    logging.info(f"No se encontró el título para el año {anio_objetivo}.")

        
            if not enlaces:
                raise Exception("Cambio de diseño: No se encontró el título o el botón de descarga en Pro Aconcagua.")

        #bloque errores
        except TimeoutException:
            logging.error("Timeout en Pro Aconcagua")
            raise Exception("La página web de Pro Aconcagua está caída o demasiado lenta (Timeout).")
        except WebDriverException:
            logging.error("Error de WebDriver en Pro Aconcagua")
            raise Exception("No se pudo acceder a la página de Pro Aconcagua. Revisa la URL.")
        except Exception as e:
            logging.error(f"Error explorando la página de Pro Aconcagua: {e}")
            if "Cambio de diseño" in str(e):
                raise e
            else:
                raise Exception("Error inesperado en Pro Aconcagua. Revisa los logs de la consola.")
        finally:
            driver.quit()

        return enlaces, titulo_encontrado

# Prueba local
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    scraper = ProAconcaguaScraperSelenium()
    links, titulo = scraper.fetch_tender_links()
    print(f"\n📌 {titulo}")
    for link in links: 
        print(f"- {link}")