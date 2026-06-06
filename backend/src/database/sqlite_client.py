"""
SQLite local storage for scraped opportunities and scraper health.
"""
import os
import sqlite3
import pandas as pd
from core.config import LOCAL_DB_PATH


class SQLiteClient:
    def __init__(self, db_path=LOCAL_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self):
        self.conn.execute(
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
        self.conn.execute(
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
        self.conn.commit()

    def insert_oportunidades(self, df: pd.DataFrame):
        if df.empty:
            return False
        df.to_sql("oportunidades", self.conn, if_exists="append", index=False)
        return True

    def insert_estado_scrapers(self, df: pd.DataFrame):
        if df.empty:
            return False
        df.to_sql("estado_scrapers", self.conn, if_exists="append", index=False)
        return True

    def query(self, sql: str) -> pd.DataFrame:
        return pd.read_sql_query(sql, self.conn)

    def close(self):
        self.conn.close()
