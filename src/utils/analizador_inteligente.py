import re
import logging
from datetime import datetime
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AnalizadorLicitaciones:
    def __init__(self):
        # Palabras clave para la alerta de negocio (Lifebox)
        self.keywords_negocio = [
            "power skills", "habilidades blandas", "soft skills", "capacitación", 
            "capacitación laboral", "capacitación corporativa", "capacitación empresarial", 
            "formación", "formación laboral", "formación profesional", "formación continua", 
            "entrenamiento corporativo", "aprendizaje corporativo", "aprendizaje organizacional", 
            "desarrollo organizacional", "desarrollo profesional", "desarrollo de carrera", 
            "desarrollo de talento", "gestión del talento", "talento humano", "gestión de personas", 
            "recursos humanos", "rrhh", "learning & development", "l&d", "aprendizaje continuo", 
            "aprendizaje permanente", "aprendizaje experiencial", "learning by doing", 
            "aprendizaje activo", "aprendizaje práctico", "aprendizaje aplicado", 
            "aprendizaje significativo", "aprendizaje colaborativo", "aprendizaje social", 
            "microlearning", "e-learning", "formación online", "formación digital", 
            "formación híbrida", "cursos online", "programas de capacitación", 
            "rutas de aprendizaje", "lms", "edtech", "tecnología educativa", 
            "inteligencia artificial", "ia aplicada", "alfabetización digital", 
            "alfabetización en ia", "prompting", "transformación digital", 
            "herramientas digitales", "learning analytics", "people analytics", 
            "medición de impacto", "kpis de capacitación", "roi de capacitación", 
            "cultura organizacional", "clima laboral", "cultura de aprendizaje", 
            "cultura de innovación", "cultura preventiva", "cambio organizacional", 
            "gestión del cambio", "transformación cultural", "liderazgo", 
            "liderazgo organizacional", "liderazgo de equipos", "liderazgo transformacional", 
            "liderazgo adaptativo", "liderazgo situacional", "liderazgo consciente", 
            "liderazgo inclusivo", "liderazgo empático", "liderazgo resiliente", 
            "liderazgo de alto impacto", "desarrollo de líderes", "gestión de equipos", 
            "trabajo en equipo", "espíritu de equipo", "colaboración", "colaboración ágil", 
            "colaboración exitosa", "equipos de alto rendimiento", "desempeño laboral", 
            "evaluación de desempeño", "feedback", "feedback continuo", "retroalimentación", 
            "feedback 360", "feedback 360 para colaboradores", "feedback 360 para líderes", 
            "feedforward", "comunicación", "comunicación efectiva", "comunicación organizacional", 
            "comunicación empática", "comunicación empática 2", "comunicación estratégica", 
            "comunicación estratégica en tiempos vica", "comunicación virtual", 
            "comunicación con ia", "escucha activa", "empatía", "habilidades interpersonales", 
            "inteligencia emocional", "autoconocimiento", "autorregulación emocional", 
            "gestión emocional", "manejo de emociones", "manejo de emociones 1", 
            "manejo de emociones 2", "gestión del estrés", "resiliencia", "resiliencia en acción", 
            "bienestar", "bienestar laboral", "bienestar organizacional", "bienestar emocional", 
            "bienestar financiero", "salud mental", "calidad de vida laboral", "autocuidado", 
            "motivación", "compromiso", "engagement", "experiencia del colaborador", 
            "employee experience", "sentido de pertenencia", "propósito organizacional", 
            "diversidad", "equidad", "inclusión", "diversidad e inclusión", "dei", 
            "cultura inclusiva", "perspectiva de género", "equidad de género", 
            "inclusión laboral", "ley karin", "ley 21.643", "ley 21.015", "acoso laboral", 
            "acoso sexual", "prevención del acoso", "ambientes laborales seguros", 
            "seguridad psicológica", "prevención de riesgos", "riesgos psicosociales", 
            "cumplimiento normativo", "toma de decisiones", "toma de decisiones proactivas", 
            "pensamiento crítico", "pensamiento crítico en acción", "pensamiento estratégico", 
            "resolución de problemas", "creatividad", "innovación", "innovación organizacional", 
            "emprendimiento", "espíritu emprendedor", "mentalidad de crecimiento", 
            "growth mindset", "mentalidad ágil", "adaptabilidad", "agilidad", 
            "agilidad organizacional", "agilidad emocional", "agilidad en el aprendizaje", 
            "metodologías ágiles", "agile learning", "design thinking", "lean", "lean startup", 
            "kanban", "scrum", "mejora continua", "kaizen", "pdca", "accountability", 
            "accountability 2", "objetivos smart", "metodología smarter", "planificación", 
            "planificación estratégica", "gestión del tiempo", "priorización", "productividad", 
            "eficiencia", "desempeño", "resultados", "impacto organizacional", 
            "aprendizaje de alto impacto", "aprendizaje aplicado al negocio", 
            "alineación estratégica", "estrategia de talento", "employer branding", 
            "marca empleadora", "evp", "atracción de talento", "retención de talento", 
            "satisfacción laboral", "empleabilidad", "upskilling", "reskilling", 
            "talento del futuro", "habilidades del futuro", "future of work", "futuro del trabajo", 
            "teletrabajo", "trabajo remoto", "trabajo híbrido", "equipos virtuales", 
            "colaboración digital", "reuniones virtuales", "reuniones virtuales de impacto", 
            "facilitación de reuniones", "mentoring", "mentoring corporativo", 
            "mentoring energiza e impacta", "coaching", "job shadowing", "job crafting", 
            "aprendizaje en el trabajo", "performance learning", "optimización del talento", 
            "desarrollo sostenible", "impacto social", "aprendizaje personalizado", 
            "aprendizaje adaptativo", "gamificación", "aprendizaje gamificado", 
            "experiencias de aprendizaje", "experiencias transformadoras", "workshops", 
            "talleres", "programas corporativos", "soluciones de capacitación", 
            "capacitación estratégica", "formación estratégica", "aprendizaje estratégico", 
            "capacitación certificada", "clientes", "experiencia de cliente", "servicio al cliente", 
            "ventas", "habilidades comerciales", "manejo de clientes difíciles", "negociación", 
            "negociación influyente", "negociación influyente 2", "logrando tus metas comerciales", 
            "marca personal", "creando tu propio futuro", "planifica y logra tus objetivos", 
            "modelo canvas", "preguntas poderosas", "construyendo un lugar al que todos quieren pertenecer", 
            "creando espacios seguros", "creando espacios seguros ley karin", 
            "promoviendo la equidad de género", "liderando con inclusión", 
            "sé el arquitecto de una cultura inclusiva", "confianza digital", 
            "protección de datos personales", "ciberseguridad", "ciberseguridad en el trabajo", 
            "ia para todos", "comunicación humano máquina", "hábitos para teletrabajo efectivo", 
            "reuniones efectivas", "revoluciona tu trabajo con kanban", "libera tu potencial con lean", 
            "dominando el pensamiento crítico", "el secreto detrás de la excelencia", 
            "cultivando emociones positivas", "transformando la frustración", 
            "renovando tu mente", "irl aprendizaje experiencial"
        ]

    def clasificar_archivo(self, nombre_archivo):
        """Asigna una categoría al archivo basándose en su nombre."""
        nombre = nombre_archivo.lower()
        
        # 🎯 Posibles nombres para la parrila de cursos 
        if ("plan" in nombre and "capacitacion" in nombre) or "parrilla" in nombre or "nomina" in nombre or "nómina" in nombre:
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
        # Ordeno la lista en base al nombre
        planes_ordenados = sorted(lista_nombres_planes, key=self.extraer_fecha_de_nombre, reverse=True)
        
        ganador = planes_ordenados[0]
        logging.info(f"Archivo ganador seleccionado: {ganador}")
        return ganador

    def analizar_excel_cursos(self, ruta_excel):
        """Abre el Excel ganador, lee los cursos y busca las palabras clave."""
        logging.info(f"Analizando cursos en: {ruta_excel}")
        try:
            
            df = pd.read_excel(ruta_excel, skiprows=13)
            
            # Limpieza de nombres en la lista
            df.columns = df.columns.str.strip().str.lower()
            
            cursos_encontrados = []
            
            
            for index, fila in df.iterrows():
                
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
    
    # Simulacion de archivos
    archivos_encontrados = [
        "Acta-Apertura-Propuestas-1ra-licitacion-2026.pdf",
        "PLAN-DE-CAPACITACION-6TA-ANO-2025-con-correcciones.xlsx",
        "Parrilla-de-cursos-6to-llamado.xlsx", # <--- prueba para Sofofa
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