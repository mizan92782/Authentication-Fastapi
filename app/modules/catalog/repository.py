from app.shared.base.base_repository import BaseRepository
from app.modules.catalog.models import Category, Product, ProductImage


class CategoryRepository(BaseRepository[Category]):
    model = Category

    @classmethod
    async def get_by_slug(cls, slug: str):
        return await Category.get_or_none(slug=slug, is_deleted=False)


class ProductRepository(BaseRepository[Product]):
    model = Product

    @classmethod
    async def get_with_details(cls, product_id):
        return await Product.get_or_none(id=product_id, is_deleted=False).prefetch_related("category", "images")

    @classmethod
    async def list_all(cls):
        return await Product.filter(is_deleted=False).prefetch_related("category", "images")

    @classmethod
    async def list_by_category(cls, category_id):
        return await Product.filter(is_deleted=False, category_id=category_id).prefetch_related("category", "images")


class ProductImageRepository(BaseRepository[ProductImage]):
    model = ProductImage
