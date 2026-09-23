from decimal import Decimal
from unittest.mock import Mock, patch
import requests
from django.test import TestCase, override_settings
from books.models import Book
from books.services import ExchangeRateService, calculate_book_price


class PriceServiceTests(TestCase):
    def setUp(self):
        self.book = Book.objects.create(
            title="El Quijote", author="Miguel de Cervantes", isbn="9788437604947",
            cost_usd=Decimal("15.99"), stock_quantity=25,
            category="Literatura Clásica", supplier_country="ES",
        )

    @patch("books.services.requests.get")
    def test_calculates_price_with_external_rate(self, get_mock):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"rates": {"EUR": 0.85}}
        get_mock.return_value = response
        result = calculate_book_price(self.book)
        self.assertEqual(result["cost_local"], Decimal("13.59"))
        self.assertEqual(result["selling_price_local"], Decimal("19.03"))
        self.assertEqual(result["rate_source"], "external_api")

    @override_settings(DEFAULT_EXCHANGE_RATE="1.25")
    @patch("books.services.requests.get", side_effect=requests.RequestException("network down"))
    def test_uses_fallback_rate(self, _get_mock):
        result = calculate_book_price(self.book)
        self.assertEqual(result["exchange_rate"], Decimal("1.25"))
        self.assertEqual(result["rate_source"], "default_fallback")
