# Ask SmartTouch Docs

<div class="rag-app">
  <section class="rag-hero">
    <p class="rag-eyebrow">SmartTouch AI Docs</p>
    <h2>Ask questions. Get cited answers.</h2>
    <p>
      Use SmartTouch documentation retrieval with grounded answers, cited sources,
      and optional knowledge graph expansion for broker, device, deployment, and
      remote access troubleshooting.
    </p>
  </section>

  <section class="rag-card rag-question-card" aria-label="Ask SmartTouch documentation">
    <div class="rag-card-kicker">Question</div>
    <label for="rag-query" class="rag-question-label">What do you want to troubleshoot?</label>
    <textarea id="rag-query" rows="4" placeholder="Example: agent cannot reach broker"></textarea>

    <div class="rag-examples" aria-label="Example questions">
      <button type="button" data-query="agent cannot reach broker">Agent cannot reach broker</button>
      <button type="button" data-query="A remote diagnostics session is already open">Diagnostics session already open</button>
      <button type="button" data-query="Why can't stctl authenticate me?">stctl authentication issue</button>
      <button type="button" data-query="How do I roll back a failed release?">Rollback a release</button>
    </div>

    <div class="rag-controls">
      <label class="rag-toggle">
        <input id="rag-use-kg" type="checkbox" checked />
        <span>Use knowledge graph expansion</span>
      </label>

      <button id="rag-submit" type="button">Ask SmartTouch Docs</button>
    </div>

    <p id="rag-status" class="rag-status" role="status" aria-live="polite"></p>
  </section>

  <section id="rag-answer-card" class="rag-card rag-answer-card rag-hidden" aria-label="Answer">
    <div class="rag-card-header">
      <div>
        <div class="rag-card-kicker">Grounded response</div>
        <h2>Answer</h2>
      </div>
      <button id="rag-copy-answer" type="button">Copy answer</button>
    </div>
    <div id="rag-answer"></div>
  </section>

  <section id="rag-sources-card" class="rag-card rag-sources-card rag-hidden" aria-label="Sources">
    <div class="rag-card-header">
      <div>
        <div class="rag-card-kicker">Evidence</div>
        <h2>Sources</h2>
      </div>
    </div>
    <div id="rag-sources"></div>
  </section>
</div>
