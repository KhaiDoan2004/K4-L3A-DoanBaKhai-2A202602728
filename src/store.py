from __future__ import annotations

from typing import Any, Callable
import copy
from .chunking import _dot, compute_similarity
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401
            import os
            persist_dir = os.getenv("CHROMA_PERSIST_DIR")
            if persist_dir:
                client = chromadb.PersistentClient(path=persist_dir)
                self._collection = client.get_or_create_collection(name=collection_name)
                self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": copy.deepcopy(doc.metadata),
            "embedding": self._embedding_fn(doc.content)
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        q_emb = self._embedding_fn(query)
        results = []
        for r in records:
            score = compute_similarity(q_emb, r["embedding"])
            results.append({
                "content": r["content"],
                "score": score,
                "id": r["id"],
                "metadata": r["metadata"]
            })
            
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        if self._use_chroma and self._collection is not None:
            ids = []
            documents = []
            embeddings = []
            metadatas = []
            for d in docs:
                self._next_index += 1
                ids.append(f"{d.id}_{self._next_index}")
                documents.append(d.content)
                embeddings.append(self._embedding_fn(d.content))
                meta = copy.deepcopy(d.metadata)
                if "doc_id" not in meta:
                    meta["doc_id"] = d.id
                metadatas.append(meta)
            if ids:
                self._collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

        for d in docs:
            self._store.append(self._make_record(d))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self.search_with_filter(query, top_k=top_k)

    def get_collection_size(self) -> int:
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        if self._use_chroma and self._collection is not None:
            q_emb = self._embedding_fn(query)
            where = metadata_filter if metadata_filter else None
            
            # ChromaDB count might be less than top_k if few docs
            n_results = min(top_k, max(1, self._collection.count()))
            if n_results == 0:
                return []
                
            results = self._collection.query(
                query_embeddings=[q_emb],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            formatted_results = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    # Chroma distances are typically 1 - cosine_similarity for cosine space, 
                    # but we just need a score for sorting. Let's return a normalized score.
                    dist = results["distances"][0][i] if results["distances"] else 0
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "score": 1.0 / (1.0 + dist) # inverted distance as score
                    })
            return formatted_results
            
        # Fallback to in-memory
        if not metadata_filter:
            records = self._store
        else:
            records = []
            for r in self._store:
                match = True
                for k, v in metadata_filter.items():
                    if r["metadata"].get(k) != v:
                        match = False
                        break
                if match:
                    records.append(r)
        return self._search_records(query, records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        original_size = len(self._store)
        self._store = [r for r in self._store if r["id"] != doc_id and r["metadata"].get("doc_id") != doc_id]
        
        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(where={"doc_id": doc_id})
            except Exception:
                pass
                
        return len(self._store) < original_size
