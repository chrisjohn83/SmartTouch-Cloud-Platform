# Render deployment handoff for SmartTouch AI Docs RAG API

Use this file when creating the production SmartTouch RAG API on Render.

## Service type

Create a Render **Web Service** connected to this repository.

## Root directory

```text
ai-docs
```

## Runtime

```text
Python
```

## Build command

```bash
pip install -r requirements.txt
```

## Start command

```bash
python -c "import os, uvicorn; uvicorn.run('ai_docs.web_app:app', host='0.0.0.0', port=int(os.environ.get('PORT', '8000')))"
```

## Health check path

```text
/health
```

## Required environment variables

```text
OPENAI_API_KEY=<your OpenAI API key>
DATABASE_URL=<Render Postgres connection string>
AI_DOCS_CORS_ORIGINS=https://chrisjohn83.github.io,http://127.0.0.1:8001,http://localhost:8001
```

## Verification URLs

After deploy, check:

```text
https://<your-render-service>.onrender.com/health
https://<your-render-service>.onrender.com/diagnostics
```

`/diagnostics` should report:

```text
database_configured: true
openai_key_configured: true
```

## Important production data note

The Render PostgreSQL database must contain the imported SmartTouch AI docs embeddings. A healthy API with an empty database will start, but retrieval will not return useful answers.
