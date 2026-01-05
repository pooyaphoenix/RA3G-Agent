<p align="center">
<img width="468" height="190" alt="RA3G-logo" src="https://github.com/user-attachments/assets/60e2bf53-e417-4bcb-ae48-12ef268b20da" />
</p>

<p align="center">
   <b>Policy-Aware RAG Multi-Agent AI System</b>
</p>

<p align="center">
  <a href="https://github.com/pooyaphoenix/RA3G-Agent/releases">
    <img src="https://img.shields.io/github/v/release/pooyaphoenix/RA3G-Agent?color=blue&label=version" alt="Release Version"/>
  </a>
  <a href="https://github.com/pooyaphoenix/RA3G-Agent/stargazers">
    <img src="https://img.shields.io/github/stars/pooyaphoenix/RA3G-Agent?style=social" alt="GitHub stars"/>
  </a>
  <a href="mailto:pooyachavoshi@gmail.com">
    <img src="https://img.shields.io/badge/Email-Contact-blue?style=flat&logo=gmail" alt="Email"/>
  </a>
</p>

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)
```bash
git clone https://github.com/pooyaphoenix/RA3G-Agent.git
cd RA3G-Agent
docker compose up --build
```

### Option 2: Local Installation
```bash
git clone https://github.com/pooyaphoenix/RA3G-Agent.git
cd RA3G-Agent
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python ra3g.py --api-port 8010 --ui-port 8501
```

**Access the application:**
- 🌐 **Web UI**: http://localhost:8501
- 📡 **API Docs**: http://localhost:8010/docs
- 🔍 **Health Check**: http://localhost:8010/health

---

## ✨ Features

- 🔍 **Local RAG System** - Query your documents without external APIs
- 🛡️ **Governance Agent** - Automatically filters sensitive information
- 🤖 **Multi-Agent Architecture** - Retriever, Reasoning, and Governance agents
- 💾 **Session Memory** - Remembers previous queries and context
- 📊 **Real-time Logs** - Monitor agent activity with live log streaming
- 📄 **PDF Document Upload** - Automatic PDF upload and vector store building
- 🎨 **Streamlit UI** - Beautiful web interface for easy interaction
- 🔌 **REST API** - Full programmatic access via FastAPI
- ⚙️ **Fully Customizable** - Easy configuration via `config.yml`

---

## 🎬 Demo

![Interface Demo](https://github.com/user-attachments/assets/15462366-45d2-43a4-a014-a06bb9be94fe)

---

## 🏗️ Architecture

<img width="600" height="400" alt="Architecture Diagram" src="https://github.com/user-attachments/assets/ec6b9b2e-569b-43af-89a5-6c81dbdb9f03" />

**Agent Flow:**
1. **Retriever Agent** - Finds relevant passages from your corpus
2. **Reasoning Agent** - Generates answers using Ollama LLM
3. **Governance Agent** - Validates and filters responses based on policies

---

## 📖 Usage Examples

### Web UI
1. Open http://localhost:8501
2. Navigate to the **Chat** tab
3. Type your question and get instant answers

### API Request
```bash
curl -X POST 'http://localhost:8010/query' \
  -H 'Content-Type: application/json' \
  -H 'session-id: my-session' \
  -d '{
    "query": "What are the benefits of regular hand washing?",
    "top_k": 5
  }'
```

### API Response
```json
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
    }
  ],
  "retrieved": [
    {
      "id": "corpus_medical_general.txt#p0",
      "text": "...",
      "source": "corpus_medical_general.txt",
      "score": 0.51
    }
  ],
  "confidence": 0.512,
  "session_id": "my-session"
}
```

### Python Client Example
```python
import requests

response = requests.post(
    'http://localhost:8010/query',
    headers={'session-id': 'my-session'},
    json={'query': 'What is machine learning?', 'top_k': 5}
)
print(response.json()['answer'])
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/query` | Ask a question through RAG |
| `GET` | `/health` | Health check for all agents |
| `GET` | `/health/{agent}` | Health check for specific agent |
| `GET` | `/trace` | Get session query history |
| `DELETE` | `/memory/clear` | Clear session memory |
| `GET` | `/docs` | Interactive Swagger UI |
| `GET` | `/logs/stream/{log_type}` | Stream logs in real-time (SSE) |

**Try it live:** http://localhost:8010/docs

---

## 🛡️ Governance Rules

The governance agent automatically blocks or approves queries based on:

❌ **Blocked:**
- Personal names, phone numbers, addresses
- Medical records and patient data
- Confidential corporate information
- Banned phrases (configurable in `config.yml`)

✅ **Allowed:**
- General medical, scientific questions
- Educational content
- Public information

---

## 📂 Adding Documents

1. **Place your documents** in `data/corpus/` directory (`.txt` or `.md` files)
2. **Automatic indexing** - The system builds the FAISS index on startup
3. **Manual indexing** (optional):
   ```bash
   python indexer.py --corpus data/corpus
   ```

**Configuration:** Edit `config.yml` to customize corpus directory and indexing behavior.

---

## ⚙️ Configuration

All settings are in `config.yml`:

```yaml
# Ollama Configuration
OLLAMA_URL: http://localhost:11434/api/generate
OLLAMA_MODEL: qwen2.5:7b-instruct

# Embedding Model
EMBED_MODEL: all-MiniLM-L6-v2

# Confidence Thresholds
THRESHOLDS:
  retriever: 0.72
  reasoner: 0.81

# Auto-build index on startup
AUTO_BUILD_FAISS: true
CORPUS_DIR: data/corpus

# Banned phrases for governance
BANNED_PHRASES:
  - diagnosis
  - prescription
  - classified
  - confidential
```

---

## 🧪 Testing

```bash
# Health check
curl http://localhost:8010/health

# Test query
curl -X POST http://localhost:8010/query \
  -H 'Content-Type: application/json' \
  -H 'session-id: test' \
  -d '{"query": "Hello", "top_k": 3}'
```

---

## 📝 Requirements

- Python 3.8+
- Ollama (for LLM inference)
- Docker (optional, for containerized deployment)

See `requirements.txt` for Python dependencies.

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📧 Contact

**pooyachavoshi@gmail.com**

---

## 📄 License

See [LICENSE](LICENSE) file for details.
