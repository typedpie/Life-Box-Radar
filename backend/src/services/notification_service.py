"""
Notification service: Telegram alerts and BigQuery health logging.
"""
import logging
import requests
import pandas as pd
from core.config import TELEGRAM_TOKEN, TIMEZONE
from database.bq_client import BigQueryClient

logger = logging.getLogger(__name__)


class NotificationService:
    """Centralized notification manager for Telegram and BigQuery."""
    
    def __init__(self):
        """Initialize Telegram client with token."""
        self.telegram_token = TELEGRAM_TOKEN
        self.telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    def enviar_notificacion_licitacion(self, titulo, cantidad, portal, link_especial=None):
        """Send Telegram notification for new tender."""
        if not self.telegram_token:
            logger.error("⚠️ Missing Telegram credentials")
            return False
        
        if link_especial:
            contenido = (
                f"🚨 <b>¡NUEVA PUBLICACIÓN EN {portal.upper()}!</b> 🚨\n"
                f"Proceso: <b>{titulo}</b>\n"
                f"⚠️ <i>Manual review required:</i> {link_especial}"
            )
        else:
            contenido = (
                f"🚨 <b>¡NUEVA LICITACIÓN EN {portal.upper()}!</b> 🚨\n"
                f"Proceso: <b>{titulo}</b>\n"
                f"🎯 Injected <b>{cantidad}</b> opportunities."
            )
        
        return self._enviar_mensaje_telegram(contenido, "HTML")
    
    def enviar_alerta_error(self, portal, mensaje_error):
        """Send critical alert when scraper fails."""
        if not self.telegram_token:
            logger.error("⚠️ Missing Telegram credentials")
            return False
        
        error_corto = str(mensaje_error)[:200]
        contenido = (
            f"🚨 *SCRAPER CRITICAL ALERT!* 🚨\n\n"
            f"🛑 *Failed Portal:* {portal}\n"
            f"⚠️ *Reason:* `{error_corto}...`\n\n"
            f"🛠️ _Check if portal design changed._"
        )
        
        return self._enviar_mensaje_telegram(contenido, "Markdown")
    
    def _enviar_mensaje_telegram(self, contenido, parse_mode="HTML"):
        """Send message to Telegram API."""
        try:
            from core.config import TELEGRAM_CHAT_ID
            
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": contenido,
                "parse_mode": parse_mode
            }
            
            url = f"{self.telegram_url}/sendMessage"
            respuesta = requests.post(url, json=payload)
            
            if respuesta.status_code == 200:
                logger.info("✅ Notification sent")
                return True
            else:
                logger.error(f"❌ Telegram rejected: {respuesta.text}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False
    
    def registrar_estado_scraper(self, portal, estado, mensaje="Funcionando correctamente"):
        """Register scraper health status to BigQuery."""
        try:
            df_estado = pd.DataFrame([{
                "fecha_ejecucion": pd.Timestamp.now(TIMEZONE),
                "portal": portal,
                "estado": estado,
                "mensaje": str(mensaje)
            }])
            
            cliente = BigQueryClient(
                "proyecto-life-box-licitaciones",
                "licitaciones",
                "estado_scrapers",
                "credenciales_gcp.json"
            )
            
            cliente.inyectar_datos(df_estado)
            logger.info(f"✅ Status {estado} for {portal}")
            return True
        
        except Exception as e:
            logger.error(f"❌ BigQuery error: {e}")
            return False
