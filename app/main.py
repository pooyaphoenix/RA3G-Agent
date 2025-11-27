from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import asyncio
import os
import json
from pathlib import Path
from app.agents.retriever_agent import RetrieverAgent
from app.agents.reasoning_agent import ReasoningAgent
from app.agents.governance_agent import GovernanceAgent
from app.utils.logger import get_logger
from app.utils.memory import memory_store

logger = get_logger("gateway", "logs/gateway.log")

app = FastAPI(title="Policy-Aware RAG")

# Lazy initialization to avoid FAISS mutex issues
_retriever = None
_reasoner = None
_governor = None

def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = RetrieverAgent()
    return _retriever

def get_reasoner():
    global _reasoner
    if _reasoner is None:
        _reasoner = ReasoningAgent()
    return _reasoner

def get_governor():
    global _governor
    if _governor is None:
        _governor = GovernanceAgent()
    return _governor

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

@app.get("/health")
async def health_check():
    retriever = get_retriever()
    reasoner = get_reasoner()
    
    if retriever and retriever.index is not None:
        index_loaded = True
    else:
        index_loaded = False
    
    if reasoner and await reasoner.reason("ping", []):
        ollama_status = True
    else:
        ollama_status = False

    if index_loaded and ollama_status:
        logger.info("Health check passed")
        return {"status": "ok", "index_loaded": index_loaded, "ollama_status": ollama_status}
    else:
        logger.error("Health check failed")
        raise HTTPException(status_code=503, detail="Health check failed")

@app.post("/query")
async def query(req: QueryRequest, session_id: Optional[str] = Header(default="default")):
    q = req.query
    top_k = req.top_k or 5
    logger.info("Received query: %s [session=%s]", q, session_id)

    # 1) Retrieve
    retriever = get_retriever()
    reasoner = get_reasoner()
    governor = get_governor()
    
    passages = retriever.retrieve(q, top_k=top_k)
    retriever_confidence = 0.0
    if passages:
        try:
            retriever_confidence = max((p.get("score", 0.0) for p in passages), default=0.0)
        except ValueError:
            retriever_confidence = 0.0

    # Memory context to reasoning
    previous_turns = memory_store.get(session_id)
    if previous_turns:
        history_text = "\n".join(
            [f"[MEMORY {i}] Q: {turn['query']} | A: {turn['answer']}" for i, turn in enumerate(previous_turns)]
        )
        # Append memory context to the query
        q = f"Previous context:\n{history_text}\n\nNew Query:\n{req.query}"

    # 2) Reason
    reasoning_result = await reasoner.reason(q, passages)
    answer = reasoning_result.get("answer", "")
    trace = reasoning_result.get("trace", [])
    confidence = float(reasoning_result.get("confidence", 0.0))

    # 3) Govern
    decision = governor.evaluate(
        answer,
        trace,
        confidence,
        retriever_confidence=retriever_confidence,
    )
    final_answer = decision.get("redacted_answer", answer)

    # 4) Save memory
    memory_store.add(session_id, req.query, final_answer, trace)

    response = {
        "query": req.query,
        "answer": final_answer,
        "governance": {"approved": decision["approved"], "reason": decision["reason"]},
        "trace": trace,
        "retrieved": passages,
        "confidence": confidence,
        "session_id": session_id
    }
    return response

@app.get("/trace")
async def get_trace(session_id: Optional[str] = Header(default="default")):
    history = memory_store.get(session_id)
    if not history:
        raise HTTPException(status_code=404, detail="No trace found for this session")
    return {
        "session_id": session_id,
        "turns": history
    }

@app.delete("/memory/clear")
def clear_memory(session_id: Optional[str] = Header(default="default")):
    history = memory_store.get(session_id)
    if not history:
        raise HTTPException(status_code=404, detail="This session not found")
    memory_store.clear(session_id)
    return {"message": f"Memory cleared for session {session_id}"}

# Log streaming endpoint
LOG_FILES = {
    "gateway": "logs/gateway.log",
    "retriever": "logs/retriever.log",
    "reasoning": "logs/reasoning.log",
    "governance": "logs/governance.log",
}

async def tail_log_file(log_type: str):
    """Generator function to tail a log file and yield new lines via SSE."""
    log_path = LOG_FILES.get(log_type.lower())
    if not log_path:
        yield f"data: {json.dumps({'error': f'Unknown log type: {log_type}'})}\n\n"
        return
    
    log_file = Path(log_path)
    if not log_file.exists():
        yield f"data: {json.dumps({'error': f'Log file not found: {log_path}'})}\n\n"
        return
    
    # Read existing content first (last 100 lines)
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Send last 100 lines
            for line in lines[-100:]:
                if line.strip():
                    yield f"data: {json.dumps({'line': line.rstrip()})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    # Now tail the file
    last_position = log_file.stat().st_size if log_file.exists() else 0
    
    while True:
        try:
            if not log_file.exists():
                await asyncio.sleep(1)
                continue
            
            current_size = log_file.stat().st_size
            
            if current_size > last_position:
                # Use binary mode for accurate position tracking
                with open(log_file, 'rb') as f:
                    f.seek(last_position)
                    new_content = f.read()
                    if new_content:
                        # Decode and split into lines
                        try:
                            new_text = new_content.decode('utf-8')
                            new_lines = new_text.splitlines()
                            for line in new_lines:
                                if line.strip():
                                    yield f"data: {json.dumps({'line': line.rstrip()})}\n\n"
                            last_position = f.tell()
                        except UnicodeDecodeError:
                            # Handle partial UTF-8 sequences at the end
                            try:
                                # Try to decode up to the last complete line
                                new_text = new_content[:-1].decode('utf-8')
                                new_lines = new_text.splitlines()
                                for line in new_lines:
                                    if line.strip():
                                        yield f"data: {json.dumps({'line': line.rstrip()})}\n\n"
                                last_position = f.tell() - 1  # Keep the last byte for next read
                            except:
                                # If still fails, skip this update
                                await asyncio.sleep(0.5)
                                continue
            
            await asyncio.sleep(0.5)  # Check every 500ms
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            await asyncio.sleep(1)

@app.get("/logs/stream/{log_type}")
async def stream_logs(log_type: str):
    """Stream logs in real-time using Server-Sent Events (SSE)."""
    if log_type.lower() not in LOG_FILES:
        raise HTTPException(
            status_code=404, 
            detail=f"Unknown log type: {log_type}. Available: {', '.join(LOG_FILES.keys())}"
        )
    
    return StreamingResponse(
        tail_log_file(log_type.lower()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )