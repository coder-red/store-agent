from typing import AsyncIterator, Literal
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, MessagesState, END
from app.config import settings
from app.tools.store_tools import (
    get_order_status,
    check_return_eligibility,
    get_product_info,
    check_fulfillment_status,
    query_store_policies,
    escalate_to_human,
)


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
            default_headers={"HTTP-Referer": "https://store-agent.onrender.com", "X-Title": "Store Agent"},
        )
    if settings.llm_provider == "openai":
        return ChatOpenAI(
            model=settings.llm_model or "gpt-4o",
            api_key=settings.openai_api_key,
            temperature=0.1,
        )
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


llm = _get_llm()


# --- Specialized agents with focused system prompts ---

ORDER_AGENT_PROMPT = f"""You are an order status specialist for {settings.store_name}. Always call get_order_status.

EXAMPLE FLOW:
User: "Where is my order #1001?"
You: [call get_order_status(order_number="1001")]
Tool: "Order #1001 | Status: paid | Fulfillment: fulfilled | Total: USD 267.00"
You: "Your order #1001 has been fulfilled and was shipped via UPS. Track it here: https://www.ups.com/track/..."

RULES:
- Call get_order_status FIRST before answering any order question
- After getting the tool result, summarize it for the customer
- Be concise"""

RETURNS_AGENT_PROMPT = f"""You are a returns specialist for {settings.store_name}. Always call check_return_eligibility.

EXAMPLE FLOW:
User: "Can I return order #1005?"
You: [call check_return_eligibility(order_number="1005")]
Tool: "Order #1005 is eligible. 15 days remaining."
You: "Yes, order #1005 is within the {settings.return_window_days}-day return window. You have 15 days left."

RULES:
- Call check_return_eligibility FIRST before answering
- After getting the tool result, summarize it for the customer
- Be empathetic"""

PRODUCT_AGENT_PROMPT = f"""You are a product specialist for {settings.store_name}. Always call get_product_info.

EXAMPLE FLOW:
User: "Do you have any backpacks?"
You: [call get_product_info(query="backpack")]
Tool: "Classic Leather Backpack (by Artisan Leather Co) - Brown/Small: $89 ..."
You: "Yes! We have the Classic Leather Backpack from Artisan Leather Co starting at $89."

RULES:
- Call get_product_info FIRST before answering any product question
- After getting the tool result, summarize it for the customer
- Be helpful and enthusiastic"""

GENERAL_AGENT_PROMPT = f"""You are the general support agent for {settings.store_name}. Always call a tool before answering.

TOOLS:
- get_order_status(order_number, customer_email) — look up orders
- check_return_eligibility(order_number) — check returns
- get_product_info(query) — product questions
- check_fulfillment_status(order_number) — shipping details
- query_store_policies(query) — store policies, FAQs, shipping, returns, etc.
- escalate_to_human(customer_message, conversation_history, reason) — when stuck

EXAMPLE FLOW:
User: "What's your return policy?"
You: [call query_store_policies(query="return policy")]
Tool: "Return Policy: Items can be returned within {settings.return_window_days} days..."
You: "We have a {settings.return_window_days}-day return window and refunds are processed in 5-10 business days."

RULES:
- Call the right tool before answering
- For policy questions, use query_store_policies
- Summarize tool results concisely
- Escalate if stuck"""


order_agent = create_react_agent(
    model=llm,
    tools=[get_order_status, check_fulfillment_status],
    state_modifier=ORDER_AGENT_PROMPT,
    checkpointer=MemorySaver(),
)

returns_agent = create_react_agent(
    model=llm,
    tools=[check_return_eligibility, escalate_to_human],
    state_modifier=RETURNS_AGENT_PROMPT,
    checkpointer=MemorySaver(),
)

product_agent = create_react_agent(
    model=llm,
    tools=[get_product_info],
    state_modifier=PRODUCT_AGENT_PROMPT,
    checkpointer=MemorySaver(),
)

general_agent = create_react_agent(
    model=llm,
    tools=[get_order_status, check_return_eligibility, get_product_info, check_fulfillment_status, query_store_policies, escalate_to_human],
    state_modifier=GENERAL_AGENT_PROMPT,
    checkpointer=MemorySaver(),
)


SUPERVISOR_PROMPT = f"""You are a supervisor routing customer support requests for {settings.store_name}.
Analyze the conversation and decide which specialist should handle it.

Categories:
- "orders" — order status, tracking, fulfillment, shipping delays
- "returns" — returns, refunds, exchanges, return eligibility
- "products" — product info, recommendations, pricing, availability
- "general" — anything else, store policy, mixed concerns

Respond with ONLY the category name, nothing else."""


def _route_message(messages: list) -> Literal["orders", "returns", "products", "general"]:
    last = messages[-1]["content"] if messages else ""
    history = "\n".join(m.get("content", "") for m in messages[-4:])
    prompt = SUPERVISOR_PROMPT + f"\n\nConversation:\n{history}\n\nCategory:"
    result = llm.invoke([{"role": "user", "content": prompt}])
    category = result.content.strip().lower().strip('"').strip("'")
    if category in ("orders", "returns", "products"):
        return category
    return "general"


async def run_agent(customer_message: str, conversation_history: list) -> AsyncIterator[dict]:
    messages = conversation_history + [{"role": "user", "content": customer_message}]
    category = _route_message(messages)
    agent = {"orders": order_agent, "returns": returns_agent, "products": product_agent, "general": general_agent}[category]
    config = {"configurable": {"thread_id": "single"}, "recursion_limit": 50}

    # Yield a routing event so the UI can show which agent was picked
    yield {
        "event": "on_supervisor_route",
        "data": {"category": category, "agent": f"{category}_agent"},
    }

    try:
        async for event in agent.astream_events({"messages": messages}, config, version="v2"):
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
