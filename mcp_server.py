"""
MCP Server for FastAPI E-Commerce Platform
-------------------------------------------
Exposes auth, catalog, orders, and user endpoints as MCP tools.

Install:
    pip install mcp httpx

Run:
    python mcp_server.py

Configure in your MCP client (e.g. Claude Desktop ~/.config/claude/claude_desktop_config.json):
    {
      "mcpServers": {
        "ecommerce": {
          "command": "python",
          "args": ["/absolute/path/to/fastry/mcp_server.py"],
          "env": {
            "API_BASE_URL": "http://localhost:8000"
          }
        }
      }
    }
"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

mcp = FastMCP(
    "ecommerce",
    instructions=(
        "You are an assistant for an e-commerce platform. "
        "Always call auth_login first to get an access_token before calling any protected tool. "
        "Reuse the access_token across all tool calls in the same session. "
        "If a tool returns 401, call auth_refresh_token then retry. "
        "For placing orders, first list products to resolve product_id, then call order_create."
    ),
)

# ─── shared HTTP helpers ───────────────────────────────────────────────────────

def _client(token: str | None = None) -> httpx.AsyncClient:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.AsyncClient(base_url=API_BASE, headers=headers, timeout=30)


async def _post_form(path: str, data: dict, token: str | None = None) -> dict:
    async with _client(token) as c:
        r = await c.post(path, data={k: v for k, v in data.items() if v is not None})
        return r.json()


async def _get(path: str, token: str, params: dict | None = None) -> dict:
    async with _client(token) as c:
        r = await c.get(path, params={k: v for k, v in (params or {}).items() if v is not None})
        return r.json()


async def _post_json(path: str, body: dict, token: str | None = None) -> dict:
    async with _client(token) as c:
        r = await c.post(path, json={k: v for k, v in body.items() if v is not None})
        return r.json()


async def _patch_json(path: str, body: dict, token: str | None = None) -> dict:
    async with _client(token) as c:
        r = await c.patch(path, json={k: v for k, v in body.items() if v is not None})
        return r.json()


async def _delete(path: str, token: str) -> dict:
    async with _client(token) as c:
        r = await c.delete(path)
        return r.json() if r.content else {"status": "deleted"}


# ─── AUTH ──────────────────────────────────────────────────────────────────────

@mcp.tool()
async def auth_register(first_name: str, last_name: str, email: str, password: str, confirm_password: str) -> dict:
    """Register a new user. Sends a 6-digit OTP to the email. OTP expires in 5 minutes."""
    return await _post_form("/api/v1/auth/user/register/", {
        "first_name": first_name, "last_name": last_name,
        "email": email, "password": password, "confirm_password": confirm_password,
    })


@mcp.tool()
async def auth_verify_otp(email: str, otp: str) -> dict:
    """Verify registration OTP. On success returns access_token and refresh_token."""
    return await _post_form("/api/v1/auth/user/otp-verify/", {"email": email, "otp": otp})


@mcp.tool()
async def auth_resend_otp(email: str) -> dict:
    """Resend registration OTP (60 second cooldown between resends)."""
    return await _post_form("/api/v1/auth/user/otp-resend/", {"email": email})


@mcp.tool()
async def auth_login(email: str, password: str) -> dict:
    """Login with email and password. Returns access_token and refresh_token."""
    return await _post_json("/api/v1/auth/user/login/", {"email": email, "password": password})


@mcp.tool()
async def auth_refresh_token(refresh_token: str) -> dict:
    """Exchange a refresh token for a new access token."""
    return await _post_form("/api/v1/auth/user/token-refresh/", {"refresh_token": refresh_token})


@mcp.tool()
async def auth_logout(refresh_token: str) -> dict:
    """Logout — blacklists the refresh token so it cannot be reused."""
    return await _post_form("/api/v1/auth/user/logout/", {"refresh_token": refresh_token})


@mcp.tool()
async def auth_password_reset(email: str) -> dict:
    """Request a password reset OTP. Always returns the same message to prevent email enumeration."""
    return await _post_form("/api/v1/auth/user/password-reset/", {"email": email})


@mcp.tool()
async def auth_password_change(email: str, otp: str, new_password: str, confirm_password: str) -> dict:
    """Change password using OTP received via email. Locked after 3 failed attempts."""
    return await _post_form("/api/v1/auth/user/password-change/", {
        "email": email, "otp": otp,
        "new_password": new_password, "confirm_password": confirm_password,
    })


# ─── CATALOG — Categories ──────────────────────────────────────────────────────

@mcp.tool()
async def catalog_list_categories() -> dict:
    """List all product categories."""
    async with _client() as c:
        r = await c.get("/api/v1/catalog/categories/")
        return r.json()


@mcp.tool()
async def catalog_get_category(category_id: str) -> dict:
    """Get a single category by its UUID."""
    async with _client() as c:
        r = await c.get(f"/api/v1/catalog/categories/{category_id}/")
        return r.json()


@mcp.tool()
async def catalog_create_category(access_token: str, name: str, slug: str, description: str = None, image: str = None) -> dict:
    """Create a new category. Requires admin access token."""
    return await _post_json("/api/v1/catalog/categories/", {
        "name": name, "slug": slug, "description": description, "image": image,
    }, token=access_token)


@mcp.tool()
async def catalog_update_category(access_token: str, category_id: str, name: str = None, slug: str = None, description: str = None, image: str = None) -> dict:
    """Update a category. Requires admin access token."""
    return await _patch_json(f"/api/v1/catalog/categories/{category_id}/", {
        "name": name, "slug": slug, "description": description, "image": image,
    }, token=access_token)


@mcp.tool()
async def catalog_delete_category(access_token: str, category_id: str) -> dict:
    """Delete a category by UUID. Requires admin access token."""
    return await _delete(f"/api/v1/catalog/categories/{category_id}/", token=access_token)


# ─── CATALOG — Products ────────────────────────────────────────────────────────

@mcp.tool()
async def catalog_list_products(category_id: str = None) -> dict:
    """List all active products. Optionally filter by category_id (UUID)."""
    async with _client() as c:
        params = {"category_id": category_id} if category_id else {}
        r = await c.get("/api/v1/catalog/products/", params=params)
        return r.json()


@mcp.tool()
async def catalog_get_product(product_id: str) -> dict:
    """Get a single product by its UUID."""
    async with _client() as c:
        r = await c.get(f"/api/v1/catalog/products/{product_id}/")
        return r.json()


@mcp.tool()
async def catalog_create_product(
    access_token: str, category_id: str, name: str, slug: str,
    price: float, sku: str, stock: int,
    description: str = None, compare_price: float = None,
) -> dict:
    """Create a new product. Requires admin access token."""
    return await _post_json("/api/v1/catalog/products/", {
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
    return await _patch_json(f"/api/v1/catalog/products/{product_id}/", {
        "name": name, "price": price, "stock": stock,
        "description": description, "is_active": is_active,
    }, token=access_token)


@mcp.tool()
async def catalog_delete_product(access_token: str, product_id: str) -> dict:
    """Delete a product by UUID. Requires admin access token."""
    return await _delete(f"/api/v1/catalog/products/{product_id}/", token=access_token)


# ─── ORDERS ────────────────────────────────────────────────────────────────────

@mcp.tool()
async def order_create(
    access_token: str,
    shipping_address: str,
    items: list[dict],
    notes: str = None,
) -> dict:
    """
    Place a new order for the authenticated user.

    items format: [{"product_id": "<uuid>", "quantity": 2}, ...]
    """
    return await _post_json("/api/v1/orders", {
        "shipping_address": shipping_address,
        "items": items,
        "notes": notes,
    }, token=access_token)


@mcp.tool()
async def order_list_mine(access_token: str, page: int = 1, page_size: int = 20) -> dict:
    """List all orders for the currently authenticated user."""
    return await _get("/api/v1/orders/me", token=access_token, params={"page": page, "page_size": page_size})


@mcp.tool()
async def order_get(access_token: str, order_id: str) -> dict:
    """Get a single order by UUID. Users can only see their own orders; admins can see all."""
    return await _get(f"/api/v1/orders/{order_id}", token=access_token)


@mcp.tool()
async def order_update_status(access_token: str, order_id: str, status: str) -> dict:
    """
    Update order status. Requires admin access token.

    status options: pending | processing | shipped | delivered | cancelled
    """
    return await _patch_json(f"/api/v1/orders/{order_id}/status", {"status": status}, token=access_token)


# ─── USERS ─────────────────────────────────────────────────────────────────────

@mcp.tool()
async def user_get_me(access_token: str) -> dict:
    """Get the profile of the currently authenticated user."""
    return await _get("/api/v1/users/me", token=access_token)


@mcp.tool()
async def user_update_me(access_token: str, first_name: str = None, last_name: str = None, dp: str = None) -> dict:
    """Update the authenticated user's own profile."""
    return await _patch_json("/api/v1/users/me", {
        "first_name": first_name, "last_name": last_name, "dp": dp,
    }, token=access_token)


@mcp.tool()
async def user_get_by_id(access_token: str, user_id: str) -> dict:
    """Get any user by UUID. Requires admin access token."""
    return await _get(f"/api/v1/users/{user_id}", token=access_token)


@mcp.tool()
async def user_delete(access_token: str, user_id: str) -> dict:
    """Soft-delete a user by UUID. Requires admin access token."""
    return await _delete(f"/api/v1/users/{user_id}", token=access_token)


# ─── entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
