"""
Seed Script — Like Django's management commands
================================================
Usage:
    python scripts/seed.py                  # seed everything
    python scripts/seed.py --only users     # seed only users
    python scripts/seed.py --only products  # seed only categories + products
    python scripts/seed.py --only orders    # seed only orders
    python scripts/seed.py --flush          # wipe all data first, then seed
    python scripts/seed.py --flush --only users  # wipe + seed only users
"""

import asyncio
import argparse
import sys
import os

# Make sure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
from app.database.connection import TORTOISE_ORM_CONFIG
from app.core.security import hash_password
from app.models.user import User
from app.models.product import Category, Product
from app.models.order import Order, OrderItem, OrderStatus
from tortoise import Tortoise


# ─────────────────────────────────────────────
# SEED DATA
# ─────────────────────────────────────────────

USERS = [
    {
        "email": "admin@ecommerce.com",
        "username": "admin",
        "full_name": "Admin User",
        "password": "Admin1234",
        "role": "admin",
        "phone": "+8801700000001",
        "address": "123 Admin Street, Dhaka, Bangladesh",
    },
    {
        "email": "john@example.com",
        "username": "john_doe",
        "full_name": "John Doe",
        "password": "Customer1234",
        "role": "customer",
        "phone": "+8801700000002",
        "address": "45 Green Road, Dhaka, Bangladesh",
    },
    {
        "email": "jane@example.com",
        "username": "jane_smith",
        "full_name": "Jane Smith",
        "password": "Customer1234",
        "role": "customer",
        "phone": "+8801700000003",
        "address": "78 Lake View, Chittagong, Bangladesh",
    },
    {
        "email": "mizan@example.com",
        "username": "mizan_dev",
        "full_name": "Mizan Developer",
        "password": "Customer1234",
        "role": "customer",
        "phone": "+8801700000004",
        "address": "12 Tech Park, Sylhet, Bangladesh",
    },
]

CATEGORIES = [
    {"name": "Electronics",    "slug": "electronics",    "description": "Phones, laptops, gadgets and accessories"},
    {"name": "Clothing",       "slug": "clothing",       "description": "Men, women and kids fashion"},
    {"name": "Books",          "slug": "books",          "description": "Fiction, non-fiction, textbooks"},
    {"name": "Home & Kitchen", "slug": "home-kitchen",   "description": "Furniture, appliances and decor"},
    {"name": "Sports",         "slug": "sports",         "description": "Outdoor, fitness and sports gear"},
]

PRODUCTS = [
    # Electronics
    {
        "name": "iPhone 15 Pro",
        "slug": "iphone-15-pro",
        "description": "Apple iPhone 15 Pro with A17 chip, 256GB storage, titanium design.",
        "price": Decimal("129999.00"),
        "compare_price": Decimal("139999.00"),
        "stock": 50,
        "sku": "APPL-IP15P-256",
        "image_url": "https://example.com/images/iphone15pro.jpg",
        "category_slug": "electronics",
    },
    {
        "name": "Samsung Galaxy S24",
        "slug": "samsung-galaxy-s24",
        "description": "Samsung Galaxy S24 with Snapdragon 8 Gen 3, 128GB.",
        "price": Decimal("89999.00"),
        "compare_price": Decimal("99999.00"),
        "stock": 35,
        "sku": "SMSNG-S24-128",
        "image_url": "https://example.com/images/galaxys24.jpg",
        "category_slug": "electronics",
    },
    {
        "name": "MacBook Air M3",
        "slug": "macbook-air-m3",
        "description": "Apple MacBook Air with M3 chip, 16GB RAM, 512GB SSD.",
        "price": Decimal("149999.00"),
        "compare_price": None,
        "stock": 20,
        "sku": "APPL-MBA-M3-512",
        "image_url": "https://example.com/images/macbookairm3.jpg",
        "category_slug": "electronics",
    },
    {
        "name": "Sony WH-1000XM5 Headphones",
        "slug": "sony-wh-1000xm5",
        "description": "Industry-leading noise cancelling wireless headphones.",
        "price": Decimal("29999.00"),
        "compare_price": Decimal("34999.00"),
        "stock": 100,
        "sku": "SONY-WH1000XM5",
        "image_url": "https://example.com/images/sonywh1000xm5.jpg",
        "category_slug": "electronics",
    },
    # Clothing
    {
        "name": "Men's Classic T-Shirt",
        "slug": "mens-classic-tshirt",
        "description": "100% cotton comfortable everyday t-shirt. Available in multiple colors.",
        "price": Decimal("799.00"),
        "compare_price": Decimal("999.00"),
        "stock": 500,
        "sku": "CLT-MEN-TSH-001",
        "image_url": "https://example.com/images/mens-tshirt.jpg",
        "category_slug": "clothing",
    },
    {
        "name": "Women's Casual Dress",
        "slug": "womens-casual-dress",
        "description": "Lightweight floral summer dress, perfect for everyday wear.",
        "price": Decimal("1499.00"),
        "compare_price": Decimal("1999.00"),
        "stock": 200,
        "sku": "CLT-WMN-DRS-001",
        "image_url": "https://example.com/images/womens-dress.jpg",
        "category_slug": "clothing",
    },
    # Books
    {
        "name": "Clean Code by Robert C. Martin",
        "slug": "clean-code-robert-martin",
        "description": "A handbook of agile software craftsmanship. Must-read for every developer.",
        "price": Decimal("1200.00"),
        "compare_price": None,
        "stock": 150,
        "sku": "BOOK-CLEANCODE-001",
        "image_url": "https://example.com/images/clean-code.jpg",
        "category_slug": "books",
    },
    {
        "name": "The Pragmatic Programmer",
        "slug": "pragmatic-programmer",
        "description": "Your journey to mastery — 20th anniversary edition.",
        "price": Decimal("1100.00"),
        "compare_price": Decimal("1300.00"),
        "stock": 80,
        "sku": "BOOK-PRAGPROG-001",
        "image_url": "https://example.com/images/pragmatic-programmer.jpg",
        "category_slug": "books",
    },
    # Home & Kitchen
    {
        "name": "Instant Pot Duo 7-in-1",
        "slug": "instant-pot-duo-7in1",
        "description": "Electric pressure cooker, slow cooker, rice cooker, steamer and more.",
        "price": Decimal("6999.00"),
        "compare_price": Decimal("8999.00"),
        "stock": 60,
        "sku": "HOME-INSTPOT-7IN1",
        "image_url": "https://example.com/images/instant-pot.jpg",
        "category_slug": "home-kitchen",
    },
    # Sports
    {
        "name": "Yoga Mat Premium",
        "slug": "yoga-mat-premium",
        "description": "Non-slip 6mm thick yoga mat with carrying strap.",
        "price": Decimal("1299.00"),
        "compare_price": Decimal("1599.00"),
        "stock": 300,
        "sku": "SPT-YOGAMAT-PREM",
        "image_url": "https://example.com/images/yoga-mat.jpg",
        "category_slug": "sports",
    },
]


