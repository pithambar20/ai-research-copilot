from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from app.config import Config

class VectorStore:
    def __init__(self, persist_dir: Path = Config.CHROMA_PERSIST_DIR):
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection_name = "research_papers"
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def index_paper_chunks(self, paper_id: str, paper_title: str, chunks: List[Dict[str, Any]]):
        """
        Indexes chunks into ChromaDB with rich metadata for grounding & citations.
        """
        if not chunks:
            return

        ids = []
        documents = []
        metadatas = []

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{paper_id}_c_{idx}"
            ids.append(chunk_id)
            documents.append(chunk["text"])
            metadatas.append({
                "paper_id": paper_id,
                "paper_title": paper_title[:100],
                "page": int(chunk.get("page", 1)),
                "section": str(chunk.get("section", "General")),
                "chunk_index": idx
            })

        # Chroma batches can be added
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.add(
                ids=ids[i:i + batch_size],
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size]
            )

    def search(
        self,
        query: str,
        paper_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Searches relevant chunks. If paper_id is provided, scopes the search to that paper.
        """
        where_filter = {"paper_id": paper_id} if paper_id else None

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter
        )

        formatted_results = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            dists = results["distances"][0] if "distances" in results and results["distances"] else [0] * len(docs)
            ids = results["ids"][0] if "ids" in results else [""] * len(docs)

            for doc, meta, dist, cid in zip(docs, metas, dists, ids):
                formatted_results.append({
                    "chunk_id": cid,
                    "text": doc,
                    "page": meta.get("page", 1),
                    "section": meta.get("section", "General"),
                    "paper_id": meta.get("paper_id", ""),
                    "paper_title": meta.get("paper_title", ""),
                    "similarity": round(1.0 - dist, 4) if dist is not None else 1.0
                })

        return formatted_results

    def delete_paper(self, paper_id: str):
        """Removes all indexed chunks for a deleted paper."""
        try:
            self.collection.delete(where={"paper_id": paper_id})
        except Exception:
            pass
