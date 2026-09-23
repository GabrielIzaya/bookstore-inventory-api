# Bookstore Inventory API

API REST desarrollada con Django REST Framework para gestionar el inventario de una cadena de librerías y calcular precios de venta en moneda local utilizando tasas de cambio en tiempo real.

## Características

- CRUD completo de libros.
- Paginación de resultados.
- Búsqueda por categoría.
- Consulta de libros con stock bajo.
- Normalización y unicidad de ISBN.
- Cálculo monetario con `Decimal`.
- Integración con API externa de tasas de cambio.
- Tasa fallback configurable cuando el proveedor externo no está disponible.
- PostgreSQL, Docker, documentación Swagger y pruebas automatizadas.

## Tecnologías

- Python 3.12
- Django 5
- Django REST Framework
- PostgreSQL 16
- Docker y Docker Compose
- Gunicorn
- drf-spectacular / OpenAPI

## Decisiones y supuestos

- El ISBN acepta guiones y espacios, pero se almacena normalizado como 10 o 13 dígitos.
- `supplier_country` utiliza un código ISO de dos letras.
- La moneda se obtiene mediante un mapa país-moneda en `books/services.py`.
- El margen de venta es fijo en 40%.
- Los importes se redondean a dos decimales con `ROUND_HALF_UP`.
- Si la API externa falla, se utiliza `DEFAULT_EXCHANGE_RATE` y la respuesta incluye `rate_source=default_fallback`.
- Si la moneda del país no está configurada, el endpoint de cálculo responde 400.

## Ejecución con Docker

1. Copiar las variables de entorno:

```bash
cp .env.example .env
```

2. Levantar la aplicación y PostgreSQL:

```bash
docker compose up --build
```

3. Abrir:

- API: `http://localhost:8000/api/books/`
- Swagger: `http://localhost:8000/api/docs/`
- Health check: `http://localhost:8000/health/`

## Ejecución local

Requiere Python 3.12 y una instancia PostgreSQL accesible.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

En Windows, activar el entorno con `.venv\\Scripts\\activate`.

## Variables de entorno

- `DJANGO_SECRET_KEY`: clave de Django.
- `DJANGO_DEBUG`: `True` o `False`.
- `DJANGO_ALLOWED_HOSTS`: hosts separados por coma.
- `CSRF_TRUSTED_ORIGINS`: orígenes HTTPS separados por coma.
- `DATABASE_URL`: conexión PostgreSQL.
- `DB_SSLMODE`: `prefer` local, `require` en nube.
- `EXCHANGE_API_URL`: proveedor de tasas.
- `EXCHANGE_API_TIMEOUT`: timeout en segundos.
- `DEFAULT_EXCHANGE_RATE`: tasa fallback.

## Endpoints

- `POST /api/books/`
- `GET /api/books/`
- `GET /api/books/{id}/`
- `PUT /api/books/{id}/`
- `PATCH /api/books/{id}/`
- `DELETE /api/books/{id}/`
- `GET /api/books/search/?category=Literatura`
- `GET /api/books/low-stock/?threshold=10`
- `POST /api/books/{id}/calculate-price/`

## Ejemplo para crear un libro

```json
{
  "title": "El Quijote",
  "author": "Miguel de Cervantes",
  "isbn": "978-84-376-0494-7",
  "cost_usd": "15.99",
  "stock_quantity": 25,
  "category": "Literatura Clásica",
  "supplier_country": "ES"
}
```

## Ejemplo del cálculo de precio

```json
{
  "book_id": 1,
  "cost_usd": "15.99",
  "exchange_rate": "0.85",
  "cost_local": "13.59",
  "margin_percentage": 40,
  "selling_price_local": "19.03",
  "currency": "EUR",
  "rate_source": "external_api",
  "calculation_timestamp": "2026-09-23T12:00:00Z"
}
```

## Pruebas

```bash
python manage.py test
```

Con cobertura:

```bash
coverage run manage.py test
coverage report -m
```

## Despliegue

Se incluye `render.yaml` para desplegar el contenedor y una base PostgreSQL gestionada en Render.

Después de crear el servicio:

1. Ajustar `DJANGO_ALLOWED_HOSTS` al dominio real.
2. Agregar el dominio HTTPS a `CSRF_TRUSTED_ORIGINS`.
3. Verificar `/health/`.
4. Importar en Postman el entorno de producción y reemplazar `base_url` por la URL real.

## Colección Postman

Los archivos están en `postman/`. La colección usa `{{base_url}}`, por lo que sirve tanto para entorno local como para producción.
