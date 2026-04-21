"""Application-layer helpers for semantic search.

We can't use a SQL JOIN because products live in MySQL and embeddings live
in Postgres. Instead we query the vector DB for IDs + distances, then
hydrate product rows from MySQL in a single follow-up query.
"""
from __future__ import annotations

from pgvector.django import CosineDistance

from catalog.models import Products

from .embeddings import embed_one
from .models import ProductEmbedding


def semantic_search(query: str, k: int = 10, max_distance: float = 1.0):
    """Return the `k` ProductEmbedding rows nearest to the query text."""
    query = (query or '').strip()
    if not query:
        return []
    q_vec = embed_one(query)
    return list(
        ProductEmbedding.objects
        .annotate(distance=CosineDistance('embedding', q_vec))
        .filter(distance__lt=max_distance)
        .order_by('distance')[:k]
    )


def similar_products(product_id: int, k: int = 5):
    """Return the `k` products most similar to the given one (excluding itself)."""
    try:
        anchor = ProductEmbedding.objects.get(product_id=product_id)
    except ProductEmbedding.DoesNotExist:
        return []
    return list(
        ProductEmbedding.objects
        .annotate(distance=CosineDistance('embedding', anchor.embedding))
        .exclude(product_id=product_id)
        .order_by('distance')[:k]
    )


def hydrate_products(rows):
    """Attach the MySQL `Products` row to each embedding row as `.product`.

    Preserves the original ordering (which is by distance).
    """
    if not rows:
        return rows
    ids = [r.product_id for r in rows]
    products = {p.id: p for p in Products.objects.filter(id__in=ids)}
    for r in rows:
        r.product = products.get(r.product_id)
        r.similarity = max(0.0, 1.0 - float(r.distance))
    return rows
