# RAG and graph

`free-hands index PROJECT PATH` explicitly indexes a text directory into the
local SQLite FTS5 store. The Ecuadorian Spanish glossary is bundled as source
code and queried locally. Graph export is written below local
`$XDG_DATA_HOME/free-hands/graphify-out`; it is not tracked by Git. External
projects are never indexed automatically.

The Omarchy metrics card renders an SVG locally from validated numeric data
for a chart or comparison request. Double-click its thumbnail to open the
full image. The project Graphify index records the rendering functions and
their service integration. Live chart files stay in the private runtime directory.

Refresh the source graph from the repository with `graphify . --code-only --update --directed`,
then render the report and diagram with `GRAPHIFY_BACKEND=none graphify cluster-only .`.
