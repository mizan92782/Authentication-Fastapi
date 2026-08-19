"""
Gemini MCP Client
-----------------
Gemini drives the MCP server tools via function calling.

Install:
    pip install mcp[cli] httpx google-generativeai python-dotenv

Run:
    python mcp_gemini_client.py
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MCP_SERVER = StdioServerParameters(
    command="python",
    args=[os.path.join(os.path.dirname(__file__), "mcp_server.py")],
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
"""


def _mcp_tools_to_gemini(mcp_tools: list) -> list:
    """Convert MCP tool definitions to Gemini function declarations."""
    declarations = []
    for tool in mcp_tools:
        schema = tool.inputSchema or {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Gemini expects snake_case type strings
        gemini_props = {}
        for prop_name, prop_def in properties.items():
            t = prop_def.get("type", "string")
            gemini_props[prop_name] = {"type": t.upper(), "description": prop_def.get("description", "")}

        declarations.append(
            genai.protos.FunctionDeclaration(
                name=tool.name,
                description=tool.description or "",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={k: genai.protos.Schema(**v) for k, v in gemini_props.items()},
                    required=required,
                ),
            )
        )
    return declarations


async def run():
    async with stdio_client(MCP_SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Fetch all tools from MCP server
            tools_result = await session.list_tools()
            gemini_tools = [genai.protos.Tool(function_declarations=_mcp_tools_to_gemini(tools_result.tools))]

            model = genai.GenerativeModel(
                model_name=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
                tools=gemini_tools,
                system_instruction=SYSTEM_INSTRUCTION,
                generation_config={"temperature": 0.2, "max_output_tokens": 2048},
            )

            chat = model.start_chat(enable_automatic_function_calling=False)
            session_state: dict = {}  # stores access_token, refresh_token across turns

            print("\n🤖  Gemini E-Commerce Assistant")
            print("    Type your request. Ctrl+C to exit.\n")

            while True:
                try:
                    user_input = input("You: ").strip()
                except (KeyboardInterrupt, EOFError):
                    print("\nGoodbye!")
                    break

                if not user_input:
                    continue

                # Inject stored tokens into context so Gemini can use them
                context_note = ""
                if session_state.get("access_token"):
                    context_note = f"\n[Session: access_token is available, use it for protected tools]"

                response = await asyncio.to_thread(chat.send_message, user_input + context_note)

                # Agentic loop — keep calling tools until Gemini gives a text response
                while True:
                    part = response.candidates[0].content.parts[0]

                    # Gemini wants to call a tool
                    if part.function_call.name:
                        fn_name = part.function_call.name
                        fn_args = dict(part.function_call.args)

                        # Auto-inject stored access_token if tool needs it
                        if "access_token" in fn_args and not fn_args.get("access_token"):
                            fn_args["access_token"] = session_state.get("access_token", "")

                        print(f"  🔧 Calling tool: {fn_name}({json.dumps({k: v for k, v in fn_args.items() if 'token' not in k})})")

                        # Execute tool via MCP
                        tool_result = await session.call_tool(fn_name, fn_args)
                        result_text = tool_result.content[0].text if tool_result.content else "{}"
                        result_data = json.loads(result_text)

                        # Persist tokens from login / otp-verify responses
                        if "access_token" in result_data:
                            session_state["access_token"] = result_data["access_token"]
                        if "refresh_token" in result_data:
                            session_state["refresh_token"] = result_data["refresh_token"]
                        # Handle nested data.access_token pattern
                        if isinstance(result_data.get("data"), dict):
                            if "access_token" in result_data["data"]:
                                session_state["access_token"] = result_data["data"]["access_token"]
                            if "refresh_token" in result_data["data"]:
                                session_state["refresh_token"] = result_data["data"]["refresh_token"]

                        # Send tool result back to Gemini
                        response = await asyncio.to_thread(
                            chat.send_message,
                            genai.protos.Content(parts=[
                                genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=fn_name,
                                        response={"result": result_data},
                                    )
                                )
                            ]),
                        )

                    # Gemini gave a final text response
                    else:
                        print(f"\nAssistant: {part.text}\n")
                        break


if __name__ == "__main__":
    asyncio.run(run())
