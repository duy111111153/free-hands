from __future__ import annotations

import re
from collections import deque
from time import monotonic


AGENT_NAME = "DOOM"
LEXICON_PROJECT = "hana-ecuadorian-spanish"
_STOP_WORDS = {
    "a", "al", "algo", "como", "con", "cuando", "de", "del", "donde", "el",
    "ella", "en", "es", "esta", "este", "esto", "la", "las", "lo", "los",
    "me", "mi", "muy", "no", "o", "para", "pero", "por", "que", "se", "si",
    "sobre", "su", "te", "tiene", "tu", "un", "una", "y", "ya",
}


class RequestWindow:
    """Count recent voice requests without retaining their text."""

    def __init__(self, window_seconds: float = 90):
        self.window_seconds = window_seconds
        self._times: deque[float] = deque()
        self._burst_active = False

    def record(self, now: float | None = None) -> tuple[int, bool]:
        current = monotonic() if now is None else now
        while self._times and current - self._times[0] > self.window_seconds:
            self._times.popleft()
        self._times.append(current)
        count = len(self._times)
        new_burst = count >= 4 and not self._burst_active
        self._burst_active = count >= 4
        return count, new_burst


def regional_context(history, text: str, limit: int = 3) -> str:
    """Retrieve only lexicon chunks matching words in this request."""
    words = list(dict.fromkeys(
        word for word in re.findall(r"[\wáéíóúüñ]+", text.casefold())
        if len(word) > 2 and word not in _STOP_WORDS
    ))[:8]
    if not words:
        return ""
    query = " OR ".join(f'"{word}"' for word in words)
    try:
        rows = history.search_context(LEXICON_PROJECT, query, limit=limit)
    except Exception:
        return ""
    return "\n".join(row["text"].strip() for row in rows if row.get("text", "").strip())[:1200]


def waiting_policy(text: str, repeated_burst: bool = False) -> tuple[bool, str]:
    """Keep greetings quiet; signal long work and quick repeated requests."""
    if repeated_burst:
        return True, "repeated"
    if len(text) > 200:
        return True, "long"
    investigation = re.search(
        r"\b(investig|busc|naveg|abr[ae]|consult|analiz|revis|instal|ejecut|comprueb|verific|descarg|internet|web|app)\w*\b",
        text.casefold(),
    )
    return bool(investigation), "investigate" if investigation else ""


def style_instruction(name: str, repeated_burst: bool, lexicon: str = "") -> str:
    instruction = (
        f"\n\nTu nombre es {name}. Habla en español ecuatoriano natural, cálido y claro. "
        "Usa expresiones locales con moderación y solo si encajan; no fuerces la jerga, "
        "no imites un estereotipo regional y conserva un registro formal cuando la situación lo pida. "
        "Tu forma normal de tratar al usuario es cercana y respetuosa."
    )
    if lexicon:
        instruction += (
            " Usa este contexto léxico recuperado del glosario local para entender o emplear "
            "las expresiones solo cuando vengan al caso:\n" + lexicon
        )
    if repeated_burst:
        instruction += (
            " El usuario ha enviado varias solicitudes en poco tiempo. Reconócelo con suavidad, "
            "sin regañar ni dejar de responder; puedes empezar con «Suave, ñaño, voy por partes» "
            "y luego atiende todos los puntos en orden. No repitas esa frase en turnos posteriores "
            "si ya la usaste."
        )
    return instruction


def camera_style(text: str, followup: bool = False) -> str:
    detail = followup or re.search(
        r"\b(?:detall\w*|a fondo|en profundidad|cada (?:foto|toma)|compara\w*)\b",
        text, re.I,
    )
    if detail:
        return (
            "\n\nEl usuario quiere detalles. Amplía la observación con los rasgos visibles que "
            "respondan a su pregunta. Distingue lo que ves de lo que solo parece. "
            "Compara las tomas únicamente si ayuda a explicar algo."
        )
    return (
        "\n\nPara una primera mirada, contesta como en una conversación. En una sola frase corta "
        "di qué es lo más llamativo o qué está mostrando el usuario. Si la identificación es "
        "incierta, di «parece» en esa misma frase. Evita inventarios del fondo, enumerar las tomas "
        "y explicar el funcionamiento de la cámara. Si viene al caso, termina con una invitación "
        "breve a ampliar. Ejemplo de tono, no de contenido: «Veo un cortauñas, ñaño. "
        "Si quieres, te cuento más». Usa «ñaño» solo si encaja con el trato."
    )


def asks_for_more(text: str) -> bool:
    return bool(re.fullmatch(
        r"[¿¡]?(?:s[ií][,.]?\s+)?(?:"
        r"(?:dame|cu[eé]ntame|dime|expl[ií]came|describe)(?:lo|me)?\s+(?:m[aá]s(?:\s+detalles)?|en detalle)"
        r"|m[aá]s\s+detalles|profundiza|det[aá]llalo|qu[eé]\s+m[aá]s\s+ves"
        r")(?:\s+por favor)?[.!?¡¿]*",
        text.strip(), re.I,
    ))


def asks_to_look_again(text: str) -> bool:
    return bool(re.fullmatch(
        r"[¿¡]?(?:s[ií][,.]?\s+)?(?:"
        r"(?:mira|observa|revisa|chequea)(?:\s+(?:de nuevo|otra vez|ahora|ahorita))?"
        r"|vuelve\s+a\s+(?:mirar|ver|revisar)"
        r"|(?:y\s+)?qu[eé]\s+(?:ves|est[aá]s viendo)(?:\s+(?:ahora(?: mismo)?|ahorita))?"
        r")(?:\s+por favor)?[.!?¡¿]*",
        text.strip(), re.I,
    ))
