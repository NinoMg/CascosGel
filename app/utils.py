import re
from datetime import date, timedelta

def limpiar_telefono_whatsapp(telefono: str) -> str:
    """
    Limpia un número de teléfono dejando solo dígitos 
    y agrega el prefijo internacional de Argentina (549) si no lo tiene.
    """
    if not telefono:
        return ""
    
    # Extraer solo los números
    numeros = re.sub(r'\D', '', telefono)
    
    # Si empieza con 0 (ej: 02604123456), quitar el 0 inicial
    if numeros.startswith('0'):
        numeros = numeros[1:]
        
    # Si no incluye el código de país (549), agregarlo
    if not numeros.startswith('549'):
        numeros = f"549{numeros}"
        
    return numeros

def generar_link_whatsapp(telefono: str, paciente_nombre: str, casco_codigo: str, fecha_vencimiento: str) -> str:
    """
    Genera la URL directa para abrir WhatsApp Web / App con un mensaje predeterminado.
    """
    num_limpio = limpiar_telefono_whatsapp(telefono)
    if not num_limpio:
        return ""
        
    mensaje = (
        f"Hola {paciente_nombre}, te escribimos de la Fundación Oncológica "
        f"para coordinar el seguimiento/devolución del casco de gel ({casco_codigo}) "
        f"prestado, cuyo vencimiento es el {fecha_vencimiento}. ¡Muchas gracias!"
    )
    
    # Codificar el texto para URL
    from urllib.parse import quote
    return f"https://wa.me/{num_limpio}?text={quote(mensaje)}"

def calcular_fecha_vencimiento(fecha_inicio: date, periodo_str: str) -> date:
    """
    Calcula la fecha de vencimiento según el texto ingresado en 'periodo' 
    o un valor por defecto de 6 meses (180 días).
    """
    dias = 180  # Por defecto 6 meses
    
    if "3" in periodo_str:
        dias = 90
    elif "12" in periodo_str or "1 año" in periodo_str.lower():
        dias = 365
    elif "1" in periodo_str and "mes" in periodo_str.lower():
        dias = 30
        
    return fecha_inicio + timedelta(days=dias)
