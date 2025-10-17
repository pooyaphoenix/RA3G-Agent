# 🧠 RAG Gateway with Governance Agent

This project is a **local Retrieval-Augmented Generation (RAG)** system with a built-in **governance agent** that filters sensitive or restricted information.  
It allows you to:
- Load and manage multiple **local corpora** (datasets)
- Interact with the system using REST APIs
- Block or approve queries based on governance rules
- Easily run locally in Docker or manually with Python

---
## ⚙️ Setup Instructions

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
uvicorn app.main:app --reload --port 8000
```
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
| Method | Endpoint  | Description                |
| ------ | --------- | -------------------------- |
| POST   | `/query`  | Ask a question through RAG |
| GET    | `/health` | Health check               |
| GET    | `/docs`   | Interactive Swagger UI     |

Also you can see **Swagger** in your local address: **http://localhost:8010/docs**
---
### 📂 Adding or Updating RAG Corpus
Place your text files (.txt) in data/corpus/ directory then run this command
```bash 
python indexer.py --corpus data/corpus
```
index.faiss and index_meta.pkl should be generated in app/ directory

---
Developed by Pooya Chavoshi | **pooyachavoshi@gmail.com**
