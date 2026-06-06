"""
Data loader utility: Load and cache BigQuery data.
"""
import os
import sqlite3

import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from google.cloud import bigquery

from utils.config import USE_LOCAL_DB, LOCAL_DB_PATH

class DataLoader:
    """BigQuery data loading and caching with optional SQLite fallback."""
    
    def __init__(self, project_id, credentials_path, sqlite_path=LOCAL_DB_PATH):
        """Initialize BigQuery and optional SQLite client."""
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.sqlite_path = sqlite_path
        self.credentials = None
        self.client = None
        self.use_sqlite = False
        self.sqlite_conn = None

    def conectar(self):
        """Connect to BigQuery, or fallback to SQLite when unavailable."""
        # 1. Si el .env dice que usemos base de datos local, omitimos BigQuery
        if USE_LOCAL_DB:
            self.use_sqlite = True
            os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
            self.sqlite_conn = sqlite3.connect(self.sqlite_path, check_same_thread=False)
            self.sqlite_conn.row_factory = sqlite3.Row
            self._ensure_sqlite_schema()
            return True
            
        # 2. Intentar conectar a BigQuery si USE_LOCAL_DB es False
        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path
            )
            self.client = bigquery.Client(
                project=self.project_id,
                credentials=self.credentials
            )
            self.use_sqlite = False
            return True
        except Exception as e:
            st.warning(f"⚠️ BigQuery connection failed, usando SQLite local: {e}")
            self.use_sqlite = True
            os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
            self.sqlite_conn = sqlite3.connect(self.sqlite_path, check_same_thread=False)
            self.sqlite_conn.row_factory = sqlite3.Row
            self._ensure_sqlite_schema()
            return True

    def _ensure_sqlite_schema(self):
        self.sqlite_conn.execute(
            """
            CREATE TABLE IF NOT EXISTS oportunidades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_deteccion TEXT,
                titulo_llamado_web TEXT,
                origen_web TEXT,
                palabra_clave TEXT,
                curso TEXT,
                region TEXT,
                comuna TEXT,
                cupos INTEGER,
                horas INTEGER,
                fecha_cierre TEXT,
                estado TEXT,
                link_documento TEXT,
                fila INTEGER DEFAULT 0
            )
            """
        )
        self.sqlite_conn.execute(
            """
            CREATE TABLE IF NOT EXISTS estado_scrapers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portal TEXT,
                estado TEXT,
                mensaje TEXT,
                fecha_ejecucion TEXT
            )
            """
        )
        self.sqlite_conn.commit()

    def _read_sqlite(self, query):
        return pd.read_sql_query(query, self.sqlite_conn)

    @st.cache_data(ttl=300)
    def cargar_oportunidades(_self):
        """Load active and expired opportunities."""
        try:
            if _self.use_sqlite:
                query_vencidos = "SELECT *, 'Vencido' as estado_filtro FROM oportunidades WHERE estado = 'Vencido'"
                query_vigentes = "SELECT *, 'Vigente' as estado_filtro FROM oportunidades WHERE estado != 'Vencido'"
                df_vencidos = _self._read_sqlite(query_vencidos)
                df_vigentes = _self._read_sqlite(query_vigentes)
            else:
                query_vencidos = f"""
                    SELECT *, 'Vencido' as estado_filtro
                    FROM `{_self.project_id}.licitaciones.oportunidades`
                    WHERE estado = 'Vencido'
                """
                query_vigentes = f"""
                    SELECT *, 'Vigente' as estado_filtro
                    FROM `{_self.project_id}.licitaciones.oportunidades`
                    WHERE estado != 'Vencido'
                """
                df_vencidos = pd.read_gbq(query_vencidos, project_id=_self.project_id, credentials=_self.credentials)
                df_vigentes = pd.read_gbq(query_vigentes, project_id=_self.project_id, credentials=_self.credentials)
            return df_vigentes, df_vencidos
        except Exception as e:
            st.error(f"❌ Load error: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    @st.cache_data(ttl=300)
    def cargar_estado_scrapers(_self):
        """Load scraper health status."""
        try:
            if _self.use_sqlite:
                query = "SELECT * FROM estado_scrapers ORDER BY fecha_ejecucion DESC LIMIT 1000"
                df_estado = _self._read_sqlite(query)
            else:
                query = f"""
                    SELECT *
                    FROM `{_self.project_id}.licitaciones.estado_scrapers`
                    ORDER BY fecha_ejecucion DESC
                    LIMIT 1000
                """
                df_estado = pd.read_gbq(query, project_id=_self.project_id, credentials=_self.credentials)
            return df_estado
        except Exception as e:
            st.warning(f"⚠️ Cannot load scraper status: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=300)
    def cargar_estadisticas(_self):
        """Load general statistics."""
        try:
            if _self.use_sqlite:
                query = """
                    SELECT 
                        COUNT(DISTINCT link_documento) as total_licitaciones,
                        COUNT(*) as total_oportunidades,
                        COUNT(DISTINCT origen_web) as total_portales,
                        SUM(CAST(cupos AS INTEGER)) as total_cupos,
                        COUNT(DISTINCT region) as total_regiones
                    FROM oportunidades
                    WHERE estado != 'Vencido'
                """
                df_stats = _self._read_sqlite(query)
            else:
                query = f"""
                    SELECT 
                        COUNT(DISTINCT link_documento) as total_licitaciones,
                        COUNT(*) as total_oportunidades,
                        COUNT(DISTINCT origen_web) as total_portales,
                        SUM(CAST(cupos AS INT64)) as total_cupos,
                        COUNT(DISTINCT region) as total_regiones
                    FROM `{_self.project_id}.licitaciones.oportunidades`
                    WHERE estado != 'Vencido'
                """
                df_stats = pd.read_gbq(query, project_id=_self.project_id, credentials=_self.credentials)
            return df_stats.iloc[0].to_dict() if not df_stats.empty else {}
        except Exception as e:
            st.warning(f"⚠️ Cannot load statistics: {e}")
            return {}
