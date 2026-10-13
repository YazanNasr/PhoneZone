import hmac
import os
import secrets

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") or secrets.token_hex(32)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "IEEE"),
    "port": int(os.getenv("DB_PORT", "3306")),
}

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


def get_conn():
    return mysql.connector.connect(**DB_CONFIG)


def product_extras(product_name, brand):
    """Adds website display information that is not stored in the database."""
    name = product_name.lower()
    brand_lower = brand.lower()

    if "iphone" in name or brand_lower == "apple":
        return {
            "old_price": 1099,
            "tagline": "Titanium design. Pro camera power. Smooth all-day performance.",
            "features": ["A17 Pro chip", "Pro camera system", "6.1-inch Super Retina XDR display", "USB-C charging", "5G connectivity"],
            "colors": ["Black Titanium", "White Titanium", "Blue Titanium", "Natural Titanium"],
            "storage": "128GB",
            "badge": "Best Seller"
        }

    if "samsung" in name or brand_lower == "samsung":
        return {
            "old_price": 999,
            "tagline": "Galaxy AI, AMOLED display, and flagship camera performance.",
            "features": ["Galaxy AI features", "Dynamic AMOLED display", "Pro camera system", "Fast wireless charging", "5G connectivity"],
            "colors": ["Phantom Black", "Marble Gray", "Cobalt Violet", "Amber Yellow"],
            "storage": "256GB",
            "badge": "Pro Pick"
        }

    if "pixel" in name or brand_lower == "google":
        return {
            "old_price": 799,
            "tagline": "Google AI, clean Android, and excellent photos in one phone.",
            "features": ["Google Tensor chip", "Advanced AI camera tools", "OLED display", "Clean Android experience", "5G connectivity"],
            "colors": ["Obsidian", "Hazel", "Rose", "Mint"],
            "storage": "128GB",
            "badge": "Best Value"
        }

    return {
        "old_price": 0,
        "tagline": "Premium smartphone with modern features and reliable performance.",
        "features": ["5G connectivity", "Fast charging", "High quality display", "Modern camera system"],
        "colors": ["Black", "White"],
        "storage": "128GB",
        "badge": "New"
    }


def format_product(row):
    extras = product_extras(row["ProductName"], row["Brand"])
    price = float(row["Price"])
    old_price = extras["old_price"] or round(price + 100)

    return {
        "id": int(row["ProductID"]),
        "name": row["ProductName"],
        "brand": row["Brand"],
        "description": row["Description"],
        "price": price,
        "old_price": old_price,
        "stock": int(row["Stock"]),
        "image": row["Image"],
        "rating": float(row["Rating"]),
        "category": row.get("CategoryName", row["Brand"]),
        "tagline": extras["tagline"],
        "features": extras["features"],
        "colors": extras["colors"],
        "storage": extras["storage"],
        "badge": extras["badge"]
    }


def fetch_all_products():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT
            p.ProductID,
            p.ProductName,
            p.Brand,
            p.Description,
            p.Price,
            p.Stock,
            p.Image,
            p.Rating,
            c.CategoryName
        FROM Products p
        JOIN Categories c ON p.CategoryID = c.CategoryID
        ORDER BY p.ProductID
    """)

    products = [format_product(row) for row in cur.fetchall()]

    cur.close()
    conn.close()
    return products


def fetch_product(product_id):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT
            p.ProductID,
            p.ProductName,
            p.Brand,
            p.Description,
            p.Price,
            p.Stock,
            p.Image,
            p.Rating,
            c.CategoryName
        FROM Products p
        JOIN Categories c ON p.CategoryID = c.CategoryID
        WHERE p.ProductID = %s
    """, (product_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    return format_product(row) if row else None


def fetch_categories():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT CategoryID, CategoryName
        FROM Categories
        ORDER BY CategoryID
    """)
    categories = cur.fetchall()
    cur.close()
    conn.close()
    return categories


def fetch_admin_stats():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT
            COUNT(*) AS total_products,
            COALESCE(SUM(Stock), 0) AS total_stock,
            COALESCE(SUM(Stock * Price), 0) AS inventory_value,
            COALESCE(SUM(CASE WHEN Stock <= 3 THEN 1 ELSE 0 END), 0) AS low_stock_count
        FROM Products
    """)
    stats = cur.fetchone()

    cur.execute("""
        SELECT ProductID, ProductName, Brand, Price, Stock, Image, Rating
        FROM Products
        WHERE Stock <= 3
        ORDER BY Stock ASC, ProductName ASC
    """)
    low_stock = cur.fetchall()

    cur.close()
    conn.close()

    return stats, low_stock


