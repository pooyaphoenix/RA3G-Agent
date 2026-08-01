from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
import asyncio
import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from app.agents.retriever_agent import RetrieverAgent
from app.agents.reasoning_agent import ReasoningAgent
from app.agents.governance_agent import GovernanceAgent
from app.utils.logger import get_logger
from app.utils.memory import memory_store
from app.routes.upload_routes import router as upload_router
from app.config import Config
import yaml


logger = get_logger("gateway", "logs/gateway.log")

app = FastAPI(title="RA3G Agent Gateway", version="0.2.0")

app.include_router(upload_router, tags=["Documents"])

# Lazy initialization to avoid FAISS mutex issues
_retriever = None
_reasoner = None
_governor = None

# Agent status tracking
_agent_start_times = {
    "gateway": time.time(),
    "retriever": None,
    "reasoning": None,
    "governance": None
}
_agent_last_activity = {
    "gateway": time.time(),
    "retriever": None,
    "reasoning": None,
    "governance": None
}
_agent_error_counts = {
    "gateway": 0,
    "retriever": 0,
    "reasoning": 0,
    "governance": 0
}
_agent_errors = {
    "gateway": [],
    "retriever": [],
    "reasoning": [],
    "governance": []
}

def get_retriever():
    global _retriever, _agent_start_times, _agent_last_activity
    if _retriever is None:
        _retriever = RetrieverAgent()
        _agent_start_times["retriever"] = time.time()
    _agent_last_activity["retriever"] = time.time()
    return _retriever

def get_reasoner():
    global _reasoner, _agent_start_times, _agent_last_activity
    if _reasoner is None:
        _reasoner = ReasoningAgent()
        _agent_start_times["reasoning"] = time.time()
    _agent_last_activity["reasoning"] = time.time()
    return _reasoner

def get_governor():
    global _governor, _agent_start_times, _agent_last_activity
    if _governor is None:
        _governor = GovernanceAgent()
        _agent_start_times["governance"] = time.time()
    _agent_last_activity["governance"] = time.time()
    return _governor

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class PIIFiltersUpdate(BaseModel):
    email: Optional[bool] = None
    phone: Optional[bool] = None
    ip: Optional[bool] = None
    date: Optional[bool] = None
    id: Optional[bool] = None
    name: Optional[bool] = None


def _get_config_path() -> str:
    return getattr(Config, "_config_path", "config.yml")


@app.get("/pii/config")
async def get_pii_config():
    """Fetch current PII filter settings (which types are redacted)."""
    filters = Config.get("PII_FILTERS")
    if not isinstance(filters, dict):
        filters = {
            "email": True, "phone": True, "ip": True,
            "date": True, "id": True, "name": True,
        }
    return {"pii_filters": {k: bool(v) for k, v in filters.items()}}


@app.put("/pii/config")
async def update_pii_config(body: PIIFiltersUpdate):
    """Update PII filter settings. Changes are saved to config file and take effect immediately."""
    path = _get_config_path()
    if not os.path.exists(path):
        raise HTTPException(status_code=500, detail="Configuration file not found")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if "PII_FILTERS" not in data or not isinstance(data["PII_FILTERS"], dict):
        data["PII_FILTERS"] = {
            "email": True, "phone": True, "ip": True,
            "date": True, "id": True, "name": True,
        }
    updates = body.model_dump(exclude_none=True)
    for key, value in updates.items():
        if key in data["PII_FILTERS"]:
            data["PII_FILTERS"][key] = value
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    Config.reload(path)
    return {"pii_filters": data["PII_FILTERS"], "message": "PII config updated and applied."}


class ConfidenceTuningRequest(BaseModel):
    weights: Dict[str, float]


@app.get("/confidence/tuning")
async def get_confidence_tuning():
    """Fetch current per-corpus confidence weights."""
    weights = Config.get("CORPUS_WEIGHTS") or {}
    return {"weights": weights}


@app.put("/confidence/tuning")
async def update_confidence_tuning(body: ConfidenceTuningRequest):
    """Update per-corpus reliability weights and persist to config file."""
    path = _get_config_path()
    if not os.path.exists(path):
        raise HTTPException(status_code=500, detail="Configuration file not found")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data["CORPUS_WEIGHTS"] = {k: float(v) for k, v in body.weights.items()}
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    Config.reload(path)
    return {"weights": data["CORPUS_WEIGHTS"], "message": "Corpus weights updated and saved."}


