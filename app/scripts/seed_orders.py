"""
Seed orders with users.

Usage:
    python -m app.scripts.seed_orders
    python -m app.scripts.seed_orders --flush
"""

import asyncio
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from decimal import Decimal
from tortoise import Tortoise
from app.core.database import TORTOISE_ORM_CONFIG
from app.core.security import hash_password
from app.modules.users.models import User
from app.modules.catalog.models import Product
from app.modules.orders.models import Order, OrderItem, OrderStatus


USERS = [
    {"first_name": "John",  "last_name": "Doe",   "email": "john@example.com",  "password": "Customer1234"},
    {"first_name": "Jane",  "last_name": "Smith",  "email": "jane@example.com",  "password": "Customer1234"},
    {"first_name": "Mizan", "last_name": "Dev",    "email": "mizan@example.com", "password": "Customer1234"},
]

# Each order: (user_email, shipping_address, status, notes, [(sku, qty), ...])
ORDERS = [
    (
        "john@example.com",
        "45 Green Road, Dhaka",
        OrderStatus.DELIVERED,
        "Please leave at door",
        [("ELEC-00-001", 1), ("CLOT-00-001", 2)],
    ),
    (
        "john@example.com",
        "45 Green Road, Dhaka",
        OrderStatus.SHIPPED,
        None,
        [("BOOK-00-001", 1), ("BOOK-01-001", 1), ("SPOR-00-001", 1)],
    ),
    (
        "jane@example.com",
        "78 Lake View, Chittagong",
        OrderStatus.PROCESSING,
        "Gift wrap please",
        [("CLOT-01-001", 1), ("SPOR-00-001", 2)],
    ),
    (
        "mizan@example.com",
        "12 Tech Park, Sylhet",
        OrderStatus.PENDING,
        None,
        [("ELEC-00-001", 1), ("ELEC-01-001", 1), ("ELEC-02-001", 1)],
    ),
    (
        "mizan@example.com",
        "12 Tech Park, Sylhet",
        OrderStatus.CANCELLED,
        "Urgent delivery",
        [("HOME-00-001", 1), ("CLOT-00-002", 3)],
    ),
]


async def flush():
    print("\n🗑️  Flushing orders & users...")
    await OrderItem.all().delete()
    await Order.all().delete()
    await User.filter(role="customer").delete()
    print("   ✅ Done\n")


async def seed_users() -> dict[str, User]:
    print("👤 Seeding users...")
    users = {}
    for data in USERS:
        user, created = await User.get_or_create(
            email=data["email"],
            defaults={
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "hashed_password": hash_password(data["password"]),
            },
        )
        users[data["email"]] = user
        print(f"   {'✅ Created' if created else '⏭️  Skipped'} : {user.first_name} {user.last_name} ({user.email})")
    return users


async def seed_orders(users: dict[str, User]):
    print("\n🛒 Seeding orders...")

    # load all products into a sku→product map
    products = {p.sku: p for p in await Product.all()}

    for user_email, address, status, notes, items in ORDERS:
        user = users.get(user_email)
        if not user:
            print(f"   ⚠️  User {user_email} not found, skipping")
            continue

        line_items = []
        for sku, qty in items:
            product = products.get(sku)
            if not product:
                print(f"   ⚠️  SKU '{sku}' not found, skipping item")
                continue
            line_items.append((product, qty, product.price, product.price * qty))

        if not line_items:
            continue

        total = sum(subtotal for _, _, _, subtotal in line_items)
        order = await Order.create(
            user=user,
            status=status,
            total_amount=total,
            shipping_address=address,
            notes=notes,
        )
        await OrderItem.bulk_create([
            OrderItem(order=order, product=p, quantity=qty, unit_price=price, subtotal=sub)
            for p, qty, price, sub in line_items
        ])

        names = ", ".join(p.name for p, *_ in line_items)
        print(f"   ✅ Order {str(order.id)[:8]}... | {user.email} | {status.value} | ৳{total} | [{names}]")


async def main(do_flush: bool):
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)
    if do_flush:
        await flush()
    users = await seed_users()
    await seed_orders(users)
    await Tortoise.close_connections()

    print("\n" + "=" * 55)
    print("  ✅  SEED COMPLETE")
    print("=" * 55)
    print(f"  {'Email':<30} {'Password'}")
    print(f"  {'-'*30} {'-'*15}")
    for u in USERS:
        print(f"  {u['email']:<30} {u['password']}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--flush", action="store_true", help="Wipe orders & users before seeding")
    args = parser.parse_args()
    asyncio.run(main(args.flush))
