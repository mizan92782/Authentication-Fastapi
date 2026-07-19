"""
Seed 500+ products for API response time testing.

Usage:
    python -m app.scripts.seed_catalog
    python -m app.scripts.seed_catalog --flush
"""

import asyncio
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from decimal import Decimal
from tortoise import Tortoise
from app.core.database import TORTOISE_ORM_CONFIG
from app.modules.catalog.models import Category, Product, ProductImage


CATEGORIES = [
    {
        "name": "Electronics",
        "slug": "electronics",
        "description": "Phones, laptops, gadgets and accessories",
        "image": "https://images.unsplash.com/photo-1498049794561-7780e7231661?w=800",
    },
    {
        "name": "Clothing",
        "slug": "clothing",
        "description": "Men, women and kids fashion",
        "image": "https://images.unsplash.com/photo-1445205170230-053b83016050?w=800",
    },
    {
        "name": "Books",
        "slug": "books",
        "description": "Fiction, non-fiction, textbooks and more",
        "image": "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=800",
    },
    {
        "name": "Home & Kitchen",
        "slug": "home-kitchen",
        "description": "Furniture, appliances and decor",
        "image": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800",
    },
    {
        "name": "Sports",
        "slug": "sports",
        "description": "Outdoor, fitness and sports gear",
        "image": "https://images.unsplash.com/photo-1517649763962-0c623066013b?w=800",
    },
]

# 100 products per category = 500 total
PRODUCTS_BY_CATEGORY = {
    "electronics": [
        ("Smartphone Pro {i}", "smartphone-pro-{i}", "High-end smartphone model {i} with AMOLED display and 5G.", 15000, 50000, 200, 2),
        ("Laptop Ultra {i}", "laptop-ultra-{i}", "Thin and light laptop with 16GB RAM and 512GB SSD.", 45000, 90000, 30, 2),
        ("Wireless Earbuds {i}", "wireless-earbuds-{i}", "True wireless earbuds with ANC and 30hr battery.", 2000, 8000, 150, 2),
        ("Smart Watch {i}", "smart-watch-{i}", "Fitness smart watch with heart rate and GPS.", 3000, 12000, 100, 1),
        ("Bluetooth Speaker {i}", "bluetooth-speaker-{i}", "Portable waterproof bluetooth speaker.", 1500, 5000, 200, 1),
    ],
    "clothing": [
        ("Men T-Shirt {i}", "men-tshirt-{i}", "100% cotton men's t-shirt, available in multiple colors.", 400, 1200, 500, 2),
        ("Women Dress {i}", "women-dress-{i}", "Casual floral summer dress for women.", 800, 2500, 300, 2),
        ("Denim Jeans {i}", "denim-jeans-{i}", "Classic slim fit denim jeans.", 1200, 3500, 250, 2),
        ("Hoodie {i}", "hoodie-{i}", "Warm fleece hoodie with front pocket.", 900, 2800, 200, 1),
        ("Sneakers {i}", "sneakers-{i}", "Lightweight casual sneakers.", 1500, 5000, 180, 2),
    ],
    "books": [
        ("Python Programming {i}", "python-programming-{i}", "Complete guide to Python programming vol {i}.", 500, 1500, 100, 1),
        ("Data Science Handbook {i}", "data-science-handbook-{i}", "Practical data science with Python and ML.", 700, 2000, 80, 1),
        ("Novel Series {i}", "novel-series-{i}", "Bestselling fiction novel series book {i}.", 300, 800, 200, 1),
        ("History of World {i}", "history-of-world-{i}", "Comprehensive world history volume {i}.", 600, 1800, 60, 1),
        ("Self Help Guide {i}", "self-help-guide-{i}", "Personal development and productivity guide {i}.", 400, 1200, 150, 1),
    ],
    "home-kitchen": [
        ("Non-Stick Pan {i}", "non-stick-pan-{i}", "Premium non-stick frying pan {i}cm diameter.", 800, 2500, 120, 2),
        ("Coffee Maker {i}", "coffee-maker-{i}", "Drip coffee maker with thermal carafe.", 2500, 7000, 60, 2),
        ("Storage Box Set {i}", "storage-box-set-{i}", "Set of 3 stackable storage boxes.", 600, 1800, 200, 1),
        ("Bed Sheet Set {i}", "bed-sheet-set-{i}", "100% cotton 400 thread count bed sheet set.", 1200, 3500, 150, 2),
        ("Wall Clock {i}", "wall-clock-{i}", "Modern minimalist wall clock.", 500, 1500, 100, 1),
    ],
    "sports": [
        ("Yoga Mat {i}", "yoga-mat-{i}", "Non-slip 6mm thick yoga mat.", 600, 1800, 300, 2),
        ("Dumbbell Set {i}", "dumbbell-set-{i}", "Adjustable dumbbell set {i}kg.", 2000, 6000, 80, 2),
        ("Running Shoes {i}", "running-shoes-{i}", "Lightweight breathable running shoes.", 2500, 7000, 120, 2),
        ("Cycling Helmet {i}", "cycling-helmet-{i}", "Aerodynamic cycling helmet with ventilation.", 1500, 4500, 70, 1),
        ("Water Bottle {i}", "water-bottle-{i}", "Insulated stainless steel water bottle 750ml.", 400, 1200, 400, 1),
    ],
}

