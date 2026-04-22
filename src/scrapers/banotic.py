import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

class BanoticScraperSelenium:
    def __init__(self):
        self.url_principal = "https://banotic.cl/becas-laborales/" 
        
        self.opciones = Options()
        #self.opciones.add_argument("--headless=new")
        self.opciones.add_argument("--no-sandbox")
        self.opciones.add_argument("--disable-dev-shm-usage")
        self.opciones.add_argument("--window-size=1920,1080")

    def fetch_tender_links(self):
        # 🔴 PARA PROBAR: Forzado a 2025 temporalmente
        anio_actual = str(datetime.now().year) 
        logging.info(f"Iniciando exploración en Banotic: {self.url_principal}")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.opciones)
        enlaces = set()
        titulo_encontrado = f"Llamado Licitación Banotic {anio_actual}"

        try:
            driver.get(self.url_principal)
            time.sleep(3)

            # --- FASE 1: BUSCAR EL BOTÓN DEL AÑO ---
            logging.info(f"Buscando el botón del año {anio_actual}...")
            url_subpagina = None

            try:
                xpath_boton = f"//a[contains(@class, 'elementor-button-link') and (contains(., '{anio_actual}') or contains(@href, 'licitaciones/{anio_actual}'))]"
                boton_anio = driver.find_element(By.XPATH, xpath_boton)
                url_subpagina = boton_anio.get_attribute("href")
                
                logging.info(f"¡Botón {anio_actual} detectado! Viajando a la bóveda: {url_subpagina}")
            except Exception:
                logging.info(f"Aún no existe el portal para el año {anio_actual} en Banotic.")
                return enlaces, titulo_encontrado 

            # --- FASE 2: ENTRAR A LA BÓVEDA Y ESTIRAR LA PÁGINA ---
            driver.get(url_subpagina)
            time.sleep(3)

            try:
                # --- EL MOTOR DE SCROLL INFINITO ---
                logging.info("Activando motor de scroll para revelar documentos ocultos...")
                last_height = driver.execute_script("return document.body.scrollHeight")
                
                # Le damos un límite máximo de 20 bajadas por seguridad para que nunca se quede en un bucle infinito
                for intento in range(20): 
                    # Ordenamos a Chrome bajar hasta el fondo
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    
                    # Le damos 2 segundos a JetEngine para que inyecte los nuevos botones en el HTML
                    time.sleep(2) 
                    
                    # Calculamos la nueva altura de la página
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    
                    # Si la altura es la misma que antes de bajar, significa que ya no hay más documentos
                    if new_height == last_height:
                        logging.info("Se llegó al fondo real de la página. Todos los documentos están a la vista.")
                        break
                        
                    last_height = new_height
                    logging.info(f"Estirando la página... (Scroll {intento + 1})")
                # -----------------------------------

                # Ahora que la página está 100% desenrollada, aspiramos TODOS los enlaces
                xpath_documentos = "//div[contains(@class, 'jet-listing-dynamic-link')]//a"
                botones_descarga = driver.find_elements(By.XPATH, xpath_documentos)

                for boton in botones_descarga:
                    href = boton.get_attribute("href")
                    if href and ("documentos-becas" in href or "wp-content/uploads" in href):
                        enlaces.add(href)
                        
                logging.info(f"Extracción exitosa: {len(enlaces)} documentos totales capturados en Banotic.")

            except Exception as e_boveda:
                logging.error(f"Error procesando la bóveda de Banotic: {e_boveda}")

        except Exception as e:
            logging.error(f"Error explorando la página principal de Banotic: {e}")
        finally:
            driver.quit()

        return enlaces, titulo_encontrado

# Bloque de prueba local
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    scraper = BanoticScraperSelenium()
    
    links, titulo = scraper.fetch_tender_links()
    
    print(f"\n📌 {titulo}")
    for link in links: 
        print(f"- {link}")