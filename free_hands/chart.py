"""Render a small, self-contained comparison chart from structured turn data."""
import json
import math
import re
from html import escape


CHART_REQUEST = re.compile(
    r"\b(?:gr[aá]fic[oa]s?|grafica(?:r)?|chart|plot|compar(?:a|ar|aci[oó]n))\b", re.I,
)
CHART_BLOCK = re.compile(r"\n?\x60{3}doom-chart[ \t]*\n(.*?)\x60{3}\s*\Z", re.S)
CHART_INSTRUCTION = (
    '\n\nSi hay datos numéricos sustentados que comparar, agrega al final del guion un '
    'único bloque ```doom-chart con JSON y ciérralo con tres acentos graves. '
    'Formato: {"title":"título","unit":"unidad común","points":[["A",12],["B",15]]}. '
    'Usa entre 2 y 8 valores de la misma escala, en el orden que deba mostrarse. '
    'No inventes valores. Si no hay datos suficientes, explica qué falta. '
    'DOOM anuncia la gráfica cuando pueda mostrarla.'
)


def _label(value, limit):
    if not isinstance(value, str):
        raise ValueError("Expected chart text")
    return escape(re.sub(r"[\x00-\x1f\x7f-\x9f\ud800-\udfff]", " ", value[:limit]).strip())


def parse_chart(answer):
    """Strip chart metadata from narration, even when the payload is invalid."""
    match = CHART_BLOCK.search(answer)
    if not match:
        return answer.split("```doom-chart", 1)[0].rstrip(), None
    spoken = answer[:match.start()].rstrip()
    try:
        if len(match[1]) > 4096:
            return spoken, None
        data = json.loads(match[1])
        title = _label(data["title"], 64)
        unit = _label(data.get("unit", ""), 28)
        points = data["points"]
        if not title or not isinstance(points, list) or not 2 <= len(points) <= 8:
            return spoken, None
        validated = []
        for label, value in points:
            label = _label(label, 22)
            if not label or type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 1e15:
                return spoken, None
            validated.append((label, value))
    except (KeyError, ValueError, TypeError, AttributeError, OverflowError, RecursionError):
        return spoken, None
    return spoken, render_chart(title, unit, validated)


def render_chart(title, unit, points):
    height = 102 + 43 * len(points)
    low = min(0, *(value for _, value in points))
    high = max(0, *(value for _, value in points))
    span = high - low or 1
    zero = 235 - 400 * (low / span)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="760" height="{height}" viewBox="0 0 760 {height}">',
        '<rect width="100%" height="100%" rx="16" fill="#181d2d"/>',
        '<g font-family="sans-serif" fill="#f1f4fd">',
        f'<text x="24" y="34" font-size="22" font-weight="bold">{title}</text>',
        f'<text x="24" y="63" font-size="17" fill="#bac8e1">{unit}</text>',
        f'<path d="M {zero:.2f},79 V {height - 16}" stroke="#78849c"/>',
    ]
    for index, (label, value) in enumerate(points):
        y = 86 + index * 43
        bar_width = 400 * (value / span)
        x = min(zero, zero + bar_width)
        color = "#78d6fa" if value >= 0 else "#f3aa8a"
        parts.extend((
            f'<text x="24" y="{y + 19}" font-size="17">{label}</text>',
            f'<rect x="{x:.2f}" y="{y}" width="{max(1, abs(bar_width)):.2f}" height="25" rx="4" fill="{color}"/>',
            f'<text x="736" y="{y + 19}" text-anchor="end" font-size="17">{value:.6g}</text>',
        ))
    return "".join(parts + ["</g></svg>"]).encode()
