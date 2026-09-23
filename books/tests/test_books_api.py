from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from books.models import Book


class BookApiTests(APITestCase):
    def payload(self, **overrides):
        data = {
            "title": "El Quijote",
            "author": "Miguel de Cervantes",
            "isbn": "978-84-376-0494-7",
            "cost_usd": "15.99",
            "stock_quantity": 25,
            "category": "Literatura Clásica",
            "supplier_country": "ES",
        }
        data.update(overrides)
        return data

    def test_create_book_normalizes_isbn(self):
        response = self.client.post(reverse("book-list"), self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["isbn"], "9788437604947")

    def test_rejects_non_positive_cost(self):
        response = self.client.post(reverse("book-list"), self.payload(cost_usd="0"), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_negative_stock(self):
        response = self.client.post(reverse("book-list"), self.payload(stock_quantity=-1), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_invalid_isbn(self):
        response = self.client.post(reverse("book-list"), self.payload(isbn="123"), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_duplicate_isbn(self):
        Book.objects.create(title="A", author="B", isbn="9788437604947", cost_usd=Decimal("5"), stock_quantity=1, category="X", supplier_country="ES")
        response = self.client.post(reverse("book-list"), self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_low_stock_filter(self):
        Book.objects.create(title="A", author="B", isbn="1234567890", cost_usd=Decimal("5"), stock_quantity=3, category="X", supplier_country="ES")
        response = self.client.get(reverse("book-low-stock"), {"threshold": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
