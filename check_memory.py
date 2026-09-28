import os
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()
h = Hindsight(base_url="https://api.hindsight.vectorize.io", api_key=os.environ["HINDSIGHT_API_KEY"])

name = "Helix Robotics"  # change to the company you added
resp = h.list_memories(bank_id="deals-demo-v2", search_query=name, limit=20)
items = getattr(resp, "items", None) or getattr(resp, "memories", None) or []
print("total:", getattr(resp, "total", "?"), "| shown:", len(items))
for m in items:
    print("-", getattr(m, "text", m))