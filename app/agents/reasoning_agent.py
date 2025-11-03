import os
import httpx
from typing import List, Dict
from app.utils.logger import get_logger
import json
import re
from app.config import Config

logger = get_logger("reasoning", "logs/reasoning.log")

OLLAMA_URL = os.getenv("OLLAMA_API_URL", Config.OLLAMA_URL)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", Config.OLLAMA_MODEL)


class ReasoningAgent:
    def __init__(self, ollama_url: str = OLLAMA_URL, model: str = OLLAMA_MODEL):
        self.ollama_url = ollama_url
        self.model = model
        logger.info("ReasoningAgent initialized (model=%s, url=%s)", model, ollama_url)

    def _build_prompt(self, query: str, passages: List[Dict]) -> str:
        ctx = "\n\n".join([f"[PASSAGE {i}] (score={p['score']:.3f})\n{p['text']}" for i, p in enumerate(passages)])
        prompt = (
            "You are a helpful assistant. Use the provided passages (do NOT hallucinate) to answer the query.\n\n"
            f"Query: {query}\n\n"
            "Passages:\n"
            f"{ctx}\n\n"
            "Instructions:\n"
            "1) Provide a concise answer in plain text.\n"
            "2) Provide a trace array listing which passages (by index) you used and a short note per passage.\n"
            "Return a JSON object with keys: 'answer' (string), 'trace' (list of {index:int, note:str}), and 'confidence' (float between 0 and 1).\n"
            "Be concise.\n"
        )
        return prompt

    async def _call_ollama(self, prompt: str, timeout: int = 60) -> str:
        """
        Call Ollama with streaming enabled and accumulate the 'response' chunks into a single string.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": 0.0,
            "stream": True
        }

        logger.info("Calling Ollama (streaming) at %s", self.ollama_url)
        response_text = ""

        timeout = httpx.Timeout(300.0, read=300.0)  # 5 minutes
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", self.ollama_url, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            response_text += data["response"]
                        if data.get("done"):
                            break
                    except Exception as e:
                        logger.warning("Failed to parse streaming chunk: %s", e)

        logger.info("Raw LLM output length: %d", len(response_text))
        return response_text

    def _parse_llm_output(self, raw_text: str) -> Dict:
        """
        Try to parse JSON from model output. Fallback to wrapping raw text if parsing fails.
        """
        try:
            return json.loads(raw_text)
        except Exception:
            m = re.search(r'\{.*\}', raw_text, re.S)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass
            return {
                "answer": raw_text.strip(),
                "trace": [],
                "confidence": 0.5
            }

    async def reason(self, query: str, passages: List[Dict]) -> Dict:
        prompt = self._build_prompt(query, passages)
        try:
            raw = await self._call_ollama(prompt)
            parsed = self._parse_llm_output(raw)
            logger.info("Reasoning completed for query '%s'", query)
            return parsed
        except Exception as e:
            logger.exception("Ollama call failed: %s", str(e))
            # Fallback: return first passages with low confidence
            fallback_answer = " ".join([p["text"] for p in passages[:2]])
            return {
                "answer": fallback_answer,
                "trace": [
                    {"index": i, "note": "fallback used"}
                    for i in range(min(2, len(passages)))
                ],
                "confidence": 0.4
            }
