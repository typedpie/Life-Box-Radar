import logging
import time
from urllib.parse import unquote
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException 

class AlianzaPymeScraperSelenium:
    def __init__(self):
        self.url_principal = "https://www.oticalianzapyme.cl/becas/" 
        
        self.opciones = Options()
        self.opciones.page_load_strategy = 'eager'
        self.opciones.add_argument("--disable-gpu")
        self.opciones.add_argument("--headless=new")
        self.opciones.add_argument("--no-sandbox")
        self.opciones.add_argument("--disable-dev-shm-usage")
        self.opciones.add_argument("--window-size=1920,1080")

    def fetch_tender_links(self):
        
        #2 años para logica de doble intento
        anio_actual = str(datetime.now().year) 
        anio_anterior = str(datetime.now().year - 1)
        
        logging.info(f"Iniciando exploración en Alianza Pyme: {self.url_principal}")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.opciones)
        driver.set_page_load_timeout(30)
        enlaces_unicos = {}
        titulo_encontrado = f"Llamado Licitación Alianza Pyme {anio_actual}" # Fallback de título

        try:
            driver.get(self.url_principal)
            time.sleep(3)

            anios_a_buscar = [anio_actual, anio_anterior]
            anio_detectado = None

            #ADAPTADO: Ahora recibe el año que quiero buscar y el año de "límite inferior"
            script_js = """
                const anioTarget = arguments[0];
                const anioCierre = arguments[1];
                
                const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, .elementor-heading-title, .elementor-widget-heading'));
                
                let startNode = null;
                let endNode = null;

                // Buscar donde empieza el año objetivo
                for (let h of headings) {
                    if (h.innerText.includes(anioTarget)) {
                        startNode = h;
                        break;
                    }
                }
                
                if (!startNode) return null; // Si no existe el título del año, abortamos en JS
                
                // Buscar donde termina (el año anterior a ese)
                for (let h of headings) {
                    if (h.innerText.includes(anioCierre) && (startNode.compareDocumentPosition(h) & 4)) {
                        endNode = h;
                        break;
                    }
                }

                const links = document.querySelectorAll('.elementor-tab-content a');
                const resultados = [];
                
                for (let link of links) {
                    const isAfterStart = (startNode.compareDocumentPosition(link) & 4);
                    const isBeforeEnd = endNode ? (endNode.compareDocumentPosition(link) & 2) : true;
                    
                    if (isAfterStart && isBeforeEnd) {
                        if (link.href) {
                            resultados.push(link.href);
                        }
                    }
                }
                return resultados;
            """

            # Intento primero con 2026, si falla, con 2025
            for anio_objetivo in anios_a_buscar:
                anio_cierre = str(int(anio_objetivo) - 1)
                logging.info(f"Ejecutando Cirugía de Código para aislar la sección del año {anio_objetivo}...")
                
                links_aislados = driver.execute_script(script_js, anio_objetivo, anio_cierre)

                if not links_aislados:
                    logging.info(f"Aún no existen documentos publicados para el año {anio_objetivo} bajo ese título.")
                else:
                    anio_detectado = anio_objetivo
                    titulo_encontrado = f"Alianza Pyme - Licitación ({anio_detectado})"
                    
                    for href in links_aislados:
                        href_limpio = href.strip()
                        if any(ext in href_limpio.lower() for ext in ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.zip']):
                            url_base = unquote(href_limpio.split('?')[0])
                            if url_base not in enlaces_unicos:
                                enlaces_unicos[url_base] = href_limpio
                    
                    logging.info(f"🎯 ¡Blanco fijado en {anio_detectado}! Se capturaron {len(enlaces_unicos)} documentos.")
                    break # se rompe el ciclo si se encuentra una paquete de licitaciones

            enlaces = set(enlaces_unicos.values())
            
    
            if not enlaces:
                raise Exception("Cambio de diseño: No se encontraron bloques de años o la estructura de la página cambió.")
            
            logging.info(f"Extracción milimétrica exitosa: {len(enlaces)} documentos únicos en total.")

        #bloque de errores
        except TimeoutException:
            logging.error("Timeout en Alianza Pyme")
            raise Exception("La página web de Alianza Pyme está caída o demasiado lenta (Timeout).")
        except WebDriverException:
            logging.error("Error de WebDriver en Alianza Pyme")
            raise Exception("No se pudo acceder a la página de Alianza Pyme. Revisa la URL.")
        except Exception as e:
            logging.error(f"Error explorando la página de Alianza Pyme: {e}")
            if "Cambio de diseño" in str(e):
                raise e
            else:
                raise Exception("Error inesperado en Alianza Pyme. Revisa los logs de la consola.")
        finally:
            driver.quit()

        return enlaces, titulo_encontrado

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    scraper = AlianzaPymeScraperSelenium()
    links, titulo = scraper.fetch_tender_links()
    print(f"\n📌 {titulo}")
    for link in links: 
        print(f"- {link}")