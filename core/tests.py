from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from .views import dashboard


class DashboardAggregationTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch('core.views.render')
    @patch('core.views.Count')
    @patch('core.views.Products.objects')
    @patch('core.views.OrderDetails.objects')
    @patch('core.views.Orders.objects')
    @patch('core.views.Employees.objects')
    @patch('core.views.Customers.objects')
    def test_monthly_sales_counts_distinct_orders(
        self,
        customers_mgr,
        employees_mgr,
        orders_mgr,
        order_details_mgr,
        products_mgr,
        count_mock,
        render_mock,
    ):
        customers_mgr.count.return_value = 10
        employees_mgr.count.return_value = 5
        orders_mgr.count.return_value = 12
        products_mgr.count.return_value = 25
        order_details_mgr.aggregate.return_value = {'rev': 0}
        order_details_mgr.values.return_value.annotate.return_value.order_by.return_value.first.return_value = None

        monthly_stage = MagicMock()
        values_stage = MagicMock()
        monthly_result = []
        orders_mgr.filter.return_value.annotate.return_value = monthly_stage
        monthly_stage.values.return_value = values_stage
        values_stage.annotate.return_value.order_by.return_value = monthly_result

        recent_stage = MagicMock()
        recent_stage.order_by.return_value.__getitem__.return_value = []
        orders_mgr.select_related.return_value = recent_stage

        employee_stage = MagicMock()
        orders_mgr.values.return_value = employee_stage
        employee_stage.annotate.return_value.order_by.return_value = []

        count_mock.side_effect = lambda *args, **kwargs: {
            'args': args,
            'kwargs': kwargs,
        }
        render_mock.return_value = 'response'

        response = dashboard(self.factory.get('/'))

        self.assertEqual(response, 'response')
        count_mock.assert_any_call('id', distinct=True)
