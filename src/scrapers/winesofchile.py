import logging
import time
from urllib.parse import unquote
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException

class ChileVinosScraperSelenium:
    def __init__(self):
        self.url_principal = "https://www.winesofchile.org/capital-humano/otic-chile-vinos/"
        
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
        
        logging.info(f"Iniciando exploración en Chile Vinos: {self.url_principal}")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.opciones)
        driver.set_page_load_timeout(30)
        enlaces_unicos = {}
        titulo_encontrado = f"Llamado Licitación Chile Vinos {anio_actual}"

        try:
            driver.get(self.url_principal)
            time.sleep(3)

            # FASE 1: Buscar el Acordeón "LICITACIONES DE BECAS"
            logging.info("Buscando el acordeón de Licitaciones...")
            xpath_acordeon = "//div[contains(@class, 'elementor-accordion-item')][.//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'licitaciones de becas')]]"
            
            try:
                acordeon_item = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, xpath_acordeon))
                )
                titulo_btn = acordeon_item.find_element(By.CLASS_NAME, "elementor-tab-title")
                
                # Desplegar si está cerrado
                if "elementor-active" not in titulo_btn.get_attribute("class"):
                    driver.execute_script("arguments[0].click();", titulo_btn)
                    time.sleep(2) 
                
                caja_contenido = acordeon_item.find_element(By.CLASS_NAME, "elementor-tab-content")
                
            except Exception:
                raise Exception("Cambio de diseño: No se encontró el acordeón 'LICITACIONES DE BECAS' en Chile Vinos.")

            # FASE 2: Cirugía JS
            anios_a_buscar = [anio_actual, anio_anterior]
            anio_detectado = None

            script_js = """
                const container = arguments[0];
                const anioTarget = arguments[1];
                const anioCierre = arguments[2];

                // 🚀 CAMBIO: Solo buscamos en etiquetas de texto fuerte
                const elementos = Array.from(container.querySelectorAll('strong, b, h1, h2, h3, h4, h5, h6, p'));

                let startNode = null;
                for (let el of elementos) {
                    let textoLimpio = (el.innerText || "").trim().toUpperCase();
                    // 🚀 CAMBIO: Exigimos coincidencia EXACTA del título
                    if (textoLimpio === "BECAS " + anioTarget || textoLimpio === "AÑO " + anioTarget || textoLimpio === anioTarget) {
                        startNode = el;
                        break;
                    }
                }

                if (!startNode) return { error: `No se encontró el título de la sección para el año ${anioTarget}` };

                // Buscar el límite inferior con la misma rigurosidad
                let endNode = null;
                for (let el of elementos) {
                    let textoLimpio = (el.innerText || "").trim().toUpperCase();
                    if ((textoLimpio === "BECAS " + anioCierre || textoLimpio === "AÑO " + anioCierre || textoLimpio === anioCierre) && (startNode.compareDocumentPosition(el) & 4)) {
                        endNode = el;
                        break;
                    }
                }

                const links = [];
                for (let a of container.querySelectorAll('a')) {
                    const isAfterStart = startNode.compareDocumentPosition(a) & 4;
                    const isBeforeEnd = endNode ? (endNode.compareDocumentPosition(a) & 2) : true;
                    
                    if (isAfterStart && isBeforeEnd && a.href) {
                        links.push(a.href);
                    }
                }
                return { links: links };
            """

            for anio_objetivo in anios_a_buscar:
                anio_cierre = str(int(anio_objetivo) - 1)
                logging.info(f"Escaneando el interior del acordeón buscando el año {anio_objetivo}...")
                
                resultado_js = driver.execute_script(script_js, caja_contenido, anio_objetivo, anio_cierre)

                if resultado_js and "error" in resultado_js:
                    logging.info(resultado_js["error"])
                elif resultado_js and "links" in resultado_js:
                    anio_detectado = anio_objetivo
                    titulo_encontrado = f"Chile Vinos - Licitación ({anio_detectado})"
                    
                    for href in resultado_js["links"]:
                        href_limpio = href.strip()
                        
                        es_archivo = any(ext in href_limpio.lower() for ext in ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.zip', '.rar'])
                        es_wordpress = "wp-content/uploads" in href_limpio.lower()
                        es_drive = "drive.google.com" in href_limpio.lower()
                        
                        if es_archivo or es_wordpress or es_drive:
                            url_base = unquote(href_limpio.split('?')[0])
                            if url_base not in enlaces_unicos:
                                enlaces_unicos[url_base] = href_limpio
                        else:
                            logging.warning(f"⚠️ Enlace ignorado por no parecer un documento válido: {href_limpio}")
                    
                    if enlaces_unicos:
                        logging.info(f"🎯 ¡Blanco fijado en {anio_detectado}! Se capturaron {len(enlaces_unicos)} documentos.")
                        break

            enlaces = set(enlaces_unicos.values())

            if not enlaces:
                logging.info(f"Aún no hay documentos subidos para los años {anio_actual} ni {anio_anterior} en Chile Vinos.")
                return enlaces, titulo_encontrado
                
            logging.info(f"Extracción exitosa: {len(enlaces)} documentos únicos capturados en Chile Vinos.")

        except TimeoutException:
            logging.error("Timeout en Chile Vinos")
            raise Exception("La página web de Chile Vinos está caída o demasiado lenta (Timeout).")
        except WebDriverException:
            logging.error("Error de WebDriver en Chile Vinos")
            raise Exception("No se pudo acceder a la página de Chile Vinos. Revisa la URL.")
        except Exception as e:
            logging.error(f"Error explorando la página de Chile Vinos: {e}")
            if "Cambio de diseño" in str(e):
                raise e
            else:
                raise Exception("Error inesperado en Chile Vinos. Revisa los logs de la consola.")
        finally:
            driver.quit()

        return enlaces, titulo_encontrado

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    scraper = ChileVinosScraperSelenium()
    links, titulo = scraper.fetch_tender_links()
    print(f"\n📌 {titulo}")
    for link in links: 
        print(f"- {link}")