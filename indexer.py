from pathlib import Path
from agents.retriever_agent import RetrieverAgent
import os
import argparse

def load_corpus(corpus_dir: Path):
    docs = []
    id_counter = 0
    for p in sorted(corpus_dir.glob("*")):
        if p.suffix.lower() not in [".txt", ".md"]:
            continue
        text = p.read_text(encoding='utf-8').strip()
        if not text:
            continue
        # naive chunking by paragraphs to create smaller passages
        paras = [para.strip() for para in text.split("\n\n") if para.strip()]
        for i, para in enumerate(paras):
            docs.append({"id": f"{p.name}#p{i}", "text": para, "source": str(p.name)})
            id_counter += 1
    return docs

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=str, default="data/corpus")
    args = parser.parse_args()
    corpus_dir = Path(args.corpus)
    docs = load_corpus(corpus_dir)
    if not docs:
        print("No documents found in", corpus_dir)
        exit(1)
    retriever = RetrieverAgent()
    retriever.build_index_from_texts(docs)
    print("Index built with", len(docs), "passages.")
