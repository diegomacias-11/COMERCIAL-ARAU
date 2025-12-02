from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def pct(value, decimals=0):
    try:
        d = Decimal(value) * Decimal(100)
        decs = int(decimals)
        s = f"{d:.{decs}f}"
        if decs == 0:
            s = s.split(".")[0]
        return f"{s}%"
    except Exception:
        return ""


@register.filter
def currency(value, decimals=2, symbol="$"):
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return ""
    try:
        decs = int(decimals)
    except Exception:
        decs = 2
    fmt = f"{{:,.{decs}f}}"
    return f"{symbol}{fmt.format(d)}"
