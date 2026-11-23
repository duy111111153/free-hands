# Instalación en Omarchy

Requisitos recomendados

- Omarchy con Hyprland, PipeWire y `pw-play`.
- Codex CLI autenticado y Handy instalado.
- Python 3.11 o posterior.

```bash
cd ~/Work/voz-codex
chmod +x voz-codex handy/transcription
./voz-codex doctor
mkdir -p ~/.local/share/com.pais.handy/hooks ~/.config/systemd/user
install -m 700 handy/transcription ~/.local/share/com.pais.handy/hooks/transcription
install -m 644 systemd/voz-codex.service ~/.config/systemd/user/voz-codex.service
systemctl --user daemon-reload
systemctl --user enable --now voz-codex.service
mkdir -p ~/.config/omarchy/plugins/local.voz-tracker
install -m 644 omarchy/local.voz-tracker/* ~/.config/omarchy/plugins/local.voz-tracker/
omarchy plugin enable local.voz-tracker --section right
omarchy-shell shell rescanPlugins
```

Configura Handy con Paste Method `None` o `External Script` según la versión. Alt+Z conserva el control de grabación de Handy. El binding de Hyprland se cambia después de validar el servicio, usando la ruta absoluta a `.venv/bin/voz-codex toggle`.

Comprueba la instalación con `voz-codex doctor`, pulsa Alt+Z en Handy y revisa que aparezca DOOM en la barra. La tarjeta admite doble clic para abrir el hilo actual, una X para ocultarla y Alt+X para cancelar una tarea activa.

## Voz neuronal local

Con PipeWire y `pw-play` disponibles, Voz Codex detecta Piper y la voz
`es_MX-ald-medium` en su directorio de datos. La síntesis funciona sin
conexión después de descargar el modelo.

```bash
voice_dir="${XDG_DATA_HOME:-$HOME/.local/share}/voz-codex"
python3 -m venv "$voice_dir/piper-venv"
"$voice_dir/piper-venv/bin/pip" install piper-tts==1.8.0
mkdir -p "$voice_dir/voices"
"$voice_dir/piper-venv/bin/python" -m piper.download_voices --data-dir "$voice_dir/voices" es_MX-ald-medium
systemctl --user restart voz-codex.service
```

Un `speech_command` explícito tiene prioridad. Si Piper no está instalado,
Voz Codex usa eSpeak NG cuando está disponible.

El perfil predeterminado `alex` usa Kokoro `em_alex`. Sintetiza por frases,
con pausas entre elementos de listas y pronunciación inglesa para nombres
técnicos conocidos y frases en inglés que reconoce.
Para volver a Piper, configura `piper_voice = "claude"` o
`piper_voice = "daniela"`.

Descarga `es_MX-claude-high` para usar Claude (español mexicano) y
`es_AR-daniela-high` para usar Daniela (español argentino) con el mismo
comando `piper.download_voices`. Claude tiene prioridad cuando los dos
modelos están disponibles. Para elegir Daniela, añade
`piper_voice = "daniela"` a `$XDG_CONFIG_HOME/voz-codex/config.toml`
(por defecto `~/.config/voz-codex/config.toml`) y reinicia el servicio.

Para preparar avisos al usar Piper, elige el nombre del modelo activo:

```bash
voice=es_MX-claude-high
"$voice_dir/piper-venv/bin/python" voz_codex/piper_play.py \
  "$voice_dir/voices/$voice.onnx" --cache-cues "$voice_dir/voices/cues/$voice"
systemctl --user restart voz-codex.service
```

### Voces Alex y Dora con Kokoro

Para usar Alex o Dora, instala `kokoro-onnx==0.4.7` en el mismo entorno virtual.
Descarga `kokoro-v1.0.int8.onnx` y `voices-v1.0.bin` en
`$voice_dir/voices/kokoro/` y reinicia el servicio. `piper_voice = "dora"`
selecciona la voz alternativa. [Archivos oficiales de Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0)

`speech_gain` ajusta la ganancia local de Kokoro entre `0.5` y `8.0`.
Por encima de `2.0` se comprime la dinámica y se limitan los picos
para que las sílabas suaves también ganen nivel. El flujo de PipeWire
sigue en `1.0`. Si cambias la ganancia, regenera los avisos con el mismo valor.

Para preparar los avisos al usar Dora, ejecuta una sola vez:

```bash
voice_dir="${XDG_DATA_HOME:-$HOME/.local/share}/voz-codex"
"$voice_dir/piper-venv/bin/python" voz_codex/kokoro_play.py \
  "$voice_dir/voices/kokoro" ef_dora --cache-cues \
  "$voice_dir/voices/cues/ef_dora" --gain 2.0
systemctl --user restart voz-codex.service
```

El comando precalcula «Dame un break», «Espérame un chance», «De una» y
«Suave, ñaño». DOOM los reproduce desde archivos locales; no carga el
sintetizador ni añade esa demora a cada aviso.