UNSPLASH_IMAGES = {
    "electronics": [
        "https://images.unsplash.com/photo-1498049794561-7780e7231661?w=600",
        "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600",
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600",
    ],
    "clothing": [
        "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600",
        "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=600",
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600",
    ],
    "books": [
        "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=600",
        "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600",
        "https://images.unsplash.com/photo-1532012197267-da84d127e765?w=600",
    ],
    "home-kitchen": [
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=600",
        "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?w=600",
        "https://images.unsplash.com/photo-1556909172-54557c7e4fb7?w=600",
    ],
    "sports": [
        "https://images.unsplash.com/photo-1517649763962-0c623066013b?w=600",
        "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=600",
        "https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=600",
    ],
}


def build_products(cat_slug: str) -> list[dict]:
    templates = PRODUCTS_BY_CATEGORY[cat_slug]
    images_pool = UNSPLASH_IMAGES[cat_slug]
    products = []
    # 5 templates × 20 iterations = 100 products per category
    for i in range(1, 21):
        for t_idx, (name_t, slug_t, desc_t, min_price, max_price, stock, img_count) in enumerate(templates):
            price = Decimal(str(min_price + (i * 100)))
            compare = Decimal(str(max_price - (i * 50))) if i % 3 != 0 else None
            sku = f"{cat_slug[:4].upper()}-{t_idx:02d}-{i:03d}"
            images = [
                {"url": images_pool[j % len(images_pool)], "alt": f"{name_t.format(i=i)} image {j+1}", "is_primary": j == 0}
                for j in range(img_count)
            ]
            products.append({
                "name": name_t.format(i=i),
                "slug": slug_t.format(i=i),
                "description": desc_t.format(i=i),
                "price": price,
                "compare_price": compare,
                "stock": stock + i,
                "sku": sku,
                "images": images,
            })
    return products


async def flush():
    print("\n🗑️  Flushing catalog data...")
    await ProductImage.all().delete()
    await Product.all().delete()
    await Category.all().delete()
    print("   ✅ Done\n")


async def seed():
    total_products = 0
    total_images = 0

    for cat_data in CATEGORIES:
        cat, created = await Category.get_or_create(
            slug=cat_data["slug"],
            defaults={k: v for k, v in cat_data.items() if k != "slug"},
        )
        print(f"{'✅ Created' if created else '⏭️  Skipped'} category : {cat.name}")

        products = build_products(cat_data["slug"])
        new_products = 0

        # bulk-friendly: create products one by one but batch image inserts
        for prod_data in products:
            images = prod_data.pop("images")
            prod, prod_created = await Product.get_or_create(
                sku=prod_data["sku"],
                defaults={"category_id": cat.id, **prod_data},
            )
            if prod_created:
                await ProductImage.bulk_create([
                    ProductImage(product_id=prod.id, **img) for img in images
                ])
                new_products += 1
                total_images += len(images)

        total_products += new_products
        print(f"   └─ {new_products} products seeded ({len(products) - new_products} skipped)\n")

    print("=" * 45)
    print(f"  ✅ Total products  : {total_products}")
    print(f"  ✅ Total images    : {total_images}")
    print(f"  ✅ Total categories: {len(CATEGORIES)}")
    print("=" * 45)


async def main(do_flush: bool):
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)
    if do_flush:
        await flush()
    await seed()
    await Tortoise.close_connections()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--flush", action="store_true", help="Wipe catalog data before seeding")
    args = parser.parse_args()
    asyncio.run(main(args.flush))
