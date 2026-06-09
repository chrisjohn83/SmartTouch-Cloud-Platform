---
docType: strategy
audience: [tech-writers, architects, platform-engineers]
status: approved
version: "1.0"
last-reviewed: "2026-06-05"
tags: [ai-tools, content-strategy, information-architecture, documentation, llm]
---

# AI Tools for Content Strategy and Information Architecture

## TL;DR

AI tools now cover every layer of the documentation workflow — from IA design and content gap analysis to structured authoring, validation, and semantic search. This document maps the right tool to the right job for SmartTouch's documentation pipeline.

---

## 1. The Documentation Workflow and Where AI Fits

```
Plan IA → Author content → Structure & tag → Validate → Publish → Retrieve
  ↓             ↓                ↓               ↓           ↓          ↓
AI IA       AI writing       AI tagging      AI linting   AI index   AI search
design      assistance       & metadata      & review     & embed    & RAG
```

---

## 2. AI Tools by Documentation Layer

### 2.1 Content Strategy & IA Design

| Tool | What it does | Best for |
| --- | --- | --- |
| **Claude (Anthropic)** | Generates IA structures, content taxonomies, navigation trees, and metadata schemas from a product brief | IA design, strategy docs, ADR drafting |
| **ChatGPT / GPT-4o** | Iterates on IA structures, proposes Diátaxis categorisations, generates controlled vocabulary lists | Brainstorming content types and tag vocabularies |
| **Notion AI** | Suggests page hierarchies and database schemas within a Notion workspace | Small-team IA in Notion-based knowledge bases |
| **Confluence AI** | Auto-generates page trees and labels from existing content | Migrating legacy wikis into structured IA |

**SmartTouch recommendation:** Use **Claude** for IA design sessions — it produces structured output (YAML, Markdown, tables) that integrates directly into the doc repo. Prompt with the product brief, audience list, and Diátaxis requirement.

---

### 2.2 Content Authoring & Drafting

| Tool | What it does | Best for |
| --- | --- | --- |
| **Claude** | Drafts technical docs from architecture diagrams, ADRs, or code comments. Follows style guides when given a sample. | How-to guides, explanations, ADR drafts |
| **GitHub Copilot (Docs mode)** | Autocompletes Markdown as you type, suggests frontmatter, and flags missing sections | In-editor drafting in VS Code |
| **Mintlify Writer** | AI documentation generation from code (OpenAPI specs, function signatures) | Reference docs from code |
| **Swimm** | Generates and keeps code-coupled docs in sync with the codebase | Inline code documentation |
| **Stenography** | Auto-generates explanations of code snippets | Explaining complex implementation sections |

**SmartTouch recommendation:** For **reference docs**, generate from OpenAPI specs using **Mintlify** or **Redocly**. For **explanations and how-to guides**, draft with Claude using the platform architecture and ADRs as context.

---

### 2.3 Metadata & Taxonomy Generation

| Tool | What it does | Best for |
| --- | --- | --- |
| **Claude** | Suggests frontmatter fields, generates controlled tag vocabularies, classifies existing docs by Diátaxis type | Bootstrapping metadata schemas, tagging legacy docs |
| **OpenAI Embeddings API** | Clusters existing documents by semantic similarity to reveal IA gaps and overlapping content | Auditing large doc sets for redundancy |
| **AWS Comprehend** | Extracts key phrases and entities from existing docs to build a controlled vocabulary | Taxonomy generation from legacy content |
| **spaCy + custom NER** | Named entity recognition to auto-tag docs with product names, versions, and commands | Automated metadata enrichment in CI |

**SmartTouch recommendation:** Run **Claude** over existing markdown files with the prompt: *"Classify this document by Diátaxis type and suggest frontmatter tags from this controlled vocabulary: [tag list]."* This bootstraps metadata on legacy content.

---

### 2.4 Content Validation & Quality

| Tool | What it does | Best for |
| --- | --- | --- |
| **Vale** | Prose linting with configurable style rules (Microsoft, Google, custom) | Tone, inclusive language, style consistency |
| **LanguageTool + AI** | Grammar, clarity, and readability suggestions | Editorial review pass |
| **Grammarly Business** | Style, clarity, and engagement scoring with team style guides | Non-technical stakeholder docs |
| **Claude (review mode)** | Reviews a doc against defined criteria: Diátaxis purity, AI-readiness, completeness | Structured doc review before publishing |
| **markdownlint** | Enforces Markdown structure rules | CI validation of heading hierarchy, frontmatter |

