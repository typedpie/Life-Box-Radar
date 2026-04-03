import re
import logging
from datetime import datetime
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AnalizadorLicitaciones:
    def __init__(self):
        # Palabras clave para la alerta de negocio (Lifebox)
        self.keywords_negocio = ["montaje de sistemas solares fotovoltaicos"]

    def clasificar_archivo(self, nombre_archivo):
        """Asigna una categoría al archivo basándose en su nombre."""
        nombre = nombre_archivo.lower()
        if "plan" in nombre and "capacitacion" in nombre:
            return "Plan de Cursos (EXCEL CLAVE)"
        elif "acta" in nombre:
            return "Acta Administrativa (Ignorar)"
        elif "preguntas" in nombre or "respuestas" in nombre:
            return "Preguntas y Respuestas (Informativo)"
        elif "anexo" in nombre or "bases" in nombre or "r.e." in nombre:
            return "Bases y Anexos (Reglas)"
        else:
            return "Documento General"

    def extraer_fecha_de_nombre(self, nombre_archivo):
        """Busca patrones de fecha como DD-MM-YYYY en el nombre del archivo."""
        patron_fecha = r'(\d{2}-\d{2}-\d{4})'
        match = re.search(patron_fecha, nombre_archivo)
        if match:
            fecha_str = match.group(1)
            return datetime.strptime(fecha_str, "%d-%m-%Y")
        return datetime.min # Si no tiene fecha, le damos la fecha más antigua posible

    def seleccionar_plan_mas_reciente(self, lista_nombres_planes):
        """Recibe una lista de planes de capacitación y devuelve el más actual."""
        if not lista_nombres_planes:
            return None
        
        logging.info(f"Resolviendo conflicto de versiones entre {len(lista_nombres_planes)} archivos...")
        # Ordenamos la lista basándonos en la fecha que encontramos en el nombre
        planes_ordenados = sorted(lista_nombres_planes, key=self.extraer_fecha_de_nombre, reverse=True)
        
        ganador = planes_ordenados[0]
        logging.info(f"Archivo ganador seleccionado: {ganador}")
        return ganador

    def analizar_excel_cursos(self, ruta_excel):
        """Abre el Excel ganador, lee los cursos y busca las palabras clave."""
        logging.info(f"Analizando cursos en: {ruta_excel}")
        try:
            # skiprows=13 le dice a pandas que ignore las primeras 13 filas de logos y títulos
            # (Este número lo ajustaremos viendo el Excel real, pero por la data que enviaste, ronda la 13 o 14)
            df = pd.read_excel(ruta_excel, skiprows=13)
            
            # Limpiamos los nombres de las columnas para evitar errores de espacios
            df.columns = df.columns.str.strip().str.lower()
            
            cursos_encontrados = []
            
            # Asumimos que hay una columna llamada "nombre del curso" o "temática"
            # Iteramos sobre las filas para buscar las palabras clave
            # (Aquí usaremos una aproximación, ya que no sé el nombre exacto de la columna en Proforma)
            for index, fila in df.iterrows():
                # Convertimos toda la fila a texto para buscar las palabras
                texto_fila = str(fila.values).lower() 
                
                coincidencias = [kw for kw in self.keywords_negocio if kw in texto_fila]
                if coincidencias:
                    cursos_encontrados.append({
                        "fila": index + 14, # Para saber dónde estaba
                        "coincidencias": coincidencias
                    })
            
            return cursos_encontrados

        except Exception as e:
            logging.error(f"Error procesando el Excel {ruta_excel}: {e}")
            return None

# --- PRUEBA DEL MOTOR DE INTELIGENCIA ---
if __name__ == "__main__":
    analizador = AnalizadorLicitaciones()
    
    # Simulamos los archivos que encontraste
    archivos_encontrados = [
        "Acta-Apertura-Propuestas-1ra-licitacion-2026.pdf",
        "PLAN-DE-CAPACITACION-6TA-ANO-2025-con-correcciones.xlsx",
        "PLAN-DE-CAPACITACION-6TA-ANO-2025-con-correcciones-al-12-02-2026.xlsx",
        "PLAN-DE-CAPACITACION-PROFORMA-14-01-2026.xlsx",
        "Preguntas-y-Respuestas-6-Licitacion-2025.xlsx"
    ]
    
    print("1. CLASIFICACIÓN DE ARCHIVOS:")
    planes_detectados = []
    for archivo in archivos_encontrados:
        categoria = analizador.clasificar_archivo(archivo)
        print(f"- {archivo} -> [{categoria}]")
        if "EXCEL CLAVE" in categoria:
            planes_detectados.append(archivo)
            
    print("\n2. RESOLUCIÓN DE VERSIONES:")
    plan_ganador = analizador.seleccionar_plan_mas_reciente(planes_detectados)
    print(f"-> De los {len(planes_detectados)} planes, el sistema analizará ÚNICAMENTE: {plan_ganador}")