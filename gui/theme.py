import re

COLORS: dict[str, str] = {
    "bg_app":   "#0f172a",
    "bg_panel": "#1e293b",
    "bg_code":  "#0d1117",
    "bg_bar":   "#020617",
    "txt":      "#e2e8f0",
    "txt_dim":  "#475569",
    "accent":   "#60a5fa",
    "ok":       "#4ade80",
    "err":      "#f87171",
    "warn":     "#fbbf24",
    "mic":      "#c084fc",
    "ia":       "#f0abfc",
    "border":   "#1e3a5f",
}

EXAMPLE_CODE = """\
# Ejemplo completo del lenguaje .acc
definir base como 5
definir altura como 10
definir area como base por altura

mostrar "Resultado del calculo:"
mostrar area

si area es mayor que 40 entonces
    mostrar "El area es grande"
sino
    mostrar "El area es pequena"
fin si

definir contador como 0
repetir 4 veces
    definir contador como contador mas 1
    mostrar contador
fin repetir

definir x como 20
mientras x es mayor que 0
    definir x como x menos 7
fin mientras
mostrar x
"""

_ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)
