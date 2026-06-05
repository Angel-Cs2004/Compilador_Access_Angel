import importlib.util
import threading

AI_AVAILABLE: bool = importlib.util.find_spec("groq") is not None

_SYSTEM_PROMPT = """\
Eres una voz guía para estudiantes que están aprendiendo el lenguaje ".acc",
un lenguaje con sintaxis en español.

Tu respuesta será leída en voz alta, así que debe sonar como una persona
explicando naturalmente, no como un informe ni como una tabla.

Explica el código en español claro, cálido y directo, como si estuvieras al
lado del estudiante mirando su programa. Usa frases conversacionales.

No uses títulos, listas, viñetas, markdown, numeraciones ni bloques de código.
No digas "este código" muchas veces. No menciones tokens, AST, compilador ni
detalles internos salvo que haya un error importante.

En 4 a 7 oraciones:
primero cuenta qué intenta hacer el programa,
luego explica el flujo principal,
y al final menciona qué resultado se espera o si hay algo raro que conviene revisar.

Si encuentras un posible error, dilo con naturalidad y sugiere cómo corregirlo.
Evita sonar robótico. Responde solo con la explicación hablada.
"""

_LINE_PROMPT = """\
Eres una voz guía para estudiantes ciegos que programan en el lenguaje ".acc".

El estudiante está explorando una línea concreta del editor. Explica esa línea
con naturalidad, usando el programa completo solo como contexto.

Responde en español hablado, sin títulos, listas, markdown ni bloques de código.
Sé breve: 2 a 4 oraciones. Primero di qué hace la línea, luego cómo encaja con
lo que la rodea. Si la línea está vacía o parece tener un error, dilo de forma
clara y amable.
"""


class AIAnalyzer:
    _MODEL = "llama-3.3-70b-versatile"

    def analyze(self, code: str, api_key: str, on_success, on_error) -> None:
        """Send code to Groq in a background thread.

        on_success(response: str) and on_error(message: str) are called from that thread.
        """
        threading.Thread(
            target=self._analyze_task,
            args=(code, api_key, on_success, on_error),
            daemon=True,
        ).start()

    def analyze_line(
        self,
        code: str,
        line_number: int,
        line_text: str,
        api_key: str,
        on_success,
        on_error,
    ) -> None:
        threading.Thread(
            target=self._analyze_line_task,
            args=(code, line_number, line_text, api_key, on_success, on_error),
            daemon=True,
        ).start()

    def _analyze_task(self, code: str, api_key: str, on_success, on_error) -> None:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model=self._MODEL,
                max_tokens=700,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user",   "content": f"Explícame de forma natural este programa .acc:\n\n```\n{code}\n```"},
                ],
            )
            on_success(response.choices[0].message.content)
        except Exception as exc:
            on_error(self._format_error(exc))

    def _analyze_line_task(self, code: str, line_number: int, line_text: str, api_key: str, on_success, on_error) -> None:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model=self._MODEL,
                max_tokens=350,
                messages=[
                    {"role": "system", "content": _LINE_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Programa completo:\n```\n{code}\n```\n\n"
                            f"Línea actual: {line_number}\n"
                            f"Contenido de la línea:\n```\n{line_text}\n```"
                        ),
                    },
                ],
            )
            on_success(response.choices[0].message.content)
        except Exception as exc:
            on_error(self._format_error(exc))

    def _format_error(self, exc: Exception) -> str:
            msg = str(exc)
            if "authentication" in msg.lower() or "api_key" in msg.lower():
                msg = "API Key inválida o expirada. Verifica tu clave de Groq."
            elif "rate" in msg.lower() or "quota" in msg.lower() or "429" in msg:
                msg = "Límite de peticiones alcanzado. Espera unos segundos e intenta de nuevo."
            return msg
