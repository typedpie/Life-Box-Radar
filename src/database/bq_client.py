import os
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BigQueryClient:
    def __init__(self, project_id, dataset_id, table_id, credentials_path):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        
        # 1. AUTENTICACIÓN
        if not os.path.exists(credentials_path):
            logging.error(f"🚨 No se encontró el archivo de credenciales en: {credentials_path}")
        else:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            
        #Ruta hacia tabla
        self.destination_table = f"{self.dataset_id}.{self.table_id}"

    def inyectar_datos(self, df):
        """Recibe un DataFrame de Pandas y lo inserta en la tabla de BigQuery."""
        if df.empty:
            logging.warning("El DataFrame está vacío. No hay nada que subir a BigQuery.")
            return False

        try:
            logging.info(f"Conectando a Google Cloud... Subiendo {len(df)} filas a {self.destination_table}")
            
            #Inyectar a bigquery
            
            df.to_gbq(
                destination_table=self.destination_table,
                project_id=self.project_id,
                if_exists='append' 
            )
            
            logging.info("✅ ¡Inyección exitosa! Los datos ya están en la nube.")
            return True
            
        except Exception as e:
            logging.error(f"❌ Falló la inyección a BigQuery: {e}")
            return False