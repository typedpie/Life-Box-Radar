import logging
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

class AgrocapScraperSelenium:
    def __init__(self):
        self.url_principal = "https://www.agrocap.cl/webid/?page_id=2922" 
        
        self.opciones = Options()
        self.opciones.add_argument("--headless=new")
        self.opciones.add_argument("--no-sandbox")
        self.opciones.add_argument("--disable-dev-shm-usage")
        self.opciones.add_argument("--window-size=1920,1080")

    def fetch_tender_links(self):
        # 🔴 PARA PROBAR: Pon "2025" temporalmente
        anio_actual = str(datetime.now().year) 
        logging.info(f"Iniciando exploración en Agrocap: {self.url_principal}")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.opciones)
        enlaces = set()
        titulo_encontrado = f"Llamado Licitación Agrocap {anio_actual}"

        try:
            driver.get(self.url_principal)
            time.sleep(3)

            # --- FASE 1: BUSCAR EL CALENDARIO ---
            logging.info(f"Buscando el calendario del año {anio_actual}...")
            url_subpagina = None
            
            try:
                # 1. Buscamos TODOS los títulos que digan el año
                xpath_textos = f"//div[contains(@class, 'elementor-widget-heading') and contains(., '{anio_actual}')]"
                textos_anio = driver.find_elements(By.XPATH, xpath_textos)
                
                for nodo in textos_anio:
                    try:
                        # 2. Subimos estrictamente a la 'envoltura' (widget-wrap) más cercana que agrupa a ESTE texto con su ícono
                        envoltura = nodo.find_element(By.XPATH, "./ancestor::div[contains(@class, 'elementor-widget-wrap')][1]")
                        
                        # 3. Buscamos el enlace (a) que vive dentro de esta misma envoltura pequeña
                        enlace = envoltura.find_element(By.XPATH, ".//a[@href]")
                        url_subpagina = enlace.get_attribute("href")
                        
                        if url_subpagina:
                            break # Si lo encontramos con éxito, rompemos el ciclo
                    except Exception:
                        continue # Si este texto no era el calendario, probamos con el siguiente "2025" de la página
                
                if url_subpagina:
                    logging.info(f"¡Calendario {anio_actual} detectado de forma aislada! Viajando a la bóveda: {url_subpagina}")
                else:
                    logging.info(f"Aún no existe el calendario para el año {anio_actual} en Agrocap.")
                    return enlaces, titulo_encontrado 

            except Exception as e:
                logging.error(f"Error en Fase 1: {e}")
                return enlaces, titulo_encontrado

            # --- FASE 2: CIRUGÍA DE CÓDIGO (DOM SLICING) ---
            driver.get(url_subpagina)
            time.sleep(3)

            try:
                # 1. Buscamos TODOS los títulos de llamados, excluyendo estrictamente los que estén dentro de un botón (etiqueta 'a')
                xpath_titulos = "//*[not(ancestor-or-self::a) and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'llamado licitación')]"
                nodos_titulos = driver.find_elements(By.XPATH, xpath_titulos)

                lista_titulos = []
                for nodo in nodos_titulos:
                    texto = nodo.text.strip()
                    match = re.search(r'(\d+)[°a-z]*\s*llamado', texto.lower())
                    if match:
                        lista_titulos.append({"nodo": nodo, "texto": texto, "num": int(match.group(1))})

                if lista_titulos:
                    # 2. Competencia Matemática (Buscamos el Nivel más alto, ej: 2)
                    max_num = max(t["num"] for t in lista_titulos)
                    
                    # Identificamos qué lugar de la lista ocupa nuestro campeón
                    idx_campeon = next(i for i, t in enumerate(lista_titulos) if t["num"] == max_num)
                    
                    titulo_encontrado = lista_titulos[idx_campeon]["texto"]
                    nodo_inicio = lista_titulos[idx_campeon]["nodo"]
                    logging.info(f"🏆 Campeón detectado: {titulo_encontrado}")

                    # 3. Identificamos el "Piso" (El siguiente título en el código, si es que existe)
                    nodo_fin = None
                    if idx_campeon + 1 < len(lista_titulos):
                        nodo_fin = lista_titulos[idx_campeon + 1]["nodo"]
                        logging.info(f"🛑 Límite inferior establecido justo antes de: '{lista_titulos[idx_campeon + 1]['texto']}'")
                    else:
                        logging.info("🛑 No hay llamados más antiguos. Se leerá hasta el final de la página.")

                    # 4. LA CIRUGÍA JAVASCRIPT: Cortar exactamente los botones que están en el medio
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
                    
                    # Inyectamos y ejecutamos el script en Chrome
                    links_aislados = driver.execute_script(script_js, nodo_inicio, nodo_fin)

                    # 5. Guardamos solo los documentos útiles
                    for href in links_aislados:
                        if any(ext in href.lower() for ext in ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.zip']):
                            enlaces.add(href)
                            
                    logging.info(f"✅ Cirugía exitosa: {len(enlaces)} documentos extraídos milimétricamente.")
                else:
                    logging.warning("No se encontraron títulos válidos en la bóveda.")

            except Exception as e_boveda:
                logging.error(f"Error procesando la bóveda: {e_boveda}")

        except Exception as e:
            logging.error(f"Error explorando la página principal de Agrocap: {e}")
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