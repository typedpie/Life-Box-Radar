# 🚀 Backend - Life-Box-Radar

## Descripción
Motor de scraping y análisis de licitaciones. Extrae datos de múltiples portales OTIC, los procesa con IA y los almacena en BigQuery.

## Estructura

```
backend/
├── src/
│   ├── scrapers/           # Módulos de extracción por portal
│   │   ├── proforma.py
│   │   ├── otic.py
│   │   ├── proaconcagua.py
│   │   ├── agrocap.py
│   │   ├── banotic.py
│   │   ├── alianzapyme.py
│   │   ├── oticsosofa.py
│   │   └── base_scraper.py
│   │
│   ├── database/           # Conexión con BigQuery
│   │   └── bq_client.py
│   │
│   └── utils/              # Herramientas de soporte
│       ├── analizador_inteligente.py  # IA para clasificación
│       ├── document_parser.py         # Extracción de PDF/Excel
│       ├── alerts.py
│       └── logger.py
│
├── main.py                 # Orquestador principal
└── requirements.txt        # Dependencias
```

## Instalación

```bash
cd backend
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

## Funcionalidad

1. **Scraping**: Extrae enlaces de 7 portales OTIC
2. **Clasificación**: Identifica planes de capacitación (Excels)
3. **Análisis IA**: Lee y extrae cursos clave del Excel
4. **Validación**: Comprueba si la licitación está vencida
5. **Inyección**: Almacena datos en BigQuery
6. **Notificaciones**: Envía alertas por Telegram

## Variables de Entorno Requeridas

```
TELEGRAM_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx
```

## Dependencias Principales

- `pandas`: Manipulación de datos
- `selenium`: Web scraping
- `google-cloud-bigquery`: Base de datos
- `PyPDF2`: Extracción de PDFs
- `requests`: HTTP requests

## Portales Monitoreados

1. Proforma
2. OTIC
3. Pro Aconcagua
4. Agrocap
5. Banotic
6. Alianza Pyme
7. OTIC Sofofa

## Observaciones

- Los scrapers tienen manejo de errores robusto
- Registra estado de salud en BigQuery
- Mantiene historial de documentos procesados
- Compatible con carpetas de Drive (alerta manual)