# ─────────────────────────────────────────────
# SEEDER FUNCTIONS
# ─────────────────────────────────────────────

async def flush_all():
    print("\n🗑️  Flushing all data...")
    await OrderItem.all().delete()
    await Order.all().delete()
    await Product.all().delete()
    await Category.all().delete()
    await User.all().delete()
    print("   ✅ All tables cleared")


async def seed_users() -> dict[str, User]:
    print("\n👤 Seeding users...")
    created = {}
    for data in USERS:
        existing = await User.get_or_none(email=data["email"])
        if existing:
            print(f"   ⏭️  Skipped  : {data['email']} (already exists)")
            created[data["username"]] = existing
            continue
        user = await User.create(
            email=data["email"],
            username=data["username"],
            full_name=data["full_name"],
            hashed_password=hash_password(data["password"]),
            role=data["role"],
            phone=data["phone"],
            address=data["address"],
        )
        created[data["username"]] = user
        print(f"   ✅ Created  : {user.full_name} ({user.role}) — {user.email}")
    return created


async def seed_categories() -> dict[str, Category]:
    print("\n📂 Seeding categories...")
    created = {}
    for data in CATEGORIES:
        existing = await Category.get_or_none(slug=data["slug"])
        if existing:
            print(f"   ⏭️  Skipped  : {data['name']} (already exists)")
            created[data["slug"]] = existing
            continue
        cat = await Category.create(
            name=data["name"],
            slug=data["slug"],
            description=data["description"],
        )
        created[data["slug"]] = cat
        print(f"   ✅ Created  : {cat.name}")
    return created


async def seed_products(categories: dict[str, Category]) -> list[Product]:
    print("\n📦 Seeding products...")
    created = []
    for data in PRODUCTS:
        existing = await Product.get_or_none(sku=data["sku"])
        if existing:
            print(f"   ⏭️  Skipped  : {data['name']} (already exists)")
            created.append(existing)
            continue
        category = categories.get(data["category_slug"])
        product = await Product.create(
            name=data["name"],
            slug=data["slug"],
            description=data["description"],
            price=data["price"],
            compare_price=data["compare_price"],
            stock=data["stock"],
            sku=data["sku"],
            image_url=data["image_url"],
            category=category,
            is_active=True,
        )
        created.append(product)
        print(f"   ✅ Created  : {product.name} — ৳{product.price} (stock: {product.stock})")
    return created


