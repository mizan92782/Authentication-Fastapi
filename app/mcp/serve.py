"""
MCP Server — E-Commerce Platform
----------------------------------
Run:
    python -m app.mcp.serve

Claude Desktop config (~/.config/claude/claude_desktop_config.json):
    {
      "mcpServers": {
        "ecommerce": {
          "command": "python",
          "args": ["-m", "app.mcp.serve"],
          "env": { "API_BASE_URL": "http://localhost:8000" }
        }
      }
    }
"""

from mcp.server.fastmcp import FastMCP
from app.mcp.tools.auth import register_auth_tools
from app.mcp.tools.product import register_catalog_tools
from app.mcp.tools.orders import register_order_tools
from app.mcp.tools.users import register_user_tools

mcp = FastMCP(
    "ecommerce",
    instructions=(
        "You are an assistant for an e-commerce platform. "
        "Always call auth_login first to get an access_token before calling any protected tool. "
        "Reuse the access_token across all tool calls in the same session. "
        "If a tool returns 401, call auth_refresh_token then retry. "
        "For placing orders, first call catalog_list_products to resolve product_id, then call order_create."
    ),
)

register_auth_tools(mcp)
register_catalog_tools(mcp)
register_order_tools(mcp)
register_user_tools(mcp)

if __name__ == "__main__":
    mcp.run()
