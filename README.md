# PhoneZone

PhoneZone is a full-stack smartphone storefront built with Flask, MySQL, HTML,
CSS, and JavaScript. Customers can browse live inventory, view product details,
manage a persistent shopping cart, and complete a stock-validated checkout.
An authenticated admin dashboard provides product and inventory management.

## Features

- Responsive storefront with product search and sorting
- Product detail pages backed by MySQL inventory data
- Browser-persisted shopping cart with live stock validation
- Transactional checkout that prevents inventory from becoming negative
- Admin authentication and dashboard statistics
- Add, edit, delete, and restock product workflows
- Parameterized SQL queries and custom error pages

## Technology

- Python and Flask
- MySQL
- Jinja templates
- HTML, CSS, and vanilla JavaScript

## Local setup

1. Create and activate a Python virtual environment.
2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy the environment template and set your local credentials:

   ```bash
   cp .env.example .env
   ```

4. Run `PhoneZoneDB.sql` in MySQL to create the `IEEE` database and seed the
   sample catalog.
5. Start the application:

   ```bash
   python app.py
   ```

6. Open <http://127.0.0.1:5000>.

## Project structure

```text
app.py             Flask routes, database access, checkout, and admin features
PhoneZoneDB.sql     Database schema and sample data
templates/          Jinja page templates
static/style.css    Responsive styling
static/script.js    Cart, inventory, checkout, search, and sorting behavior
```

## Security notes

Credentials and the Flask secret key are loaded from `.env`, which is excluded
from version control. Use strong values before running the application outside
a local development environment. The included checkout is an educational demo;
it updates inventory but does not process or store real payment information.
