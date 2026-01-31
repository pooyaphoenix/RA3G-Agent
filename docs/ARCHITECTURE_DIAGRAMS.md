# RA3G-Agent - Architecture Diagrams

## Table of Contents
1. [High-Level System Overview](#1-high-level-system-overview)
2. [Mid-Level Component Architecture](#2-mid-level-component-architecture)
3. [Low-Level Flow Diagrams](#3-low-level-flow-diagrams)
4. [Data Lineage](#4-data-lineage)
5. [Class Structure](#5-class-structure)
6. [Sequence Diagrams](#6-sequence-diagrams)

---

## 1. High-Level System Overview

### 1.1 Complete System Architecture

```mermaid
graph TD
    subgraph "User Interface"
        STREAMLIT[Streamlit Web UI]
        API_CLIENT[REST API Clients]
    end

    subgraph "API Layer"
        FASTAPI[FastAPI Server]
        HEALTH[/health Endpoint]
        QUERY[/query Endpoint]
        UPLOAD[/upload Endpoint]
    end

    subgraph "Multi-Agent System"
        RETRIEVER[Retriever Agent]
        REASONING[Reasoning Agent]
        GOVERNANCE[Governance Agent]
    end

    subgraph "RAG Pipeline"
        INDEXER[Document Indexer]
        VECTORDB[Vector Store]
        EMBEDDINGS[Embedding Model]
        LLM[Local LLM]
    end

    subgraph "Data Layer"
        DOCS[PDF Documents]
        LOGS[Session Logs]
        CONFIG[config.yml]
    end

    STREAMLIT --> FASTAPI
    API_CLIENT --> FASTAPI
    
    FASTAPI --> HEALTH
    FASTAPI --> QUERY
    FASTAPI --> UPLOAD
    
    QUERY --> RETRIEVER
    RETRIEVER --> REASONING
    REASONING --> GOVERNANCE
    
    RETRIEVER --> VECTORDB
    VECTORDB --> EMBEDDINGS
    REASONING --> LLM
    
    UPLOAD --> INDEXER
    INDEXER --> EMBEDDINGS
    EMBEDDINGS --> VECTORDB
    
    DOCS --> INDEXER
    CONFIG --> FASTAPI

    classDef ui fill:#e1f5fe
    classDef api fill:#fff3e0
    classDef agent fill:#e8f5e9
    classDef rag fill:#fce4ec
    classDef data fill:#f3e5f5
    
    class STREAMLIT,API_CLIENT ui
    class FASTAPI,HEALTH,QUERY,UPLOAD api
    class RETRIEVER,REASONING,GOVERNANCE agent
    class INDEXER,VECTORDB,EMBEDDINGS,LLM rag
    class DOCS,LOGS,CONFIG data
```

### 1.2 Simplified System Map

```mermaid
graph LR
    USER[User Query] --> UI[Streamlit/API]
    UI --> AGENTS[Multi-Agent System]
    AGENTS --> RAG[RAG Pipeline]
    RAG --> RESPONSE[Filtered Response]
    RESPONSE --> USER
```

---

## 2. Mid-Level Component Architecture

### 2.1 Multi-Agent Pipeline

```mermaid
flowchart TB
    subgraph "Retriever Agent"
        R_INPUT[User Query]
        R_EMBED[Query Embedding]
        R_SEARCH[Vector Search]
        R_RANK[Result Ranking]
        R_OUTPUT[Retrieved Chunks]
    end

    subgraph "Reasoning Agent"
        A_INPUT[Query + Context]
        A_PROMPT[Prompt Construction]
        A_LLM[LLM Inference]
        A_PARSE[Response Parsing]
        A_OUTPUT[Raw Answer]
    end

    subgraph "Governance Agent"
        G_INPUT[Raw Answer]
        G_RULES[Policy Rules]
        G_FILTER[Content Filter]
        G_REDACT[Sensitive Data Redaction]
        G_OUTPUT[Safe Response]
    end

    R_INPUT --> R_EMBED
    R_EMBED --> R_SEARCH
    R_SEARCH --> R_RANK
    R_RANK --> R_OUTPUT
    
    R_OUTPUT --> A_INPUT
    A_INPUT --> A_PROMPT
    A_PROMPT --> A_LLM
    A_LLM --> A_PARSE
    A_PARSE --> A_OUTPUT
    
    A_OUTPUT --> G_INPUT
    G_INPUT --> G_RULES
    G_RULES --> G_FILTER
    G_FILTER --> G_REDACT
    G_REDACT --> G_OUTPUT
```

### 2.2 API Endpoints Structure

```mermaid
flowchart TB
    subgraph "FastAPI Application"
        APP[FastAPI App]
        
        subgraph "Endpoints"
            HEALTH[GET /health]
            QUERY[POST /query]
            UPLOAD[POST /upload]
            STATUS[GET /status]
            LOGS[GET /logs]
        end
        
        subgraph "Models"
            QUERY_REQ[QueryRequest]
            QUERY_RESP[QueryResponse]
            UPLOAD_REQ[UploadRequest]
        end
    end
    
    APP --> HEALTH
    APP --> QUERY
    APP --> UPLOAD
    APP --> STATUS
    APP --> LOGS
    
    QUERY --> QUERY_REQ
    QUERY_REQ --> QUERY_RESP
```

### 2.3 Document Processing Pipeline

```mermaid
flowchart TB
    subgraph "Document Ingestion"
        PDF[PDF Upload]
        PARSE[PDF Parser]
        CHUNK[Text Chunker]
        CLEAN[Text Cleaner]
    end

    subgraph "Embedding Generation"
        TEXT[Clean Text Chunks]
        EMBED_MODEL[Embedding Model]
        VECTORS[Vector Representations]
    end

    subgraph "Storage"
        VECTORDB[(Vector Database)]
        METADATA[Metadata Store]
    end

    PDF --> PARSE
    PARSE --> CHUNK
    CHUNK --> CLEAN
    
    CLEAN --> TEXT
    TEXT --> EMBED_MODEL
    EMBED_MODEL --> VECTORS
    
    VECTORS --> VECTORDB
    TEXT --> METADATA
```

---

## 3. Low-Level Flow Diagrams

### 3.1 Query Processing Flow

```mermaid
flowchart TD
    QUERY[User Query] --> VALIDATE[Validate Input]
    VALIDATE --> SESSION[Create/Load Session]
    
    SESSION --> MEMORY_CHECK{Previous Context?}
    MEMORY_CHECK -->|Yes| LOAD_CONTEXT[Load Session Memory]
    MEMORY_CHECK -->|No| NEW_CONTEXT[Initialize Context]
    
    LOAD_CONTEXT --> RETRIEVER[Retriever Agent]
    NEW_CONTEXT --> RETRIEVER
    
    RETRIEVER --> EMBED[Embed Query]
    EMBED --> SEARCH[Vector Search]
    SEARCH --> TOP_K[Get Top-K Results]
    TOP_K --> RERANK[Rerank Results]
    
    RERANK --> CONTEXT[Build Context]
    CONTEXT --> REASONING[Reasoning Agent]
    
    REASONING --> PROMPT[Construct Prompt]
    PROMPT --> LLM[LLM Inference]
    LLM --> PARSE[Parse Response]
    
    PARSE --> GOVERNANCE[Governance Agent]
    GOVERNANCE --> CHECK_POLICY[Check Policies]
    CHECK_POLICY --> FILTER[Filter Sensitive Content]
    FILTER --> REDACT[Redact PII]
    
    REDACT --> UPDATE_MEMORY[Update Session Memory]
    UPDATE_MEMORY --> LOG[Log Interaction]
    LOG --> RESPONSE[Return Response]
```

### 3.2 Document Indexing Flow

```mermaid
flowchart TD
    UPLOAD[File Upload] --> VALIDATE[Validate File Type]
    VALIDATE --> TYPE{File Type?}
    
    TYPE -->|PDF| PDF_PARSE[PyPDF Parser]
    TYPE -->|TXT| TXT_READ[Text Reader]
    TYPE -->|Other| REJECT[Reject Upload]
    
    PDF_PARSE --> EXTRACT[Extract Text]
    TXT_READ --> EXTRACT
    
    EXTRACT --> CLEAN[Clean Text]
    CLEAN --> CHUNK[Split into Chunks]
    
    CHUNK --> OVERLAP{Overlap Strategy}
    OVERLAP --> SLIDING[Sliding Window]
    
    SLIDING --> EMBED_LOOP[For Each Chunk]
    EMBED_LOOP --> EMBED[Generate Embedding]
    EMBED --> STORE[Store in Vector DB]
    
    STORE --> INDEX_META[Index Metadata]
    INDEX_META --> COMPLETE[Indexing Complete]
```

### 3.3 Governance Filter Flow

```mermaid
flowchart TD
    INPUT[Raw LLM Response] --> POLICY_LOAD[Load Policy Rules]
    
    POLICY_LOAD --> CHECK_SENSITIVE[Check Sensitive Topics]
    CHECK_SENSITIVE --> TOPICS{Contains Sensitive?}
    
    TOPICS -->|Yes| FLAG[Flag Content]
    TOPICS -->|No| CONTINUE[Continue]
    
    FLAG --> STRATEGY{Handling Strategy}
    STRATEGY -->|Redact| REDACT[Redact Content]
    STRATEGY -->|Block| BLOCK[Block Response]
    STRATEGY -->|Warn| WARN[Add Warning]
    
    CONTINUE --> PII_CHECK[Check for PII]
    REDACT --> PII_CHECK
    WARN --> PII_CHECK
    
    PII_CHECK --> PII{Contains PII?}
    PII -->|Yes| MASK[Mask PII]
    PII -->|No| PASS[Pass Through]
    
    MASK --> FORMAT[Format Response]
    PASS --> FORMAT
    
    FORMAT --> OUTPUT[Governance-Approved Response]
    BLOCK --> SAFE_MSG[Return Safe Message]
```

---

## 4. Data Lineage

### 4.1 Query Data Lineage

```mermaid
flowchart TB
    subgraph "Input"
        USER_QUERY[User Query String]
    end

    subgraph "Processing"
        CLEAN_QUERY[Cleaned Query]
        QUERY_EMBED[Query Embedding]
        SEARCH_RESULTS[Search Results]
        CONTEXT_CHUNKS[Context Chunks]
    end

    subgraph "Inference"
        PROMPT[Constructed Prompt]
        RAW_RESPONSE[Raw LLM Response]
        FILTERED[Filtered Response]
    end

    subgraph "Output"
        FINAL_ANSWER[Final Answer]
        SESSION_LOG[Session Log]
        METRICS[Query Metrics]
    end

    USER_QUERY --> CLEAN_QUERY
    CLEAN_QUERY --> QUERY_EMBED
    QUERY_EMBED --> SEARCH_RESULTS
    SEARCH_RESULTS --> CONTEXT_CHUNKS
    
    CONTEXT_CHUNKS --> PROMPT
    PROMPT --> RAW_RESPONSE
    RAW_RESPONSE --> FILTERED
    
    FILTERED --> FINAL_ANSWER
    FILTERED --> SESSION_LOG
    FILTERED --> METRICS
```

### 4.2 Document Data Lineage

```mermaid
flowchart TB
    subgraph "Source"
        PDF_FILE[PDF Document]
    end

    subgraph "Extraction"
        RAW_TEXT[Raw Text]
        PAGES[Page Segments]
    end

    subgraph "Processing"
        CLEAN_TEXT[Cleaned Text]
        CHUNKS[Text Chunks]
        EMBEDDINGS[Vector Embeddings]
    end

    subgraph "Storage"
        VECTOR_STORE[(Vector Database)]
        DOC_METADATA[(Document Metadata)]
    end

    subgraph "Retrieval"
        QUERY_MATCH[Query-Matched Chunks]
        CONTEXT[Retrieved Context]
    end

    PDF_FILE --> RAW_TEXT
    RAW_TEXT --> PAGES
    PAGES --> CLEAN_TEXT
    CLEAN_TEXT --> CHUNKS
    CHUNKS --> EMBEDDINGS
    
    EMBEDDINGS --> VECTOR_STORE
    CHUNKS --> DOC_METADATA
    
    VECTOR_STORE --> QUERY_MATCH
    DOC_METADATA --> QUERY_MATCH
    QUERY_MATCH --> CONTEXT
```

---

## 5. Class Structure

### 5.1 Core Components

```mermaid
classDiagram
    class RA3GApp {
        +Config config
        +VectorStore vector_store
        +List~Agent~ agents
        +initialize()
        +query(question) Response
        +upload(file) bool
    }

    class Agent {
        <<abstract>>
        +String name
        +process(input)* Output
        +log_activity(message)
    }

    class RetrieverAgent {
        +VectorStore store
        +EmbeddingModel embedder
        +int top_k
        +retrieve(query) List~Chunk~
        +embed_query(query) Vector
        +search(vector) Results
    }

    class ReasoningAgent {
        +LLM model
        +PromptTemplate template
        +reason(query, context) str
        +construct_prompt(query, chunks) str
        +generate(prompt) str
    }

    class GovernanceAgent {
        +PolicyEngine policy
        +List~Pattern~ pii_patterns
        +filter(response) str
        +check_policies(text) Violations
        +redact_pii(text) str
    }

    Agent <|-- RetrieverAgent
    Agent <|-- ReasoningAgent
    Agent <|-- GovernanceAgent
    RA3GApp *-- RetrieverAgent
    RA3GApp *-- ReasoningAgent
    RA3GApp *-- GovernanceAgent
```

### 5.2 Data Models

```mermaid
classDiagram
    class QueryRequest {
        +String question
        +String session_id
        +Dict options
    }

    class QueryResponse {
        +String answer
        +List~Source~ sources
        +float confidence
        +String session_id
        +Dict metadata
    }

    class Source {
        +String document
        +int page
        +float score
        +String snippet
    }

    class Document {
        +String id
        +String filename
        +int num_pages
        +DateTime indexed_at
        +List~Chunk~ chunks
    }

    class Chunk {
        +String id
        +String document_id
        +int page
        +String text
        +Vector embedding
    }

    class Session {
        +String id
        +List~Message~ history
        +DateTime created_at
        +DateTime last_active
    }

    QueryResponse --> Source
    Document --> Chunk
    Session --> QueryRequest
    Session --> QueryResponse
```

### 5.3 Policy Engine

```mermaid
classDiagram
    class PolicyEngine {
        +List~Policy~ policies
        +evaluate(text) List~Violation~
        +apply_actions(violations) str
    }

    class Policy {
        +String name
        +String pattern
        +Action action
        +String replacement
        +check(text) Violation
    }

    class Action {
        <<enumeration>>
        REDACT
        BLOCK
        WARN
        ALLOW
    }

    class Violation {
        +Policy policy
        +String matched_text
        +int start
        +int end
    }

    PolicyEngine --> Policy
    Policy --> Action
    Policy --> Violation
```

---

## 6. Sequence Diagrams

### 6.1 Query Processing Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Streamlit UI
    participant API as FastAPI
    participant R as Retriever Agent
    participant A as Reasoning Agent
    participant G as Governance Agent
    participant V as Vector Store
    participant L as LLM

    U->>UI: Enter query
    UI->>API: POST /query {question, session_id}
    
    API->>R: retrieve(query)
    R->>R: embed_query(query)
    R->>V: similarity_search(vector, k=5)
    V-->>R: top_k chunks
    R-->>API: retrieved_context
    
    API->>A: reason(query, context)
    A->>A: construct_prompt(query, chunks)
    A->>L: generate(prompt)
    L-->>A: raw_response
    A-->>API: answer
    
    API->>G: filter(answer)
    G->>G: check_policies(answer)
    G->>G: redact_pii(answer)
    G-->>API: safe_response
    
    API->>API: update_session(session_id)
    API-->>UI: QueryResponse
    UI-->>U: Display answer with sources
```

### 6.2 Document Upload Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Streamlit UI
    participant API as FastAPI
    participant I as Indexer
    participant E as Embedding Model
    participant V as Vector Store

    U->>UI: Upload PDF file
    UI->>API: POST /upload {file}
    
    API->>API: Validate file type
    API->>I: index_document(file)
    
    I->>I: Extract text from PDF
    I->>I: Clean and preprocess text
    I->>I: Split into chunks
    
    loop For each chunk
        I->>E: embed(chunk_text)
        E-->>I: vector
        I->>V: add(vector, metadata)
    end
    
    V-->>I: Indexing complete
    I-->>API: Document indexed
    API-->>UI: Success response
    UI-->>U: Show confirmation
```

### 6.3 Session Memory Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant SM as Session Manager
    participant M as Memory Store

    Note over U,M: First Query
    U->>API: POST /query {question, session_id: null}
    API->>SM: create_session()
    SM->>SM: generate_session_id()
    SM->>M: init_memory(session_id)
    SM-->>API: session_id
    API-->>U: Response + session_id

    Note over U,M: Follow-up Query
    U->>API: POST /query {question, session_id: "abc123"}
    API->>SM: load_session("abc123")
    SM->>M: get_history("abc123")
    M-->>SM: previous_messages
    SM-->>API: session_context
    
    API->>API: Process with context
    API->>SM: update_session("abc123", new_message)
    SM->>M: append_history("abc123", message)
    API-->>U: Context-aware response
```

---

## 7. Unified System Map

```mermaid
graph TB
    subgraph "RA3G Multi-Agent RAG System"
        subgraph "Interface"
            UI[Streamlit UI]
            API[FastAPI REST]
        end

        subgraph "Agent Layer"
            RETRIEVER[Retriever]
            REASONING[Reasoning]
            GOVERNANCE[Governance]
        end

        subgraph "AI Core"
            EMBEDDER[Embedding Model]
            LLM[Local LLM]
        end

        subgraph "Storage"
            VECTOR[(Vector Store)]
            MEMORY[(Session Memory)]
            LOGS[(Activity Logs)]
        end

        subgraph "Policy"
            RULES[Policy Rules]
            PII[PII Patterns]
        end
    end

    UI --> API
    API --> RETRIEVER
    RETRIEVER --> REASONING
    REASONING --> GOVERNANCE
    
    RETRIEVER --> EMBEDDER
    RETRIEVER --> VECTOR
    REASONING --> LLM
    
    GOVERNANCE --> RULES
    GOVERNANCE --> PII
    
    API --> MEMORY
    API --> LOGS

    classDef interface fill:#e1f5fe
    classDef agent fill:#c8e6c9
    classDef ai fill:#fff3e0
    classDef storage fill:#f3e5f5
    classDef policy fill:#ffccbc

    class UI,API interface
    class RETRIEVER,REASONING,GOVERNANCE agent
    class EMBEDDER,LLM ai
    class VECTOR,MEMORY,LOGS storage
    class RULES,PII policy
```

---

## Usage

View these diagrams in:
- GitHub/GitLab markdown preview
- VS Code with Mermaid extension
- [Mermaid Live Editor](https://mermaid.live/)
