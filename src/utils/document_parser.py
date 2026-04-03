import os
import requests
import pandas as pd
import logging
import json
import time
from groq import Groq

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DocumentAnalyzer:
    def __init__(self):
        # 🔴 PEGA TU API KEY DE GROQ AQUÍ 🔴
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY")) 
        
        # Usaremos el modelo Llama 3 de 70 billones de parámetros (Ultra inteligente y rápido)
        self.modelo_ia = "llama-3.3-70b-versatile" 
        
        self.temp_dir = "temp_docs"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def descargar_archivo(self, url):
        nombre_archivo = url.split('/')[-1].split('?')[0] 
        ruta_local = os.path.join(self.temp_dir, nombre_archivo)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*;q=0.8"
        }
        
        try:
            logging.info(f"Descargando documento: {nombre_archivo}...")
            respuesta = requests.get(url, headers=headers, stream=True, timeout=15)
            respuesta.raise_for_status()
            
            with open(ruta_local, 'wb') as f:
                for chunk in respuesta.iter_content(chunk_size=8192):
                    f.write(chunk)
            return ruta_local
        except Exception as e:
            logging.error(f"Error descargando {url}: {e}")
            return None

    def extraer_datos_batch_con_ia(self, filas_a_procesar):
        """Envía TODO el lote de filas juntas en un solo disparo a Groq."""
        texto_batch = ""
        for f in filas_a_procesar:
            texto_batch += f"ID_FILA: {f['id']} | PALABRA_CLAVE: {f['palabra_clave']} | DATOS: {f['texto']}\n"

        prompt_sistema = """Eres un sistema automatizado de extracción de datos. Tu ÚNICO propósito es leer texto crudo y devolver un array JSON válido. NUNCA escribas saludos, explicaciones, ni texto fuera del bloque JSON."""
        
        prompt_usuario = f"""
        Procesa este lote de filas de un Excel de licitaciones.
        
        DATOS CRUDOS:
        {texto_batch}

        Devuelve un JSON estricto con esta estructura:
        [
            {{
                "id_fila": <entero>,
                "palabra_clave": "<string>",
                "curso": "<string>",
                "region": "<string>",
                "comuna": "<string>",
                "cupos": "<string>",
                "horas": "<string>",
                "modalidad": "<string>"
            }}
        ]
        """
        
        max_reintentos = 3
        for intento in range(max_reintentos):
            try:
                # El formato de llamada de Groq es idéntico al de OpenAI
                respuesta = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": prompt_sistema},
                        {"role": "user", "content": prompt_usuario}
                    ],
                    model=self.modelo_ia,
                    temperature=0.1, # Temperatura baja para que sea analítico y no invente datos
                )
                
                texto_limpio = respuesta.choices[0].message.content.strip()
                
                # Limpiamos los marcadores de código por si la IA los incluye
                if texto_limpio.startswith("```json"):
                    texto_limpio = texto_limpio[7:-3].strip()
                elif texto_limpio.startswith("```"):
                    texto_limpio = texto_limpio[3:-3].strip()
                
                return json.loads(texto_limpio)
                
            except Exception as e:
                error_str = str(e)
                if '429' in error_str:
                    espera = 10 
                    logging.warning(f"Límite de velocidad en Groq... pausando {espera} seg (Intento {intento + 1}/{max_reintentos})")
                    time.sleep(espera)
                else:
                    logging.error(f"Error procesando lote con Groq: {e}")
                    break
                    
        return []

    def analizar_excel(self, ruta_excel, palabras_clave):
        logging.info(f"Escaneando interior del Excel: {ruta_excel}...")
        resultados_finales = []
        filas_relevantes = []
        
        try:
            df = pd.read_excel(ruta_excel, header=None)
            
            for index, fila in df.iterrows():
                texto_fila = " | ".join([str(val).strip() for val in fila.values if pd.notna(val)])
                coincidencias = [kw.upper() for kw in palabras_clave if kw.lower() in texto_fila.lower()]

                if coincidencias:
                    filas_relevantes.append({
                        "id": index + 1,
                        "palabra_clave": coincidencias[0],
                        "texto": texto_fila
                    })

            if not filas_relevantes:
                return []
                
            logging.info(f"Se encontraron {len(filas_relevantes)} filas clave. ¡Enviando lote a Groq (Llama 3)!")
            
            datos_ia = self.extraer_datos_batch_con_ia(filas_relevantes)
            
            for item in datos_ia:
                resultados_finales.append({
                    "palabra_clave": item.get("palabra_clave", "Desconocido"),
                    "curso": item.get("curso", "No especificado"),
                    "region": item.get("region", "No especificado"),
                    "comuna": item.get("comuna", "No especificado"),
                    "cupos": str(item.get("cupos", "N/A")),
                    "horas": str(item.get("horas", "N/A")),
                    "modalidad": item.get("modalidad", "No especificado"),
                    "fila": item.get("id_fila", 0)
                })
                
            return resultados_finales
            
        except Exception as e:
            logging.error(f"Error leyendo Excel {ruta_excel}: {e}")
            return []
        finally:
            if os.path.exists(ruta_excel):
                os.remove(ruta_excel)
                logging.info("Archivo temporal eliminado.")