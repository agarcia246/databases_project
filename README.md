# Northwind Django Dashboard

A Django 6.0 web application that provides a management dashboard on top of the classic **Northwind** sample database running in MySQL. It includes modules for CRM (customers, employees, suppliers), sales (orders, invoices), product catalog, purchasing, and reporting with charts.

## Prerequisites

- **Python 3.12+**
- **MySQL 8.0+** (or MySQL 5.6.5+ if using the `CURRENT_TIMESTAMP` variant)
- **pip** (comes with Python)

## 1. Set Up the MySQL Northwind Database

The SQL scripts live in the `mywind/` directory. You need to run them against a MySQL server to create and populate the database.

### Start your MySQL server

Make sure MySQL is running. On macOS with Homebrew:

```bash
brew services start mysql
```

### Connect to MySQL

```bash
mysql -u root -p
```

### Create the schema and load data

From the MySQL prompt, run the two scripts **in order**:

```sql
SOURCE mywind/northwind.sql;
SOURCE mywind/northwind-data.sql;
```

> **Note:** The paths above assume your MySQL client's working directory is the project root (`djangoProject/`). If you launched `mysql` from a different directory, use absolute paths instead, e.g.:
>
> ```sql
> SOURCE /full/path/to/djangoProject/mywind/northwind.sql;
> SOURCE /full/path/to/djangoProject/mywind/northwind-data.sql;
> ```

Alternatively, you can pipe the files directly from your shell without entering the MySQL prompt:

```bash
mysql -u root -p < mywind/northwind.sql
mysql -u root -p northwind < mywind/northwind-data.sql
```

### Verify the database was created

```sql
USE northwind;
SHOW TABLES;
```

You should see tables like `customers`, `employees`, `orders`, `order_details`, `products`, `suppliers`, and more.

## 2. Create a Python Virtual Environment

From the project root:

```bash
cd northwind
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install django python-dotenv mysqlclient
```

> `mysqlclient` requires the MySQL C client library. On macOS: `brew install mysql pkg-config`. On Ubuntu/Debian: `sudo apt-get install python3-dev default-libmysqlclient-dev build-essential`.

## 4. Configure Environment Variables

Create a `.env` file inside the `northwind/` directory:

```bash
cp .env.example .env   # or create it manually
```

It should contain the following variables:

```dotenv
DB_NAME=northwind
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

Replace `your_mysql_password` with the password you set for your MySQL user.

## 5. Run Django Migrations

The Northwind models use `managed = False` (they map to the existing MySQL tables), but Django's built-in apps (auth, sessions, admin, etc.) still need their tables:

```bash
python manage.py migrate
```

## 6. Create a Superuser (Optional)

To access the Django admin panel at `/admin/`:

```bash
python manage.py createsuperuser
```

## 7. Start the Development Server

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser to see the dashboard.

## Project Structure

```
djangoProject/
├── mywind/                  # Northwind SQL scripts & ERD diagrams
│   ├── northwind.sql        # Schema creation (tables, indexes, FKs)
│   ├── northwind-data.sql   # Sample data inserts
│   └── ...
├── northwind/               # Django application root
│   ├── config/              # Django project settings & root URL conf
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── ...
│   ├── core/                # Dashboard home page & KPIs
│   ├── crm/                 # Customers, employees, suppliers
│   ├── sales/               # Orders, order details, invoices
│   ├── catalog/             # Products
│   ├── purchasing/          # Purchase orders & inventory
│   ├── reporting/           # Reports & charts (top customers, trends)
│   ├── templates/           # Shared HTML templates
│   ├── static/              # CSS & JS assets
│   ├── manage.py
│   └── .env                 # Environment variables (not committed)
└── README.md
```

## Available Routes

| URL | Description |
|-----|-------------|
| `/` | Dashboard with KPIs and charts |
| `/crm/customers/` | Customer list |
| `/crm/employees/` | Employee list |
| `/crm/suppliers/` | Supplier list |
| `/sales/orders/` | Order list |
| `/sales/invoices/` | Invoice list |
| `/catalog/products/` | Product list |
| `/reports/` | Reports home |
| `/reports/top-customers/` | Top customers report |
| `/reports/top-products/` | Top products report |
| `/reports/sales-trends/` | Sales trends chart |
| `/admin/` | Django admin panel |
