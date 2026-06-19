"""
Create all database tables directly using Tortoise generate_schemas.
Use this instead of aerich for initial dev setup.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from app.database.connection import TORTOISE_ORM_CONFIG


async def main():
    print("🔌 Connecting to database...")
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)
    print("✅ Connected")

    print("🏗️  Creating tables...")
    await Tortoise.generate_schemas(safe=True)
    print("✅ All tables created successfully")

    await Tortoise.close_connections()
    print("✅ Done — database is ready")


if __name__ == "__main__":
    asyncio.run(main())
