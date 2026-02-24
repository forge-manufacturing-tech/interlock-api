import asyncio

from ai.agent import get_agent

test_agent = get_agent(api_key="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5MjFkOWZlMC1jODQxLTQyZjQtYjc5Yy1mOTUzMzU2ZmE2NmIiLCJlbWFpbCI6Im5hdGhhbkBpbnRlcmxvY2stc3lzdGVtcy5pbyIsImV4cCI6MTc3MjA0OTI3M30._mPQVC8NwjENx-hobZ7Kt6eJGcsk6sr0qW9ksHSwWrk")


async def main():
    result = await test_agent.run(
        "Create a new part called 'Test Part' with unit of measure 'each' and description 'Test Part'",
    )
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
