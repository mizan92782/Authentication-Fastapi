"""
MCP Client — Claude drives the MCP server tools
-------------------------------------------------
Run:
    python -m app.mcp.client
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import anthropic

load_dotenv()

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MCP_SERVER = StdioServerParameters(
    command="python",
    args=["-m", "app.mcp.serve"],
    env={"API_BASE_URL": os.getenv("API_BASE_URL", "http://localhost:8000")},
)

SYSTEM_INSTRUCTION = """
You are an intelligent assistant for an e-commerce platform.
You have access to tools for authentication, catalog browsing, order management, and user profiles.

Rules:
- Always call auth_login first when the user wants to do something that needs authentication.
- Reuse the access_token from login across all subsequent tool calls in the session.
- If a tool returns a 401 error, call auth_refresh_token then retry the original tool.
- When placing an order, first call catalog_list_products to find the correct product_id.
- Be concise and friendly in your final responses.
- Never expose raw tokens to the user.
""".strip()


def _mcp_tools_to_claude(mcp_tools: list) -> list:
    """Convert MCP tool definitions to Claude tool format."""
    result = []
    for tool in mcp_tools:
        schema = tool.inputSchema or {}
        result.append({
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", []),
            },
        })
    return result


async def run():
    client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

    async with stdio_client(MCP_SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            claude_tools = _mcp_tools_to_claude(tools_result.tools)

            session_state: dict = {}
            messages: list = []

            print("\n🤖  E-Commerce AI Assistant (Claude + MCP)")
            print("    Type your request. Ctrl+C to exit.\n")

            while True:
                try:
                    user_input = input("You: ").strip()
                except (KeyboardInterrupt, EOFError):
                    print("\nGoodbye!")
                    break

                if not user_input:
                    continue

                messages.append({"role": "user", "content": user_input})

                # agentic loop
                while True:
                    response = await asyncio.to_thread(
                        client.messages.create,
                        model=os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001"),
                        max_tokens=2048,
                        system=SYSTEM_INSTRUCTION,
                        tools=claude_tools,
                        messages=messages,
                    )

                    if response.stop_reason == "end_turn":
                        answer = next(b.text for b in response.content if hasattr(b, "text"))
                        messages.append({"role": "assistant", "content": answer})
                        print(f"\nAssistant: {answer}\n")
                        break

                    # handle tool calls
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            fn_args = dict(block.input)

                            # auto-inject stored access_token
                            if "access_token" in fn_args and not fn_args.get("access_token"):
                                fn_args["access_token"] = session_state.get("access_token", "")

                            safe_args = {k: v for k, v in fn_args.items() if "token" not in k}
                            print(f"  🔧 {block.name}({json.dumps(safe_args)})")

                            tool_result = await session.call_tool(block.name, fn_args)
                            result_text = tool_result.content[0].text if tool_result.content else "{}"

                            try:
                                result_data = json.loads(result_text)
                            except Exception:
                                result_data = {"result": result_text}

                            # persist tokens
                            for d in [result_data, result_data.get("data", {})]:
                                if isinstance(d, dict):
                                    if "access_token" in d:
                                        session_state["access_token"] = d["access_token"]
                                    if "refresh_token" in d:
                                        session_state["refresh_token"] = d["refresh_token"]

                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result_text,
                            })

                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    asyncio.run(run())
