# 🧠 RAG Gateway with Governance Agent

This project is a **local Retrieval-Augmented Generation (RAG)** system with a built-in **governance agent** that filters sensitive or restricted information.  
It allows you to:
- Load and manage multiple **local corpora** (datasets)
- Multi-agent orchestration
- Shared memory to recall previous queries and reasoning chains
- Block or approve queries based on governance rules
- Interact with the system using REST APIs
- Easily run locally in Docker or manually with Python
- Separated Logs system in each agent

---
## Interface

![Recording2025-11-04140044-ezgif com-video-to-gif-converter](https://github.com/user-attachments/assets/15462366-45d2-43a4-a014-a06bb9be94fe)

## Architecture
<img width="600" height="400" alt="Untitled Diagram drawio" src="https://github.com/user-attachments/assets/ec6b9b2e-569b-43af-89a5-6c81dbdb9f03" />


## ⚙️ Setup Instructions
All project settings are centralized in **app/config.py** to make the system easy to configure and maintain.
#### Clone the repository
```bash
git clone https://github.com/pooyaphoenix/RAG-Gateway-with-Governance-Agent.git
cd RAG-Gateway-with-Governance-Agent
```

Build and run with Docker

```bash
docker compose up --build
```

Or run locally (without Docker)
```bash
python3 -m venv venv
source venv/bin/activate       # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
python ra3g.py --api-port 8010 --ui-port 8501
```

- --api-port: Port for FastAPI backend (default: 8010)
- --ui-port: Port for Streamlit frontend (default: 8501)
---
## Example cURL Requests
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/query' \
  -H 'accept: application/json' \
  -H 'session-id: default' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "What are the benefits of regular hand washing?",
  "top_k": 5
}'

```

Response
```bash
{
  "query": "What are the benefits of regular hand washing?",
  "answer": "Preventing the spread of infections is one of the simplest ways.",
  "governance": {
    "approved": true,
    "reason": "approved"
  },
  "trace": [
    {
      "index": 0,
      "note": "relevant passage about benefits of hand washing"
    },
    {
      "index": 4,
      "note": "direct mention of hand washing benefits"
    }
  ],
  "retrieved": [
    {
      "id": "corpus_medical_general.txt#p0",
      "text": "...",
      "source": "corpus_medical_general.txt",
      "score": 0.5118035674095154
    },
    {
      "id": "corpus_medical_governance.txt#p0",
      "text": "...",
      "score": 0.036167800426483154
    },
    {
      "id": "patient_record_001.txt#p0",
      "text": "...",
      "source": "patient_record_001.txt",
      "score": -0.003944195806980133
    }
  ],
  "confidence": 0.512,
  "session_id": "default"
}
```
---
### Governance Rules

❌ Block queries containing personal names, phone numbers, addresses, or medical records.
❌ Block queries asking for confidential corporate data.
✅ Allow general medical, scientific, or educational questions.

### API Endpoints
| Method | Endpoint        | Description                |
| ------ | --------------- | -------------------------- |
| POST   | `/query`        | Ask a question through RAG |
| GET    | `/health`       | Health check               |
| GET    | `/trace`        | Get session query history  |
| DELETE | `/memory/clear` | Clear session memory       |
| GET    | `/docs`         | Interactive Swagger UI     |


Also you can see **Swagger** in your local address: **http://localhost:8010/docs**

---
### 📂 Adding or Updating RAG Corpus

Place your text files (`.txt` or `.md`) in `data/corpus/` directory.

**Automatic Index Building (Default):**
By default, the system automatically builds the FAISS index on startup if it doesn't exist. This feature is controlled by `AUTO_BUILD_FAISS = True` in `app/config.py`.

When the FastAPI server starts, if the index is missing:
- The system will automatically scan `data/corpus/` for documents
- Build and save the FAISS index to `app/index.faiss` and `app/index_meta.pkl`
- Log the indexing process

**Manual Index Building (Optional):**
If you prefer to build the index manually or need to rebuild after updating corpus files:

```bash 
python indexer.py --corpus data/corpus
```

**Configuration:**
- Set `AUTO_BUILD_FAISS = False` in `app/config.py` to disable auto-building
- Configure the corpus directory via `CORPUS_DIR = "data/corpus"` in `app/config.py`

---

 **pooyachavoshi@gmail.com**