async def seed_orders(users: dict[str, User], products: list[Product]):
    print("\n🛒 Seeding orders...")

    # helper to find product by sku
    def get_product(sku: str):
        return next((p for p in products if p.sku == sku), None)

    orders_data = [
        {
            "user_key": "john_doe",
            "shipping_address": "45 Green Road, Dhaka, Bangladesh",
            "notes": "Please leave at door",
            "status": OrderStatus.DELIVERED,
            "items": [
                {"sku": "SONY-WH1000XM5",  "quantity": 1},
                {"sku": "CLT-MEN-TSH-001", "quantity": 2},
            ],
        },
        {
            "user_key": "john_doe",
            "shipping_address": "45 Green Road, Dhaka, Bangladesh",
            "notes": None,
            "status": OrderStatus.SHIPPED,
            "items": [
                {"sku": "BOOK-CLEANCODE-001", "quantity": 1},
                {"sku": "BOOK-PRAGPROG-001",  "quantity": 1},
            ],
        },
        {
            "user_key": "jane_smith",
            "shipping_address": "78 Lake View, Chittagong, Bangladesh",
            "notes": "Gift wrap please",
            "status": OrderStatus.PROCESSING,
            "items": [
                {"sku": "CLT-WMN-DRS-001", "quantity": 1},
                {"sku": "SPT-YOGAMAT-PREM", "quantity": 1},
            ],
        },
        {
            "user_key": "mizan_dev",
            "shipping_address": "12 Tech Park, Sylhet, Bangladesh",
            "notes": None,
            "status": OrderStatus.PENDING,
            "items": [
                {"sku": "APPL-IP15P-256",  "quantity": 1},
                {"sku": "APPL-MBA-M3-512", "quantity": 1},
            ],
        },
        {
            "user_key": "mizan_dev",
            "shipping_address": "12 Tech Park, Sylhet, Bangladesh",
            "notes": "Urgent delivery",
            "status": OrderStatus.CANCELLED,
            "items": [
                {"sku": "HOME-INSTPOT-7IN1", "quantity": 1},
            ],
        },
    ]

    for order_data in orders_data:
        user = users.get(order_data["user_key"])
        if not user:
            print(f"   ⚠️  Skipped order: user '{order_data['user_key']}' not found")
            continue

        total = Decimal("0.00")
        line_items = []
        for item in order_data["items"]:
            product = get_product(item["sku"])
            if not product:
                print(f"   ⚠️  Product SKU '{item['sku']}' not found, skipping item")
                continue
            subtotal = product.price * item["quantity"]
            total += subtotal
            line_items.append((product, item["quantity"], product.price, subtotal))

        if not line_items:
            continue

        order = await Order.create(
            user=user,
            status=order_data["status"],
            total_amount=total,
            shipping_address=order_data["shipping_address"],
            notes=order_data["notes"],
        )

        for product, qty, unit_price, subtotal in line_items:
            await OrderItem.create(
                order=order,
                product=product,
                quantity=qty,
                unit_price=unit_price,
                subtotal=subtotal,
            )

        item_names = ", ".join(p.name for p, *_ in line_items)
        print(f"   ✅ Order #{str(order.id)[:8]}... | {user.username} | {order.status} | ৳{total} | [{item_names}]")


def print_summary(users):
    print("\n" + "=" * 60)
    print("  ✅  SEED COMPLETE — Test Credentials")
    print("=" * 60)
    print(f"  {'Role':<12} {'Email':<30} {'Password'}")
    print(f"  {'-'*12} {'-'*30} {'-'*15}")
    creds = {
        "admin":      ("admin@ecommerce.com",  "Admin1234"),
        "john_doe":   ("john@example.com",     "Customer1234"),
        "jane_smith": ("jane@example.com",     "Customer1234"),
        "mizan_dev":  ("mizan@example.com",    "Customer1234"),
    }
    roles = {
        "admin":      "admin",
        "john_doe":   "customer",
        "jane_smith": "customer",
        "mizan_dev":  "customer",
    }
    for username, (email, password) in creds.items():
        role = roles[username]
        print(f"  {role:<12} {email:<30} {password}")
    print("=" * 60)
    print("  API Docs  →  http://localhost:8000/docs")
    print("  Health    →  http://localhost:8000/health")
    print("=" * 60 + "\n")


# ─────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────

async def main(only: str | None, flush: bool):
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)
    print("✅ Database connected")

    if flush:
        await flush_all()

    users = {}
    categories = {}
    products = []

    if only == "users":
        users = await seed_users()
    elif only == "products":
        categories = await seed_categories()
        products = await seed_products(categories)
    elif only == "orders":
        # orders need users + products already in DB
        all_users = await User.all()
        users = {u.username: u for u in all_users}
        products = await Product.all()
        await seed_orders(users, products)
    else:
        # seed everything
        users = await seed_users()
        categories = await seed_categories()
        products = await seed_products(categories)
        await seed_orders(users, products)

    await Tortoise.close_connections()
    print_summary(users)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the database with test data")
    parser.add_argument(
        "--only",
        choices=["users", "products", "orders"],
        help="Seed only a specific section",
    )
    parser.add_argument(
        "--flush",
        action="store_true",
        help="Wipe all existing data before seeding",
    )
    args = parser.parse_args()
    asyncio.run(main(only=args.only, flush=args.flush))
