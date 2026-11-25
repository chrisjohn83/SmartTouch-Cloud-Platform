# Collector Interface

**Status: Proposed for Phase 1.1**

The collection service selects the sources and resolves the collection window. Each source adapter implements `collect(since, until)` and returns records in a shared format. GitHub will be the first adapter to use this contract, followed by Jira, Confluence, and Bitbucket.

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Protocol


@dataclass(frozen=True)
class CollectedRecord:
    source_id: str
    item_type: str
    title: str
    changed_at: datetime
    raw_payload: dict[str, Any]
    source_url: str | None = None
    source_created_at: datetime | None = None
    source_updated_at: datetime | None = None


class Collector(Protocol):
    def collect(
        self, *, since: datetime, until: datetime
    ) -> Iterable[CollectedRecord]:
        """Yield records whose changed_at falls in [since, until)."""
        ...
```

## Collector responsibilities

Authenticate, fetch every page, and map source records to the shared format. Keep each `source_id` stable within its configured source and preserve the original payload. Use timezone-aware timestamps. Raise an error if retrieval fails, including during pagination. An empty result means retrieval succeeded and found no matching records.

## Collection service responsibilities

Resolve the window in UTC. Include the start and exclude the end. Record each source's outcome independently. Advance a source checkpoint only after that source's incremental run finishes and its records are saved. Fixed and named release windows leave operational checkpoints untouched.

## Release history

Save changed payloads as new snapshots. Each release references its selected snapshots, so collecting a newer release leaves an older frozen release's records intact.

A fixed window filters records by their change timestamps. It can reproduce an earlier payload only when that version was previously captured or the source exposes it.
