import logging
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException

class AgrocapScraperSelenium:
    def __init__(self):
        self.url_principal = "https://www.agrocap.cl/webid/?page_id=292"#2" 
        
        self.opciones = Options()
        self.opciones.page_load_strategy = 'eager'
        self.opciones.add_argument("--disable-gpu")
        self.opciones.add_argument("--headless=new")
        self.opciones.add_argument("--no-sandbox")
        self.opciones.add_argument("--disable-dev-shm-usage")
        self.opciones.add_argument("--window-size=1920,1080")
         

    def fetch_tender_links(self):
        
        # logica de doble intento para transicion de años
        anio_actual = str(datetime.now().year) 
        anio_anterior = str(datetime.now().year - 1)
        
        logging.info(f"Iniciando exploración en Agrocap: {self.url_principal}")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.opciones)
        driver.set_page_load_timeout(30)
        enlaces = set()
        titulo_encontrado = f"Llamado Licitación Agrocap {anio_actual}" # Título por defecto

        try:
            driver.get(self.url_principal)
            time.sleep(3)

            # --- FASE 1: BUSCAR EL CALENDARIO  ---
            url_subpagina = None
            anio_detectado = None
            anios_a_buscar = [anio_actual, anio_anterior] # Intentará primero el actual, luego el anterior

            for anio_objetivo in anios_a_buscar:
                logging.info(f"Buscando el calendario del año {anio_objetivo}...")
                try:
                    # 1. Titulos que contengan el año iterado
                    xpath_textos = f"//div[contains(@class, 'elementor-widget-heading') and contains(., '{anio_objetivo}')]"
                    textos_anio = driver.find_elements(By.XPATH, xpath_textos)
                    
                    for nodo in textos_anio:
                        try:
                            envoltura = nodo.find_element(By.XPATH, "./ancestor::div[contains(@class, 'elementor-widget-wrap')][1]")
                            
                            # Busco el enlace (a) que vive dentro de esta misma envoltura pequeña
                            enlace = envoltura.find_element(By.XPATH, ".//a[@href]")
                            url_subpagina = enlace.get_attribute("href")
                            
                            if url_subpagina:
                                anio_detectado = anio_objetivo
                                break # Romper ciclo de nodos si se encuentra
                        except Exception:
                            continue 
                    
                    if url_subpagina:
                        logging.info(f"¡Calendario {anio_objetivo} detectado! Viajando a la bóveda: {url_subpagina}")
                        break # Romper ciclo de años 
                        
                except Exception as e:
                    logging.warning(f"Error evaluando el año {anio_objetivo}: {e}")

            # Si después de intentar ambos años no hay url, aborta
            if not url_subpagina:
                raise Exception (f"Error 404 o Cambio de Diseño: No se encontró la estructura esperada en la URL {self.url_principal}")
                #logging.info(f"No se encontró el calendario ni para {anio_actual} ni para {anio_anterior} en Agrocap.")
                #return enlaces, titulo_encontrado 

            # --- FASE 2: CIRUGÍA DE CÓDIGO ---
            driver.get(url_subpagina)
            time.sleep(3)

            try:
                # 1. Busca todos los titulos de llamados
                xpath_titulos = "//*[not(ancestor-or-self::a) and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'llamado licitación')]"
                nodos_titulos = driver.find_elements(By.XPATH, xpath_titulos)

                lista_titulos = []
                for nodo in nodos_titulos:
                    texto = nodo.text.strip()
                    match = re.search(r'(\d+)[°a-z]*\s*llamado', texto.lower())
                    if match:
                        lista_titulos.append({"nodo": nodo, "texto": texto, "num": int(match.group(1))})

                if lista_titulos:
                    
                    max_num = max(t["num"] for t in lista_titulos)
                    
                    idx_campeon = next(i for i, t in enumerate(lista_titulos) if t["num"] == max_num)
                    
                    # Le inyecto el año detectado al título final para mayor claridad
                    titulo_encontrado = f"Agrocap - {lista_titulos[idx_campeon]['texto']} ({anio_detectado})"
                    nodo_inicio = lista_titulos[idx_campeon]["nodo"]
                    logging.info(f"🏆 Campeón detectado: {titulo_encontrado}")

                    # Límite inferior
                    nodo_fin = None
                    if idx_campeon + 1 < len(lista_titulos):
                        nodo_fin = lista_titulos[idx_campeon + 1]["nodo"]
                        logging.info(f"🛑 Límite inferior establecido justo antes de: '{lista_titulos[idx_campeon + 1]['texto']}'")
                    else:
                        logging.info("🛑 No hay llamados más antiguos. Se leerá hasta el final de la página.")

                    # Javascript Extractor
                    script_js = """
                        var startNode = arguments[0];
                        var endNode = arguments[1];
                        var buttons = document.querySelectorAll('a.elementor-button-link');
                        var result = [];
                        
                        for (var i = 0; i < buttons.length; i++) {
                            var btn = buttons[i];
                            // Magia HTML: ¿El botón está 'después' del título 2? (Retorna 4)
                            var isAfterStart = (startNode.compareDocumentPosition(btn) & 4);
                            
                            // Magia HTML: ¿El botón está 'antes' del título 1? (Retorna 2)
                            var isBeforeEnd = endNode ? (endNode.compareDocumentPosition(btn) & 2) : true;

                            if (isAfterStart && isBeforeEnd) {
                                var href = btn.getAttribute('href');
                                if (href) {
                                    result.push(href);
                                }
                            }
                        }
                        return result;
                    """
                    
                    # Ejecuto el script en Chrome
                    links_aislados = driver.execute_script(script_js, nodo_inicio, nodo_fin)

                    # Guardo
                    for href in links_aislados:
                        if any(ext in href.lower() for ext in ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.zip']):
                            enlaces.add(href)
                            
                    logging.info(f"✅ Cirugía exitosa: {len(enlaces)} documentos extraídos milimétricamente.")
                else:
                    logging.warning("No se encontraron títulos válidos en la bóveda.")

            except Exception as e_boveda:
                logging.error(f"Error procesando la bóveda: {e_boveda}")
                raise Exception("Cambio de diseño en la bóveda: No se pudieron extraer los enlaces.")
        
        except TimeoutException:
            logging.error("Timeoout en agrocap")
            raise Exception("La página web de Agrocap está caída o demasiado lenta (Timeout).")
        except WebDriverException:
            logging.error("Error de Webdriver en agrocap")
            raise Exception("No se pudo acceder al enlace principal de Agrocap. Revisa la URL.")

        except Exception as e:
            logging.error(f"Error explorando la página principal de Agrocap: {e}")
            if "Error 404" in str(e):
                raise e
            else:
                raise Exception("Error inesperado en Agrocap. Revisa los logs de la consola.")
        finally:
            driver.quit()

        return enlaces, titulo_encontrado

# Bloque de prueba local
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    scraper = AgrocapScraperSelenium()
    
    links, titulo = scraper.fetch_tender_links()
    
    print(f"\n📌 {titulo}")
    for link in links: 
        print(f"- {link}")