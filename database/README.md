# 📊 Database - BigQuery Configuration

## Overview
This folder contains the database configuration and BigQuery setup for the Life-Box-Radar project.

## Schema Tables

### `licitaciones.oportunidades`
Main table storing all detected opportunities:
- `palabra_clave`: Keywords
- `curso`: Course name
- `region`: Region
- `comuna`: Municipality
- `cupos`: Available spots
- `horas`: Hours
- `modalidad`: Modality (online/presencial)
- `link_documento`: Document link
- `fecha_deteccion`: Detection date
- `origen_web`: Portal source
- `titulo_llamado_web`: Web title
- `fecha_cierre`: Closing date
- `estado`: Status (Activo/Vencido/Revisión Manual)

### `licitaciones.estado_scrapers`
Scraper health monitoring:
- `fecha_ejecucion`: Execution timestamp
- `portal`: Portal name
- `estado`: Status (OK/ERROR)
- `mensaje`: Status message

## Project ID
```
proyecto-life-box-licitaciones
```

## Authentication
Uses Google Cloud service account credentials: `credenciales_gcp.json`

## Notes
- All timestamps use America/Santiago timezone
- Date format: YYYY-MM-DD
