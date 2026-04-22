from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from .services import hydrate_products, semantic_search


class SemanticSearchServiceTests(SimpleTestCase):
    @patch('search.services.embed_one')
    def test_empty_query_short_circuits_without_embedding(self, embed_one_mock):
        self.assertEqual(semantic_search('   '), [])
        embed_one_mock.assert_not_called()

    @patch('search.services.Products.objects')
    def test_hydrate_products_preserves_order_and_sets_similarity(self, products_mgr):
        tea = SimpleNamespace(id=1, product_name='Tea')
        coffee = SimpleNamespace(id=2, product_name='Coffee')
        products_mgr.filter.return_value = [tea, coffee]

        rows = [
            SimpleNamespace(product_id=2, distance=0.12),
            SimpleNamespace(product_id=1, distance=0.35),
        ]

        hydrated = hydrate_products(rows)

        self.assertEqual([row.product_id for row in hydrated], [2, 1])
        self.assertIs(hydrated[0].product, coffee)
        self.assertIs(hydrated[1].product, tea)
        self.assertAlmostEqual(hydrated[0].similarity, 0.88)
        self.assertAlmostEqual(hydrated[1].similarity, 0.65)
