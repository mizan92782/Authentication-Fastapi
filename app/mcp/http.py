import os
import httpx

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


def _client(token: str | None = None) -> httpx.AsyncClient:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.AsyncClient(base_url=API_BASE, headers=headers, timeout=30)


async def post_form(path: str, data: dict, token: str | None = None) -> dict:
    async with _client(token) as c:
        r = await c.post(path, data={k: v for k, v in data.items() if v is not None})
        return r.json()


async def post_json(path: str, body: dict, token: str | None = None) -> dict:
    async with _client(token) as c:
        r = await c.post(path, json={k: v for k, v in body.items() if v is not None})
        return r.json()


async def get(path: str, token: str | None = None, params: dict | None = None) -> dict:
    async with _client(token) as c:
        r = await c.get(path, params={k: v for k, v in (params or {}).items() if v is not None})
        return r.json()


async def patch_json(path: str, body: dict, token: str | None = None) -> dict:
    async with _client(token) as c:
        r = await c.patch(path, json={k: v for k, v in body.items() if v is not None})
        return r.json()


async def delete(path: str, token: str | None = None) -> dict:
    async with _client(token) as c:
        r = await c.delete(path)
        return r.json() if r.content else {"status": "deleted"}
