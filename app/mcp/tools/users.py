from app.mcp.http import get, patch_json, delete


def register_user_tools(mcp):

    @mcp.tool()
    async def user_get_me(access_token: str) -> dict:
        """Get the profile of the currently authenticated user."""
        return await get("/api/v1/users/me", token=access_token)

    @mcp.tool()
    async def user_update_me(access_token: str, first_name: str = None, last_name: str = None, dp: str = None) -> dict:
        """Update the authenticated user's own profile."""
        return await patch_json("/api/v1/users/me", {
            "first_name": first_name, "last_name": last_name, "dp": dp,
        }, token=access_token)

    @mcp.tool()
    async def user_get_by_id(access_token: str, user_id: str) -> dict:
        """Get any user by UUID. Requires admin access token."""
        return await get(f"/api/v1/users/{user_id}", token=access_token)

    @mcp.tool()
    async def user_delete(access_token: str, user_id: str) -> dict:
        """Soft-delete a user by UUID. Requires admin access token."""
        return await delete(f"/api/v1/users/{user_id}", token=access_token)
