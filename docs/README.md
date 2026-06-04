proyecto_lifebox/
│
├── src/                        # Carpeta principal del código fuente
│   ├── scrapers/               # Módulos de extracción específicos por OTIC
│   │   ├── __init__.py
│   │   ├── base_scraper.py     # Clase base con funciones comunes (request, headers)
│   │   └── proforma.py         # Script exclusivo para extraer datos de OTIC Proforma
│   │
│   ├── database/               # Lógica de conexión y manipulación de datos
│   │   ├── __init__.py
│   │   └── bq_client.py        # Módulo para interactuar con Google BigQuery
│   │
│   └── utils/                  # Herramientas de soporte
│       ├── __init__.py
│       ├── logger.py           # Sistema de registro de errores y eventos
│       └── alerts.py           # Módulo para disparar notificaciones (correo/Slack)
│   
│                    
├── main.py                     # Orquestador central (Ejecuta los scrapers y compara datos)
├── .env                        # Variables de entorno (Credenciales, contraseñas, tokens)
├── .gitignore                  # Archivos que no se subirán al repositorio (ej. .env, __pycache__)
├── requirements.txt            # Listado de librerías de Python requeridas
└── README.md                   # Documentación técnica del proyecto



streamlit run dashboard.py