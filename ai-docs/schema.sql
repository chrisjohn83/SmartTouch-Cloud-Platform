CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    id text PRIMARY KEY,
    source_path text NOT NULL,
    source_url text,
    title text,
    heading text,
    heading_path jsonb NOT NULL DEFAULT '[]'::jsonb,
    content text NOT NULL,
    content_hash text NOT NULL,
    chunk_index integer NOT NULL,
    start_line integer,
    end_line integer,
    word_count integer,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    embedding_model text NOT NULL,
    embedding_dimensions integer NOT NULL,
    embedding vector(1536) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS document_chunks_source_path_idx
    ON document_chunks (source_path);

CREATE INDEX IF NOT EXISTS document_chunks_heading_idx
    ON document_chunks (heading);

CREATE INDEX IF NOT EXISTS document_chunks_metadata_gin_idx
    ON document_chunks USING gin (metadata);

CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx
    ON document_chunks
    USING hnsw (embedding vector_cosine_ops);
