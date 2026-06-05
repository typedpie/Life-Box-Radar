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

class FrancoChilenoScraperSelenium:
    def __init__(self):
        self.url_principal = "https://www.oticfrancochileno.cl/becas-laborales/"
        
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

        enlaces = set()
        titulo_encontrado = f"Llamado Licitación Franco Chileno {anio_actual}"
        
        logging.info(f"Iniciando exploración en Franco Chileno: {self.url_principal}")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.opciones)
        driver.set_page_load_timeout(30)
        enlaces_unicos = {}
        titulo_encontrado = f"Llamado Licitación Franco Chileno {anio_actual}"

        try:
            driver.get(self.url_principal)
            time.sleep(3)

            anios_a_buscar = [anio_actual, anio_anterior]
            url_subpagina = None
            anio_detectado = None

            # FASE 1: Buscar el botón del año en la página principal
            for anio_objetivo in anios_a_buscar:
                logging.info(f"Buscando acceso para el año {anio_objetivo}...")
                try:
                    
                    xpath_boton = f"//a[contains(@class, 'fl-icon-text-link') and normalize-space(.)='{anio_objetivo}']"
                    
                    boton_anio = driver.find_element(By.XPATH, xpath_boton)
                    url_subpagina = boton_anio.get_attribute("href")
                    
                    if url_subpagina:
                        anio_detectado = anio_objetivo
                        logging.info(f"¡Botón {anio_objetivo} detectado! Viajando a la bóveda: {url_subpagina}")
                        break
                except Exception:
                    logging.info(f"No se encontró el botón para {anio_objetivo}.")
                    continue
            
            
            
            if not url_subpagina:
                logging.info(f"Aún no existen botones para {anio_actual} ni {anio_anterior} en Franco Chileno.")
                return enlaces, titulo_encontrado

            # FASE 2: Extraer documentos del último llamado en la subpágina
            driver.get(url_subpagina)
            time.sleep(4)

            # JavaScript para encontrar el título del último llamado y enlaces
            script_js = """
                const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, .fl-heading-text'));
                
                // Filtramos los títulos que parezcan ser de un llamado
                const validHeadings = headings.filter(h => {
                    const txt = (h.innerText || "").toLowerCase();
                    return txt.includes('llamado') || txt.includes('programa de becas') || txt.includes('licitación');
                });

                if (validHeadings.length === 0) return { error: "No se encontraron títulos de llamados en la subpágina." };

                // Tomamos el ÚLTIMO título de la lista (el más profundo en la página)
                const lastHeading = validHeadings[validHeadings.length - 1];
                const titleName = lastHeading.innerText.trim();

                const allLinks = Array.from(document.querySelectorAll('a'));
                const linksAfter = [];

                for(let link of allLinks) {
                    // Magia HTML: ¿El enlace está 'después' del último título? (Retorna 4)
                    if (lastHeading.compareDocumentPosition(link) & 4) {
                        if (link.href) {
                            linksAfter.push(link.href);
                        }
                    }
                }
                return { titulo: titleName, links: linksAfter };
            """

            resultado_js = driver.execute_script(script_js)

            if resultado_js and "error" in resultado_js:
                logging.warning(f"⚠️ {resultado_js['error']}")
                raise Exception(f"Cambio de diseño en la bóveda: {resultado_js['error']}")
                
            elif resultado_js and "links" in resultado_js:
                nombre_llamado = resultado_js["titulo"]
                titulo_encontrado = f"Franco Chileno - {nombre_llamado} ({anio_detectado})"
                logging.info(f"🎯 ¡Último llamado aislado!: {nombre_llamado}")

                for href in resultado_js["links"]:
                    href_limpio = href.strip()
                    # Filtrar por extension
                    if any(ext in href_limpio.lower() for ext in ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.zip', '.rar']):
                        url_base = unquote(href_limpio.split('?')[0])
                        if url_base not in enlaces_unicos:
                            enlaces_unicos[url_base] = href_limpio

            enlaces = set(enlaces_unicos.values())
            
            
            if not enlaces:
                raise Exception("Cambio de diseño: No se extrajeron documentos válidos de la bóveda de Franco Chileno.")

            logging.info(f"Extracción exitosa: {len(enlaces)} documentos únicos capturados.")

        except TimeoutException:
            logging.error("Timeout en Franco Chileno")
            raise Exception("La página web de Franco Chileno está caída o demasiado lenta (Timeout).")
        except WebDriverException:
            logging.error("Error de WebDriver en Franco Chileno")
            raise Exception("No se pudo acceder a la página de Franco Chileno. Revisa la URL.")
        except Exception as e:
            logging.error(f"Error explorando la página de Franco Chileno: {e}")
            if "Cambio de diseño" in str(e):
                raise e
            else:
                raise Exception("Error inesperado en Franco Chileno. Revisa los logs de la consola.")
        finally:
            driver.quit()

        return enlaces, titulo_encontrado

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    scraper = FrancoChilenoScraperSelenium()
    links, titulo = scraper.fetch_tender_links()
    print(f"\n📌 {titulo}")
    for link in links: 
        print(f"- {link}")