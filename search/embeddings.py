"""Text → vector helpers for the semantic product search.

A single `SentenceTransformer` is loaded lazily and cached for the lifetime
of the process. Embeddings are L2-normalised so cosine distance in pgvector
and dot-product similarity agree.
"""
from __future__ import annotations

import hashlib
from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_model()
    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return vectors.tolist()


def embed_one(text: str) -> list[float]:
    return embed_texts([text])[0]


def build_content(product) -> str:
    """Compose the text we embed for a product.

    Richer content = better semantic hits. We deliberately include the
    category so "drinks" matches "Beverages" even when the word doesn't
    appear in the product name.
    """
    parts = [
        product.product_name or '',
        f'Category: {product.category}' if product.category else '',
        product.description or '',
        product.quantity_per_unit or '',
    ]
    return '\n'.join(p for p in parts if p).strip()


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