def _check_ollama_reachable() -> bool:
    """Lightweight check — does NOT call reason(), just pings the Ollama base URL."""
    try:
        import requests as _req
        ollama_url = Config.get("OLLAMA_URL") or "http://localhost:11434/api/generate"
        # Derive base: http://host:port
        parts = ollama_url.split("/")
        base = "/".join(parts[:3])
        r = _req.get(f"{base}/", timeout=2)
        return r.status_code < 500
    except Exception:
        return False


@app.get("/health")
async def health_check():
    """Lightweight overall health summary — never initialises agents as a side-effect."""
    agents_status: Dict[str, str] = {}

    # Gateway: always alive if this handler runs
    agents_status["gateway"] = "healthy"

    # Retriever: inspect global without forcing init
    index_loaded = False
    if _retriever is None:
        agents_status["retriever"] = "not_started"
    elif _retriever.index is None:
        agents_status["retriever"] = "down"
    else:
        agents_status["retriever"] = "healthy"
        index_loaded = True

    # Reasoning: check Ollama reachability, no LLM call
    ollama_ok = _check_ollama_reachable()
    if _reasoner is None:
        agents_status["reasoning"] = "not_started" if not ollama_ok else "healthy"
    else:
        agents_status["reasoning"] = "healthy" if ollama_ok else "down"
    ollama_status = ollama_ok

    # Governance: inspect global
    if _governor is None:
        agents_status["governance"] = "not_started"
    else:
        agents_status["governance"] = "healthy"

    any_down  = any(s in ("down", "error") for s in agents_status.values())
    all_good  = all(s in ("healthy", "not_started") for s in agents_status.values())
    overall   = "ok" if all_good and not any_down else "degraded"

    logger.info("Health check: %s %s", overall, agents_status)
    return {
        "status": overall,
        "index_loaded": index_loaded,
        "ollama_status": ollama_status,
        "agents": agents_status,
        "timestamp": datetime.now().isoformat(),
    }

@app.get("/health/{agent}")
async def get_agent_health(agent: str):
    """Detailed per-agent health — does NOT initialise agents as a side-effect."""
    agent = agent.lower()
    valid_agents = ["gateway", "retriever", "reasoning", "governance"]
    if agent not in valid_agents:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown agent: {agent}. Valid: {', '.join(valid_agents)}",
        )

    # ── Uptime ────────────────────────────────────────────────
    start_time = _agent_start_times.get(agent)
    if start_time:
        uptime_str = str(timedelta(seconds=int(time.time() - start_time)))
    else:
        uptime_str = "N/A"

    # ── Last activity ─────────────────────────────────────────
    last_activity_time = _agent_last_activity.get(agent)
    if last_activity_time:
        secs = int(time.time() - last_activity_time)
        if secs < 60:
            last_activity_str = f"{secs}s ago"
        elif secs < 3600:
            last_activity_str = f"{secs // 60}m ago"
        else:
            last_activity_str = f"{secs // 3600}h ago"
    else:
        last_activity_str = "N/A"

    error_count = _agent_error_counts.get(agent, 0)
    errors = _agent_errors.get(agent, [])[-10:]
    status = "unknown"
    response_latency = None

    try:
        if agent == "gateway":
            status = "healthy"
            response_latency = 0.001

        elif agent == "retriever":
            # Inspect global — NO forced init
            if _retriever is None:
                status = "not_started"
            elif _retriever.index is None:
                status = "down"
            else:
                t0 = time.time()
                try:
                    _retriever.retrieve("health check", top_k=1)
                    response_latency = time.time() - t0
                    status = "healthy" if response_latency < 0.5 else "slow"
                except Exception as exc:
                    status = "error"
                    _agent_error_counts[agent] += 1
                    _agent_errors[agent].append(f"{datetime.now()}: {exc}")

        elif agent == "reasoning":
            # Lightweight: ping Ollama base URL, never call reason()
            t0 = time.time()
            ok = _check_ollama_reachable()
            response_latency = time.time() - t0
            if _reasoner is None:
                status = "not_started" if ok else "down"
            else:
                status = "healthy" if ok else "down"
                if not ok:
                    _agent_error_counts[agent] += 1
                    _agent_errors[agent].append(f"{datetime.now()}: Ollama not reachable")

        elif agent == "governance":
            if _governor is None:
                status = "not_started"
            else:
                t0 = time.time()
                try:
                    _governor.evaluate("health check", [], 0.9)
                    response_latency = time.time() - t0
                    status = "healthy" if response_latency < 0.1 else "slow"
                except Exception as exc:
                    status = "error"
                    _agent_error_counts[agent] += 1
                    _agent_errors[agent].append(f"{datetime.now()}: {exc}")

    except Exception as exc:
        status = "error"
        _agent_error_counts[agent] += 1
        _agent_errors[agent].append(f"{datetime.now()}: {exc}")
        logger.error("Error checking %s health: %s", agent, exc)

    # ── Recent logs ────────────────────────────────────────────
    log_file_map = {
        "gateway":    "logs/gateway.log",
        "retriever":  "logs/retriever.log",
        "reasoning":  "logs/reasoning.log",
        "governance": "logs/governance.log",
    }
    recent_logs: list = []
    log_file = log_file_map.get(agent)
    if log_file and os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                recent_logs = [ln.strip() for ln in f.readlines()[-10:] if ln.strip()]
        except Exception:
            pass

    return {
        "agent": agent,
        "status": status,
        "uptime": uptime_str,
        "last_activity": last_activity_str,
        "response_latency": response_latency,
        "error_count": error_count,
        "errors": errors,
        "recent_logs": recent_logs,
        "timestamp": datetime.now().isoformat(),
    }

