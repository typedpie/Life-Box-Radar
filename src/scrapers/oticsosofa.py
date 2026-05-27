import logging
import time
from urllib.parse import unquote
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

class OticSofofaScraperSelenium:
    def __init__(self):
        self.url_principal = "https://www.oticsofofa.cl/becas-laborales/" 
        
        self.opciones = Options()
        #self.opciones.add_argument("--headless=new")
        self.opciones.add_argument("--no-sandbox")
        self.opciones.add_argument("--disable-dev-shm-usage")
        self.opciones.add_argument("--window-size=1920,1080")

    def fetch_tender_links(self):
        
        anio_actual = str(datetime.now().year) 
        
        logging.info(f"Iniciando exploración en OTIC Sofofa: {self.url_principal}")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.opciones)
        enlaces_unicos = {}
        titulo_encontrado = f"Llamado Licitación OTIC Sofofa {anio_actual}"

        try:
            driver.get(self.url_principal)
            time.sleep(4) 

            logging.info(f"Buscando el llamado más reciente debajo del título {anio_actual}...")

            # SCRIPT ADAPTADO
            script_js = """
                const anioTarget = arguments[0];
                
                // 1. Buscamos el título (ej: <p>Licitaciones 2025</p>)
                const elementos = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, span, p, div, strong, b'));
                let startNode = null;
                
                for (let el of elementos) {
                    let txt = (el.innerText || el.textContent || "").trim().toUpperCase();
                    if (txt === "LICITACIONES " + anioTarget || txt === "AÑO " + anioTarget || txt === anioTarget) {
                        startNode = el;
                        break;
                    }
                }

                if (!startNode) return { error: `No se encontró visualmente el título para el año ${anioTarget}.` };

                // 2. Buscamos el módulo de Pestañas (Tabs) que está DESPUÉS del título
                const allTabs = Array.from(document.querySelectorAll('.et_pb_tabs'));
                let tabsContainer = null;
                
                for(let tab of allTabs) {
                    if (startNode.compareDocumentPosition(tab) & Node.DOCUMENT_POSITION_FOLLOWING) {
                        tabsContainer = tab;
                        break; // Tomamos el primer bloque de pestañas debajo del título
                    }
                }

                if (!tabsContainer) return { error: "No se encontró la caja de pestañas de licitaciones." };

                // 3. Encontramos todas las pestañas (1er llamado, 2do llamado, etc.)
                const tabControls = Array.from(tabsContainer.querySelectorAll('ul.et_pb_tabs_controls li'));
                if (tabControls.length === 0) return { error: "Las pestañas están vacías." };

                // 4. Tomamos la ÚLTIMA pestaña de la lista (El llamado más reciente)
                let lastTab = tabControls[tabControls.length - 1];
                let nombreLlamado = (lastTab.innerText || lastTab.textContent || "").trim();
                
                // Extraemos la clase que conecta la pestaña con el contenido (ej: "et_pb_tab_5")
                let tabClasses = Array.from(lastTab.classList);
                let targetClass = tabClasses.find(c => c.startsWith('et_pb_tab_') && c !== 'et_pb_tab_active');

                if (!targetClass) return { error: "No se pudo identificar el identificador del llamado." };

                // 5. Ubicamos la caja de contenido correspondiente a esa pestaña
                const contentBox = tabsContainer.querySelector(`div.et_pb_all_tabs div.${targetClass}`);
                if (!contentBox) return { error: "No se encontró el contenido del documento." };

                // 6. Extraemos todos los links directamente de esa caja
                const links = Array.from(contentBox.querySelectorAll('a')).map(a => a.href).filter(href => href);

                return { llamado: nombreLlamado, links: links };
            """

            resultado_js = driver.execute_script(script_js, anio_actual)

            if resultado_js and "error" in resultado_js:
                logging.warning(f"⚠️ {resultado_js['error']}")
            elif resultado_js and "links" in resultado_js:
                nombre_llamado = resultado_js["llamado"]
                
                titulo_encontrado = f"OTIC Sofofa - {nombre_llamado} ({anio_actual})"
                logging.info(f"🎯 ¡Blanco fijado! Extrayendo documentos de: {nombre_llamado}")

                for href in resultado_js["links"]:
                    href_limpio = href.strip()
                    # filtro para Archivo real
                    if any(ext in href_limpio.lower() for ext in ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.zip', '.rar']):
                        url_base = unquote(href_limpio.split('?')[0])
                        if url_base not in enlaces_unicos:
                            enlaces_unicos[url_base] = href_limpio

            enlaces = set(enlaces_unicos.values())
            logging.info(f"Extracción exitosa: {len(enlaces)} documentos únicos capturados en Sofofa.")

        except Exception as e:
            logging.error(f"Error explorando la página de OTIC Sofofa: {e}")
        finally:
            driver.quit()

        return enlaces, titulo_encontrado

# Bloque de prueba local
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    scraper = OticSofofaScraperSelenium()
    
    links, titulo = scraper.fetch_tender_links()
    
    print(f"\n📌 {titulo}")
    for link in links: 
        print(f"- {link}")