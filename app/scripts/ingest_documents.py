"""
Equine Knowledge Base Ingestion Script
Indexes all documents from knowledge/ (and its subfolders) into Qdrant.

Usage:
    python app/scripts/ingest_documents.py            # index new/changed files only
    python app/scripts/ingest_documents.py --reset    # clear collection and re-index everything
"""

import hashlib
import json
import argparse
from pathlib import Path
from typing import List, Dict

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_core.documents import Document

# ─── Configuration ────────────────────────────────────────────────────────────
QDRANT_URL      = "http://localhost:6333"
COLLECTION_NAME = "equine_database"

EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
VECTOR_SIZE     = 768

CHUNK_SIZE      = 1024
CHUNK_OVERLAP   = 128
BATCH_SIZE      = 100

# ─── Paths ────────────────────────────────────────────────────────────────────
THIS_DIR      = Path(__file__).parent          # try2/app/scripts/
KNOWLEDGE_DIR = THIS_DIR.parent.parent / "knowledge"  # try2/knowledge/
INDEX_LOG     = KNOWLEDGE_DIR / ".indexed_hashes.json"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_index_log() -> Dict[str, str]:
    if INDEX_LOG.exists():
        return json.loads(INDEX_LOG.read_text(encoding="utf-8"))
    return {}


def _save_index_log(log: Dict[str, str]) -> None:
    INDEX_LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")


def _splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " "],
    )


def _tag(docs: List[Document], source: str, doc_type: str, topic: str) -> List[Document]:
    for d in docs:
        d.metadata.update({"source": source, "doc_type": doc_type, "topic": topic})
    return docs


# ─── Loaders ──────────────────────────────────────────────────────────────────

def load_pdfs(log: Dict[str, str]) -> List[Document]:
    docs, sp = [], _splitter()

    if not KNOWLEDGE_DIR.exists():
        print(f"  [WARN] Knowledge folder not found: {KNOWLEDGE_DIR}")
        return docs

    for pdf in sorted(KNOWLEDGE_DIR.rglob("*.pdf")):
        h = _file_hash(pdf)
        if log.get(str(pdf)) == h:
            rel = pdf.relative_to(KNOWLEDGE_DIR)
            print(f"  [SKIP] {rel}")
            continue

        rel = pdf.relative_to(KNOWLEDGE_DIR)
        category = rel.parts[0] if len(rel.parts) > 1 else "root"

        print(f"  [PDF]  {rel}")
        try:
            raw = PyPDFLoader(str(pdf)).load()
            for d in raw:
                d.metadata["category"] = category
            chunks = sp.split_documents(_tag(raw, pdf.name, "knowledge_pdf", "equine_manual"))
            docs.extend(chunks)
            log[str(pdf)] = h
            print(f"         -> {len(chunks)} chunks")
        except Exception as e:
            print(f"  [ERR]  {rel}: {e}")
    return docs


def load_knowledge_texts(log: Dict[str, str]) -> List[Document]:
    docs, sp = [], _splitter()
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    text_files = sorted(
        f for f in KNOWLEDGE_DIR.rglob("*")
        if f.suffix in (".md", ".txt") and f.is_file() and f.name != "link.txt"
    )

    for f in text_files:
        h = _file_hash(f)
        rel = f.relative_to(KNOWLEDGE_DIR)
        if log.get(str(f)) == h:
            print(f"  [SKIP] {rel}")
            continue

        category = rel.parts[0] if len(rel.parts) > 1 else "root"

        print(f"  [TEXT] {rel}")
        try:
            raw = TextLoader(str(f), encoding="utf-8").load()

            content = raw[0].page_content if raw else ""
            topic    = f.stem
            doc_type = "knowledge_base"
            if content.startswith("SOURCE:"):
                lines = content.splitlines()
                for line in lines[:6]:
                    if line.startswith("TOPIC:"):
                        topic    = line.replace("TOPIC:", "").strip()
                    if line.startswith("DOC_TYPE:"):
                        doc_type = line.replace("DOC_TYPE:", "").strip()
                    if line.startswith("CATEGORY:"):
                        category = line.replace("CATEGORY:", "").strip()
                sep_idx = next(
                    (i for i, ln in enumerate(lines) if ln.startswith("─" * 10)),
                    None,
                )
                if sep_idx is not None:
                    body = "\n".join(lines[sep_idx + 1:]).lstrip("\n")
                else:
                    body = "\n".join(lines[5:]).lstrip("\n")
                raw[0].page_content = body

            for d in raw:
                d.metadata["category"] = category

            chunks = sp.split_documents(_tag(raw, f.name, doc_type, topic))
            docs.extend(chunks)
            log[str(f)] = h
            print(f"         -> {len(chunks)} chunks")
        except Exception as e:
            print(f"  [ERR]  {rel}: {e}")
    return docs


# ─── Qdrant Setup ─────────────────────────────────────────────────────────────

def setup_collection(client: QdrantClient, reset: bool) -> None:
    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME in existing and reset:
        print(f"  [RESET] Deleting '{COLLECTION_NAME}'...")
        client.delete_collection(COLLECTION_NAME)
        existing.discard(COLLECTION_NAME)
    if COLLECTION_NAME not in existing:
        print(f"  [CREATE] Creating '{COLLECTION_NAME}'...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
    else:
        print(f"  [OK] Collection '{COLLECTION_NAME}' already exists.")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main(reset: bool = False) -> None:
    print("\n╔══════════════════════════════════════════════════════╗")
    print("║      Equine Database — Document Ingestion            ║")
    print("╚══════════════════════════════════════════════════════╝\n")

    print("→ [1/5] Connecting to Qdrant at", QDRANT_URL)
    client = QdrantClient(url=QDRANT_URL)
    setup_collection(client, reset)

    print("\n→ [2/5] Loading embedding model:", EMBEDDING_MODEL)
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    print("\n→ [3/5] Loading documents...")
    log = {} if reset else _load_index_log()
    all_docs: List[Document] = []
    all_docs.extend(load_knowledge_texts(log))
    all_docs.extend(load_pdfs(log))

    if not all_docs:
        print("\n✓ Nothing new to index. 'equine_database' is up to date.")
        col = client.get_collection(COLLECTION_NAME)
        print(f"  Current vector count: {col.points_count}")
        return

    print(f"\n  New chunks to index: {len(all_docs)}")

    print("\n→ [4/5] Upserting into 'equine_database'...")
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )
    for i in range(0, len(all_docs), BATCH_SIZE):
        batch = all_docs[i : i + BATCH_SIZE]
        vector_store.add_documents(batch)
        n = min(i + BATCH_SIZE, len(all_docs))
        print(f"  {n}/{len(all_docs)} chunks indexed...")

    print("\n→ [5/5] Saving index log...")
    _save_index_log(log)

    col = client.get_collection(COLLECTION_NAME)
    print(f"\n✓ Done!  Total vectors in 'equine_database': {col.points_count}")
    print(f"  Dashboard: http://localhost:6333/dashboard\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest equine docs into Qdrant")
    parser.add_argument("--reset", action="store_true", help="Delete and re-index everything")
    args = parser.parse_args()
    main(reset=args.reset)
