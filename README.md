# Northwind Django Dashboard

A Django 6 application that turns the classic **Northwind** sample database
into a modern management dashboard with CRM, sales, catalog, purchasing and
reporting modules — plus a **semantic product search** powered by sentence
embeddings stored in Postgres via the `pgvector` extension.

**Two databases, one Django project:**

- **MySQL** holds the authoritative Northwind schema (orders, products,
  customers, invoices, …). Models are `managed = False`, so Django maps to
  the existing tables without owning them.
- **Postgres + pgvector** holds derived data: 384-dimensional embeddings of
  every product, used for natural-language search and "similar products"
  recommendations. Routed through a custom `DATABASE_ROUTERS` entry.

![Northwind ERD](mywind/northwind-erd.png)

---

## Features

| Area           | What it does                                                             |
|----------------|--------------------------------------------------------------------------|
| **Dashboard**  | KPI tiles and revenue/orders charts over the whole data set              |
| **CRM**        | Customers, employees, suppliers — list + detail pages                    |
| **Sales**      | Orders, order details, invoices; breakdowns on each                      |
| **Catalog**    | Products with stats, recent orders, and semantic "similar products"      |
| **Reporting**  | Top customers, top products, sales trends (Chart.js)                     |
| **Semantic search** | Free-text queries like *"cold refreshing drink"* → ranked products  |
| **Admin**      | Full Django admin at `/admin/` (requires a superuser)                    |

---

## Prerequisites

- **Python 3.12+**
- **MySQL 8.0+** (5.7 works with the `CURRENT_TIMESTAMP` variant SQL file)
- **Docker** (for the pgvector Postgres instance)
- On macOS: `brew install mysql pkg-config` so `mysqlclient` can compile.
  On Debian/Ubuntu: `sudo apt-get install python3-dev default-libmysqlclient-dev build-essential`.

---

## 1. Clone and create a virtualenv

```bash
git clone <your-repo-url>
cd northwind
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` pins the minimum versions of Django, mysqlclient,
python-dotenv, psycopg, pgvector, and sentence-transformers.

---

## 2. Configure environment variables

Create `.env` in the project root (same folder as `manage.py`):

```dotenv
# MySQL (Northwind)
DB_NAME=northwind
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306

# Django
SECRET_KEY="django-insecure-change-me"
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000

# Postgres + pgvector (semantic search)
VDB_NAME=northwind_vectors
VDB_USER=northwind
VDB_PASSWORD=northwind
VDB_HOST=127.0.0.1
VDB_PORT=5432
```

And `.env.postgres` — read by `docker-compose.yml` to seed the Postgres
container:

```dotenv
POSTGRES_USER=northwind
POSTGRES_PASSWORD=northwind
POSTGRES_DB=northwind_vectors
```

Both files are in `.gitignore`.

---

## 3. Load the Northwind MySQL database

Make sure MySQL is running (macOS Homebrew: `brew services start mysql`),
then from the project root:

```bash
mysql -u root -p < mywind/northwind.sql
mysql -u root -p northwind < mywind/northwind-data.sql
```

Or from the MySQL prompt:

```sql
SOURCE mywind/northwind.sql;
SOURCE mywind/northwind-data.sql;
```

Verify:

```sql
USE northwind;
SHOW TABLES;
-- customers, employees, orders, order_details, products, suppliers, ...
```

---

## 4. Apply Django migrations (MySQL)

Django's auth/sessions/admin tables still need to exist, even though the
Northwind models themselves are `managed = False`:

```bash
python manage.py migrate
```

Optionally create a superuser for the admin at `/admin/`:

```bash
python manage.py createsuperuser
```

---

## 5. Start the vector database (Postgres + pgvector)

```bash
docker compose up -d pgvector
```

This spins up `pgvector/pgvector:pg16` on port 5432, with credentials from
`.env.postgres`. Data persists in the `pgvector_data` named volume across
restarts.

Check it's up:

```bash
docker compose exec pgvector psql -U northwind -d northwind_vectors -c "SELECT 1;"
```

---

## 6. Build the semantic search index

```bash
# First run will download the MiniLM embedding model (~80 MB).
# Keep the cache inside the repo instead of ~/.cache:
export HF_HOME="$(pwd)/.cache/hf"

python manage.py migrate search --database=vectors
python manage.py embed_products
```

What this does:

1. `migrate` runs `CREATE EXTENSION vector` and creates
   `product_embeddings(product_id, embedding vector(384), …)` with an HNSW
   cosine index.
2. `embed_products` encodes each product's name + category + description with
   `sentence-transformers/all-MiniLM-L6-v2` and upserts the vectors.
   A SHA-256 content hash means repeat runs only re-embed changed rows.
   Use `--force` to rebuild everything.

---

## 7. Run the development server

```bash
python manage.py runserver
```

Open <http://127.0.0.1:8000>. Suggested things to try:

