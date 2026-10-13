// PhoneZone professional cart + live stock system
// Cart is stored in localStorage. Product stock is validated by Flask during checkout.

const CART_KEY = "phonezone_cart";
let inventoryCache = {};

const money = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
});

function getCart() {
    try {
        const cart = JSON.parse(localStorage.getItem(CART_KEY));
        return Array.isArray(cart) ? cart : [];
    } catch (error) {
        console.error("Could not read cart:", error);
        return [];
    }
}

function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    updateCartCount();
}

async function refreshInventory() {
    try {
        const response = await fetch("/api/products");
        if (!response.ok) throw new Error("Inventory request failed");
        inventoryCache = await response.json();
        updateStockDisplays();
        return inventoryCache;
    } catch (error) {
        console.error("Could not refresh inventory:", error);
        return inventoryCache;
    }
}

function getAvailableStock(id) {
    const product = inventoryCache[id];
    if (product && Number.isFinite(Number(product.stock))) return Number(product.stock);

    const stockElement = document.getElementById(`stock-${id}`);
    if (stockElement) {
        const match = stockElement.textContent.match(/\d+/);
        if (match) return Number(match[0]);
    }

    return Infinity;
}

function updateStockDisplays() {
    Object.entries(inventoryCache).forEach(([id, product]) => {
        const stock = Number(product.stock || 0);
        const stockText = stock > 0 ? `${stock} in stock` : "Out of stock";

        document.querySelectorAll(`#stock-${id}`).forEach(element => {
            element.textContent = stockText;
            element.classList.toggle("out", stock <= 0);
            element.classList.toggle("low", stock > 0 && stock <= 3);
        });

        document.querySelectorAll(`[data-product-id="${id}"]`).forEach(card => {
            card.dataset.stock = stock;
        });

        document.querySelectorAll(`[data-add-button="${id}"]`).forEach(button => {
            button.disabled = stock <= 0;
            button.textContent = stock <= 0 ? "Out of Stock" : "Add to Cart";
        });
    });
}

async function addToCart(id, name, price, image) {
    if (!id || !name || isNaN(Number(price))) {
        showToast("Could not add this item. Product data is missing.");
        return;
    }

    await refreshInventory();

    const cart = getCart();
    const productId = Number(id);
    const existingItem = cart.find(item => Number(item.id) === productId);
    const currentQuantity = existingItem ? Number(existingItem.quantity || 0) : 0;
    const availableStock = getAvailableStock(id);

    if (availableStock <= 0) {
        showToast(`${name} is currently out of stock.`);
        return;
    }

    if (currentQuantity >= availableStock) {
        showToast(`Only ${availableStock} ${name} available.`);
        return;
    }

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            id: Number(id),
            name: String(name),
            price: Number(price),
            image: String(image || ""),
            quantity: 1
        });
    }

    saveCart(cart);
    renderCart();
    renderCheckoutSummary();
    showToast(`${name} added to cart`);
}

function updateCartCount() {
    const cartCount = document.getElementById("cartCount");
    if (!cartCount) return;

    const totalItems = getCart().reduce((sum, item) => sum + Number(item.quantity || 0), 0);
    cartCount.textContent = totalItems;
}

function renderCart() {
    const cartItems = document.getElementById("cartItems");
    if (!cartItems) return;

    const cart = getCart();

    if (cart.length === 0) {
        cartItems.innerHTML = `
            <div class="empty-cart">
                <h2>Your cart is empty</h2>
                <p>Add a phone first, then come back here.</p>
                <a class="btn primary" href="/products">Shop Products</a>
            </div>
        `;
        updateTotals();
        return;
    }

    cartItems.innerHTML = cart.map(item => {
        const availableStock = getAvailableStock(item.id);
        const stockNote = Number.isFinite(availableStock)
            ? `<p class="cart-stock">${availableStock} left in stock</p>`
            : "";
        const plusDisabled = Number.isFinite(availableStock) && Number(item.quantity) >= availableStock ? "disabled" : "";

        return `
            <article class="cart-item">
                <img src="/static/${escapeHTML(item.image)}" alt="${escapeHTML(item.name)}">
                <div>
                    <h3>${escapeHTML(item.name)}</h3>
                    <p>${money.format(item.price)} each</p>
                    ${stockNote}
                    <div class="qty-control" aria-label="Quantity controls">
                        <button type="button" onclick="changeQuantity('${escapeHTML(item.id)}', -1)">−</button>
                        <strong>${item.quantity}</strong>
                        <button type="button" ${plusDisabled} onclick="changeQuantity('${escapeHTML(item.id)}', 1)">+</button>
                    </div>
                    <button type="button" class="remove-btn" onclick="removeItem('${escapeHTML(item.id)}')">Remove</button>
                </div>
                <strong>${money.format(item.price * item.quantity)}</strong>
            </article>
        `;
    }).join("");

    updateTotals();
}

async function changeQuantity(id, amount) {
    const cart = getCart();
    const productId = Number(id);
    const item = cart.find(product => Number(product.id) === productId);
    if (!item) return;

    if (amount > 0) {
        await refreshInventory();
        const availableStock = getAvailableStock(id);
        if (Number(item.quantity) >= availableStock) {
            showToast(`Only ${availableStock} ${item.name} left in stock.`);
            return;
        }
    }

    item.quantity += amount;

    if (item.quantity <= 0) {
        removeItem(id);
        return;
    }

    saveCart(cart);
    renderCart();
    renderCheckoutSummary();
}

