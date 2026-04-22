import logging
import time
from urllib.parse import unquote
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

class AlianzaPymeScraperSelenium:
    def __init__(self):
        self.url_principal = "https://www.oticalianzapyme.cl/becas/" 
        
        self.opciones = Options()
        self.opciones.add_argument("--headless=new")
        self.opciones.add_argument("--no-sandbox")
        self.opciones.add_argument("--disable-dev-shm-usage")
        self.opciones.add_argument("--window-size=1920,1080")

    def fetch_tender_links(self):
        # 🎯 DINÁMICO: El bot lee el reloj del servidor y busca el año actual automáticamente (2026, 2027...)
        anio_actual = str(datetime.now().year) 
        logging.info(f"Iniciando exploración en Alianza Pyme: {self.url_principal}")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.opciones)
        enlaces_unicos = {}
        titulo_encontrado = f"Llamado Licitación Alianza Pyme {anio_actual}"

        try:
            driver.get(self.url_principal)
            time.sleep(3)

            logging.info(f"Ejecutando Cirugía de Código para aislar la sección del año {anio_actual}...")

            script_js = """
                const anioTarget = arguments[0];
                const anioAnterior = (parseInt(anioTarget) - 1).toString();
                
                const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, .elementor-heading-title, .elementor-widget-heading'));
                
                let startNode = null;
                let endNode = null;

                for (let h of headings) {
                    if (h.innerText.includes(anioTarget)) {
                        startNode = h;
                        break;
                    }
                }
                
                if (startNode) {
                    for (let h of headings) {
                        if (h.innerText.includes(anioAnterior) && (startNode.compareDocumentPosition(h) & 4)) {
                            endNode = h;
                            break;
                        }
                    }
                }

                const links = document.querySelectorAll('.elementor-tab-content a');
                const resultados = [];
                
                for (let link of links) {
                    if (!startNode) break; 
                    
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
            
            links_aislados = driver.execute_script(script_js, anio_actual)

            if not links_aislados:
                logging.info(f"Aún no existen documentos publicados para el año {anio_actual} bajo ese título.")
            else:
                for href in links_aislados:
                    href_limpio = href.strip()
                    if any(ext in href_limpio.lower() for ext in ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.zip']):
                        url_base = unquote(href_limpio.split('?')[0])
                        if url_base not in enlaces_unicos:
                            enlaces_unicos[url_base] = href_limpio

            enlaces = set(enlaces_unicos.values())
            logging.info(f"Extracción milimétrica exitosa: {len(enlaces)} documentos únicos de {anio_actual} capturados.")

        except Exception as e:
            logging.error(f"Error explorando la página de Alianza Pyme: {e}")
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