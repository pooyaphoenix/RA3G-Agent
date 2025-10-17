from collections import defaultdict
from typing import List, Dict

class MemoryStore:
    def __init__(self):
        # session_id -> list of dicts {query, answer, trace}
        self.memory = defaultdict(list)

    def add(self, session_id: str, query: str, answer: str, trace: list):
        self.memory[session_id].append({
            "query": query,
            "answer": answer,
            "trace": trace
        })

    def get(self, session_id: str) -> List[Dict]:
        return self.memory.get(session_id, [])

    def clear(self, session_id: str):
        if session_id in self.memory:
            del self.memory[session_id]

memory_store = MemoryStore()
