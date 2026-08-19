import json
from app.modules.catalog.models import Product, Category
from app.modules.orders.models import Order
from app.modules.orders.schemas import OrderCreate, OrderItemCreate
from app.modules.orders.service import OrderService
from app.infrastructure.ai.claude_client import generate_with_tools, generate_response

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

# ── Tool definitions Claude will see ──────────────────────────────────────────

_TOOLS = [
    {
        "name": "search_products",
        "description": "Search products by name or category to find product IDs and prices before placing an order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Product name or category to search"},
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
                "product_id": {"type": "string", "description": "UUID of the product"},
                "quantity": {"type": "integer", "description": "Number of items"},
                "shipping_address": {"type": "string", "description": "Delivery address"},
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
                "order_id": {"type": "string", "description": "UUID of the order to cancel"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "list_my_orders",
        "description": "Get the user's recent orders to find order IDs and statuses.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
]

# ── Tool executors ─────────────────────────────────────────────────────────────

async def _search_products(query: str) -> str:
    products = await Product.filter(
        is_deleted=False, is_active=True, name__icontains=query
    ).prefetch_related("category").limit(10)

    if not products:
        # try category match
        cat = await Category.get_or_none(is_deleted=False, name__icontains=query)
        if cat:
            products = await Product.filter(
                is_deleted=False, is_active=True, category=cat
            ).prefetch_related("category").limit(10)

    if not products:
        return "No products found matching your search."

    lines = [
        f"- {p.name} | ID: {p.id} | Price: ৳{p.price} | Stock: {p.stock} | Category: {p.category.name}"
        for p in products
    ]
    return "\n".join(lines)


async def _place_order(product_id: str, quantity: int, shipping_address: str, user) -> str:
    try:
        data = OrderCreate(
            shipping_address=shipping_address,
            items=[OrderItemCreate(product_id=product_id, quantity=quantity)],
        )
        order = await OrderService.create(user, data)
        return (
            f"Order placed successfully!\n"
            f"Order ID: {order.id}\n"
            f"Items: {', '.join(f'{i.product_name} x{i.quantity}' for i in order.items)}\n"
            f"Total: ৳{order.total_amount}\n"
            f"Status: {order.status}"
        )
    except Exception as e:
        return f"Failed to place order: {str(e)}"


async def _cancel_order(order_id: str, user) -> str:
    try:
        order = await OrderService.cancel(order_id, user)
        return f"Order {order.id} has been cancelled successfully."
    except Exception as e:
        return f"Failed to cancel order: {str(e)}"


async def _list_orders(user) -> str:
    orders, _ = await OrderService.list_mine(user, page=1, page_size=5)
    if not orders:
        return "You have no orders."
    lines = [
        f"- Order ID: {o.id} | Status: {o.status} | Total: ৳{o.total_amount} | "
        f"Items: {', '.join(f'{i.product_name} x{i.quantity}' for i in o.items)}"
        for o in orders
    ]
    return "\n".join(lines)


async def _execute_tool(name: str, inputs: dict, user) -> str:
    if name == "search_products":
        return await _search_products(inputs["query"])
    elif name == "place_order":
        return await _place_order(inputs["product_id"], inputs["quantity"], inputs["shipping_address"], user)
    elif name == "cancel_order":
        return await _cancel_order(inputs["order_id"], user)
    elif name == "list_my_orders":
        return await _list_orders(user)
    return "Unknown tool."


# ── Main entry point ───────────────────────────────────────────────────────────

async def chat(
    question: str,
    history: list[dict] | None = None,
    category: str | None = None,
    user=None,
) -> tuple[str, list[dict]]:

    # unauthenticated — simple product Q&A only, no tools
    if not user:
        qs = Product.filter(is_deleted=False, is_active=True)
        if category:
            cat = await Category.get_or_none(is_deleted=False, name__icontains=category)
            if cat:
                qs = qs.filter(category=cat)
        products = await qs.prefetch_related("category").limit(50)
        context = "\n".join(
            f"- {p.name} | Price: ৳{p.price} | Stock: {p.stock} | Category: {p.category.name}"
            for p in products
        )
        prompt = f"PRODUCT DATA:\n{context}\n\nUSER QUESTION:\n{question}" if not history else question
        answer = await generate_response(prompt, history=history, system=_SYSTEM)
        updated = list(history or [])
        updated.append({"role": "user", "content": prompt})
        updated.append({"role": "assistant", "content": answer})
        return answer, updated

    # authenticated — full tool use loop
    messages = list(history or [])
    messages.append({"role": "user", "content": question})

    while True:
        response = await generate_with_tools(
            messages=messages,
            tools=_TOOLS,
            system=_SYSTEM,
        )

        # no tool call — Claude gave a final text answer
        if response.stop_reason == "end_turn":
            answer = next(b.text for b in response.content if hasattr(b, "text"))
            messages.append({"role": "assistant", "content": answer})
            clean_history = [m for m in messages if isinstance(m.get("content"), str)]
            return answer, clean_history

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

        # append assistant tool_use block + tool results
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
