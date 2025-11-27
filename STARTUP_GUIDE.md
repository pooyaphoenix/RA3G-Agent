# RA3G Agent - Startup Guide

## After Docker Build Completes

### 1. Stop Old Container and Start New One

```bash
cd RA3G-Agent
docker-compose down
docker-compose up -d
```

### 2. Check Container Status

```bash
docker ps
# You should see:
# - rag_gateway (ports 8010, 8501)
# - ollama (port 11434)
```

### 3. Verify Services

**FastAPI Backend:**
```bash
curl http://localhost:8010/health
# Should return: {"status": "ok", ...}

# View API docs:
open http://localhost:8010/docs
```

**Streamlit UI:**
```bash
open http://localhost:8501
```

### 4. Test New Features

**Real-time Log Streaming:**
- Go to Streamlit UI → "Logs" tab
- Enable "🔴 Live Logs" toggle
- Select a log type (Gateway, Retriever, Reasoning, or Governance)
- Logs will stream in real-time with error/warning highlighting

**Health Check:**
```bash
curl http://localhost:8010/health
```

**Log Streaming Endpoint (SSE):**
```bash
curl -N http://localhost:8010/logs/stream/gateway
```

### 5. View Logs

```bash
# Container logs
docker logs rag_gateway -f

# Application logs (on host)
tail -f logs/gateway.log
tail -f logs/retriever.log
tail -f logs/reasoning.log
tail -f logs/governance.log
```

### 6. Troubleshooting

**If FastAPI doesn't respond:**
```bash
docker logs rag_gateway --tail 50
```

**If agents fail to initialize:**
- Check Ollama is running: `docker ps | grep ollama`
- Check Ollama models: `curl http://localhost:11434/api/tags`

**Rebuild if needed:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Features Included

✅ Real-time log streaming (SSE)
✅ Live Logs toggle in Streamlit UI
✅ Pause/Resume log streaming
✅ Error/Warning highlighting
✅ Health check endpoint
✅ Lazy agent initialization (fixes mutex issues)

