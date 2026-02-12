import traceback

from ai.agent import get_tech_transfer_agent

try:
    print("Initializing agent...")
    agent = get_tech_transfer_agent()
    print("Agent initialized. Invoking...")
    response = agent.invoke({"question": "Create the process plan for a lamp"})
    print("Response:", response)
except Exception:
    traceback.print_exc()
