# Chat memory

SQLite stores local thread metadata, messages, topics, and the active Codex
thread. `chat-sync` imports lightweight metadata visible to App Server;
`chat-search`, `chat-select`, and `chat-route` operate locally. The database
is never part of a public checkout. Deleting the local data directory erases
continuity.