**SmartTouch recommendation:** Run **Vale + markdownlint** in CI (pre-merge gate). Run **Claude** as an optional review pass using a structured prompt: *"Review this document against: (1) single Diátaxis type, (2) self-contained sections, (3) complete frontmatter, (4) code blocks with language identifiers."*

---

### 2.5 AI Consumption Layer (RAG & Semantic Search)

| Tool | What it does | Best for |
| --- | --- | --- |
| **OpenAI Embeddings** (`text-embedding-3-large`) | Generates dense vector embeddings for semantic search | Vector index for RAG |
| **pgvector** (PostgreSQL extension) | Stores and queries vector embeddings alongside metadata | Self-hosted semantic search |
| **Pinecone** | Managed vector database with metadata filtering | Production-scale RAG with audience/version filters |
| **Weaviate** | Vector database with built-in hybrid search (BM25 + vector) | When keyword + semantic search are both needed |
| **LlamaIndex** | Framework for ingesting, chunking, and indexing docs into a RAG pipeline | Building the SmartTouch docs assistant |
| **LangChain** | Orchestration layer for multi-step RAG chains with tool calling | Complex query workflows (e.g., "compare ADR-001 and ADR-003") |
| **Docusaurus + Algolia** | Full-text search with crawler — lightweight, pre-semantic | Standard keyword search on the docs site |

**SmartTouch recommendation for the AI Consumption Layer:**

```
Documents (Markdown + frontmatter)
        ↓
LlamaIndex ingestion pipeline
        ↓
Chunk by ## heading → attach frontmatter as metadata
        ↓
OpenAI text-embedding-3-large
        ↓
pgvector (self-hosted) or Pinecone (managed)
        ↓
RAG query with metadata filters (docType, audience, platform-version)
        ↓
Claude or GPT-4o as answer synthesiser
```

---

### 2.6 Diagram & Visual IA Tools

| Tool | What it does | Best for |
| --- | --- | --- |
| **Mermaid + Claude** | Claude generates Mermaid diagram code from a prose architecture description | Architecture diagrams in Markdown |
| **Eraser.io** | AI-native diagramming from prose; exports as code | IA maps, system diagrams |
| **Whimsical AI** | Generates flowcharts and mind maps from prompts | IA brainstorming and navigation wireframes |
| **Structurizr + C4 model** | AI-assisted C4 architecture diagrams | Formal architecture documentation |

---

## 3. Recommended Tool Stack for SmartTouch

| Phase | Tool | Usage |
|--- | --- | --- |
| IA Design | Claude | Generate navigation trees, content types, metadata schemas |
| Content Drafting | Claude + GitHub Copilot | Draft how-to guides, explanations, ADRs |
| Reference Docs | Mintlify / Redocly | Generate from OpenAPI specs |
| Metadata Tagging | Claude (batch) | Classify and tag existing docs |
| Prose Linting | Vale + markdownlint | CI gate on every PR |
| Docs Site | Docusaurus + Algolia | Human-navigable docs site with keyword search |
| Semantic Search | LlamaIndex + pgvector | AI-consumable RAG pipeline |
| Answer Synthesis | Claude API | Docs assistant / chatbot |

---

## 4. Prompts for Common Documentation Tasks

### Generate a navigation tree from a product brief

```
You are a technical information architect. Given the following product brief for [Product],
design a documentation navigation tree following the Diátaxis framework.
Include: Get Started (tutorials), Platform Guide (how-to), Architecture (explanations + ADRs),
and Reference sections. Output as an indented tree in Markdown code block.

Product brief: [paste brief]
```

### Classify a document by Diátaxis type

```
Classify the following document as one of: tutorial, how-to guide, reference, or explanation.
Explain your reasoning in one sentence. Then suggest 3-5 metadata tags from this vocabulary: [tag list].

Document: [paste document]
```

### Draft a how-to guide from an architecture description

```
Write a how-to guide titled "[Task]" for an audience of [role].
Base the guide on the following architecture description: [paste].
Follow this structure: Prerequisites → Steps (numbered) → Expected result → Troubleshooting.
Use second-person ("you"). Define all acronyms on first use.
```

### Review a document for AI-readiness

```
Review the following document for AI-readiness. Check:
1. Does it have complete YAML frontmatter (docType, audience, status, version, last-reviewed, tags)?
2. Is each ## section self-contained (understandable without reading other sections)?
3. Do all code blocks have a language identifier?
4. Are acronyms defined on first use?
5. Is there a TL;DR or Summary section?
Flag any issues. Output a checklist with pass/fail per criterion.
```
