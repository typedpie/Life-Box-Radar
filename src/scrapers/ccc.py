import logging
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException

class CccScraperSelenium:
    def __init__(self):
        self.url_principal = "https://www.ccc.cl/becas-laborales"
        
        self.opciones = Options()
        self.opciones.page_load_strategy = 'eager'
        self.opciones.add_argument("--disable-gpu")
        self.opciones.add_argument("--headless=new")
        self.opciones.add_argument("--no-sandbox")
        self.opciones.add_argument("--disable-dev-shm-usage")
        self.opciones.add_argument("--window-size=1920,1080")

    def fetch_tender_links(self):
        anio_actual = str(datetime.now().year)
        anio_anterior = str(datetime.now().year - 1)
        
        logging.info(f"Iniciando exploración en CCC: {self.url_principal}")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.opciones)
        driver.set_page_load_timeout(30)
        enlaces = set()
        titulo_encontrado = f"Llamado Licitación CCC {anio_actual}"

        try:
            driver.get(self.url_principal)
            
            # carga component react
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ant-collapse-item"))
            )
            time.sleep(2)

            anios_a_buscar = [anio_actual, anio_anterior]
            
            for anio_objetivo in anios_a_buscar:
                logging.info(f"Buscando acordeones del año {anio_objetivo}...")
                
                acordeones = driver.find_elements(By.CLASS_NAME, "ant-collapse-item")
                acordeon_campeon = None
                
                for acordeon in acordeones:
                    try:
                        titulo_elemento = acordeon.find_element(By.CLASS_NAME, "ant-collapse-title")
                        texto_titulo = titulo_elemento.text.strip()
                        
                        if anio_objetivo in texto_titulo:
                            
                            acordeon_campeon = acordeon
                            titulo_encontrado = f"CCC - {texto_titulo}"
                            logging.info(f"¡Acordeón objetivo detectado!: '{texto_titulo}'")
                            break
                    except Exception:
                        continue
                        
                if acordeon_campeon:
                    header = acordeon_campeon.find_element(By.CLASS_NAME, "ant-collapse-header")
                    
                    
                    clases_acordeon = acordeon_campeon.get_attribute("class")
                    if "ant-collapse-item-active" not in clases_acordeon:
                        driver.execute_script("arguments[0].click();", header)
                        time.sleep(2) # Esperar animación de React
                        
                    
                    caja_contenido = acordeon_campeon.find_element(By.CLASS_NAME, "ant-collapse-body")
                    etiquetas_a = caja_contenido.find_elements(By.TAG_NAME, "a")
                    
                    for a in etiquetas_a:
                        href = a.get_attribute("href")
                        texto_link = a.get_attribute("textContent").lower().strip()
                        
                        if href and "/api/assets/" in href.lower():
                            
                            palabras_clave_excel = ['plan', 'parrilla', 'excel', 'matriz', 'cursos', 'informe', 'tecnico', 'técnico']
                            
                            if any(k in texto_link for k in palabras_clave_excel):
                                href_modificado = href + "#Plan_de_Capacitacion.xlsx"
                            else:
                                nombre_limpio = "".join(c if c.isalnum() else "_" for c in texto_link)
                                href_modificado = href + f"#{nombre_limpio}.pdf"
                                
                            enlaces.add(href_modificado)
                            
                    logging.info(f"Extracción exitosa: {len(enlaces)} documentos encontrados para {anio_objetivo}.")
                    break 
                else:
                    logging.info(f"No se encontraron acordeones para el año {anio_objetivo} en CCC.")

            if not enlaces:
                raise Exception("Cambio de diseño: No se encontraron los acordeones o documentos válidos en CCC.")

        except TimeoutException:
            logging.error("Timeout en CCC")
            raise Exception("La página web de CCC está caída o demasiado lenta (Timeout).")
        except WebDriverException:
            logging.error("Error de WebDriver en CCC")
            raise Exception("No se pudo acceder a la página de CCC. Revisa la URL.")
        except Exception as e:
            logging.error(f"Error explorando la página de CCC: {e}")
            if "Cambio de diseño" in str(e):
                raise e
            else:
                raise Exception("Error inesperado en CCC. Revisa los logs de la consola.")
        finally:
            driver.quit()

        return enlaces, titulo_encontrado

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    scraper = CccScraperSelenium()
    links, titulo = scraper.fetch_tender_links()
    print(f"\n📌 {titulo}")
    for link in links: 
        print(f"- {link}")