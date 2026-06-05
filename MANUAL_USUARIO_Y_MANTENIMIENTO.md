# 📚 Manual de Usuario y Mantenimiento - Life-Box-Radar

## Tabla de Contenidos
- [Introducción](#introducción)
- [Manual de Usuario](#manual-de-usuario)
- [Guía de Mantenimiento del Código](#guía-de-mantenimiento-del-código)
- [Instalación y Configuración](#instalación-y-configuración)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Desarrollo y Contribuciones](#desarrollo-y-contribuciones)
- [Troubleshooting](#troubleshooting)

---

## Introducción

**Life-Box-Radar** es un sistema automatizado de vigilancia de licitaciones de capacitación en Chile. Rastrea múltiples portales OTIC para detectar nuevas oportunidades de formación, extrae información de documentos usando IA y notifica en tiempo real a través de Telegram.

### ¿Para quién es este documento?
- **Usuarios finales**: Personas que usan el dashboard y reciben notificaciones.
- **Desarrolladores**: Programadores que mantienen y extienden el código.
- **Administradores de sistemas**: Personas responsables de la infraestructura y configuración.

---

## Manual de Usuario

### 1. Acceder al Dashboard

El dashboard se ejecuta con Streamlit y proporciona una interfaz visual para:
- Ver licitaciones registradas
- Filtrar por estado, portal u otros criterios
- Analizar tendencias y estadísticas
- Exportar datos

**Para iniciar el dashboard:**

```bash
cd frontend
streamlit run app.py
```

El dashboard se abrirá en `http://localhost:8501`.

### 2. Funcionalidades del Dashboard

#### 📊 Panel Principal
- **Health Cards**: Estado de cada scraper (última ejecución, errores)
- **KPI Cards**: Número total de licitaciones, últimas 24h, tasa de actualización
- **Data Table**: Lista filtrable de licitaciones con opciones de búsqueda

#### 🔍 Filtros Disponibles
- **Portal**: Selecciona un portal específico (Proforma, OTIC, etc.)
- **Estado**: Vigente, Vencida, En evaluación
- **Rango de fechas**: Filtra por fecha de publicación o vencimiento
- **Tipo de capacitación**: Por categoría o palabras clave

#### 📥 Exportar Datos
- Descarga resultados en CSV
- Exporta reportes en PDF (próxima versión)

### 3. Recibir Notificaciones en Telegram

Las notificaciones se envían automáticamente cuando:
- Se detecta una nueva licitación
- Una licitación está próxima a vencer (7 días)
- Hay un error crítico en un scraper

**Para habilitar notificaciones:**
1. Crea un bot en Telegram (habla con `@BotFather`)
2. Obtén tu `TELEGRAM_TOKEN` y `TELEGRAM_CHAT_ID`
3. Configúralos en el archivo `.env` (ver sección Configuración)

**Formato de notificaciones:**
```
🎯 Nueva Licitación Detectada
Portal: Proforma
Título: Curso de Seguridad en Altura
Fecha de Publicación: 2026-06-04
Vencimiento: 2026-06-20
Acceso rápido: [Ver en portal]
```

### 4. Interpretación de los Datos

#### Estados de Licitación
- **Vigente**: Abierta y aceptando postulaciones
- **Vencida**: Fecha de cierre pasada
- **En Evaluación**: En proceso de análisis de propuestas
- **Desierta**: Sin postulaciones válidas

#### Health Status de Scrapers
- 🟢 **Exitoso**: Última ejecución sin errores
- 🟡 **Advertencia**: Ejecución con errores no críticos
- 🔴 **Error**: Última ejecución falló completamente

### 5. Casos de Uso Comunes

#### Caso 1: Buscar licitaciones de un portal específico
1. Abre el dashboard
2. Selecciona el portal en el filtro
3. Ordena por fecha más reciente
4. Haz clic en cualquier licitación para ver detalles

#### Caso 2: Exportar todas las licitaciones de este mes
1. Usa el filtro de rango de fechas
2. Selecciona "Este mes"
3. Haz clic en "Descargar CSV"
4. Abre el archivo en Excel/Google Sheets

#### Caso 3: Verificar salud de los scrapers
1. Ve al panel de "Health Cards"
2. Revisa la fecha/hora de última ejecución
3. Si hay errores, consulta los logs (próxima sección)

---

## Guía de Mantenimiento del Código

### 1. Estructura General del Proyecto

```
Life-Box-Radar/
├── backend/                          # Core de scrapers y lógica
│   ├── main_new.py                   # Punto de entrada principal
│   ├── requirements.txt               # Dependencias backend
│   └── src/
│       ├── core/                      # Configuración centralizada
│       │   └── config.py
│       ├── database/                  # Integración BigQuery
│       │   └── bq_client.py
│       ├── scrapers/                  # Scrapers de cada portal
│       │   ├── base_scraper.py        # Clase base compartida
│       │   ├── proforma.py
│       │   ├── otic.py
│       │   ├── agrocap.py
│       │   ├── banotic.py
│       │   ├── alianzapyme.py
│       │   ├── proaconcagua.py
│       │   └── oticsosofa.py
│       ├── services/                  # Servicios orquestadores
│       │   ├── scraper_service.py     # Ejecuta scrapers
│       │   ├── analysis_service.py    # IA y análisis
│       │   └── notification_service.py # Alertas Telegram
│       └── utils/                     # Utilidades compartidas
│           ├── document_parser.py     # Parseo de PDFs/Excels
│           ├── analizador_inteligente.py # IA/LLM
│           ├── logger.py              # Logging
│           └── alerts.py
├── frontend/                         # Dashboard Streamlit
│   ├── app.py                         # Punto de entrada
│   ├── dashboard.py                   # Lógica principal
│   ├── requirements.txt
│   ├── components/                    # Componentes reutilizables
│   │   ├── data_table.py
│   │   ├── health_cards.py
│   │   └── kpi_cards.py
│   ├── pages/                         # Páginas multi-página
│   ├── styles/                        # CSS personalizado
│   └── utils/
│       ├── config.py
│       ├── data_loader.py
│       ├── formatters.py
│       └── styles_loader.py
├── database/                         # Esquemas BigQuery
├── docs/                             # Documentación técnica
├── assets/                           # Imágenes, logos
└── .vscode/settings.json             # Configuración VS Code
```

### 2. Flujo de Datos

```
┌─────────────────────────────────────────────────────────┐
│                    BACKEND (Python)                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. main_new.py                                        │
│     └─> ScraperService.ejecutar()                      │
│                                                         │
│  2. Cada Scraper (otic.py, proforma.py, ...)         │
│     └─> Rasquea portal web → JSON/tabla               │
│                                                         │
│  3. DocumentParser                                     │
│     └─> Extrae fechas, cursos de PDFs/Excels         │
│                                                         │
│  4. AnalizadorInteligente (LLM)                       │
│     └─> Clasifica licitaciones, detecta relevancia    │
│                                                         │
│  5. BigQueryClient                                     │
│     └─> Almacena en Google Cloud                      │
│                                                         │
│  6. NotificationService                               │
│     └─> Envía alertas Telegram                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────────┐
│                   FRONTEND (Streamlit)                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. app.py          → Punto de entrada                 │
│  2. dashboard.py    → Lógica principal                 │
│  3. Components      → Tarjetas, tablas, gráficos       │
│  4. DataLoader      → Consulta BigQuery                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3. Tareas Comunes de Mantenimiento

#### 3.1 Agregar un nuevo scraper para un portal

**Pasos:**
1. Crea un archivo en `backend/src/scrapers/nuevo_portal.py`
2. Hereda de `BaseScraper`:
```python
from scrapers.base_scraper import BaseScraper

class NuevoPortalScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            name="Nuevo Portal",
            base_url="https://ejemplo.com"
        )
    
    def scrape(self):
        """Rasquea el portal y retorna lista de licitaciones."""
        try:
            # Tu lógica de scraping aquí
            licitaciones = self.driver.find_elements(...)
            return [self.parse_licitacion(lic) for lic in licitaciones]
        except Exception as e:
            self.logger.error(f"Error scraping: {e}")
            raise
    
    def parse_licitacion(self, element):
        """Parsea un elemento HTML a diccionario."""
        return {
            'titulo': element.find_element(...).text,
            'fecha': element.find_element(...).text,
            'url': element.get_attribute('href'),
            # ... más campos
        }
```

3. Registra el scraper en `backend/main_new.py`:
```python
from scrapers.nuevo_portal import NuevoPortalScraper

def get_scrapers():
    return [
        # ... scrapers existentes ...
        ("Nuevo Portal", NuevoPortalScraper()),
    ]
```

4. Prueba localmente:
```bash
cd backend
python -c "from src.scrapers.nuevo_portal import NuevoPortalScraper; s = NuevoPortalScraper(); print(s.scrape())"
```

#### 3.2 Modificar la lógica de análisis IA

El archivo `backend/src/utils/analizador_inteligente.py` contiene la lógica de clasificación.

**Para mejorar la clasificación:**
1. Edita el prompt de IA
2. Ajusta los parámetros (temperatura, max_tokens)
3. Prueba con datos de muestra:
```python
from src.utils.analizador_inteligente import AnalizadorInteligente

ai = AnalizadorInteligente()
resultado = ai.clasificar_licitacion({
    'titulo': 'Curso de Seguridad en Altura',
    'descripcion': '...'
})
print(resultado)
```

#### 3.3 Cambiar la configuración global

Edita `backend/src/core/config.py`:
```python
# Ejemplo: cambiar el dataset de BigQuery
BQ_DATASET = "licitaciones_nuevo"

# Ejemplo: agregar nuevo portal
PORTALES_ACTIVOS = [
    "proforma", "otic", "agrocap", "nuevo_portal"
]
```

#### 3.4 Depuración de errores de scraping

**Revisar logs:**
```bash
# Ver último error
tail -f backend/logs/scraper.log

# O en el código
from src.utils.logger import get_logger
logger = get_logger("mi_scraper")
logger.error("Mensaje de error detallado")
```

**Debugging interactivo:**
```python
# En un script de prueba
from src.scrapers.otic import OticScraperSelenium
scraper = OticScraperSelenium()
try:
    resultados = scraper.scrape()
    print(f"Éxito: {len(resultados)} licitaciones")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
```

#### 3.5 Actualizar dependencias

**Backend:**
```bash
cd backend
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt  # Guardar versiones actuales
```

**Frontend:**
```bash
cd frontend
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
```

### 4. Estándares de Código

#### 4.1 Convenciones de Nombres
- **Funciones/variables**: `snake_case` (ej: `obtener_licitaciones`)
- **Clases**: `PascalCase` (ej: `OticScraper`)
- **Constantes**: `UPPER_SNAKE_CASE` (ej: `MAX_RETRIES`)
- **Archivos privados**: prefijo `_` (ej: `_internal_helper.py`)

#### 4.2 Docstrings
Usa formato Google:
```python
def extraer_fecha(texto: str) -> datetime:
    """Extrae fecha del texto de una licitación.
    
    Args:
        texto: String con contenido de licitación
        
    Returns:
        datetime: Objeto de fecha parseado
        
    Raises:
        ValueError: Si no se encuentra una fecha válida
        
    Examples:
        >>> extraer_fecha("Vencimiento: 15-06-2026")
        datetime(2026, 6, 15)
    """
    # Implementación...
```

#### 4.3 Type Hints
Siempre incluye type hints:
```python
from typing import List, Dict, Optional

def procesar_licitaciones(
    licitaciones: List[Dict[str, any]],
    filtro: Optional[str] = None
) -> List[Dict]:
    """Procesa y filtra licitaciones."""
    pass
```

#### 4.4 Logging
```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

logger.debug("Mensaje de depuración")
logger.info("Información general")
logger.warning("Advertencia")
logger.error("Error:", exc_info=True)
```

### 5. Testing y Validación

#### 5.1 Escribir tests
```python
# tests/test_parsers.py
import pytest
from src.utils.document_parser import DocumentParser

def test_extrae_fecha_valida():
    parser = DocumentParser()
    resultado = parser.extraer_fecha("Cierre: 20-06-2026")
    assert resultado.day == 20
    assert resultado.month == 6

def test_maneja_formato_invalido():
    parser = DocumentParser()
    with pytest.raises(ValueError):
        parser.extraer_fecha("Fecha desconocida")
```

**Ejecutar tests:**
```bash
pip install pytest
pytest tests/
```

#### 5.2 Validación de esquemas
```python
# Valida que los datos tengan los campos esperados
from src.database.bq_client import BigQueryClient

def validar_licitacion(lic_dict: Dict) -> bool:
    campos_requeridos = ['titulo', 'fecha_publicacion', 'url']
    return all(campo in lic_dict for campo in campos_requeridos)
```

### 6. Monitoreo y Logs

#### Archivos de Log Importantes
```
backend/
├── logs/
│   ├── scraper.log           # Ejecución de scrapers
│   ├── analysis.log          # IA y análisis
│   ├── database.log          # Conexión BigQuery
│   └── notifications.log     # Alertas Telegram
```

**Interpretar logs:**
```
[2026-06-04 14:32:15] INFO    scraper_service.py - Iniciando scraping...
[2026-06-04 14:32:45] INFO    otic.py - ✅ 5 licitaciones encontradas
[2026-06-04 14:32:50] ERROR   proforma.py - ❌ Timeout en elemento
[2026-06-04 14:33:20] INFO    database.py - 📊 Insertadas 5 registros en BigQuery
```

---

## Instalación y Configuración

### 1. Requisitos Previos
- Python 3.8 o superior
- Git
- Acceso a Google Cloud (BigQuery)
- Token de Telegram Bot
- Conexión a internet

### 2. Instalación

**Clonar repositorio:**
```bash
git clone https://github.com/tu-usuario/Life-Box-Radar.git
cd Life-Box-Radar
```

**Crear entorno virtual:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

**Instalar dependencias:**
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend (en otra carpeta)
cd ../frontend
pip install -r requirements.txt
```

### 3. Configuración

**Crear archivo `.env` en la raíz del proyecto:**
1. Copia el archivo de ejemplo:
```bash
copy .env.example .env
```
2. Edita `.env` y reemplaza los valores:
```text
# Telegram
TELEGRAM_TOKEN=tu_token_de_bot
TELEGRAM_CHAT_ID=tu_chat_id

# Google Cloud
GCP_PROJECT_ID=proyecto-life-box-licitaciones
GCP_CREDENTIALS_PATH=credenciales_gcp.json
GOOGLE_APPLICATION_CREDENTIALS=credenciales_gcp.json

# Opcionales
DEBUG=False
LOG_LEVEL=INFO
```

**Obtener credenciales nuevas**

1. **Telegram**
   - Abre Telegram y crea un bot con `@BotFather`
   - Envía `/newbot` y sigue los pasos
   - Copia el token que te entregue `BotFather`
   - Recupera tu `TELEGRAM_CHAT_ID` enviando un mensaje al bot y consultando:
     ```bash
     curl "https://api.telegram.org/bot<token>/getUpdates"
     ```
   - Busca el campo `chat.id` en la respuesta JSON

2. **Google Cloud / BigQuery**
   - Ve a Google Cloud Console: https://console.cloud.google.com/
   - Crea o selecciona el proyecto `proyecto-life-box-licitaciones`
   - Abre IAM & Admin > Service Accounts
   - Crea una nueva cuenta de servicio
   - Asigna el rol `BigQuery User` o `BigQuery Data Editor`
   - Genera una clave JSON
   - Descarga el archivo y renómbralo a `credenciales_gcp.json`
   - Mueve el archivo a la raíz del proyecto

> Asegúrate de que `.env` y `credenciales_gcp.json` estén en `.gitignore` para no subirlos a Git.

### 4. Primer Ejecutar

**Backend:**
```bash
cd backend
python main_new.py
```

**Frontend:**
```bash
cd frontend
streamlit run app.py
```

---

## Estructura del Proyecto

### Carpeta `backend/src/core/`
**Responsabilidad**: Configuración centralizada

- `config.py`: Variables de entorno, constantes, credenciales

### Carpeta `backend/src/scrapers/`
**Responsabilidad**: Extracción de datos de portales

- `base_scraper.py`: Clase base con métodos comunes
- `[nombre_portal].py`: Implementación específica del portal

**Métodos clave:**
- `__init__()`: Inicializa Selenium y configuración
- `scrape()`: Extrae licitaciones
- `parse_licitacion()`: Convierte HTML a diccionario
- `close()`: Cierra navegador

### Carpeta `backend/src/database/`
**Responsabilidad**: Integración con Google BigQuery

- `bq_client.py`: Cliente para crear/insertar/consultar datos

**Métodos clave:**
- `crear_tablas()`: Crea esquemas si no existen
- `insertar_licitaciones()`: Bulk insert
- `consultar()`: SQL queries personalizadas

### Carpeta `backend/src/services/`
**Responsabilidad**: Orquestación y lógica de negocio

- `scraper_service.py`: Ejecuta todos los scrapers
- `analysis_service.py`: Procesa con IA
- `notification_service.py`: Envía alertas Telegram

### Carpeta `backend/src/utils/`
**Responsabilidad**: Utilidades compartidas

- `document_parser.py`: Parsea PDFs/Excels
- `analizador_inteligente.py`: Clasifica con LLM
- `logger.py`: Sistema de logging
- `alerts.py`: Formatea alertas

### Carpeta `frontend/`
**Responsabilidad**: Dashboard web interactivo

- `app.py`: Punto de entrada
- `dashboard.py`: Layout y lógica principal
- `components/`: Componentes reutilizables (tablas, gráficos)
- `pages/`: Páginas adicionales (multipage app)
- `utils/`: Helpers para datos y estilos

---

## Desarrollo y Contribuciones

### Workflow Recomendado

1. **Crear rama de feature:**
```bash
git checkout -b feature/nueva-funcionalidad
```

2. **Hacer cambios y testear:**
```bash
# Backend
cd backend
python -c "from src.scrapers.mimodulo import MiClase; MiClase().test()"

# Frontend
cd frontend
streamlit run app.py
```

3. **Commit y push:**
```bash
git add .
git commit -m "Add: nueva funcionalidad de X"
git push origin feature/nueva-funcionalidad
```

4. **Crear Pull Request en GitHub**

### Buenas Prácticas

✅ **HACER:**
- Comentar código complejo
- Usar nombres descriptivos
- Escribir docstrings
- Incluir type hints
- Hacer commits frecuentes con mensajes claros
- Testar antes de pushear

❌ **NO HACER:**
- Pushear a `main` directamente
- Commitear credenciales o `.env`
- Ignorar warnings de linting
- Escribir funciones >100 líneas sin dividir
- Dejar código comentado permanentemente

### Git Commit Messages

```
Formato: <tipo>: <descripción breve>

Tipos:
- add:  Nueva funcionalidad
- fix:  Corrección de bug
- docs: Cambios de documentación
- refactor: Mejora de código sin funcionalidad
- test: Agregar/actualizar tests
- chore: Tareas mantenimiento

Ejemplos:
add: Scraper para nuevo portal XYZ
fix: Manejo de timeout en Selenium
docs: Actualizar README con instrucciones
refactor: Extraer lógica común a BaseScraper
```

---

## Troubleshooting

### Problema: "No se ha podido resolver la importación"

**Causa**: `sys.path` no incluye `backend/src`

**Solución:**
1. Asegúrate de ejecutar desde `backend/`:
```bash
cd backend
python main_new.py
```

2. O configura `PYTHONPATH`:
```bash
# Windows
set PYTHONPATH=%PYTHONPATH%;.\src

# Mac/Linux
export PYTHONPATH="${PYTHONPATH}:./src"
```

### Problema: Selenium no encuentra elementos

**Causa**: El portal cambió de estructura HTML

**Solución:**
1. Abre el portal en navegador y revisa el HTML (F12)
2. Actualiza los selectores en el scraper:
```python
# Viejo selector (no funciona)
element = self.driver.find_element("css selector", ".licitacion-titulo")

# Nuevo selector (actualizado)
element = self.driver.find_element("css selector", ".titulo-licitacion-v2")
```

3. Prueba localmente antes de pushear

### Problema: Timeout en BigQuery

**Causa**: Conexión lenta o credenciales inválidas

**Solución:**
1. Verifica credenciales en `credenciales_gcp.json`
2. Aumenta timeout:
```python
from src.database.bq_client import BigQueryClient
client = BigQueryClient(timeout=60)
```

3. Revisa estado de Google Cloud Console

### Problema: Telegram no envía notificaciones

**Causa**: Token o Chat ID inválidos

**Solución:**
1. Verifica `.env`:
```bash
TELEGRAM_TOKEN=correctamente_copiado
TELEGRAM_CHAT_ID=numero_sin_errores
```

2. Prueba con curl:
```bash
curl -X POST https://api.telegram.org/bot{TOKEN}/sendMessage \
  -d chat_id={CHAT_ID} \
  -d text="Test"
```

3. Revisa que el bot tiene permisos en el chat

### Problema: Dashboard Streamlit lento

**Causa**: Muchas consultas a BigQuery o datos sin cachear

**Solución:**
```python
import streamlit as st

# Cachea datos por 5 minutos
@st.cache_data(ttl=300)
def cargar_licitaciones():
    return consultar_bq()

# Uso
df = cargar_licitaciones()
```

### Problema: Error "Webdriver no encontrado"

**Causa**: Selenium no encuentra Chrome/Firefox

**Solución:**
1. Instala ChromeDriver:
```bash
# Mac (con brew)
brew install chromedriver

# Windows (manual)
# Descarga de https://chromedriver.chromium.org/
# Coloca en PATH
```

2. O especifica ruta en scraper:
```python
from selenium import webdriver
driver = webdriver.Chrome("/ruta/a/chromedriver")
```

---

## Soporte y Contacto

- **Issues**: Reporta bugs en GitHub Issues
- **Documentación técnica**: Ver carpeta `docs/`
- **Preguntas**: Abre una discussion en GitHub

---

**Última actualización**: 4 de junio de 2026  
**Versión**: 1.0.0
