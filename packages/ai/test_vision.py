import os
import sys
import traceback

# Add src to path so we can import ai
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from ai.agent import get_tech_transfer_agent

# Small 1x1 black PNG image
DUMMY_IMAGE = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

try:
    print("Initializing agent...")
    agent = get_tech_transfer_agent()
    print("Agent initialized. Invoking with vision input...")

    question = [{"type": "text", "text": "What do you see in this image? Please be brief."}, {"type": "image_url", "image_url": {"url": DUMMY_IMAGE}}]

    response = agent.invoke({"question": question, "history": []})
    print("Response type:", type(response))

    if isinstance(response, dict):
        print("Response keys:", response.keys())
        print("Response text:", response.get("response", ""))
        if response.get("response"):
            print("SUCCESS: Agent returned a response for multi-modal input.")
        else:
            print("FAILURE: Agent returned empty response.")
    else:
        print("Response:", response)
        print("SUCCESS: Agent returned a response.")

except Exception:
    traceback.print_exc()
    sys.exit(1)
