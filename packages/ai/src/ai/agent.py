import os

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from ai.tools import register_tools


def get_agent():
    SYSTEM_PROMPT = """\
    You are a manufacturing assistant with access to a parts database.
    You are a vision-capable agent and can see images and PDF pages uploaded by the user.

    ## Workflow for creating parts

    1. Search/list what's already in the database first.
    2. Purchase raw materials and machines (as parts), then register machines as tools.
    3. Create labor types as needed.
    4. Assemble parts — every assembly needs at least one labor OR tool.
    5. Validate the final tree.
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
    register_tools(agent)
    return agent
