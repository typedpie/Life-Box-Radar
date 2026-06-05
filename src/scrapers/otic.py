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

class OticScraperSelenium:
    def __init__(self):
        self.url = "https://otic.cl/becas-laborales/"
        
        # Configuracion de chrome
        self.opciones = Options()
        self.opciones.page_load_strategy = 'eager'
        self.opciones.add_argument("--disable-gpu")
        self.opciones.add_argument("--headless=new")
        self.opciones.add_argument("--no-sandbox")
        self.opciones.add_argument("--disable-dev-shm-usage")
        self.opciones.add_argument("--window-size=1920,1080")
        self.opciones.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    def fetch_tender_links(self):
        
        # 🎯 logica de 2 intentos
        anio_actual = str(datetime.now().year)
        anio_anterior = str(datetime.now().year - 1)
        
        logging.info(f"Iniciando exploración en OTIC: {self.url}")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.opciones)
        driver.set_page_load_timeout(30)
        enlaces = set()
        titulo_encontrado = f"Llamado Licitación OTIC {anio_actual}" 

        try:
            driver.get(self.url)
            
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "et_pb_toggle"))
            )
            time.sleep(2) 

            # Saco los acordeones de la pagina
            acordeones = driver.find_elements(By.CLASS_NAME, "et_pb_toggle")
            
            anios_a_buscar = [anio_actual, anio_anterior]
            
            for anio_objetivo in anios_a_buscar:
                logging.info(f"Buscando acordeones del año {anio_objetivo}...")
                
                acordeones_validos = []
                
                # --- PRE-ESCANEO: Clasificar todos los acordeones de este año ---
                for acordeon in acordeones:
                    try:
                        titulo_elemento = acordeon.find_element(By.CLASS_NAME, "et_pb_toggle_title")
                        titulo_texto = titulo_elemento.text.strip()
                        
                        if anio_objetivo in titulo_texto:
                            # 🧠 Extraer el número del llamado
                            match = re.search(r'(\d+)[°a-zA-Z]*\s*(?:licitaci[oó]n|llamado)', titulo_texto.lower())
                            num_llamado = int(match.group(1)) if match else 0
                            
                            acordeones_validos.append({
                                "elemento": acordeon,
                                "titulo_elemento": titulo_elemento,
                                "titulo_texto": titulo_texto,
                                "num_llamado": num_llamado
                            })
                    except Exception:
                        continue
                
                # --- SELECCIÓN ---
                if acordeones_validos:
                    # Encontrar el número de llamado más reciente
                    max_llamado = max(item["num_llamado"] for item in acordeones_validos)
                    
                    # Filtrar SOLO los acordeones que pertenecen a este llamado reciente
                    acordeones_campeones = [item for item in acordeones_validos if item["num_llamado"] == max_llamado]
                    
                    # Actualizar el título con el nombre del acordeón principal
                    titulo_encontrado = f"OTIC - {acordeones_campeones[0]['titulo_texto']}"
                    
                    for item in acordeones_campeones:
                        logging.info(f"¡Acordeón objetivo detectado!: '{item['titulo_texto']}'")
                        acordeon = item["elemento"]
                        titulo_elemento = item["titulo_elemento"]
                        
                        # Abrir acordeon
                        clases_acordeon = acordeon.get_attribute("class")
                        if "et_pb_toggle_close" in clases_acordeon:
                            logging.info("Desplegando acordeón...")
                            driver.execute_script("arguments[0].click();", titulo_elemento)
                            time.sleep(1.5) 
                        
                        # Extracción: saco links de ese acordeón
                        caja_contenido = acordeon.find_element(By.CLASS_NAME, "et_pb_toggle_content")
                        etiquetas_a = caja_contenido.find_elements(By.TAG_NAME, "a")
                        
                        for a in etiquetas_a:
                            href = a.get_attribute("href")
                            if href and any(ext in href.lower() for ext in ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.zip']):
                                enlaces.add(href)
                                
                    logging.info(f"Extracción exitosa: {len(enlaces)} documentos encontrados para el año {anio_objetivo} (Llamado #{max_llamado}).")
                    break # rompo el ciclo 
                else:
                    logging.info(f"Aún no hay licitaciones publicadas para el año {anio_objetivo} en OTIC.")

            
            if not enlaces:
                raise Exception("Cambio de diseño: No se encontraron los acordeones de los años recientes en OTIC.")

        # bloque de errores
        except TimeoutException:
            logging.error("Timeout en OTIC")
            raise Exception("La página web de OTIC está caída o demasiado lenta (Timeout).")
        except WebDriverException:
            logging.error("Error de WebDriver en OTIC")
            raise Exception("No se pudo acceder a la página de OTIC. Revisa la URL.")
        except Exception as e:
            logging.error(f"Error explorando la página de OTIC: {e}")
            if "Cambio de diseño" in str(e):
                raise e
            else:
                raise Exception("Error inesperado en OTIC. Revisa los logs de la consola.")
        finally:
            driver.quit()

        return enlaces, titulo_encontrado

# Bloque de prueba local
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    scraper = OticScraperSelenium()
    links, titulo = scraper.fetch_tender_links()
    
    print(f"\n--- TÍTULO DEL LLAMADO ---")
    print(f"📌 {titulo}")
    
    print(f"\n--- Documentos Vigentes ---")
    if links:
        for link in links:
            print(f"- {link}")
    else:
        print("No se encontraron enlaces.")