from typing import AsyncIterator
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from openai import RateLimitError
from app.config import settings
from app.tools.store_tools import (
    get_order_status,
    check_return_eligibility,
    get_product_info,
    check_fulfillment_status,
    escalate_to_human,
)

tools = [
    get_order_status,
    check_return_eligibility,
    get_product_info,
    check_fulfillment_status,
    escalate_to_human,
]


def _get_llm():
    if settings.llm_provider == "groq":
        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            temperature=0.1,
        )
    if settings.llm_provider == "openrouter":
        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            temperature=0.1,
            default_headers={"HTTP-Referer": "https://shopify-support-agent.onrender.com", "X-Title": "Shopify Support Agent"},
        )
    if settings.llm_provider == "openai":
        return ChatOpenAI(
            model=settings.llm_model or "gpt-4o",
            api_key=settings.openai_api_key,
            temperature=0.1,
        )
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


SYSTEM_PROMPT = f"""You are the support agent for {settings.store_name}, an e-commerce store.

YOUR JOB:
Answer customer questions by using the tools available to you. NEVER make up information — always check Shopify data first.

CAPABILITIES (use the appropriate tool for each):
1. Order status inquiries → use get_order_status
2. Return/refund requests → use check_return_eligibility
3. Product questions → use get_product_info
4. Delivery delays / fulfillment tracking → use check_fulfillment_status
5. Anything else or uncertain → use escalate_to_human

RULES:
- Be friendly, helpful, and concise
- Never reveal you are an AI unless directly asked
- If a customer asks something outside these 5 categories, escalate
- Always check data before responding — never guess
- After you get the result from any tool, respond immediately with your final answer. Do NOT call another tool.
- Never call more than one tool in a row. Call a tool, get the result, then respond to the customer.
- If a customer asks "where is my order", call get_order_status once and then respond.

STORE POLICY:
- Return window: {settings.return_window_days} days from delivery
- Refunds processed within 5-10 business days
- Free shipping on orders over $75"""

agent_executor = create_react_agent(
    model=_get_llm(),
    tools=tools,
    state_modifier=SYSTEM_PROMPT,
    checkpointer=MemorySaver(),
)


async def run_agent(customer_message: str, conversation_history: list) -> AsyncIterator[dict]:
    messages = conversation_history + [{"role": "user", "content": customer_message}]
    config = {"configurable": {"thread_id": "single"}, "recursion_limit": 50}
    try:
        async for event in agent_executor.astream_events(
            {"messages": messages}, config, version="v2"
        ):
            yield event
    except Exception:
        yield {"event": "on_chat_model_stream", "data": {"chunk": type("Chunk", (), {"content": "I encountered an issue. Please try again."})()}}


async def run_agent_sync(customer_message: str, conversation_history: list) -> str:
    response_text = ""
    async for event in run_agent(customer_message, conversation_history):
        kind = event.get("event", "")
        if kind == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk", None)
            if chunk and hasattr(chunk, "content") and chunk.content:
                response_text += str(chunk.content)
    return response_text or "I'm processing your request. One moment please."
