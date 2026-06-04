import os
import requests
import pandas as pd
import logging
import json
import time
import PyPDF2 
from groq import Groq

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DocumentAnalyzer:
    def __init__(self):
        # Lee la llave secreta desde GitHub Actions de forma segura
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        
        # Modelo Llama 3 de 70 billones de parámetros
        self.modelo_ia = "llama-3.3-70b-versatile" 
        
        self.temp_dir = "temp_docs"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def descargar_archivo(self, url):
        nombre_archivo = url.split('/')[-1].split('?')[0] 
        ruta_local = os.path.join(self.temp_dir, nombre_archivo)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/pdf,*/*;q=0.8"
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

    # ==========================================
    # FUNCIÓN: EXTRACCIÓN DE FECHA
    # ==========================================
    def extraer_fecha_pdf(self, ruta_pdf):
        if not self.client:
            return "No especificada"
            
        logging.info(f"🔎 Analizando PDF para encontrar fecha de cierre: {ruta_pdf}")
        
        try:
            texto_pdf = ""
            with open(ruta_pdf, 'rb') as file:
                lector = PyPDF2.PdfReader(file)
                paginas_a_leer = min(5, len(lector.pages))
                for i in range(paginas_a_leer):
                    texto_extraido = lector.pages[i].extract_text()
                    if texto_extraido:
                        texto_pdf += texto_extraido + "\n"
                        
            prompt_sistema = "Eres un asistente legal experto en licitaciones públicas de Chile. Tu ÚNICO objetivo es extraer la fecha exacta de cierre."
            prompt_usuario = f"""
            Analiza el siguiente extracto de las bases de una licitación y encuentra la FECHA LÍMITE o MÁXIMA PARA LA "RECEPCIÓN DE OFERTAS", "RECEPCIÓN DE PROPUESTAS" o "POSTULACIÓN".
            
            TEXTO DEL DOCUMENTO:
            {texto_pdf[:4000]} 
            
            REGLAS:
            1. Devuelve ÚNICAMENTE la fecha en formato estricto YYYY-MM-DD.
            2. Ejemplo: si dice "13 de febrero de 2026 a las 18:00hrs", debes devolver exactamente: 2026-02-13
            3. NO ESCRIBAS NADA MÁS. NI INTRODUCCIONES NI EXPLICACIONES. SOLO LA FECHA.
            4. Si no la encuentras, responde: No especificada
            """
            
            respuesta = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": prompt_usuario}
                ],
                model=self.modelo_ia,
                temperature=0.0, 
            )
            
            fecha_encontrada = respuesta.choices[0].message.content.strip()
            logging.info(f"📅 Fecha de cierre detectada en PDF: {fecha_encontrada}")
            return fecha_encontrada
            
        except Exception as e:
            logging.error(f"Error extrayendo fecha del PDF {ruta_pdf}: {e}")
            return "No especificada"

    
    def extraer_lote_con_ia(self, lote_filas):
        texto_batch = ""
        for f in lote_filas:
            texto_batch += f"ID_FILA: {f['id']} | PALABRA_CLAVE: {f['palabra_clave']} | DATOS: {f['texto']}\n"

        max_reintentos = 3
        json_estructurado = []
        
        # ==========================================
        # FASE 1: Extracción y Formateo
        # ==========================================
        prompt_sistema_1 = "Eres un autómata extractor de datos. Tu único objetivo es leer texto crudo y devolver un array JSON válido. NO evalúes ni filtres la información, solo ordénala."
        
        prompt_usuario_1 = f"""
        Procesa este lote de filas de un Excel:
        {texto_batch}

        Devuelve un JSON estricto con esta estructura (no omitas ninguna fila, conviértelas todas):
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
        
        for intento in range(max_reintentos):
            try:
                res_1 = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": prompt_sistema_1},
                        {"role": "user", "content": prompt_usuario_1}
                    ],
                    model=self.modelo_ia,
                    temperature=0.0, 
                )
                txt_1 = res_1.choices[0].message.content.strip()
                
                # 🛡️ EXTRACCIÓN  DE JSON (FASE 1)
                inicio = txt_1.find('[')
                fin = txt_1.rfind(']') + 1
                if inicio != -1 and fin != -1:
                    txt_1 = txt_1[inicio:fin]
                else:
                    txt_1 = "[]" # Si no hay corchetes, asumo array vacío
                
                json_estructurado = json.loads(txt_1)
                break # Éxito, rompo el bucle
            except Exception as e:
                if '429' in str(e) or '413' in str(e):
                    espera = 60 # <-- MÁS PACIENCIA: Aumentado a 60s si falla, para garantizar el reseteo
                    logging.warning(f"Límite en Groq (Fase 1)... pausando {espera}s (Intento {intento + 1}/{max_reintentos})")
                    time.sleep(espera)
                else:
                    logging.error(f"Error en Fase 1 con Groq: {e}\nTexto devuelto por IA: {txt_1}")
                    break
        
        if not json_estructurado:
            return []

        # ==========================================
        # FASE 2:Filtro Semántico de Calidad
        # ==========================================
        prompt_sistema_2 = "Eres un analista experto en licitaciones de Recursos Humanos (Power Skills). Tu trabajo es recibir un JSON de cursos, eliminar la basura operativa y devolver solo las oportunidades válidas."
        
        prompt_usuario_2 = f"""
        Analiza el siguiente array de cursos en formato JSON:
        {json.dumps(json_estructurado, ensure_ascii=False)}

        ⚠️ REGLA DE RECHAZO:
        Elimina por completo del JSON cualquier objeto cuyo "curso" sea un oficio técnico, manual, operativo, de agricultura o de computación básica (ej: peluquería canina, hornos solares, gastronomía, excel, maquinaria, conducción, costura, etc.).
        
        ✅ CRITERIO DE ACEPTACIÓN:
        Mantén en el JSON solo los objetos cuyo "curso" sea genuinamente sobre habilidades blandas, liderazgo, clima laboral, trabajo en equipo, bienestar, inclusión o normativas laborales (Ley Karin).

        Devuelve ÚNICAMENTE el array JSON resultante. Mantén la misma estructura de los objetos que pasen la prueba. Si ninguno sirve, devuelve: []
        """
        
        for intento in range(max_reintentos):
            try:
                res_2 = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": prompt_sistema_2},
                        {"role": "user", "content": prompt_usuario_2}
                    ],
                    model=self.modelo_ia,
                    temperature=0.0, 
                )
                txt_2 = res_2.choices[0].message.content.strip()
                
                # 🛡️ EXTRACCIÓN DE JSON (FASE 2)
                inicio = txt_2.find('[')
                fin = txt_2.rfind(']') + 1
                if inicio != -1 and fin != -1:
                    txt_2 = txt_2[inicio:fin]
                else:
                    txt_2 = "[]"
                
                json_final = json.loads(txt_2)
                logging.info(f"⚖️ Filtro del Juez: Entraron {len(json_estructurado)} cursos brutos, pasaron la prueba {len(json_final)} cursos de alto valor.")
                return json_final
                
            except Exception as e:
                if '429' in str(e) or '413' in str(e):
                    espera = 60 # <-- MÁS PACIENCIA
                    logging.warning(f"Límite en Groq (Fase 2)... pausando {espera}s (Intento {intento + 1}/{max_reintentos})")
                    time.sleep(espera)
                else:
                    logging.error(f"Error en Fase 2 con Groq: {e}")
                    break
                    
        return []

    def analizar_excel(self, ruta_excel, palabras_clave):
        if not self.client:
            logging.error("No se encontró GROQ_API_KEY. Asegúrate de que el Secret de GitHub esté configurado.")
            return []

        logging.info(f"Escaneando interior del Excel: {ruta_excel}...")
        resultados_finales = []
        filas_relevantes = []
        
        try:
            df = pd.read_excel(ruta_excel, header=None)
            
            # --- PRE-FILTRO ESTRICTO ---
            for index, fila in df.iterrows():
                textos_cortos_validos = []
                texto_fila_completa = [] # Guardo toda la info para la IA
                
                for val in fila.values:
                    if pd.notna(val):
                        val_str = str(val).strip()
                        texto_fila_completa.append(val_str)
                        
                        # Regla: Si tiene 150 caracteres o menos, es candidato para buscar palabras clave
                        if 0 < len(val_str) <= 150:
                            textos_cortos_validos.append(val_str)

                # Uno solo las celdas cortas para hacer la búsqueda
                texto_para_buscar = " | ".join(textos_cortos_validos).lower()
                
                coincidencias = [kw.upper() for kw in palabras_clave if kw.lower() in texto_para_buscar]

                if coincidencias:
                    # Si encuentro coincidencia, guardo la fila COMPLETA para que Groq no pierda datos
                    filas_relevantes.append({
                        "id": index + 1,
                        "palabra_clave": coincidencias[0],
                        "texto": " | ".join(texto_fila_completa)
                    })
            # ----------------------------------

            if not filas_relevantes:
                return []
                
            logging.info(f"Se encontraron {len(filas_relevantes)} filas clave. Iniciando procesamiento por lotes...")
            
            # 2. SISTEMA DE LOTES (Ajustado para no quemar tokens del modelo 70b)
            tamano_lote = 5 # <--- Bajado a 5 filas por lote para no romper la API.
            
            for i in range(0, len(filas_relevantes), tamano_lote):
                lote = filas_relevantes[i:i + tamano_lote]
                logging.info(f"🧠 Analizando lote {i//tamano_lote + 1} (Filas {i+1} a {min(i+tamano_lote, len(filas_relevantes))})...")
                
                datos_ia = self.extraer_lote_con_ia(lote)
                
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
                
                # 3. PAUSA: Modificada para no chocar con el límite de Groq
                if i + tamano_lote < len(filas_relevantes):
                    logging.info("⏱️ Enfriando el motor de Groq por 45 segundos para respetar los límites...")
                    time.sleep(45) # <---  Pausa más larga
                    
            return resultados_finales
            
        except Exception as e:
            logging.error(f"Error leyendo Excel {ruta_excel}: {e}")
            return []
        finally:
            if os.path.exists(ruta_excel):
                os.remove(ruta_excel)
                logging.info("Archivo temporal eliminado.")