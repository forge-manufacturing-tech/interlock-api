import asyncio

import httpx
import pydantic_monty
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext


class CodeExecutionResult(BaseModel):
    output: str
    error: str


def http_get(url: str, headers: dict | None = None) -> str:
    """Make a GET request to a URL."""
    with httpx.Client(timeout=60.0) as client:
        return client.get(url, headers=headers).text


def http_post(url: str, json_data: dict, headers: dict | None = None) -> str:
    """Make a POST request to a URL."""
    with httpx.Client(timeout=60.0) as client:
        return client.post(url, json=json_data, headers=headers).text


def http_delete(url: str, headers: dict | None = None) -> str:
    """Make a DELETE request to a URL."""
    with httpx.Client(timeout=60.0) as client:
        return client.delete(url, headers=headers).text


async def run_code(code: str, api_key: str | None = None) -> CodeExecutionResult:
    """run code"""

    try:
        m = pydantic_monty.Monty(
            code,
            external_functions=["http_get", "http_post", "http_delete"],
        )
        printed_lines: list[str] = []

        def capture_print(_kind, text):
            # Capture strings printed inside the sandbox
            printed_lines.append(text)

        await asyncio.to_thread(
            m.run,
            external_functions={"http_get": http_get, "http_post": http_post, "http_delete": http_delete},
            print_callback=capture_print,
        )
        return CodeExecutionResult(output="\n".join(printed_lines), error="")
    except Exception as e:
        return CodeExecutionResult(output="", error=str(e))


def register_tools(agent: Agent, api_key: str | None = None):
    @agent.tool
    async def run_agent_code(ctx: RunContext[int], code: str) -> str:
        """Run Python code in a sandboxed environment using the Monty interpreter.

        The following external functions are available to be used directly (no imports needed):
        - http_get(url: str, headers: dict | None = None) -> str: Make a GET request and return the response text.
        - http_post(url: str, json_data: dict, headers: dict | None = None) -> str: Make a POST request with JSON data and return the response text.
        - http_delete(url: str, headers: dict | None = None) -> str: Make a DELETE request and return the response text.

        IMPORTANT Monty Limitations:
        - NO `import json`, `import requests`, etc. (Standard library is VERY limited).
        - NO multi-module imports (e.g., use `import os; import sys` instead of `import os, sys`).
        - NO context managers (e.g., `with` statements are NOT supported).
        - Direct assignment to `external_functions` is supported.
        - You must rely on `print()` to output results you want to see.
        """
        print(f"Running code: {code}")
        print(code)
        print("----------")
        result = await run_code(code, api_key=api_key)
        print("Result:")
        print(result)
        print("-----------")
        if result.error:
            return f"""
            Error: {result.error}
            """
        return result.output
