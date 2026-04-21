from django.db import models
from pgvector.django import VectorField, HnswIndex

EMBEDDING_DIM = 384

class ProductEmbedding(models.Model):
    # product_id is the PK on the MySQL side; here it's just an int we trust
    product_id = models.IntegerField(primary_key=True)
    product_name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True)
    content = models.TextField()
    content_hash = models.CharField(max_length=64, db_index=True)
    embedding = VectorField(dimensions=EMBEDDING_DIM)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_embeddings'
        indexes = [
            HnswIndex(
                name='product_embedding_hnsw',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops'],
            ),
        ]

    def __str__(self):
        return f'{self.product_id}: {self.product_name}'