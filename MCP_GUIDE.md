# AI Integration Guide — FastAPI E-Commerce

Everything you need to understand how AI works in this project — from basics to full implementation.

---

## Table of Contents

1. [Two AI Systems in This Project](#1-two-ai-systems-in-this-project)
2. [The Claude Client — claude_client.py](#2-the-claude-client--claude_clientpy)
3. [System Prompt — What It Is and Why It Matters](#3-system-prompt--what-it-is-and-why-it-matters)
4. [RAG — Answering Questions About Products](#4-rag--answering-questions-about-products)
5. [Tool Use — AI That Takes Actions](#5-tool-use--ai-that-takes-actions)
6. [Conversation History — Iterative Questions](#6-conversation-history--iterative-questions)
7. [The /ai/ask/ Endpoint — Full Picture](#7-the-aiask-endpoint--full-picture)
8. [MCP — What It Is](#8-mcp--what-it-is)
9. [MCP Server — mcp_server.py](#9-mcp-server--mcp_serverpy)
10. [MCP Client — mcp_gemini_client.py](#10-mcp-client--mcp_gemini_clientpy)
11. [Full Flow Diagrams](#11-full-flow-diagrams)
12. [RAG vs Tool Use vs MCP — When to Use What](#12-rag-vs-tool-use-vs-mcp--when-to-use-what)
13. [Glossary](#13-glossary)

---

## 1. Two AI Systems in This Project

This project has two separate AI integrations. It is important to understand the difference:

```
┌─────────────────────────────────────────────────────────────────┐
│  SYSTEM 1 — /ai/ask/ endpoint  (app/modules/ai/)               │
│                                                                 │
│  A FastAPI endpoint that uses Claude to:                        │
│  - Answer questions about products (RAG)                        │
│  - Place orders on behalf of the user (Tool Use)                │
│  - Cancel orders on behalf of the user (Tool Use)               │
│  - Remember conversation history (multi-turn chat)              │
│                                                                 │
│  Used by: frontend, mobile app, Swagger UI                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  SYSTEM 2 — MCP Server  (mcp_server.py)                        │
│                                                                 │
│  A standalone server that exposes ALL API endpoints as tools    │
│  so external AI clients (Claude Desktop, etc.) can use them.   │
│                                                                 │
│  Used by: Claude Desktop, AI agents, mcp_gemini_client.py      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. The Claude Client — claude_client.py

**File:** `app/infrastructure/ai/claude_client.py`

This is the single place in the project that talks to the Anthropic API. Everything else calls functions from here.

```python
import asyncio
import anthropic
from app.core.config import settings

_client: anthropic.Anthropic | None = None

def get_claude_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.claude_api_key)
    return _client
```

**Why singleton pattern (`_client` global)?**
The Anthropic client holds an HTTP connection pool. Creating it once and reusing it is faster and uses fewer resources than creating a new one on every request.

### Two functions

**`generate_response`** — simple text in, text out. Used for Q&A.

```python
async def generate_response(prompt, history=None, system=None) -> str:
    messages = list(history or [])
    messages.append({"role": "user", "content": prompt})
    message = await asyncio.to_thread(
        client.messages.create,
        model=settings.claude_model,
        max_tokens=1024,
        system=system or "",
        messages=messages,
    )
    return message.content[0].text.strip()
```

**`generate_with_tools`** — sends tool definitions, returns raw response so caller can handle tool calls.

```python
async def generate_with_tools(messages, tools, system=None) -> anthropic.types.Message:
    return await asyncio.to_thread(
        client.messages.create,
        model=settings.claude_model,
        max_tokens=1024,
        system=system or "",
        tools=tools,
        messages=messages,
    )
```

**Why `asyncio.to_thread`?**
The Anthropic SDK is synchronous (blocking). FastAPI is async. If you call a blocking function directly inside an async function, it freezes the entire server — no other requests can be handled while waiting for Claude. `asyncio.to_thread` runs the blocking call in a separate thread so FastAPI stays responsive.

```
Without asyncio.to_thread:
  Request 1 → calls Claude (blocks for 2 seconds) → server frozen
  Request 2 → waiting... waiting... waiting...

With asyncio.to_thread:
  Request 1 → calls Claude in thread → server free
  Request 2 → handled immediately while Request 1 waits for Claude
```

---

## 3. System Prompt — What It Is and Why It Matters

A system prompt is a special instruction you give Claude before the conversation starts. It defines Claude's role, rules, and behavior for the entire session.

```python
_SYSTEM = """
You are a helpful e-commerce assistant. You can:
1. Answer questions about products and orders
2. Place new orders on behalf of the user
3. Cancel existing orders for the user

Rules:
- Use the provided tools to take actions — never make up order IDs or product IDs
- Before placing an order, always confirm the product name and price with the user
- Only cancel orders that are in 'pending' or 'processing' status
- Be concise and friendly
""".strip()
```

**How it is sent to Claude:**

```python
client.messages.create(
    model="claude-haiku-4-5-20251001",
    system=_SYSTEM,          # ← goes here, separate from messages
    messages=[
        {"role": "user", "content": "what laptops do you have?"},
        {"role": "assistant", "content": "Here are our laptops..."},
        {"role": "user", "content": "which one is cheapest?"},
    ]
)
```

The `system` parameter is NOT part of the `messages` array. It is a separate field that Claude treats as persistent instructions throughout the entire conversation.

**What happens without a system prompt?**
Claude behaves as a general assistant and might make up product details, go off-topic, or not know it should use tools.

**What happens with a system prompt?**
Claude stays focused, uses tools correctly, and follows your business rules.

---

## 4. RAG — Answering Questions About Products

**RAG = Retrieval Augmented Generation**

Claude does not have access to your database. To answer questions about your specific products, you must fetch the data yourself and inject it into the prompt.

```
Retrieve  →  fetch products from PostgreSQL
Augment   →  inject into the prompt as context
Generate  →  Claude answers based only on that context
```

### How it works in this project (unauthenticated users)

```python
# 1. Fetch products from DB
products = await Product.filter(is_deleted=False, is_active=True)
                        .prefetch_related("category").limit(50)

# 2. Format as plain text
context = "\n".join(
    f"- {p.name} | Price: ৳{p.price} | Stock: {p.stock} | Category: {p.category.name}"
    for p in products
)

# 3. Build prompt with data injected
prompt = f"PRODUCT DATA:\n{context}\n\nUSER QUESTION:\n{question}"

# 4. Send to Claude
answer = await generate_response(prompt, system=_SYSTEM)
```

### Why limit to 50 products?

Claude has a context window (max tokens it can read). Sending 500 products would exceed it and cost more. 50 is enough for Q&A.

### The strict rules in the system prompt prevent hallucination

```
"Answer questions using ONLY the product data provided below."
"Never make up prices, stock, or product details."
```

Without these rules, Claude might invent products that don't exist in your store.

---

## 5. Tool Use — AI That Takes Actions

Tool use (also called function calling) is how you give Claude the ability to DO things, not just answer questions.

### The concept

Instead of returning text, Claude returns a structured "I want to call this function with these arguments":

```
Normal response:
  Claude → "Here are some laptops..."

Tool use response:
  Claude → {
    "type": "tool_use",
    "name": "search_products",
    "input": {"query": "laptop"}
  }
```

Your code then executes the function and sends the result back to Claude, which uses it to form a final answer.

### Tools defined in this project

```python
_TOOLS = [
    {
        "name": "search_products",
        "description": "Search products by name or category to find product IDs and prices.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Product name or category"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "place_order",
        "description": "Place a new order for the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "quantity":   {"type": "integer"},
                "shipping_address": {"type": "string"},
            },
            "required": ["product_id", "quantity", "shipping_address"],
        },
    },
    {
        "name": "cancel_order",
        "description": "Cancel an existing order. Only works for pending or processing orders.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "list_my_orders",
        "description": "Get the user's recent orders to find order IDs and statuses.",
        "input_schema": {"type": "object", "properties": {}},
    },
]
```

**The description is critical** — Claude reads it to decide when to call the tool. Write it like you are explaining to a smart person what the function does and when to use it.

### The agentic loop

This is the core pattern for tool use. Claude may call multiple tools before giving a final answer:

```python
messages = [{"role": "user", "content": question}]

while True:
    response = await generate_with_tools(messages, tools=_TOOLS, system=_SYSTEM)

    if response.stop_reason == "end_turn":
        # Claude is done — extract text answer
        answer = next(b.text for b in response.content if hasattr(b, "text"))
        break

    # Claude wants to call tools
    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            result = await _execute_tool(block.name, block.input, user)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })

    # Append Claude's tool_use block + our results back into messages
    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user",      "content": tool_results})
    # Loop again — Claude will now read the results and decide next step
```

### Real example: "order 2 yoga mats, ship to Dhaka"

```
Turn 1:
  messages → Claude
  Claude → tool_use: search_products(query="yoga mat")

  We execute: search DB → "Yoga Mat 1 | ID: abc-123 | Price: ৳700"
  Append result to messages

Turn 2:
  messages → Claude
  Claude → tool_use: place_order(product_id="abc-123", quantity=2, shipping_address="Dhaka")

  We execute: OrderService.create() → order created in DB
  Append result to messages

Turn 3:
  messages → Claude
  Claude → end_turn: "Your order for 2x Yoga Mat has been placed! Total: ৳1,400. Order ID: xyz-789"
```

### Why must we append both the tool_use block AND the result?

Claude's API requires the conversation to be consistent. When Claude emits a `tool_use` block, the next message must contain the corresponding `tool_result`. If you skip either, the API returns a 400 error.

```
messages must look like:
  user:      "order 2 yoga mats"
  assistant: [tool_use block]       ← Claude's decision
  user:      [tool_result block]    ← our execution result
  assistant: "Your order is placed" ← Claude's final answer
```

---

## 6. Conversation History — Iterative Questions

Every request to Claude is stateless — it has no memory between API calls. To support follow-up questions, the client sends the full conversation history with each request.

### How it works

**Turn 1 — first question:**
```json
POST /ai/ask/
{
  "question": "what products do you have?",
  "history": []
}
```

**Response includes history:**
```json
{
  "data": {
    "answer": "We have Electronics, Clothing, Books...",
    "history": [
      {"role": "user",      "content": "PRODUCT DATA:\n...\nUSER QUESTION:\nwhat products do you have?"},
      {"role": "assistant", "content": "We have Electronics, Clothing, Books..."}
    ]
  }
}
```

**Turn 2 — follow-up, pass history back:**
```json
POST /ai/ask/
{
  "question": "which ones are under ৳1000?",
  "history": [
    {"role": "user",      "content": "PRODUCT DATA:\n...\nUSER QUESTION:\nwhat products do you have?"},
    {"role": "assistant", "content": "We have Electronics, Clothing, Books..."}
  ]
}
```

Claude now sees the full conversation and understands "which ones" refers to the products from turn 1.

### Why client-side history (not server-side session)?

- No Redis/DB needed to store sessions
- Backend stays fully stateless — scales horizontally
- Client controls how long to keep the conversation
- Simple to implement

### First turn vs follow-up turns

```python
if not history:
    # First turn: inject product data into the prompt
    prompt = f"PRODUCT DATA:\n{context}\n\nUSER QUESTION:\n{question}"
else:
    # Follow-up: just send the question, history already has the product data
    prompt = question
```

On the first turn, product data is injected. On follow-up turns, the history already contains it — no need to re-fetch and re-inject.

---

## 7. The /ai/ask/ Endpoint — Full Picture

**File:** `app/api/v1/ai_routes.py`

```
POST /api/v1/ai/ask/
```

### Request

```json
{
  "question": "cancel my last order",
  "category": "Electronics",
  "history": []
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `question` | Yes | What the user wants to know or do |
| `category` | No | Filter products by category name (e.g. "Electronics") |
| `history` | No | Previous turns for follow-up questions |

### Two modes based on authentication

```
No Bearer token → unauthenticated mode
  - RAG only: fetches products, answers questions
  - Cannot place or cancel orders

Bearer token → authenticated mode
  - Full tool use: can search products, place orders, cancel orders
  - Also has access to user's order history
```

### Response

```json
{
  "data": {
    "answer": "Your order has been cancelled successfully.",
    "history": [
      {"role": "user",      "content": "cancel my last order"},
      {"role": "assistant", "content": "Your order has been cancelled successfully."}
    ]
  }
}
```

Always pass the returned `history` back in the next request to continue the conversation.

---

## 8. MCP — What It Is

**MCP (Model Context Protocol)** is an open standard created by Anthropic. It defines how AI models communicate with external tools and services.

```
Without MCP:
  Every AI provider has its own tool format.
  You write custom glue code for each one.

With MCP:
  One standard protocol.
  Any AI client that speaks MCP can use your tools.
  Switch AI providers without rewriting your tools.
```

MCP is to AI tools what HTTP is to web APIs — a universal language.

### Core concepts

| Concept | Meaning |
|---------|---------|
| Tool | A function the AI can call (name + description + input schema) |
| Server | Process that hosts tools and executes them |
| Client | The AI side that connects and calls tools |
| Session | A live connection between client and server |
| Transport | How they communicate — this project uses **stdio** (subprocess pipes) |

---

## 9. MCP Server — mcp_server.py

**File:** `mcp_server.py` (project root)

This server exposes all FastAPI endpoints as MCP tools. It does NOT contain business logic — it just translates tool calls into HTTP requests.

### Starting the server

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "ecommerce",
    instructions=(
        "Always call auth_login first to get an access_token. "
        "Reuse the token across all tool calls. "
        "If a tool returns 401, call auth_refresh_token then retry."
    ),
)
```

The `instructions` field is the system prompt the AI reads when it connects. It tells the AI how to behave with these tools.

### Defining a tool

```python
@mcp.tool()
async def auth_login(email: str, password: str) -> dict:
    """Login with email and password. Returns access_token and refresh_token."""
    return await _post_json("/api/v1/auth/user/login/", {
        "email": email,
        "password": password,
    })
```

FastMCP automatically:
- Reads the function signature → builds `inputSchema`
- Reads the docstring → sets as `description`
- Validates args when called
- Serializes return value to JSON

### HTTP helpers — why the server calls FastAPI over HTTP

```python
def _client(token=None) -> httpx.AsyncClient:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.AsyncClient(base_url=API_BASE, headers=headers, timeout=30)
```

The MCP server does not import your FastAPI app or touch the database directly. It calls the HTTP API. This means:
- Business logic stays in one place (FastAPI)
- MCP server is a thin adapter layer
- You can run the MCP server separately from the API

### All 22 tools

| Group | Tools | Auth |
|-------|-------|------|
| `auth_` | register, verify_otp, resend_otp, login, refresh_token, logout, password_reset, password_change | No |
| `catalog_` | list_categories, get_category, create_category, update_category, delete_category, list_products, get_product, create_product, update_product, delete_product | No (read) / Yes (write) |
| `order_` | create, list_mine, get, update_status | Yes |
| `user_` | get_me, update_me, get_by_id, delete | Yes |

### Running

```bash
python -m app.mcp.serve
```

The server waits on stdin. It does not open a port. Communication happens through subprocess pipes.

---

## 10. MCP Client — mcp_gemini_client.py

**File:** `mcp_gemini_client.py` (project root)

> Named `mcp_gemini_client.py` for historical reasons — it now uses Claude (Anthropic).

This is a terminal chat app that connects to the MCP server and uses Claude to drive it.

### How it connects

```python
MCP_SERVER = StdioServerParameters(
    command="python",
    args=["mcp_server.py"],
    env={"API_BASE_URL": "http://localhost:8000"},
)

async with stdio_client(MCP_SERVER) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools_result = await session.list_tools()
```

`stdio_client` spawns `mcp_server.py` as a child process and connects via stdin/stdout pipes.

### The agentic loop

```python
while True:
    response = chat.send_message(user_input)

    while True:
        if response has tool_call:
            result = await session.call_tool(tool_name, tool_args)
            response = chat.send_message(tool_result)
        else:
            print(response.text)
            break
```

### Token persistence

```python
session_state = {}

# After login:
session_state["access_token"] = result_data["data"]["access_token"]

# Before protected tool calls:
if "access_token" in fn_args:
    fn_args["access_token"] = session_state.get("access_token", "")
```

The client stores the JWT in memory and auto-injects it. The user never types tokens manually.

### Running

```bash
pip install mcp[cli] httpx anthropic python-dotenv
python -m app.mcp.client
```

---

## 11. Full Flow Diagrams

### Flow A — /ai/ask/ with tool use: "order 2 yoga mats"

```
POST /ai/ask/  { "question": "order 2 yoga mats, ship to Dhaka" }
Authorization: Bearer <token>
        │
        ▼
ai_routes.py
  get_optional_user() → resolves JWT → user object
        │
        ▼
ai/service.py  chat()
  authenticated → tool use mode
  messages = [{"role": "user", "content": "order 2 yoga mats, ship to Dhaka"}]
        │
        ▼
claude_client.py  generate_with_tools(messages, tools=_TOOLS)
        │
        ▼
Anthropic API
  reads tool definitions + user message
  returns: tool_use { name: "search_products", input: {query: "yoga mat"} }
        │
        ▼
ai/service.py  _execute_tool("search_products", ...)
  Product.filter(name__icontains="yoga mat") → DB query
  returns: "- Yoga Mat 1 | ID: abc-123 | Price: ৳700 | Stock: 300"
        │
        ▼
messages updated:
  assistant: [tool_use block]
  user:      [tool_result: "Yoga Mat 1 | ID: abc-123..."]
        │
        ▼
Anthropic API (second call)
  reads tool result
  returns: tool_use { name: "place_order", input: {product_id: "abc-123", quantity: 2, ...} }
        │
        ▼
ai/service.py  _execute_tool("place_order", ...)
  OrderService.create() → creates Order + OrderItems in DB
  returns: "Order placed! Order ID: xyz-789 | Total: ৳1,400"
        │
        ▼
Anthropic API (third call)
  stop_reason: "end_turn"
  text: "Your order for 2x Yoga Mat has been placed! Total ৳1,400. Order ID: xyz-789"
        │
        ▼
{ "data": { "answer": "Your order for 2x Yoga Mat...", "history": [...] } }
```

### Flow B — MCP: "show me my orders" via terminal

```
User types: "show me my orders"
        │
        ▼
mcp_gemini_client.py
  sends to Claude: user message + 22 tool definitions
        │
        ▼
Claude API
  decides: need to login first
  returns: tool_use { name: "auth_login", args: {email, password} }
        │
        ▼
mcp_gemini_client.py
  session.call_tool("auth_login", {...})
        │
        ▼
mcp_server.py  auth_login()
  POST http://localhost:8000/api/v1/auth/user/login/
        │
        ▼
FastAPI → AuthService → PostgreSQL
  returns: { access_token: "eyJ..." }
        │
        ▼
mcp_gemini_client.py
  stores token in session_state
  sends result back to Claude
        │
        ▼
Claude API
  returns: tool_use { name: "order_list_mine", args: {access_token: "eyJ..."} }
        │
        ▼
mcp_server.py  order_list_mine()
  GET http://localhost:8000/api/v1/orders/me
  Authorization: Bearer eyJ...
        │
        ▼
FastAPI → OrderService → PostgreSQL
  returns: paginated orders
        │
        ▼
Claude API
  stop_reason: end_turn
  text: "You have 2 orders: one delivered, one pending..."
        │
        ▼
Terminal: "You have 2 orders: one delivered, one pending..."
```

---

## 12. RAG vs Tool Use vs MCP — When to Use What

| | RAG | Tool Use | MCP |
|---|---|---|---|
| What it does | Answers questions using injected data | Takes real actions (create, cancel) | Exposes your whole API to external AI clients |
| Who uses it | Your frontend via REST API | Your frontend via REST API | Claude Desktop, AI agents, terminal |
| Auth | Optional | Required for actions | Managed by AI client |
| DB access | Read only | Read + Write | Via HTTP to your API |
| Complexity | Low | Medium | High |
| Example | "what laptops do you have?" | "order 2 yoga mats" | Any natural language command |

**Use RAG** when you want Claude to answer questions about your data without taking any action.

**Use Tool Use** when you want Claude to perform actions on behalf of the user inside your app.

**Use MCP** when you want to expose your entire API to external AI clients or build a standalone AI agent.

---

## 13. Glossary

| Term | Meaning |
|------|---------|
| RAG | Retrieval Augmented Generation — fetch data from DB, inject into prompt, Claude answers from it |
| Tool Use | Claude returns a structured function call instead of text — your code executes it |
| Agentic loop | `while True` loop where Claude keeps calling tools until it has enough info to answer |
| System prompt | Persistent instructions sent to Claude that define its role and rules for the session |
| `asyncio.to_thread` | Runs a blocking (sync) function in a thread so async FastAPI stays responsive |
| Singleton | Design pattern — create an object once, reuse it everywhere (used for Anthropic client) |
| MCP | Model Context Protocol — standard for AI ↔ tool communication |
| stdio transport | MCP communication via subprocess stdin/stdout pipes |
| Session state | In-memory dict storing JWT tokens across tool calls in MCP client |
| History | List of `{role, content}` dicts sent with each request so Claude remembers previous turns |
| `stop_reason: end_turn` | Claude's signal that it is done calling tools and has a final text answer |
| `tool_use` block | Claude's structured response saying "call this function with these args" |
| `tool_result` block | Your code's response after executing the tool — sent back to Claude |
| Bearer token | JWT passed as `Authorization: Bearer <token>` to authenticate API requests |
