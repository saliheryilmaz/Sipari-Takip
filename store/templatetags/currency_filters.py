from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def turkish_currency(value):
    """
    Türkçe para formatı: 4000.00 -> 4.000,00 ₺
    """
    if value is None:
        return "0,00 ₺"
    
    try:
        # Sayıyı float'a çevir
        num = float(value)
        
        # Binlik ayırıcı ile formatla
        formatted = f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        return f"₺{formatted}"
    except (ValueError, TypeError):
        return "0,00 ₺"

@register.filter
def turkish_number(value):
    """
    Türkçe sayı formatı: 4000 -> 4.000
    """
    if value is None:
        return "0"
    
    try:
        # Sayıyı int'e çevir
        num = int(float(value))
        
        # Binlik ayırıcı ile formatla
        formatted = f"{num:,}".replace(",", ".")
        
        return formatted
    except (ValueError, TypeError):
        return "0"