function removeItem(id) {
    const productId = Number(id);
    const cart = getCart().filter(item => Number(item.id) !== productId);
    saveCart(cart);
    renderCart();
    renderCheckoutSummary();
    showToast("Item removed");
}

function clearCart() {
    saveCart([]);
    renderCart();
    renderCheckoutSummary();
    showToast("Cart cleared");
}

function calculateTotals() {
    const cart = getCart();
    const subtotal = cart.reduce((sum, item) => sum + Number(item.price) * Number(item.quantity), 0);
    const shipping = subtotal === 0 || subtotal >= 900 ? 0 : 25;
    const tax = Math.round(subtotal * 0.05);
    const total = subtotal + shipping + tax;

    return { subtotal, shipping, tax, total };
}

function updateTotals() {
    const totals = calculateTotals();
    setText("subtotal", money.format(totals.subtotal));
    setText("shipping", totals.shipping === 0 ? "Free" : money.format(totals.shipping));
    setText("tax", money.format(totals.tax));
    setText("total", money.format(totals.total));
}

function renderCheckoutSummary() {
    const summary = document.getElementById("checkoutSummary");
    if (!summary) return;

    const cart = getCart();
    const totals = calculateTotals();

    if (cart.length === 0) {
        summary.innerHTML = `
            <p>Your cart is empty.</p>
            <a class="btn primary wide" href="/products">Shop Products</a>
        `;
    } else {
        summary.innerHTML = cart.map(item => `
            <div class="summary-line">
                <span>${escapeHTML(item.name)} × ${item.quantity}</span>
                <strong>${money.format(item.price * item.quantity)}</strong>
            </div>
        `).join("") + `
            <div class="summary-line"><span>Shipping</span><strong>${totals.shipping === 0 ? "Free" : money.format(totals.shipping)}</strong></div>
            <div class="summary-line"><span>Tax</span><strong>${money.format(totals.tax)}</strong></div>
        `;
    }

    setText("checkoutTotal", money.format(totals.total));
}

async function placeOrder(event) {
    event.preventDefault();

    const cart = getCart();
    if (cart.length === 0) {
        showToast("Your cart is empty. Add a phone first.");
        return;
    }

    const fields = ["name", "email", "address", "city", "postal", "card", "expiry", "cvv"];
    const missingField = fields.some(id => {
        const input = document.getElementById(id);
        return !input || input.value.trim() === "";
    });

    if (missingField) {
        showToast("Please fill in all fields");
        return;
    }

    const email = document.getElementById("email").value.trim();
    if (!email.includes("@") || !email.includes(".")) {
        showToast("Please enter a valid email address");
        return;
    }

    const submitButton = event.target.querySelector("button[type='submit']");
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = "Processing...";
    }

    try {
        const response = await fetch("/api/checkout", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ cart })
        });

        const data = await response.json();

        if (!response.ok || !data.ok) {
            if (data.products) {
                inventoryCache = data.products;
                updateStockDisplays();
                renderCart();
            }
            showToast(data.message || "Checkout failed. Please try again.");
            return;
        }

        inventoryCache = data.products || inventoryCache;
        saveCart([]);
        updateStockDisplays();
        renderCheckoutSummary();
        showToast(data.message || "Order placed successfully");

        setTimeout(() => {
            window.location.href = "/products";
        }, 1300);
    } catch (error) {
        console.error("Checkout error:", error);
        showToast("Checkout failed. Please make sure Flask is running.");
    } finally {
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = "Place Order";
        }
    }
}

function filterProducts() {
    const input = document.getElementById("searchInput");
    if (!input) return;

    const query = input.value.toLowerCase();
    document.querySelectorAll(".product-card").forEach(card => {
        const name = (card.dataset.name || "").toLowerCase();
        card.style.display = name.includes(query) ? "block" : "none";
    });
}

function sortProducts() {
    const grid = document.getElementById("productsGrid");
    const sortSelect = document.getElementById("sortSelect");
    if (!grid || !sortSelect) return;

    const sort = sortSelect.value;
    const cards = Array.from(grid.querySelectorAll(".product-card"));

    cards.sort((a, b) => {
        if (sort === "low") return Number(a.dataset.price) - Number(b.dataset.price);
        if (sort === "high") return Number(b.dataset.price) - Number(a.dataset.price);
        if (sort === "rating") return Number(b.dataset.rating) - Number(a.dataset.rating);
        return 0;
    });

    cards.forEach(card => grid.appendChild(card));
}

function toggleMenu() {
    const navLinks = document.getElementById("navLinks");
    if (navLinks) navLinks.classList.toggle("open");
}

function showToast(message) {
    const toast = document.getElementById("toast");
    if (!toast) {
        alert(message);
        return;
    }

    toast.textContent = message;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2400);
}

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}

function escapeHTML(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

window.addToCart = addToCart;
window.changeQuantity = changeQuantity;
window.removeItem = removeItem;
window.clearCart = clearCart;
window.placeOrder = placeOrder;
window.filterProducts = filterProducts;
window.sortProducts = sortProducts;
window.toggleMenu = toggleMenu;

document.addEventListener("DOMContentLoaded", async () => {
    updateCartCount();
    await refreshInventory();
    renderCart();
    renderCheckoutSummary();
});

window.addEventListener("storage", () => {
    updateCartCount();
    renderCart();
    renderCheckoutSummary();
});
