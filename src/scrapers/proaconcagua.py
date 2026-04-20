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


class ProAconcaguaScraperSelenium:
    def __init__(self):
        self.url = "https://www.oticproaconcagua.cl/becas-laborales/"
        
        self.opciones = Options()
        self.opciones.add_argument("--headless=new")
        self.opciones.add_argument("--no-sandbox")
        self.opciones.add_argument("--disable-dev-shm-usage")
        self.opciones.add_argument("--window-size=1920,1080")

    def fetch_tender_links(self):
        anio_actual = str(datetime.now().year)
        logging.info(f"Iniciando exploración en Pro Aconcagua: {self.url}")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.opciones)
        enlaces = set()
        titulo_encontrado = f"Llamado Licitación Pro Aconcagua {anio_actual}"

        try:
            driver.get(self.url)
            
            # Esperamos a que carguen los bloques de Elementor
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "elementor-text-editor"))
            )
            time.sleep(2)

            # Buscamos cualquier <h2> que contenga el año actual
            xpath_titulo = f"//h2[contains(., '{anio_actual}')]"
            titulos = driver.find_elements(By.XPATH, xpath_titulo)

            if titulos:
                titulo_elemento = titulos[0]
                titulo_encontrado = titulo_elemento.text.strip()
                logging.info(f"¡Título detectado!: '{titulo_encontrado}'")

                # Truco de XPath: Buscamos el PRIMER botón de descarga que esté justo después de este título
                xpath_boton = "./following::a[contains(@class, 'elementor-button-link')][1]"
                try:
                    boton = titulo_elemento.find_element(By.XPATH, xpath_boton)
                    href = boton.get_attribute("href")
                    if href:
                        enlaces.add(href)
                        logging.info(f"Link a la carpeta capturado: {href}")
                except Exception:
                    logging.warning("Se encontró el título pero no el botón de descarga.")
            else:
                logging.info(f"Aún no hay licitaciones publicadas para el año {anio_actual} en Pro Aconcagua.")

        except Exception as e:
            logging.error(f"Error explorando la página: {e}")
        finally:
            driver.quit()

        return enlaces, titulo_encontrado

# Prueba local
if __name__ == "__main__":
    scraper = ProAconcaguaScraperSelenium()
    links, titulo = scraper.fetch_tender_links()
    print(f"\n📌 {titulo}")
    for link in links: print(f"- {link}")