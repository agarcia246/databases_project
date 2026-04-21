"""Build/refresh the product embedding index.

Incremental by default: products whose embedded content hasn't changed
(tracked by a SHA-256 hash) are skipped. Pass --force to rebuild everything.

Usage:
    python manage.py embed_products
    python manage.py embed_products --force
"""
from django.core.management.base import BaseCommand

from catalog.models import Products
from search.embeddings import build_content, content_hash, embed_texts
from search.models import ProductEmbedding


BATCH = 32


class Command(BaseCommand):
    help = 'Embed Northwind products into the pgvector index (incremental).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-embed every product, ignoring the content hash.',
        )

    def handle(self, *args, force=False, **opts):
        products = list(Products.objects.all())
        existing = {
            pe.product_id: pe.content_hash
            for pe in ProductEmbedding.objects.all()
        }

        to_embed = []
        for p in products:
            content = build_content(p)
            if not content:
                continue
            h = content_hash(content)
            if force or existing.get(p.id) != h:
                to_embed.append((p, content, h))

        self.stdout.write(
            f'{len(products)} products in catalog, '
            f'{len(to_embed)} need (re)embedding.'
        )

        for i in range(0, len(to_embed), BATCH):
            chunk = to_embed[i:i + BATCH]
            vectors = embed_texts([c for _, c, _ in chunk])
            for (p, content, h), vec in zip(chunk, vectors):
                ProductEmbedding.objects.update_or_create(
                    product_id=p.id,
                    defaults={
                        'product_name': (p.product_name or '')[:100],
                        'category': (p.category or '')[:100],
                        'content': content,
                        'content_hash': h,
                        'embedding': vec,
                    },
                )
            self.stdout.write(
                f'  {min(i + BATCH, len(to_embed))}/{len(to_embed)} embedded'
            )

        live_ids = {p.id for p in products}
        stale = ProductEmbedding.objects.exclude(product_id__in=live_ids)
        removed = stale.count()
        stale.delete()

        self.stdout.write(self.style.SUCCESS(
            f'done: {len(to_embed)} (re)embedded, {removed} stale removed, '
            f'{ProductEmbedding.objects.count()} total vectors.'
        ))
