# Arquitectura

Voz Codex se divide en procesos pequeños para que la respuesta de voz no bloquee la captura ni el historial.

1. Handy ejecuta `handy/transcription` cuando termina una transcripción.
2. `voz_codex/service.py` recibe la consulta por un socket local privado.
3. `history.py` guarda la interacción en SQLite con WAL y actualiza el grafo incremental.
4. `codex.py` usa el Codex App Server y conserva el `threadId` real.
5. `persona.py` marca solicitudes recientes sin almacenar su texto, recupera del RAG local solo las voces ecuatorianas relacionadas y añade el nombre e instrucciones de estilo de DOOM.
6. `speech.py` limpia Markdown, emojis y enlaces, transforma números y unidades a texto natural y envía la frase al sintetizador. Las frases breves de espera se dejan precalculadas en WAV para no cargar Kokoro durante una consulta.
7. `omarchy/local.free-hands` lee `task.json` y muestra la tarjeta de estado, las cuatro tomas por fuente o la gráfica SVG. El botón de silencio actúa sobre el trabajador de voz del turno actual.

Los datos de ejecución están en `$XDG_DATA_HOME/voz-codex` y `$XDG_RUNTIME_DIR/voz-codex`. No se escriben credenciales ni conversaciones en el repositorio.

## Rendimiento

Kokoro se mantiene precalentado, las frases se sintetizan en bloques y el servicio publica solo resúmenes de progreso. El historial y Graphify usan SQLite local para evitar embeddings o llamadas adicionales por cada interacción.

## Permisos

Codex usa el modo de solo lectura por defecto. `FREE_HANDS_FULL_ACCESS=1` en el
servicio permite ejecutar comandos y modificar archivos sin confirmación.
Consulta la [configuración](CONFIGURATION.md) antes de activarlo.
