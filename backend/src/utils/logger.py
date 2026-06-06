import logging
import os
import sys
from core.config import LOG_FORMAT, LOG_LEVEL

def get_logger(name: str) -> logging.Logger:
    """
    Crea y configura un logger centralizado con salida a consola y archivo.
    """
    logger = logging.getLogger(name)
    
    # Evita que se dupliquen los logs si la función se llama múltiples veces
    if not logger.handlers:
        # 1. Configurar el nivel de log desde core/config.py
        level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(level)
        logger.propagate = False
        
        # 2. Configurar el formato desde core/config.py
        formatter = logging.Formatter(LOG_FORMAT)
        
        # 3. Handler para la consola (Terminal)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 4. Handler para archivo (Guarda en backend/logs/scraper.log)
        # Calcula la ruta base del backend (3 niveles arriba desde utils/logger.py)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logs_dir = os.path.join(base_dir, "logs")
        
        # Crea la carpeta logs/ si no existe
        os.makedirs(logs_dir, exist_ok=True)
        
        # Configura el archivo de salida
        file_handler = logging.FileHandler(
            os.path.join(logs_dir, "scraper.log"), 
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger
