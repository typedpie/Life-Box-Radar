# 🎯 Life-Box-Radar

Sistema automatizado de **vigilancia de licitaciones de capacitación** en Chile. Rastrea múltiples portales OTIC para detectar nuevas oportunidades de formación.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Stack Tecnológico](#stack-tecnológico)
- [Inicio Rápido](#inicio-rápido)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Configuración](#configuración)
- [Documentación](#documentación)

## ✨ Características

✅ **Monitoreo Multi-Portal**: Rastrea 7 portales OTIC simultáneamente  
✅ **Análisis IA**: Clasifica documentos y extrae información automáticamente  
✅ **Extracción Inteligente**: Lee PDFs y Excels para obtener fechas y cursos  
✅ **Validación de Vigencia**: Ignora licitaciones vencidas  
✅ **Notificaciones Telegram**: Alertas en tiempo real de nuevas oportunidades  
✅ **Dashboard Interactivo**: Visualiza datos en tiempo real con Streamlit  
✅ **BigQuery Integration**: Base de datos escalable en Google Cloud  
✅ **Monitoreo de Salud**: Registra estado de cada scraper  

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| **Backend** | Python, Selenium, Pandas |
| **Frontend** | Streamlit |
| **Database** | Google BigQuery |
| **Notificaciones** | Telegram API |
| **Hosting** | Google Cloud (GCP) |

## 🚀 Inicio Rápido

### Prerrequisitos
- Python 3.8+
- Git
- Cuenta Google Cloud con BigQuery habilitado
- Token de Telegram Bot

### 1. Clonar repositorio

```bash
git clone https://github.com/typedpie/Life-Box-Radar.git
cd Life-Box-Radar
```

### 2. Configurar credenciales

Descarga tu `credenciales_gcp.json` desde Google Cloud Console y colócalo en la raíz.

### 3. Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 4. Frontend (en otra terminal)

```bash
cd frontend
pip install -r requirements.txt
streamlit run dashboard.py
```

Accede a: `http://localhost:8501`

## 📁 Estructura del Proyecto

```
Life-Box-Radar/
├── 🔧 backend/              # Motor de scraping y análisis
│   ├── src/
│   │   ├── scrapers/        # Extractores por portal
│   │   ├── database/        # Cliente BigQuery
│   │   └── utils/           # Análisis IA y parseo
│   ├── main.py              # Orquestador principal
│   ├── requirements.txt
│   └── README.md
│
├── 📊 frontend/             # Dashboard Streamlit
│   ├── dashboard.py
│   ├── requirements.txt
│   └── README.md
│
├── 🗄️ database/             # Documentación BigQuery
│   └── README.md
│
├── 📚 docs/                 # Documentación del proyecto
│   ├── README.md
│   └── ESTRUCTURA.md
│
├── 🎨 assets/               # Logos e imágenes
│   ├── logo_lifebox.png
│   ├── logo_radar.png
│   └── logo_udd.png
│
├── ⚙️ .github/              # GitHub Actions
│   └── workflows/
│       └── motor.yml        # CI/CD
│
├── .gitignore
├── credenciales_gcp.json    # GCP credentials (⚠️ NO COMMITEAR)
└── .env                     # Variables de entorno (⚠️ NO COMMITEAR)
```

## ⚙️ Configuración

### Variables de Entorno

Copia el archivo de ejemplo `.env.example` a `.env` en la raíz del proyecto y completa las credenciales:

```bash
copy .env.example .env
```

Edita `.env` y reemplaza los valores:

```text
TELEGRAM_TOKEN=tu_token_de_bot
TELEGRAM_CHAT_ID=tu_chat_id
GCP_PROJECT_ID=proyecto-life-box-licitaciones
GCP_CREDENTIALS_PATH=credenciales_gcp.json
GOOGLE_APPLICATION_CREDENTIALS=credenciales_gcp.json
```

> No subas `.env` ni `credenciales_gcp.json` al repositorio. Ambos están ignorados en `.gitignore`.

### Obtener credenciales nuevas

1. **Telegram**
   - Abre Telegram y habla con `@BotFather`
   - Escribe `/newbot` y sigue las instrucciones
   - Copia el token que te entrega `BotFather`
   - Para obtener `TELEGRAM_CHAT_ID`, abre una conversación con tu bot y usa `https://api.telegram.org/bot<token>/getUpdates`

2. **Google Cloud**
   - Entra a Google Cloud Console: https://console.cloud.google.com/
   - Ve al proyecto `proyecto-life-box-licitaciones` o crea uno nuevo
   - Abre IAM & Admin > Service Accounts
   - Crea una cuenta de servicio con rol `BigQuery User` o `BigQuery Data Editor`
   - Genera una clave JSON y descárgala como `credenciales_gcp.json`
   - Guarda el archivo en la raíz del proyecto

### BigQuery Project

```
Project ID: proyecto-life-box-licitaciones
Dataset: licitaciones
Tables: oportunidades, estado_scrapers
```

## 📖 Documentación

| Carpeta | Descripción |
|---------|-----------|
| [backend/README.md](backend/README.md) | Guía del motor de scraping |
| [frontend/README.md](frontend/README.md) | Guía del dashboard |
| [database/README.md](database/README.md) | Esquema de BigQuery |
| [docs/ESTRUCTURA.md](docs/ESTRUCTURA.md) | Detalles de la estructura |

## 🔍 Portales Monitoreados

1. **Proforma**
2. **OTIC**
3. **Pro Aconcagua**
4. **Agrocap**
5. **Banotic**
6. **Alianza Pyme**
7. **OTIC Sofofa**

## 📊 Flujo de Ejecución

```
main.py
  ├─→ Obtener historial de BigQuery
  ├─→ Para cada portal:
  │   ├─ Scraper: Extraer enlaces
  │   ├─ Clasificación: Filtrar por tipo
  │   ├─ PDF Parser: Extraer fecha de cierre
  │   ├─ Validar vigencia
  │   ├─ Excel Parser (IA): Extraer cursos
  │   ├─ BigQuery: Inyectar datos
  │   └─ Telegram: Notificar
  └─→ Registrar estado de salud
```

## 🔐 Seguridad

⚠️ **Archivos confidenciales (NO COMMITEAR)**:
- `credenciales_gcp.json`
- `.env`

Estos archivos están en `.gitignore`

## 📝 Notas Importantes

- Las notificaciones se envían en **HTML** para mejor formato
- Los errores de scraper envían alerta inmediata
- La lógica de vencimiento usa zona horaria **America/Santiago**
- BigQuery registra un "fila fantasma" para mantener memoria de documentos

## 🚧 Próximas Mejoras

- [ ] Tests unitarios
- [ ] Documentación API completa
- [ ] Docker setup
- [ ] CI/CD improvements
- [ ] Caché en Redis
- [ ] Logging más estructurado

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📧 Contacto

Para más información, contacta al equipo de LifeBox UDD.

---

**Última actualización**: Junio 2026
