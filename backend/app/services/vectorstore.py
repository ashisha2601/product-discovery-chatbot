from typing import Any, Dict, List, Tuple

import chromadb


# Use an in-memory (ephemeral) Chroma client for simplicity and to avoid
# local configuration/version issues. The index can be rebuilt at runtime
# using the /admin/build-index endpoint.
_client = chromadb.EphemeralClient()

_collection = _client.get_or_create_collection(name="traya_products")


def reset_collection() -> None:
    """
    Danger: deletes all vectors. Useful for local development.
    """
    _client.delete_collection("traya_products")


def index_products(
    items: List[Tuple[int, str, Dict[str, Any]]],
) -> None:
    """
    Index a list of products in Chroma.

    Each item: (product_id, text, metadata_dict)
    """
    if not items:
        return

    ids = [str(pid) for pid, _, _ in items]
    documents = [text for _, text, _ in items]
    metadatas = [meta for _, _, meta in items]

    _collection.add(ids=ids, documents=documents, metadatas=metadatas)


def query_products(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Query similar products for a free-text query.
    Returns Chroma's raw query result.
    """
    return _collection.query(query_texts=[query], n_results=top_k)


