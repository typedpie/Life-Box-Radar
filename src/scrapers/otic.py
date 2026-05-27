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

class OticScraperSelenium:
    def __init__(self):
        self.url = "https://otic.cl/becas-laborales/"
        
        # Configuracion de chrome
        self.opciones = Options()
        self.opciones.add_argument("--headless=new")
        self.opciones.add_argument("--no-sandbox")
        self.opciones.add_argument("--disable-dev-shm-usage")
        self.opciones.add_argument("--window-size=1920,1080")
        self.opciones.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    def fetch_tender_links(self):
        
        anio_actual = str(datetime.now().year)
        
        logging.info(f"Iniciando exploración en OTIC: {self.url}")
        logging.info(f"Filtro temporal activado: Buscando exclusivamente licitaciones del año {anio_actual}")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.opciones)
        enlaces = set()
        titulo_encontrado = f"Llamado Licitación OTIC {anio_actual}" 
        primer_titulo_capturado = False 

        try:
            driver.get(self.url)
            
            
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "et_pb_toggle"))
            )
            time.sleep(2) 

            # saco los acordeones de la pagina
            acordeones = driver.find_elements(By.CLASS_NAME, "et_pb_toggle")
            
            for acordeon in acordeones:
                try:
                    titulo_elemento = acordeon.find_element(By.CLASS_NAME, "et_pb_toggle_title")
                    titulo_texto = titulo_elemento.text.strip()
                    
                    # 2. Filtro de año en acordeon 
                    if anio_actual in titulo_texto:
                        logging.info(f"¡Acordeón detectado!: '{titulo_texto}'")
                        
                        
                        if not primer_titulo_capturado:
                            titulo_encontrado = titulo_texto
                            primer_titulo_capturado = True
                        
                        #Abrir acordeon
                        clases_acordeon = acordeon.get_attribute("class")
                        if "et_pb_toggle_close" in clases_acordeon:
                            logging.info("Desplegando acordeón...")
                            driver.execute_script("arguments[0].click();", titulo_elemento)
                            time.sleep(1.5) 
                        
                        # 3. Extraccion, saco links 
                        caja_contenido = acordeon.find_element(By.CLASS_NAME, "et_pb_toggle_content")
                        etiquetas_a = caja_contenido.find_elements(By.TAG_NAME, "a")
                        
                        for a in etiquetas_a:
                            href = a.get_attribute("href")
                            
                            if href and any(ext in href.lower() for ext in ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.zip']):
                                enlaces.add(href)
                
                except Exception as inner_e:
                    logging.warning(f"Ignorando un acordeón por error de lectura: {inner_e}")
                    continue
                    
            if not enlaces:
                logging.info(f"Aún no hay licitaciones publicadas para el año {anio_actual} en OTIC.")
            else:
                logging.info(f"Extracción exitosa: {len(enlaces)} documentos encontrados para el año {anio_actual}.")

        except Exception as e:
            logging.error(f"Error explorando la página de OTIC: {e}")
        finally:
            driver.quit()

        return enlaces, titulo_encontrado

# Bloque de prueba local
if __name__ == "__main__":
    scraper = OticScraperSelenium()
    links, titulo = scraper.fetch_tender_links()
    
    print(f"\n--- TÍTULO DEL LLAMADO ---")
    print(f"📌 {titulo}")
    
    print(f"\n--- Documentos Vigentes ({datetime.now().year}) ---")
    if links:
        for link in links:
            print(f"- {link}")
    else:
        print("No se encontraron enlaces para el año en curso.")