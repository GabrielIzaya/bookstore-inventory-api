import re
from rest_framework import serializers
from .models import Book


def normalize_isbn(value: str) -> str:
    return re.sub(r"[-\s]", "", value or "")


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            "id", "title", "author", "isbn", "cost_usd", "selling_price_local",
            "stock_quantity", "category", "supplier_country", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "selling_price_local", "created_at", "updated_at"]

    def validate_isbn(self, value):
        normalized = normalize_isbn(value)
        if not normalized.isdigit() or len(normalized) not in (10, 13):
            raise serializers.ValidationError("El ISBN debe contener 10 o 13 dígitos; se permiten espacios y guiones.")
        queryset = Book.objects.filter(isbn=normalized)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Ya existe un libro registrado con este ISBN.")
        return normalized

    def validate_cost_usd(self, value):
        if value <= 0:
            raise serializers.ValidationError("El costo debe ser mayor que cero.")
        return value

    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("La cantidad en inventario no puede ser negativa.")
        return value

    def validate_supplier_country(self, value):
        value = value.upper().strip()
        if len(value) != 2 or not value.isalpha():
            raise serializers.ValidationError("El país proveedor debe usar un código ISO de dos letras.")
        return value
