from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from .views import sales_trends


class SalesTrendTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch('reporting.views.render')
    @patch('reporting.views.Count')
    @patch('reporting.views.Orders.objects')
    def test_sales_trends_counts_distinct_orders(
        self,
        orders_mgr,
        count_mock,
        render_mock,
    ):
        monthly_stage = MagicMock()
        values_stage = MagicMock()
        values_stage.annotate.return_value.order_by.return_value = []
        orders_mgr.filter.return_value.annotate.return_value = monthly_stage
        monthly_stage.values.return_value = values_stage

        count_mock.side_effect = lambda *args, **kwargs: {
            'args': args,
            'kwargs': kwargs,
        }
        render_mock.return_value = 'response'

        response = sales_trends(self.factory.get('/reports/sales-trends/'))

        self.assertEqual(response, 'response')
        count_mock.assert_any_call('id', distinct=True)
