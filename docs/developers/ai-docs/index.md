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

```powershell
$env:OPENAI_API_KEY = "<your-key>"
$env:DATABASE_URL = "postgresql://smarttouch:SmartTouch123@127.0.0.1:55432/smarttouch_ai"
python -m uvicorn ai_docs.web_app:app --reload --port 800

### Prerequisites

Start Docker Desktop, then start PostgreSQL with pgvector:

```powershell
docker compose up -d
docker ps
```

## RAG answer API

The retrieval service can return grounded answers with citations.

Start the local API:

## SmartTouch AI docs

Utilities for indexing, searching, and answering questions from SmartTouch documentation.

## Knowledge graph query expansion

The AI docs service can build a lightweight knowledge graph from embedded documentation chunks and use it to expand retrieval queries.

### Build the knowledge graph

Run from the `ai-docs` directory:

```powershell
python -m ai_docs.build_knowledge_graph `
  --input build/embedded-chunks.jsonl `
  --entities-output build/kg-entities.jsonl `
  --relationships-output build/kg-relationships.jsonl
```

This writes:

- `build/kg-entities.jsonl`
- `build/kg-relationships.jsonl`

These files are generated artifacts and should not be committed.

### Check knowledge graph availability

Start the API server, then call:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/diagnostics"
```

A healthy KG setup reports:

```json
{
  "knowledge_graph_configured": true,
  "knowledge_graph_entities_path": "build\\kg-entities.jsonl",
  "knowledge_graph_relationships_path": "build\\kg-relationships.jsonl"
}
```

### Use KG expansion from the CLI

```powershell
python -m ai_docs.retrieval_service_cli `
  --query "device cannot connect to broker" `
  --limit 3 `
  --format search `
  --use-knowledge-graph
```

For citation-ready context:

```powershell
python -m ai_docs.retrieval_service_cli `
  --query "device cannot connect to broker" `
  --limit 3 `
  --format context `
  --use-knowledge-graph
```

For grounded answers:

```powershell
python -m ai_docs.retrieval_service_cli `
  --query "device cannot connect to broker" `
  --limit 3 `
  --format answer `
  --use-knowledge-graph
```

### Use KG expansion from HTTP

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/search" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"query":"device cannot connect to broker","limit":3,"use_knowledge_graph":true}'
```

The public response keeps the original user query. The expanded query is only used internally for retrieval.
