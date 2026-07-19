from fastapi import HTTPException, status
from app.modules.catalog.repository import CategoryRepository, ProductRepository, ProductImageRepository
from app.modules.catalog.schemas import CategoryCreate, CategoryUpdate, ProductCreate, ProductUpdate


class CategoryService:

    @staticmethod
    async def list():
        return await CategoryRepository.get_all()

    @staticmethod
    async def get(category_id):
        cat = await CategoryRepository.get_by_id(category_id)
        if not cat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return cat

    @staticmethod
    async def create(data: CategoryCreate):
        if await CategoryRepository.get_by_slug(data.slug):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already exists")
        return await CategoryRepository.create(**data.model_dump())

    @staticmethod
    async def update(category_id, data: CategoryUpdate):
        cat = await CategoryService.get(category_id)
        return await CategoryRepository.update(cat, data.model_dump(exclude_none=True))

    @staticmethod
    async def delete(category_id):
        cat = await CategoryService.get(category_id)
        await CategoryRepository.soft_delete(cat)


class ProductService:

    @staticmethod
    async def list(category_id=None):
        if category_id:
            return await ProductRepository.list_by_category(category_id)
        return await ProductRepository.list_all()

    @staticmethod
    async def get(product_id):
        product = await ProductRepository.get_with_details(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    @staticmethod
    async def create(data: ProductCreate):
        cat = await CategoryRepository.get_by_id(data.category_id)
        if not cat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        images = data.images
        product_data = data.model_dump(exclude={"images"})
        product = await ProductRepository.create(**product_data)

        for img in images:
            await ProductImageRepository.create(product_id=product.id, **img.model_dump())

        return await ProductRepository.get_with_details(product.id)

    @staticmethod
    async def update(product_id, data: ProductUpdate):
        product = await ProductService.get(product_id)
        return await ProductRepository.update(product, data.model_dump(exclude_none=True))

    @staticmethod
    async def delete(product_id):
        product = await ProductService.get(product_id)
        await ProductRepository.soft_delete(product)
