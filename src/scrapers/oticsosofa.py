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
        self.opciones.add_argument("--headless") 
        self.opciones.add_argument("--no-sandbox")
        self.opciones.add_argument("--disable-dev-shm-usage") 
        self.opciones.add_argument("--disable-gpu") 
        self.opciones.add_argument("--disable-software-rasterizer")
        self.opciones.add_argument("--window-size=1920,1080")

    def fetch_tender_links(self):
        
        # 🎯 ambos años
        anio_actual = str(datetime.now().year) 
        anio_anterior = str(datetime.now().year - 1)
        
        logging.info(f"Iniciando exploración en OTIC Sofofa: {self.url_principal}")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.opciones)
        enlaces_unicos = {}
        titulo_encontrado = f"Llamado Licitación OTIC Sofofa {anio_actual}"

        try:
            driver.get(self.url_principal)
            time.sleep(4) 

            logging.info(f"Buscando llamados del {anio_actual} (Plan B: {anio_anterior})...")

            # script con la fase 2 por si la 2 falla"
            script_js = """
                const anioActual = arguments[0];
                const anioAnterior = arguments[1];
                
                const elementos = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, span, p, div, strong, b'));
                
                // Función interna para buscar el bloque de un año específico
                function buscarBloqueAnio(anioTarget) {
                    let startNode = null;
                    for (let el of elementos) {
                        let txt = (el.innerText || el.textContent || "").trim().toUpperCase();
                        if (txt === "LICITACIONES " + anioTarget || txt === "AÑO " + anioTarget || txt === anioTarget) {
                            startNode = el;
                            break;
                        }
                    }
                    if (!startNode) return null;

                    const allTabs = Array.from(document.querySelectorAll('.et_pb_tabs'));
                    let tabsContainer = null;
                    for(let tab of allTabs) {
                        if (startNode.compareDocumentPosition(tab) & Node.DOCUMENT_POSITION_FOLLOWING) {
                            tabsContainer = tab;
                            break; 
                        }
                    }
                    return tabsContainer;
                }

                // 1. INTENTAMOS CON EL AÑO ACTUAL
                let tabsContainer = buscarBloqueAnio(anioActual);
                let anioUsado = anioActual;

                // 2. SI FALLA (O NO HAY TABS), ACTIVAMOS PLAN B (AÑO ANTERIOR)
                if (!tabsContainer || tabsContainer.querySelectorAll('ul.et_pb_tabs_controls li').length === 0) {
                    tabsContainer = buscarBloqueAnio(anioAnterior);
                    anioUsado = anioAnterior;
                }

                // Si fallan ambos, abortamos
                if (!tabsContainer) {
                    return { error: `No se encontró el título ni para ${anioActual} ni para ${anioAnterior}.` };
                }

                // 3. Encontramos todas las pestañas del año ganador
                const tabControls = Array.from(tabsContainer.querySelectorAll('ul.et_pb_tabs_controls li'));
                if (tabControls.length === 0) return { error: `Las pestañas para el año ${anioUsado} están vacías.` };

                // 4. Tomamos la ÚLTIMA pestaña de la lista (El llamado más reciente)
                let lastTab = tabControls[tabControls.length - 1];
                let nombreLlamado = (lastTab.innerText || lastTab.textContent || "").trim();
                
                let tabClasses = Array.from(lastTab.classList);
                let targetClass = tabClasses.find(c => c.startsWith('et_pb_tab_') && c !== 'et_pb_tab_active');

                if (!targetClass) return { error: "No se pudo identificar el identificador del llamado." };

                // 5. Ubicamos la caja de contenido correspondiente a esa pestaña
                const contentBox = tabsContainer.querySelector(`div.et_pb_all_tabs div.${targetClass}`);
                if (!contentBox) return { error: "No se encontró el contenido del documento." };

                // 6. Extraemos todos los links directamente de esa caja
                const links = Array.from(contentBox.querySelectorAll('a')).map(a => a.href).filter(href => href);

                // Retornamos también el año que usamos para los logs
                return { llamado: nombreLlamado, links: links, anio_detectado: anioUsado };
            """

            resultado_js = driver.execute_script(script_js, anio_actual, anio_anterior)

            if resultado_js and "error" in resultado_js:
                logging.warning(f"⚠️ {resultado_js['error']}")
            elif resultado_js and "links" in resultado_js:
                nombre_llamado = resultado_js["llamado"]
                anio_detectado = resultado_js["anio_detectado"] # Recibimos si usó 2026 o 2025
                
                # Actualizo el titulo con el año donde s encontro 
                titulo_encontrado = f"OTIC Sofofa - {nombre_llamado} ({anio_detectado})"
                logging.info(f"🎯 ¡Blanco fijado en {anio_detectado}! Extrayendo documentos de: {nombre_llamado}")

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