
class Config():
    #Governance Agent
    BANNED_PHRASES = ["diagnosis", "prescription", "classified", "confidential"]
    CONFIDENCE_THRESHOLD = 0.5

    #Reasoning Agent
    OLLAMA_URL = "http://localhost:11434/api/generate"
    OLLAMA_MODEL = "qwen2.5:7b-instruct"

    #Retriever Agent
    EMBED_MODEL = "all-MiniLM-L6-v2"
    EMBED_DIM = 384  # for all-MiniLM-L6-v2
    AUTO_BUILD_FAISS = True  # Automatically build FAISS index if missing
    CORPUS_DIR = "data/corpus"  # Corpus directory for auto-indexing


