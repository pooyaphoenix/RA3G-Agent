# Quick Start Guide

## Services Setup Complete! ✅

Virtual environment created with all dependencies installed.

## To Run the Services:

### Option 1: Run the convenience script
```bash
./run_services.sh
```

### Option 2: Run in separate terminals

**Terminal 1: Start FastAPI Backend**
```bash
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2: Start Streamlit Dashboard**
```bash
source venv/bin/activate
streamlit run viewer.py
```

## Access URLs:

- **FastAPI Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Streamlit Dashboard**: http://localhost:8501

## Prerequisites:

Make sure Ollama is running with the llama3.1 model:
```bash
ollama serve  # if not already running
```

Have fun exploring the RAG Gateway! 🚀
