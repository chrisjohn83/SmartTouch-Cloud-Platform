PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    enabled INTEGER NOT NULL DEFAULT 1,
    configuration_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS collection_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL CHECK (
        status IN ('running', 'completed', 'failed', 'partial')
    ),
    trigger_type TEXT NOT NULL DEFAULT 'manual',
    collected_count INTEGER NOT NULL DEFAULT 0,
    new_count INTEGER NOT NULL DEFAULT 0,
    updated_count INTEGER NOT NULL DEFAULT 0,
    unchanged_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS source_checkpoints (
    source_name TEXT PRIMARY KEY,
    cursor_value TEXT,
    last_successful_sync TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (source_name) REFERENCES sources(name)
);

CREATE TABLE IF NOT EXISTS raw_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_url TEXT,
    item_type TEXT NOT NULL,
    title TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    source_created_at TEXT,
    source_updated_at TEXT,
    content_hash TEXT NOT NULL,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    collection_status TEXT NOT NULL CHECK (
        collection_status IN ('new', 'updated', 'unchanged')
    ),
    collection_run_id INTEGER NOT NULL,

    UNIQUE (source_name, source_id),

    FOREIGN KEY (source_name) REFERENCES sources(name),
    FOREIGN KEY (collection_run_id) REFERENCES collection_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_raw_items_source
    ON raw_items(source_name);

CREATE INDEX IF NOT EXISTS idx_raw_items_source_updated
    ON raw_items(source_name, source_updated_at);

CREATE INDEX IF NOT EXISTS idx_raw_items_collection_status
    ON raw_items(collection_status);

CREATE INDEX IF NOT EXISTS idx_raw_items_collection_run
    ON raw_items(collection_run_id);
