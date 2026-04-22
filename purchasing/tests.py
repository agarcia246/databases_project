from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse

from .views import inventory_activity, purchase_order_detail, purchase_order_list


class PurchasingRoutingTests(SimpleTestCase):
    def test_named_routes_reverse(self):
        self.assertEqual(reverse('purchasing:index'), '/purchasing/')
        self.assertEqual(reverse('purchasing:purchase_order_list'), '/purchasing/orders/')
        self.assertEqual(reverse('purchasing:inventory_activity'), '/purchasing/inventory/')


class PurchasingViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch('purchasing.views.render')
    @patch('purchasing.views.Paginator')
    @patch('purchasing.views.PurchaseOrderStatus.objects')
    @patch('purchasing.views.PurchaseOrders.objects')
    def test_purchase_order_list_applies_filters_and_builds_context(
        self,
        purchase_orders_mgr,
        status_mgr,
        paginator_cls,
        render_mock,
    ):
        queryset = MagicMock()
        purchase_orders_mgr.select_related.return_value.order_by.return_value = queryset
        queryset.filter.return_value = queryset
        purchase_orders_mgr.exclude.return_value.values_list.return_value.distinct.return_value.order_by.return_value = [
            (1, 'Exotic Liquids'),
        ]
        status_mgr.order_by.return_value = [SimpleNamespace(pk=1, status='Submitted')]

        page_obj = SimpleNamespace(number=1, paginator=SimpleNamespace(count=3))
        paginator = paginator_cls.return_value
        paginator.count = 3
        paginator.get_page.return_value = page_obj
        render_mock.return_value = 'response'

        request = self.factory.get('/purchasing/orders/', {
            'q': 'Exotic',
            'status': '1',
            'supplier': '1',
        })
        response = purchase_order_list(request)

        self.assertEqual(response, 'response')
        self.assertGreaterEqual(queryset.filter.call_count, 3)
        render_mock.assert_called_once()
        context = render_mock.call_args.args[2]
        self.assertEqual(context['active_nav'], 'purchasing')
        self.assertEqual(context['query_string'], 'q=Exotic&status=1&supplier=1')

    @patch('purchasing.views.render')
    @patch('purchasing.views.InventoryTransactions.objects')
    @patch('purchasing.views.PurchaseOrderDetails.objects')
    @patch('purchasing.views.get_object_or_404')
    def test_purchase_order_detail_computes_line_totals(
        self,
        get_or_404_mock,
        po_details_mgr,
        inventory_mgr,
        render_mock,
    ):
        purchase_order = SimpleNamespace(
            pk=9,
            supplier=SimpleNamespace(company='Exotic Liquids'),
            created_by=SimpleNamespace(first_name='Nancy', last_name='Davolio'),
            status=SimpleNamespace(status='Submitted'),
            creation_date=None,
            expected_date=None,
            shipping_fee=0,
            taxes=0,
        )
        line_item = SimpleNamespace(
            quantity=3,
            unit_cost=4,
            product=SimpleNamespace(product_name='Chai'),
            inventory=None,
            date_received=None,
        )
        line_items = [line_item]
        line_qs = MagicMock()
        line_qs.__iter__.return_value = iter(line_items)
        line_qs.aggregate.return_value = {
            'subtotal': 12,
            'total_quantity': 3,
            'total_lines': 1,
            'received_lines': 0,
        }

        get_or_404_mock.return_value = purchase_order
        po_details_mgr.filter.return_value.select_related.return_value = line_qs
        inventory_mgr.filter.return_value.select_related.return_value.order_by.return_value = []
        render_mock.return_value = 'response'

        response = purchase_order_detail(self.factory.get('/purchasing/orders/9/'), 9)

        self.assertEqual(response, 'response')
        self.assertEqual(line_item.line_total, 12)
        context = render_mock.call_args.args[2]
        self.assertEqual(context['subtotal'], 12)
        self.assertEqual(context['total_lines'], 1)

    @patch('purchasing.views.render')
    @patch('purchasing.views.Paginator')
    @patch('purchasing.views.InventoryTransactionTypes.objects')
    @patch('purchasing.views.InventoryTransactions.objects')
    def test_inventory_activity_filters_and_tracks_query_string(
        self,
        inventory_mgr,
        transaction_types_mgr,
        paginator_cls,
        render_mock,
    ):
        queryset = MagicMock()
        inventory_mgr.select_related.return_value.order_by.return_value = queryset
        queryset.filter.return_value = queryset
        transaction_types_mgr.order_by.return_value = [SimpleNamespace(pk=1, type_name='Purchase')]

        page_obj = SimpleNamespace(number=1, paginator=SimpleNamespace(count=2))
        paginator = paginator_cls.return_value
        paginator.count = 2
        paginator.get_page.return_value = page_obj
        render_mock.return_value = 'response'

        request = self.factory.get('/purchasing/inventory/', {'q': 'chai', 'type': '1'})
        response = inventory_activity(request)

        self.assertEqual(response, 'response')
        self.assertGreaterEqual(queryset.filter.call_count, 2)
        context = render_mock.call_args.args[2]
        self.assertEqual(context['active_nav'], 'inventory')
        self.assertEqual(context['query_string'], 'q=chai&type=1')
