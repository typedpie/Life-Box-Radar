"""
Formatter utility: Data formatting and presentation.
"""
import pandas as pd
from datetime import datetime


class Formatter:
    """Data formatting utilities."""
    
    @staticmethod
    def formato_fecha(fecha):
        """Format date as dd/mm/yyyy."""
        if isinstance(fecha, str):
            try:
                fecha = pd.to_datetime(fecha)
            except:
                return fecha
        
        return fecha.strftime('%d/%m/%Y') if fecha else "N/A"
    
    @staticmethod
    def formato_fecha_hora(fecha):
        """Format date and time as dd/mm/yyyy HH:MM:SS."""
        if isinstance(fecha, str):
            try:
                fecha = pd.to_datetime(fecha)
            except:
                return fecha
        
        return fecha.strftime('%d/%m/%Y %H:%M:%S') if fecha else "N/A"
    
    @staticmethod
    def formato_numero(numero, decimales=0):
        """Format number with thousands separator."""
        try:
            numero = float(numero)
            return f"{numero:,.{decimales}f}"
        except:
            return str(numero)
    
    @staticmethod
    def formato_moneda(numero):
        """Format as Chilean currency."""
        try:
            numero = float(numero)
            return f"${numero:,.0f}"
        except:
            return str(numero)
    
    @staticmethod
    def truncar_texto(texto, limite=50):
        """Truncate text to character limit."""
        if len(str(texto)) > limite:
            return str(texto)[:limite] + "..."
        return str(texto)
    
    @staticmethod
    def estado_badge(estado):
        """Return HTML badge for status."""
        estados = {
            "Activo": ("✅ Active", "success"),
            "Vencido": ("❌ Expired", "error"),
            "Revisión Manual": ("⚠️ Manual", "warning")
        }
        
        if estado in estados:
            texto, tipo = estados[estado]
            return f'<span class="badge badge-{tipo}">{texto}</span>'
        
        return f'<span class="badge">{estado}</span>'
    
    @staticmethod
    def portal_badge(portal):
        """Return badge with portal icon."""
        iconos = {
            "Proforma": "🏢",
            "OTIC": "🏭",
            "Pro Aconcagua": "🌄",
            "Agrocap": "🌾",
            "Banotic": "🏦",
            "Alianza Pyme": "💼",
            "OTIC Sofofa": "🏗️"
        }
        
        icono = iconos.get(portal, "📌")
        return f"{icono} {portal}"
    
    @staticmethod
    def preparar_dataframe_vista(df, columnas_mostrar=None):
        """Prepare DataFrame for display."""
        if df.empty:
            return df
        
        df_mostrar = df.copy()
        
        # Format dates
        for col in df_mostrar.columns:
            if 'fecha' in col.lower():
                df_mostrar[col] = df_mostrar[col].apply(Formatter.formato_fecha)
        
        # Truncate long text
        for col in ['titulo_llamado_web', 'curso', 'palabra_clave']:
            if col in df_mostrar.columns:
                df_mostrar[col] = df_mostrar[col].apply(
                    lambda x: Formatter.truncar_texto(str(x), 40)
                )
        
        return df_mostrar
