# 🧠 Policy-Aware RAG System — Project Report

## 1. Architecture Rationale

This project follows a **multi-agent architecture** to make the Retrieval-Augmented Generation (RAG) pipeline **modular**, **policy-aware**, and **explainable**.  
The key motivation behind this separation of concerns is:

- **Retriever Agent** — Responsible for efficient and deterministic passage retrieval using vector similarity search (e.g., FAISS). This separation ensures that the retrieval logic can evolve independently (e.g., switch embedding models, add rerankers) without breaking the reasoning logic.

- **Reasoning Agent** — Focused purely on generating answers and explanation traces using a large language model (e.g., via Ollama). This clean boundary allows:
  - LLM reasoning to be swapped, updated, or scaled independently.
  - Easier debugging and evaluation of reasoning quality.

- **Governance Agent** — Enforces trust, safety, and compliance:
  - Banned phrase checks
  - PII redaction
  - Confidence threshold enforcement
  - Trace auditing
  This ensures the system doesn’t return unsafe, low-confidence, or policy-violating answers.

- **Gateway (FastAPI)** — Acts as the orchestrator, chaining agents in a clean and inspectable flow:  
  `query → retrieval → reasoning → governance → response`.

- **Memory Recall (Future)** — A new layer to remember previous user queries and answers across sessions, enabling contextual reasoning and long-term knowledge fabric.

- **Trace Endpoint (`/trace`)** — Exposes explainability data so developers or auditors can inspect which passages and reasoning steps contributed to a final answer.

This architecture aligns with scalable, distributed RAG patterns used in production-grade AI systems.

---

## 2. Governance Logic

Governance was designed to be **transparent, auditable, and simple** at first, with clear upgrade paths.

### Current Rules:
- **Banned Phrases**: e.g., `diagnosis`, `prescription`, `classified`, `confidential`.  
  → These trigger an automatic rejection of the response.
- **PII Redaction**: Dates, IDs, and name-like patterns are replaced with `[REDACTED_*]` placeholders.
- **Confidence Threshold**: Responses below a configurable threshold (default **0.6**) are not approved.
- **Logging**: Every governance decision is logged for future audits.

### Design Decision:
- Keep governance **agent-based and modular**, so new rules can be plugged in without touching retrieval or reasoning.
- Thresholds are **tunable** — allowing more or less strict policies depending on the deployment context.

---

## 3. Scaling Vision

While the current implementation runs as a **single-node FastAPI service**, the long-term vision is to **scale into a distributed memory and reasoning fabric**

- **Distributed Retriever Shards**: Parallel FAISS nodes for large corpora.
- **Stateless Reasoning Workers**: Horizontal scaling of LLM inference (Ollama or other backends).
- **Memory Fabric**: Shared memory layer to recall previous queries and reasoning chains.
- **Audit Trails**: Central governance audit ledger for policy compliance and traceability.
- **AXON/NAYAR Integration**: Multi-agent orchestration and event-based communication between nodes (e.g., retriever nodes, policy nodes, memory nodes).

This makes the system more resilient, explainable, and suitable for enterprise or regulated environments.

---

## 4. Limitations & Future Work

Being transparent is more valuable than being perfect. Current limitations include:

- **No persistent memory yet** — queries are stateless. Planned fix: add memory recall to preserve conversation history.
- **Basic governance rules** — currently regex-based and limited. Future improvement:
  - Named Entity Recognition for more robust PII detection.
  - Policy graphs and structured rule engines.
- **Single-node deployment** — not optimized for heavy loads. Future step: Docker Compose and container orchestration for scaling agents.
- **Simple trace visualization** — the `/trace` endpoint returns structured data, but a dedicated UI or dashboard would improve explainability.

---

## 5. Deployment Strategy

The project is containerized and will use **Docker Compose** for multi-agent orchestration:

- `gateway` — FastAPI app
- `retriever` — FAISS indexing + retrieval
- `reasoner` — Ollama worker
- `governance` — policy enforcement
- `memory` — context store
- `logger` — centralized log aggregation

This separation allows easy scaling and swapping of components without modifying the core logic.

---

**Author:** Pooya Chavoshi | Pooyachavoshi@gmail.com
**Stack:** FastAPI, FAISS, Ollama, Python, Docker  
**Version:** 1.0.0