@app.post("/query")
async def query(req: QueryRequest, session_id: Optional[str] = Header(default="default")):
    q = req.query
    top_k = req.top_k or 5
    logger.info("Received query: %s [session=%s]", q, session_id)
    _agent_last_activity["gateway"] = time.time()

    # 1) Retrieve
    try:
        retriever = get_retriever()
        reasoner = get_reasoner()
        governor = get_governor()
        
        passages = retriever.retrieve(q, top_k=top_k)
    except Exception as e:
        _agent_error_counts["retriever"] += 1
        _agent_errors["retriever"].append(f"{datetime.now()}: {str(e)}")
        logger.error(f"Retriever error: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")
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
    try:
        reasoning_result = await reasoner.reason(q, passages)
        answer = reasoning_result.get("answer", "")
        trace = reasoning_result.get("trace", [])
        confidence = float(reasoning_result.get("confidence", 0.0))
    except Exception as e:
        _agent_error_counts["reasoning"] += 1
        _agent_errors["reasoning"].append(f"{datetime.now()}: {str(e)}")
        logger.error(f"Reasoning error: {e}")
        raise HTTPException(status_code=500, detail=f"Reasoning failed: {str(e)}")

    # 3) Govern
    try:
        decision = governor.evaluate(
            answer,
            trace,
            confidence,
            retriever_confidence=retriever_confidence,
        )
    except Exception as e:
        _agent_error_counts["governance"] += 1
        _agent_errors["governance"].append(f"{datetime.now()}: {str(e)}")
        logger.error(f"Governance error: {e}")
        # Don't fail the query if governance fails, just log it
    final_answer = decision.get("redacted_answer", answer)

    # 4) Save memory
    memory_store.add(session_id, req.query, final_answer, trace)

    # 5) Audit log (PostgreSQL hybrid storage, Issue #38)
    try:
        from app.db.store import insert_query_log
        insert_query_log(
            session_id=session_id,
            query_text=req.query,
            redacted_response=final_answer,
            governance_decision={"approved": decision["approved"], "reason": decision["reason"]},
        )
    except Exception:
        pass

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
        # Keep connection alive even after error
        while True:
            await asyncio.sleep(30)
            yield f": keep-alive\n\n"
    
    log_file = Path(log_path)
    if not log_file.exists():
        yield f"data: {json.dumps({'error': f'Log file not found: {log_path}'})}\n\n"
        # Keep connection alive and check if file gets created
        ping_counter = 0
        while True:
            ping_counter += 1
            if ping_counter >= 30:  # Every 15 seconds
                yield f": keep-alive\n\n"
                ping_counter = 0
            # Check if file was created
            if log_file.exists():
                break
            await asyncio.sleep(0.5)
    
    # Read existing content first (last 50 lines for faster initial load)
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Send last 50 lines in batches for better performance
            existing_lines = [line.rstrip() for line in lines[-50:] if line.strip()]
            # Send in batches of 10 to avoid blocking
            for i in range(0, len(existing_lines), 10):
                batch = existing_lines[i:i+10]
                for line in batch:
                    yield f"data: {json.dumps({'line': line})}\n\n"
                # Small delay between batches to allow rendering
                if i + 10 < len(existing_lines):
                    await asyncio.sleep(0.05)
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    # Now tail the file
    last_position = log_file.stat().st_size if log_file.exists() else 0
    ping_counter = 0
    
    while True:
        try:
            # Send keep-alive ping every 15 seconds
            ping_counter += 1
            if ping_counter >= 30:  # 30 * 0.5s = 15 seconds
                yield f": keep-alive\n\n"
                ping_counter = 0
            
            if not log_file.exists():
                await asyncio.sleep(0.5)
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
            # Log error but don't exit - keep connection alive
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
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Cache-Control",
        }
    )