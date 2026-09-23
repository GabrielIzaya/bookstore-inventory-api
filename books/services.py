from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import requests
from django.conf import settings

COUNTRY_CURRENCY_MAP = {
    "AR": "ARS", "BR": "BRL", "CA": "CAD", "CL": "CLP", "CO": "COP",
    "ES": "EUR", "GB": "GBP", "MX": "MXN", "PE": "PEN", "US": "USD", "VE": "VES",
}


class UnsupportedCurrencyError(ValueError):
    pass


class ExchangeRateUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class RateResult:
    rate: Decimal
    currency: str
    source: str


class ExchangeRateService:
    def currency_for_country(self, country_code: str) -> str:
        currency = COUNTRY_CURRENCY_MAP.get(country_code.upper())
        if not currency:
            raise UnsupportedCurrencyError(f"No existe una moneda configurada para el país {country_code}.")
        return currency

    def get_rate(self, currency: str) -> RateResult:
        try:
            response = requests.get(settings.EXCHANGE_API_URL, timeout=settings.EXCHANGE_API_TIMEOUT)
            response.raise_for_status()
            raw_rate = response.json().get("rates", {}).get(currency)
            if raw_rate is None:
                raise ExchangeRateUnavailableError(f"La API no devolvió una tasa para {currency}.")
            return RateResult(Decimal(str(raw_rate)), currency, "external_api")
        except (requests.RequestException, ValueError, KeyError, ExchangeRateUnavailableError):
            fallback = settings.DEFAULT_EXCHANGE_RATE
            if fallback in (None, ""):
                raise ExchangeRateUnavailableError("No fue posible obtener la tasa de cambio y no hay fallback configurado.")
            return RateResult(Decimal(str(fallback)), currency, "default_fallback")


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_book_price(book, service=None):
    service = service or ExchangeRateService()
    currency = service.currency_for_country(book.supplier_country)
    rate_result = service.get_rate(currency)
    cost_local = money(book.cost_usd * rate_result.rate)
    selling_price = money(cost_local * Decimal("1.40"))
    return {
        "book_id": book.id,
        "cost_usd": money(book.cost_usd),
        "exchange_rate": rate_result.rate,
        "cost_local": cost_local,
        "margin_percentage": 40,
        "selling_price_local": selling_price,
        "currency": currency,
        "rate_source": rate_result.source,
    }