- `/search/?q=something sweet for breakfast`
- `/search/?q=cold refreshing drink`
- Click any product — the detail page shows a **Similar Products** panel
  built from the same vector index.

---

## Available routes

| URL                         | Description                                   |
|-----------------------------|-----------------------------------------------|
| `/`                         | Dashboard with KPIs and charts                |
| `/crm/customers/`           | Customer list                                 |
| `/crm/employees/`           | Employee list                                 |
| `/crm/suppliers/`           | Supplier list                                 |
| `/sales/orders/`            | Order list                                    |
| `/sales/invoices/`          | Invoice list                                  |
| `/catalog/products/`        | Product list (keyword filter)                 |
| `/catalog/products/<id>/`   | Product detail with "Similar Products"        |
| `/search/`                  | Semantic product search                       |
| `/reports/`                 | Reports landing page                          |
| `/reports/top-customers/`   | Top customers by revenue                      |
| `/reports/top-products/`    | Top products by revenue                       |
| `/reports/sales-trends/`    | Monthly sales trends                          |
| `/admin/`                   | Django admin                                  |

---

## Project structure

```
northwind/
├── config/                  # Django project (settings, urls, routers)
│   ├── settings.py
│   ├── urls.py
│   └── routers.py           # VectorRouter: send `search` to pgvector
├── core/                    # Dashboard home + KPIs
├── crm/                     # Customers, employees, suppliers
├── catalog/                 # Products (incl. similar-products panel)
├── sales/                   # Orders, order details, invoices
├── purchasing/              # Purchase orders, inventory
├── reporting/               # Charts & aggregate reports
├── search/                  # Semantic search app (pgvector)
│   ├── models.py            # ProductEmbedding (vector(384), HNSW index)
│   ├── embeddings.py        # SentenceTransformer helpers
│   ├── services.py          # semantic_search / similar_products
│   ├── views.py, urls.py
│   └── management/commands/embed_products.py
├── templates/               # Shared Bootstrap templates
├── static/                  # CSS & JS
├── mywind/                  # Northwind SQL scripts + ERD images
├── docker-compose.yml       # pgvector service
├── requirements.txt
├── manage.py
├── .env                     # Local env vars (not committed)
└── .env.postgres            # Postgres container env (not committed)
```

---

## Architecture notes

**Two databases, cleanly separated.** `config/routers.py` routes the
`search` app to the `vectors` connection and everything else to `default`.
Django forbids cross-DB foreign keys, so `ProductEmbedding` references
products by ID only; the view layer joins them with a single `IN (...)`
lookup against MySQL (see `search.services.hydrate_products`).

**Why pgvector over a dedicated vector DB?** Keeps everything in SQL — the
search query is a one-liner with `ORDER BY embedding <=> :query_vector`,
and the HNSW index gives sub-millisecond nearest-neighbour lookups. Adding
metadata filters later is just a `WHERE` clause.

**Why `all-MiniLM-L6-v2`?** 384 dims, CPU-friendly, fully local, no API
key required. Swap to OpenAI or a larger model by changing `MODEL_NAME`
and `EMBEDDING_DIM` in `search/embeddings.py` and rerunning
`embed_products --force`.

**Keeping the index fresh.** The current flow is manual: rerun
`embed_products` when the product catalog changes. A `post_save` signal on
`Products` would make this real-time — the incremental content-hash check
already makes single-row re-embedding free.

---

## Troubleshooting

| Symptom                                                                 | Fix                                                                                      |
|------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| `Lost connection to MySQL server at 'reading initial communication packet'` | MySQL isn't running, or `DB_HOST`/`DB_PORT` are wrong. Check `brew services list`.      |
| `type "vector" does not exist` during migrate                           | Vector extension missing. Ensure migration runs `VectorExtension()` or run `CREATE EXTENSION vector` manually. |
| `'django.contrib.postgres' must be in INSTALLED_APPS`                   | Required by `HnswIndex` system checks — it's already listed; confirm settings weren't reverted. |
| `PermissionError` downloading from Hugging Face                          | Set `HF_HOME="$(pwd)/.cache/hf"` before running `embed_products`.                        |
| `connection refused` on port 5432                                        | `docker compose up -d pgvector` and wait ~5s for it to boot.                             |
| Search returns nothing                                                  | Index empty — run `python manage.py embed_products`.                                     |

---

## Useful commands

```bash
# Rebuild all embeddings from scratch
python manage.py embed_products --force

# Inspect the vector table
docker compose exec pgvector psql -U northwind -d northwind_vectors \
  -c "\d product_embeddings"

# Show that the HNSW index is being used
docker compose exec pgvector psql -U northwind -d northwind_vectors -c "
EXPLAIN ANALYZE
SELECT product_id
FROM product_embeddings
ORDER BY embedding <=> (SELECT embedding FROM product_embeddings WHERE product_id = 43)
LIMIT 5;"

# Reset pgvector volume (deletes all embeddings)
docker compose down -v
```
