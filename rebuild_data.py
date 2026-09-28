"""Generates 12 synthetic deals (clear ROI-vs-discount pattern) and ingests them into a fresh Hindsight bank."""
import os, json, re
from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight

load_dotenv()
BANK = "deals-demo-v2"
groq = Groq(api_key=os.environ["GROQ_API_KEY"])
hindsight = Hindsight(base_url="https://api.hindsight.vectorize.io", api_key=os.environ["HINDSIGHT_API_KEY"])

PROMPT = """Generate 2 realistic, invented B2B SaaS sales deals as JSON.
Deal 1: industry INDUSTRY1. On its single pricing-objection call the rep uses approach "roi_framing" (quantifies business value/ROI). Final stage: STAGE1.
Deal 2: industry INDUSTRY2. On its single pricing-objection call the rep uses approach "discount_only" (only offers a discount). Final stage: STAGE2.
Each deal has: deal_id, company_name (unique, invented), deal_size (USD integer), stage, and exactly 3 call_notes.
Each call note has: call_number, date (2024, YYYY-MM-DD), notes (2 sentences, concrete numbers, like a real CRM note), objection_type (pricing/competitor/timing/authority/none), stakeholder (job title), approach.
Exactly one call per deal has objection_type "pricing"; all other calls have approach "none".
Return ONLY compact valid JSON, no markdown: {"deals":[{"deal_id":"","company_name":"","deal_size":0,"stage":"","call_notes":[{"call_number":1,"date":"","notes":"","objection_type":"","stakeholder":"","approach":""}]}]}"""

# 6 batches x (1 ROI deal + 1 discount deal): ROI wins 4 of 6, discount-only wins 0 of 6
BATCHES = [
    ("manufacturing", "closed_won", "fintech", "closed_lost"),
    ("healthcare", "closed_won", "retail", "closed_lost"),
    ("logistics", "closed_won", "energy", "closed_lost"),
    ("insurance", "closed_won", "telecom", "closed_lost"),
    ("real estate", "negotiation", "media", "negotiation"),
    ("automotive", "negotiation", "hospitality", "negotiation"),
]


def generate(i1, s1, i2, s2):
    prompt = (PROMPT.replace("INDUSTRY1", i1).replace("STAGE1", s1)
                    .replace("INDUSTRY2", i2).replace("STAGE2", s2))
    for _ in range(3):
        try:
            r = groq.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                reasoning_effort="low",
                max_completion_tokens=6000,
            )
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", r.choices[0].message.content.strip())
            return json.loads(text)["deals"]
        except Exception as e:
            print("  Retrying after error:", e)
    raise SystemExit("Generation failed 3 times")


deals = []
for n, batch in enumerate(BATCHES, 1):
    print(f"Generating batch {n}/{len(BATCHES)}...")
    deals += generate(*batch)

seen = set()
for i, d in enumerate(deals, 1):
    d["deal_id"] = f"D{i:03d}"
    while d["company_name"] in seen:
        d["company_name"] += " Group"
    seen.add(d["company_name"])

with open("deals_data.json", "w") as f:
    json.dump({"deals": deals}, f, indent=2)
print(f"Saved {len(deals)} deals to deals_data.json")

for d in deals:
    for c in d["call_notes"]:
        content = (
            f"Deal: {d['company_name']} (${d['deal_size']}, outcome: {d['stage']}). "
            f"Call {c['call_number']} on {c['date']} with {c['stakeholder']}: {c['notes']} "
            f"[Objection: {c['objection_type']}, rep approach: {c['approach']}]"
        )
        hindsight.retain(
            bank_id=BANK,
            content=content,
            tags=[f"company:{d['company_name']}", f"objection:{c['objection_type']}", f"approach:{c['approach']}"],
            metadata={"deal_id": d["deal_id"], "stage": d["stage"]},
        )
    print("Ingested", d["company_name"])
print("Done. Memory bank:", BANK)