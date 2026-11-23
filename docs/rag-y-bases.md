# RAG y proyectos

Indexa una carpeta de texto con `voz-codex index mi-proyecto /ruta`. El índice usa SQLite FTS5, divide documentos en fragmentos pequeños y mantiene la fuente de cada resultado. Si un archivo no cambió, se reutilizan sus fragmentos existentes.

Al iniciar, DOOM indexa el glosario versionado en `voz_codex/data/ecuadorismos.md` con el proyecto `hana-ecuadorian-spanish`. Antes de enviar una consulta a Codex, busca hasta tres fragmentos que coincidan con sus palabras y adjunta un máximo de 1200 caracteres al contexto. La conversación conserva el prompt y el comportamiento habitual aunque la búsqueda local no encuentre coincidencias. No se generan embeddings ni se hace una llamada de red para el glosario.

El glosario recoge vocabulario de fuentes públicas ecuatorianas y separa las definiciones del diccionario de las frases de interfaz añadidas por el usuario. La variedad de habla cambia por región; DOOM mantiene un registro natural y evita forzar expresiones.
