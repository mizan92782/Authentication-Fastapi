from app.mcp.http import get, post_json, patch_json, delete


def register_catalog_tools(mcp):

    @mcp.tool()
    async def catalog_list_categories() -> dict:
        """List all product categories."""
        return await get("/api/v1/catalog/categories/")

    @mcp.tool()
    async def catalog_get_category(category_id: str) -> dict:
        """Get a single category by its UUID."""
        return await get(f"/api/v1/catalog/categories/{category_id}/")

    @mcp.tool()
    async def catalog_create_category(access_token: str, name: str, slug: str, description: str = None, image: str = None) -> dict:
        """Create a new category. Requires admin access token."""
        return await post_json("/api/v1/catalog/categories/", {
            "name": name, "slug": slug, "description": description, "image": image,
        }, token=access_token)

    @mcp.tool()
    async def catalog_update_category(access_token: str, category_id: str, name: str = None, slug: str = None, description: str = None, image: str = None) -> dict:
        """Update a category. Requires admin access token."""
        return await patch_json(f"/api/v1/catalog/categories/{category_id}/", {
            "name": name, "slug": slug, "description": description, "image": image,
        }, token=access_token)

    @mcp.tool()
    async def catalog_delete_category(access_token: str, category_id: str) -> dict:
        """Delete a category by UUID. Requires admin access token."""
        return await delete(f"/api/v1/catalog/categories/{category_id}/", token=access_token)

    @mcp.tool()
    async def catalog_list_products(category_id: str = None) -> dict:
        """List all active products. Optionally filter by category_id (UUID)."""
        return await get("/api/v1/catalog/products/", params={"category_id": category_id} if category_id else None)

    @mcp.tool()
    async def catalog_get_product(product_id: str) -> dict:
        """Get a single product by its UUID."""
        return await get(f"/api/v1/catalog/products/{product_id}/")

    @mcp.tool()
    async def catalog_create_product(
        access_token: str, category_id: str, name: str, slug: str,
        price: float, sku: str, stock: int,
        description: str = None, compare_price: float = None,
    ) -> dict:
        """Create a new product. Requires admin access token."""
        return await post_json("/api/v1/catalog/products/", {
            "category_id": category_id, "name": name, "slug": slug,
            "price": price, "sku": sku, "stock": stock,
            "description": description, "compare_price": compare_price,
        }, token=access_token)

    @mcp.tool()
    async def catalog_update_product(
        access_token: str, product_id: str,
        name: str = None, price: float = None, stock: int = None,
        description: str = None, is_active: bool = None,
    ) -> dict:
        """Update a product. Requires admin access token."""
        return await patch_json(f"/api/v1/catalog/products/{product_id}/", {
            "name": name, "price": price, "stock": stock,
            "description": description, "is_active": is_active,
        }, token=access_token)

    @mcp.tool()
    async def catalog_delete_product(access_token: str, product_id: str) -> dict:
        """Delete a product by UUID. Requires admin access token."""
        return await delete(f"/api/v1/catalog/products/{product_id}/", token=access_token)