def admin_required():
    return session.get("admin_logged_in") is True



@app.route("/")
def home():
    products = fetch_all_products()
    return render_template("index.html", products=products)


@app.route("/products")
def products():
    products = fetch_all_products()
    return render_template("products.html", products=products)


@app.route("/details/<int:product_id>")
def details(product_id):
    product = fetch_product(product_id)

    if product is None:
        return render_template("404.html"), 404

    return render_template("details.html", product=product)


@app.route("/details/iphone")
def details_iphone():
    return details(1)


@app.route("/details/samsung")
def details_samsung():
    return details(2)


@app.route("/details/pixel")
def details_pixel():
    return details(3)


@app.route("/cart")
def cart():
    return render_template("cart.html")


@app.route("/checkout")
def checkout():
    return render_template("checkout.html")


@app.get("/api/products")
def api_products():
    products = fetch_all_products()
    return jsonify({str(product["id"]): product for product in products})


@app.post("/api/checkout")
def api_checkout():
    data = request.get_json(silent=True) or {}
    cart = data.get("cart", [])

    print("CART RECEIVED FROM BROWSER:", cart)

    if not isinstance(cart, list) or len(cart) == 0:
        return jsonify({"ok": False, "message": "Your cart is empty."}), 400

    requested_quantities = {}

    for item in cart:
        try:
            product_id = int(item.get("id"))
            quantity = int(item.get("quantity"))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "message": "Invalid cart item. Product ID must be a number."}), 400

        if quantity <= 0:
            return jsonify({"ok": False, "message": "Invalid item quantity."}), 400

        requested_quantities[product_id] = requested_quantities.get(product_id, 0) + quantity

    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    try:
        conn.start_transaction()

        # First, check every product exists and has enough stock.
        for product_id, quantity in requested_quantities.items():
            cur.execute("""
                SELECT ProductID, ProductName, Stock
                FROM Products
                WHERE ProductID = %s
                FOR UPDATE
            """, (product_id,))

            product = cur.fetchone()

            if product is None:
                conn.rollback()
                return jsonify({"ok": False, "message": "One product in your cart no longer exists."}), 404

            if int(product["Stock"]) < quantity:
                conn.rollback()
                products = fetch_all_products()
                return jsonify({
                    "ok": False,
                    "message": f"Only {product['Stock']} {product['ProductName']} left in stock.",
                    "products": {str(p["id"]): p for p in products}
                }), 409

        # Second, update stock. The AND Stock >= quantity protects against negative stock.
        for product_id, quantity in requested_quantities.items():
            cur.execute("""
                UPDATE Products
                SET Stock = Stock - %s
                WHERE ProductID = %s AND Stock >= %s
            """, (quantity, product_id, quantity))

            print(f"UPDATED PRODUCT {product_id}: quantity={quantity}, rowcount={cur.rowcount}")

            if cur.rowcount != 1:
                conn.rollback()
                return jsonify({
                    "ok": False,
                    "message": "Stock update failed. Please refresh and try again."
                }), 409

        conn.commit()

        products = fetch_all_products()
        print("STOCK AFTER CHECKOUT:", [(p["id"], p["name"], p["stock"]) for p in products])

        return jsonify({
            "ok": True,
            "message": "Order placed successfully. Stock has been updated in MySQL.",
            "products": {str(p["id"]): p for p in products}
        })

    except Error as e:
        conn.rollback()
        app.logger.exception("Checkout database error")
        return jsonify({"ok": False, "message": "A database error prevented checkout."}), 500

    finally:
        cur.close()
        conn.close()



@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        credentials_configured = bool(ADMIN_USERNAME and ADMIN_PASSWORD)
        credentials_match = (
            credentials_configured
            and hmac.compare_digest(username, ADMIN_USERNAME)
            and hmac.compare_digest(password, ADMIN_PASSWORD)
        )

        if credentials_match:
            session["admin_logged_in"] = True
            flash("Welcome back, admin.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin username or password.", "danger")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("admin_login"))


