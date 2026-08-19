from app.mcp.http import get, post_json, patch_json


def register_order_tools(mcp):

    @mcp.tool()
    async def order_create(access_token: str, shipping_address: str, items: list[dict], notes: str = None) -> dict:
        """
        Place a new order for the authenticated user.
        items format: [{"product_id": "<uuid>", "quantity": 2}, ...]
        """
        return await post_json("/api/v1/orders/", {
            "shipping_address": shipping_address,
            "items": items,
            "notes": notes,
        }, token=access_token)

    @mcp.tool()
    async def order_list_mine(access_token: str, page: int = 1, page_size: int = 20) -> dict:
        """List all orders for the currently authenticated user."""
        return await get("/api/v1/orders/me/", token=access_token, params={"page": page, "page_size": page_size})

    @mcp.tool()
    async def order_get(access_token: str, order_id: str) -> dict:
        """Get a single order by UUID. Users can only see their own orders."""
        return await get(f"/api/v1/orders/{order_id}/", token=access_token)

    @mcp.tool()
    async def order_cancel(access_token: str, order_id: str) -> dict:
        """Cancel an order. Only pending or processing orders can be cancelled."""
        return await post_json(f"/api/v1/orders/{order_id}/cancel/", {}, token=access_token)

    @mcp.tool()
    async def order_update_status(access_token: str, order_id: str, status: str) -> dict:
        """Update order status. Requires admin. Options: pending | processing | shipped | delivered | cancelled"""
        return await patch_json(f"/api/v1/orders/{order_id}/status/", {"status": status}, token=access_token)
