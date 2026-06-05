import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException 

class BanoticScraperSelenium:
    def __init__(self):
        self.url_principal = "https://banotic.cl/becas-laborales/" 
        
        self.opciones = Options()
        self.opciones.page_load_strategy = 'eager'
        self.opciones.add_argument("--disable-gpu")
        self.opciones.add_argument("--headless=new")
        self.opciones.add_argument("--no-sandbox")
        self.opciones.add_argument("--disable-dev-shm-usage")
        self.opciones.add_argument("--window-size=1920,1080")

    def fetch_tender_links(self):
        
        # 2 años para la logica de doble intento
        anio_actual = str(datetime.now().year) 
        anio_anterior = str(datetime.now().year - 1)
        
        logging.info(f"Iniciando exploración en Banotic: {self.url_principal}")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.opciones)
        driver.set_page_load_timeout(30)
        enlaces = set()
        titulo_encontrado = f"Llamado Licitación Banotic {anio_actual}" 

        try:
            driver.get(self.url_principal)
            time.sleep(3)

            # --- FASE 1: BUSCAR EL BOTÓN DEL AÑO  ---
            url_subpagina = None
            anio_detectado = None
            anios_a_buscar = [anio_actual, anio_anterior]

            for anio_objetivo in anios_a_buscar:
                logging.info(f"Buscando el botón del año {anio_objetivo}...")
                try:
                    xpath_boton = f"//a[contains(@class, 'elementor-button-link') and (contains(., '{anio_objetivo}') or contains(@href, 'licitaciones/{anio_objetivo}'))]"
                    boton_anio = driver.find_element(By.XPATH, xpath_boton)
                    url_subpagina = boton_anio.get_attribute("href")
                    
                    anio_detectado = anio_objetivo
                    titulo_encontrado = f"Banotic - Licitaciones ({anio_detectado})"
                    logging.info(f"¡Botón {anio_objetivo} detectado! Viajando a la bóveda: {url_subpagina}")
                    break 
                except Exception:
                    logging.info(f"No se encontró el botón para {anio_objetivo}.")
                    continue 

            
            if not url_subpagina:
                raise Exception("Cambio de diseño: No se encontró el botón de acceso para los años recientes en Banotic.")

            # --- FASE 2: DETECCIÓN DE PESTAÑAS Y EXTRACCIÓN (SOLO LA MÁS RECIENTE) ---
            driver.get(url_subpagina)
            time.sleep(3)

            try:
                # 1. Busco todas las pestañas de llamados 
                xpath_pestanas = "//*[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'llamado') and string-length(normalize-space(text())) < 25]"
                pestanas_encontradas = driver.find_elements(By.XPATH, xpath_pestanas)
                
                # Filtro las que realmente se ven en pantalla
                pestanas_validas = [p for p in pestanas_encontradas if p.is_displayed()]

                if pestanas_validas:
                    # solo tomo la ultima pestaña
                    ultima_pestana = pestanas_validas[-1]
                    nombre_tab = ultima_pestana.text.strip()
                    
                    # actualizo el titulo para que dashboard sepa de que pestaña es
                    titulo_encontrado = f"Banotic - {nombre_tab} ({anio_detectado})"
                    
                    logging.info(f"Se detectaron {len(pestanas_validas)} pestañas. 👉 Apuntando ÚNICAMENTE al más reciente: {nombre_tab}")
                    
                    driver.execute_script("arguments[0].click();", ultima_pestana)
                    time.sleep(3) # Esperar que carguen los documentos de esa pestaña
                    
                    # Hacer scroll de seguridad solo para esta pestaña
                    last_height = driver.execute_script("return document.body.scrollHeight")
                    for intento in range(20): 
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2) 
                        new_height = driver.execute_script("return document.body.scrollHeight")
                        if new_height == last_height: break
                        last_height = new_height
                    
                    # Extraer enlaces SOLO de esta pestaña
                    xpath_documentos = "//div[contains(@class, 'jet-listing-dynamic-link')]//a"
                    botones_descarga = driver.find_elements(By.XPATH, xpath_documentos)
                    
                    for boton in botones_descarga:
                        href = boton.get_attribute("href")
                        if href and ("documentos-becas" in href or "wp-content/uploads" in href):
                            enlaces.add(href)
                            
                else:
                    # Fallback por si la web cambia su diseño y ya no usa pestañas
                    logging.info("No se detectaron pestañas. Usando escaneo estándar...")
                    last_height = driver.execute_script("return document.body.scrollHeight")
                    for intento in range(20): 
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2) 
                        new_height = driver.execute_script("return document.body.scrollHeight")
                        if new_height == last_height: break
                        last_height = new_height
                        
                    botones_descarga = driver.find_elements(By.XPATH, "//div[contains(@class, 'jet-listing-dynamic-link')]//a")
                    for boton in botones_descarga:
                        href = boton.get_attribute("href")
                        if href and ("documentos-becas" in href or "wp-content/uploads" in href):
                            enlaces.add(href)

                logging.info(f"Extracción exitosa: {len(enlaces)} documentos capturados de lo más reciente en Banotic.")

            except Exception as e_boveda:
                logging.error(f"Error procesando la bóveda de Banotic: {e_boveda}")
                # 🚀 NUEVO: Grito al Orquestador si la fase 2 falla
                raise Exception("Cambio de diseño en la bóveda: No se pudieron extraer los enlaces de los documentos.")

        # bloque de errores
        except TimeoutException:
            logging.error("Timeout en Banotic")
            raise Exception("La página web de Banotic está caída o demasiado lenta (Timeout).")
        except WebDriverException:
            logging.error("Error de WebDriver en Banotic")
            raise Exception("No se pudo acceder a la página de Banotic. Revisa la URL.")
        except Exception as e:
            logging.error(f"Error explorando la página principal de Banotic: {e}")
            if "Cambio de diseño" in str(e):
                raise e
            else:
                raise Exception("Error inesperado en Banotic. Revisa los logs de la consola.")
        finally:
            driver.quit()

        return enlaces, titulo_encontrado

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    scraper = BanoticScraperSelenium()
    links, titulo = scraper.fetch_tender_links()
    print(f"\n📌 {titulo}")
    for link in links: 
        print(f"- {link}")