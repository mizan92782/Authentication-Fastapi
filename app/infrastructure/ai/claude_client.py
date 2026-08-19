import asyncio
import anthropic
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: anthropic.Anthropic | None = None


def get_claude_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.claude_api_key)
    return _client


async def generate_response(prompt: str, history: list[dict] | None = None, system: str | None = None) -> str:
    try:
        client = get_claude_client()
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
    except Exception as e:
        logger.error("claude_api_error", error=str(e))
        raise


async def generate_with_tools(
    messages: list[dict],
    tools: list[dict],
    system: str | None = None,
) -> anthropic.types.Message:
    """Send messages with tool definitions. Returns raw Message so caller can handle tool_use blocks."""
    try:
        client = get_claude_client()
        return await asyncio.to_thread(
            client.messages.create,
            model=settings.claude_model,
            max_tokens=1024,
            system=system or "",
            tools=tools,
            messages=messages,
        )
    except Exception as e:
        logger.error("claude_tool_error", error=str(e))
        raise