@app.route("/admin")
def admin_dashboard():
    if not admin_required():
        return redirect(url_for("admin_login"))

    products = fetch_all_products()
    stats, low_stock = fetch_admin_stats()
    return render_template("admin.html", products=products, stats=stats, low_stock=low_stock)


@app.route("/admin/add", methods=["GET", "POST"])
def admin_add_product():
    if not admin_required():
        return redirect(url_for("admin_login"))

    categories = fetch_categories()

    if request.method == "POST":
        name = (request.form.get("ProductName") or "").strip()
        brand = (request.form.get("Brand") or "").strip()
        description = (request.form.get("Description") or "").strip()
        price = request.form.get("Price")
        stock = request.form.get("Stock", type=int)
        image = (request.form.get("Image") or "").strip()
        rating = request.form.get("Rating")
        category_id = request.form.get("CategoryID", type=int)

        if not name or not brand or not description or not price or stock is None or not image or not rating or not category_id:
            flash("Please fill in every field.", "danger")
            return render_template("admin_form.html", mode="add", product=None, categories=categories)

        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO Products (ProductName, Brand, Description, Price, Stock, Image, Rating, CategoryID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, brand, description, price, stock, image, rating, category_id))
            conn.commit()
            flash("Product added successfully.", "success")
            return redirect(url_for("admin_dashboard"))
        except Error as e:
            conn.rollback()
            flash(f"Database error: {e}", "danger")
        finally:
            cur.close()
            conn.close()

    return render_template("admin_form.html", mode="add", product=None, categories=categories)


@app.route("/admin/edit/<int:product_id>", methods=["GET", "POST"])
def admin_edit_product(product_id):
    if not admin_required():
        return redirect(url_for("admin_login"))

    categories = fetch_categories()

    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT ProductID, ProductName, Brand, Description, Price, Stock, Image, Rating, CategoryID
        FROM Products
        WHERE ProductID = %s
    """, (product_id,))
    product = cur.fetchone()
    cur.close()
    conn.close()

    if product is None:
        flash("Product not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        name = (request.form.get("ProductName") or "").strip()
        brand = (request.form.get("Brand") or "").strip()
        description = (request.form.get("Description") or "").strip()
        price = request.form.get("Price")
        stock = request.form.get("Stock", type=int)
        image = (request.form.get("Image") or "").strip()
        rating = request.form.get("Rating")
        category_id = request.form.get("CategoryID", type=int)

        if not name or not brand or not description or not price or stock is None or not image or not rating or not category_id:
            flash("Please fill in every field.", "danger")
            return render_template("admin_form.html", mode="edit", product=product, categories=categories)

        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE Products
                SET ProductName = %s,
                    Brand = %s,
                    Description = %s,
                    Price = %s,
                    Stock = %s,
                    Image = %s,
                    Rating = %s,
                    CategoryID = %s
                WHERE ProductID = %s
            """, (name, brand, description, price, stock, image, rating, category_id, product_id))
            conn.commit()
            flash("Product updated successfully.", "success")
            return redirect(url_for("admin_dashboard"))
        except Error as e:
            conn.rollback()
            flash(f"Database error: {e}", "danger")
        finally:
            cur.close()
            conn.close()

    return render_template("admin_form.html", mode="edit", product=product, categories=categories)


@app.post("/admin/delete/<int:product_id>")
def admin_delete_product(product_id):
    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM Products WHERE ProductID = %s", (product_id,))
        conn.commit()
        flash("Product deleted successfully.", "success")
    except Error as e:
        conn.rollback()
        flash(f"Database error: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("admin_dashboard"))


@app.post("/admin/restock/<int:product_id>/<int:amount>")
def admin_restock_product(product_id, amount):
    if not admin_required():
        return redirect(url_for("admin_login"))

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE Products
            SET Stock = GREATEST(Stock + %s, 0)
            WHERE ProductID = %s
        """, (amount, product_id))
        conn.commit()
        flash("Stock updated successfully.", "success")
    except Error as e:
        conn.rollback()
        flash(f"Database error: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("admin_dashboard"))


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"}
    app.run(debug=debug_mode, port=5000)
