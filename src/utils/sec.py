import requests
import sys
import logging

def verificar_lic():
    
    url_licencia = "URL_GIST"
    
    try:
        respuesta = requests.get(url_licencia, timeout=5).text.strip()
        if respuesta != "ACTIVO":
            logging.error("🚨 Expirado")
            sys.exit(1)
    except Exception as e:
        
        logging.error(f"Error de validación de lic: {e}")
        sys.exit(1)