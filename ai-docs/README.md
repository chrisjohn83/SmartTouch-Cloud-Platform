# SmartTouch AI documentation ingestion

This component parses MkDocs Markdown, preserves YAML front matter, splits content
along heading and block boundaries, and emits deterministic JSONL records for a
later embedding and vector-storage stage.

## Run

From the `ai-docs` directory in the SmartTouch repository:

```powershell
python -m ai_docs.ingest `
  --docs-root ../docs `
  --output build/chunks.jsonl `
  --exclude "test-*.md"
```

Each JSONL record includes:

- a deterministic chunk ID and content hash;
- source path, source URL, document title, heading, and heading hierarchy;
- line locations, chunk index, and word count;
- all source YAML front matter, including SmartTouch personas, tasks, tags,
  related documents, owners, review metadata, and retrieval questions.

## Test

```powershell
python -m unittest discover -s tests -v
```

## Run the local retrieval API

The retrieval API exposes the SmartTouch documentation search layer over HTTP.

### Prerequisites

Start Docker Desktop, then start PostgreSQL with pgvector:

```powershell
docker compose up -d
docker ps
```

## RAG answer API

The retrieval service can return grounded answers with citations.

Start the local API:

```powershell
$env:OPENAI_API_KEY = "<your-key>"
$env:DATABASE_URL = "postgresql://smarttouch:SmartTouch123@127.0.0.1:55432/smarttouch_ai"
python -m uvicorn ai_docs.web_app:app --reload --port 800
