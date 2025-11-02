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
        
        # Check if index exists, auto-build if enabled and missing
        if not (INDEX_PATH.exists() and META_PATH.exists()):
            if Config.AUTO_BUILD_FAISS:
                logger.info("FAISS index not found. Auto-building from corpus...")
                self._auto_build_index()
            else:
                logger.warning("FAISS index not found. Set AUTO_BUILD_FAISS=True to auto-build.")
        else:
            self._load_index()
    
    def _auto_build_index(self):
        """Automatically build FAISS index from corpus directory if missing."""
        corpus_dir = Path(Config.CORPUS_DIR)
        
        if not corpus_dir.exists():
            logger.error("Corpus directory not found: %s", corpus_dir)
            logger.warning("Cannot auto-build index. Please create the corpus directory and add documents.")
            return
        
        logger.info("Loading corpus from %s", corpus_dir)
        docs = self._load_corpus(corpus_dir)
        
        if not docs:
            logger.error("No documents found in %s. Cannot build index.", corpus_dir)
            return
        
        logger.info("Building FAISS index with %d passages", len(docs))
        self.build_index_from_texts(docs)
        logger.info("Auto-build complete. Index created with %d passages", len(docs))
    
    def _load_corpus(self, corpus_dir: Path) -> List[Dict[str, str]]:
        """Load documents from corpus directory."""
        docs = []
        
        # Find all .txt and .md files in corpus directory
        for p in sorted(corpus_dir.glob("*")):
            if p.suffix.lower() not in [".txt", ".md"]:
                continue
            
            try:
                text = p.read_text(encoding='utf-8').strip()
                if not text:
                    continue
                
                # Naive chunking by paragraphs to create smaller passages
                paras = [para.strip() for para in text.split("\n\n") if para.strip()]
                for i, para in enumerate(paras):
                    docs.append({
                        "id": f"{p.name}#p{i}",
                        "text": para,
                        "source": str(p.name)
                    })
            except Exception as e:
                logger.warning("Failed to load file %s: %s", p, e)
        
        return docs

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
