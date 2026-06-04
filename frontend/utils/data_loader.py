"""
Data loader utility: Load and cache BigQuery data.
"""
import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from google.cloud import bigquery
import os


class DataLoader:
    """BigQuery data loading and caching."""
    
    def __init__(self, project_id, credentials_path):
        """Initialize BigQuery client."""
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.credentials = None
        self.client = None
    
    def conectar(self):
        """Connect to BigQuery."""
        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path
            )
            self.client = bigquery.Client(
                project=self.project_id,
                credentials=self.credentials
            )
            return True
        except Exception as e:
            st.error(f"❌ BigQuery connection error: {e}")
            return False
    
    @st.cache_data(ttl=300)
    def cargar_oportunidades(_self):
        """Load active and expired opportunities."""
        try:
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
            return df_stats.iloc[0].to_dict()
        
        except Exception as e:
            st.warning(f"⚠️ Cannot load statistics: {e}")
            return {}
