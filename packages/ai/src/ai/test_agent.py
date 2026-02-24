import asyncio

from ai.agent import get_agent

test_agent = get_agent()


async def main():
    result = await test_agent.run(
        "Make a GET request to https://api.restful-api.dev/objects to fetch a list of objects. "
        "The `http_get` function is available directly in your sandbox. "
        "Note: The `json` module is NOT available, so you'll have to reason about the raw string "
        "returned by the API (or use simple string methods to 'parse' it). "
        "Describe one of the objects you find."
    )
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
