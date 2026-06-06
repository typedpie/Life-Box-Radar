# 📊 Frontend - Life-Box-Radar

## Descripción
Dashboard interactivo con Streamlit que visualiza las licitaciones detectadas desde BigQuery en tiempo real.

## Instalación

```bash
cd frontend
pip install -r requirements.txt
```

## Uso

```bash
streamlit run app.py
```

O también puedes ejecutar:

```bash
streamlit run dashboard.py
```

El dashboard se abrirá en `http://localhost:8501`

## Características

- **Live View**: Auto-actualiza cada 5 minutos
- **KPIs**: Métricas en tiempo real
- **Filtros**: Por portal, región, estado
- **Visualizaciones**: Tablas y gráficos
- **Responsive**: Compatible con móvil y desktop

## Dependencias

- `streamlit`: Framework web
- `pandas`: Análisis de datos
- `google-cloud-bigquery`: Conexión a BD
- `streamlit-autorefresh`: Auto-actualización

## Archivos

- `app.py`: Aplicación principal
- `dashboard.py`: Entrypoint wrapper que lanza `app.py`
- `components/`: Componentes reutilizables de UI
- `utils/`: Configuración y carga de datos

## Temas

El dashboard soporta temas claro y oscuro de Streamlit.

## Credenciales

Requiere `credenciales_gcp.json` en el mismo directorio para conectar con BigQuery.
