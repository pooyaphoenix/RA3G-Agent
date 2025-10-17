from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from app.agents.retriever_agent import RetrieverAgent
from app.agents.reasoning_agent import ReasoningAgent
from app.agents.governance_agent import GovernanceAgent
from app.utils.logger import get_logger
from app.utils.memory import memory_store

logger = get_logger("gateway", "logs/gateway.log")

app = FastAPI(title="Policy-Aware RAG")

retriever = RetrieverAgent()
reasoner = ReasoningAgent()
governor = GovernanceAgent()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/query")
async def query(req: QueryRequest, session_id: Optional[str] = Header(default="default")):
    q = req.query
    top_k = req.top_k or 5
    logger.info("Received query: %s [session=%s]", q, session_id)

    # 1) Retrieve
    passages = retriever.retrieve(q, top_k=top_k)

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
    decision = governor.evaluate(answer, trace, confidence)
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