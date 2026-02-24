import os

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from ai.tools import register_tools


def get_agent(api_key: str | None = None):
    auth_doc = (
        f'\n\n    **AUTHENTICATION:**\n    Your API token for this session is: `{api_key}`. You must include this in the headers of all HTTP requests you make to 127.0.0.1, for example `headers={{"Authorization": "{api_key}" if "{api_key}".startswith("Bearer") else "Bearer {api_key}"}}`.'
        if api_key
        else ""
    )

    SYSTEM_PROMPT = f"""\
    You are a manufacturing assistant with access to a parts database.
    You are a vision-capable agent and can see images and PDF pages uploaded by the user.

    ## Workflow for creating parts

    1. Search/list what's already in the database first.
    2. Purchase raw materials and machines (as parts), then register machines as tools.
    3. Create labor types as needed.
    4. Assemble parts — every assembly needs at least one labor OR tool.
    5. Validate the final tree.

    ## Tools
    Use the local API running at http://127.0.0.1:8000 to interact with the program
    and perform operations.{auth_doc}

    **IMPORTANT:** You can ALWAYS fetch the API schema by checking:
    `res = http_get("http://127.0.0.1:8000/openapi.json")`
    Do this if you are ever unsure about the specific endpoints, HTTP methods, or request body schemas required to build out a plan. You must use `run_agent_code` to execute Python that fetches, parses, or interacts with the endpoints.

    **CRITICAL:** Do NOT just show the user a plan or a python script. Your job is to DO it.
    1. First, always fetch the openapi schema `http_get("http://127.0.0.1:8000/openapi.json")` and print it using `run_agent_code` so you know the exact URLs and schemas.
    2. Then, iteratively write python code in `run_agent_code` to make HTTP requests out to the local API on the user's behalf.
    3. Do not stop until you have completely populated the required objects into the database. Work step-by-step and show the user your final results.
    """

    provider = OpenAIProvider(
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    )
    model = OpenAIChatModel("openai/gpt-oss-safeguard-20b", provider=provider)

    agent = Agent(
        model,
        system_prompt=SYSTEM_PROMPT,
        # Force tool execution even if the model outputs text alongside the tool request
        end_strategy="exhaustive",
        # Allow the model up to 3 retries if it calls a non-existent tool
        retries=3,
        # Allow the model up to 3 retries if it outputs plain text instead of a tool call
        output_retries=3,
    )
    register_tools(agent, api_key)
    return agent
