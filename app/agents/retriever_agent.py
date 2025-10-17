import os
import numpy as np
from pathlib import Path
import pickle
from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Tuple, Dict
from app.utils.logger import get_logger
from app.config import Config
logger = get_logger("retriever", "logs/retriever.log")

INDEX_PATH = Path("app/index.faiss")
META_PATH = Path("app/index_meta.pkl")
EMBED_MODEL = os.getenv("EMBED_MODEL", Config.EMBED_MODEL)
EMBED_DIM = Config.EMBED_DIM

class RetrieverAgent:
    def __init__(self, model_name: str = EMBED_MODEL):
        logger.info("Initializing RetrieverAgent with model %s", model_name)
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.meta = []
        if INDEX_PATH.exists() and META_PATH.exists():
            self._load_index()

    def _load_index(self):
        logger.info("Loading FAISS index from %s", INDEX_PATH)
        self.index = faiss.read_index(str(INDEX_PATH))
        with open(META_PATH, "rb") as f:
            self.meta = pickle.load(f)
        logger.info("Loaded %d passages", len(self.meta))

    def save_index(self, index, meta):
        logger.info("Saving FAISS index to %s", INDEX_PATH)
        faiss.write_index(index, str(INDEX_PATH))
        with open(META_PATH, "wb") as f:
            pickle.dump(meta, f)

    def build_index_from_texts(self, texts: List[Dict[str, str]]):
        logger.info("Building new FAISS index with %d texts", len(texts))
        embeddings = self.model.encode([t["text"] for t in texts], show_progress_bar=True, convert_to_numpy=True)
        # normalize for inner product similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1
        embeddings = embeddings / norms

        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
        # store meta in same order
        meta = texts
        self.save_index(index, meta)
        self.index = index
        self.meta = meta
        logger.info("Index built and saved.")

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        if self.index is None:
            raise RuntimeError("Index not built. Run indexer to build it first.")
        q_emb = self.model.encode([query], convert_to_numpy=True)
        q_emb = q_emb / np.linalg.norm(q_emb, axis=1, keepdims=True)
        D, I = self.index.search(q_emb, top_k)
        scores = D[0].tolist()
        idxs = I[0].tolist()
        results = []
        for idx, score in zip(idxs, scores):
            if idx < 0 or idx >= len(self.meta):
                continue
            meta = self.meta[idx]
            results.append({
                "id": meta.get("id", idx),
                "text": meta.get("text"),
                "source": meta.get("source", ""),
                "score": float(score)
            })
        logger.info("Retrieved %d passages for query '%s'", len(results), query)
        return results
