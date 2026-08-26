"""Quick test to verify the agent works end-to-end without starting the server."""
import os
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("LLM_MODEL", "openai/gpt-oss-120b")
os.environ.setdefault("CHANNEL", "webchat")
os.environ.setdefault("STORE_NAME", "Northlane")

import asyncio
from app.agents.support_agent import run_agent_sync


async def main():
    print("Testing agent...")
    result = await run_agent_sync("where is my order #1001?", [])
    print(f"RESULT: {result}")
    print("SUCCESS!")


if __name__ == "__main__":
    asyncio.run(main())
