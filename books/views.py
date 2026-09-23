from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Book
from .serializers import BookSerializer
from .services import (
    ExchangeRateUnavailableError,
    UnsupportedCurrencyError,
    calculate_book_price,
)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        category = request.query_params.get("category", "").strip()
        queryset = self.get_queryset()
        if category:
            queryset = queryset.filter(category__icontains=category)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, request):
        try:
            threshold = int(request.query_params.get("threshold", 10))
            if threshold < 0:
                raise ValueError
        except ValueError:
            return Response({"threshold": ["Debe ser un entero mayor o igual a cero."]}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.get_queryset().filter(stock_quantity__lt=threshold)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @extend_schema(responses={200: dict, 400: dict, 404: dict, 503: dict})
    @action(detail=True, methods=["post"], url_path="calculate-price")
    def calculate_price(self, request, pk=None):
        book = self.get_object()
        try:
            result = calculate_book_price(book)
        except UnsupportedCurrencyError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ExchangeRateUnavailableError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        book.selling_price_local = result["selling_price_local"]
        book.save(update_fields=["selling_price_local", "updated_at"])
        result["calculation_timestamp"] = timezone.now()
        return Response(result)
