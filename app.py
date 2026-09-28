import os, json
from datetime import date
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from hindsight_client import Hindsight
from groq import Groq

load_dotenv()
BANK = "deals-demo-v2"
MODEL = "openai/gpt-oss-120b"
EXTRA_FILE = "extra_companies.json"
NEW_OPT = "➕ New company"
STAGE = {"closed_won": "🟢 Closed won", "closed_lost": "🔴 Closed lost", "negotiation": "🟡 Negotiation"}
EXAMPLE_NOTE = ("CFO said our price is 20% over budget and mentioned they are also talking to a competitor. "
                "Procurement wants a decision by end of quarter.")

st.set_page_config(page_title="Deal Intelligence Agent", page_icon="🧠", layout="wide")
st.markdown("""
<style>
.hero {padding: 1.4rem 1.6rem; border-radius: 16px; margin-bottom: 1rem;
       background: linear-gradient(135deg, #4f46e5 0%, #9333ea 60%, #db2777 100%);}
.hero h1 {color: white; margin: 0; font-size: 2rem;}
.hero p {color: rgba(255,255,255,0.88); margin: .3rem 0 0 0;}
.step {padding: .5rem .8rem; border-left: 3px solid #9333ea; background: rgba(147,51,234,.10);
       border-radius: 6px; margin-bottom: .5rem; font-size: .88rem;}
</style>
""", unsafe_allow_html=True)

hindsight = Hindsight(base_url="https://api.hindsight.vectorize.io", api_key=os.environ["HINDSIGHT_API_KEY"])
groq = Groq(api_key=os.environ["GROQ_API_KEY"])


# ---------- data helpers ----------
def load_deals():
    with open("deals_data.json") as f:
        return json.load(f)["deals"]


def load_extra():
    if os.path.exists(EXTRA_FILE):
        with open(EXTRA_FILE) as f:
            return json.load(f)
    return []


def save_extra(names):
    with open(EXTRA_FILE, "w") as f:
        json.dump(names, f)


deals = load_deals()
deal_map = {d["company_name"]: d for d in deals}
extras = load_extra()
companies = list(deal_map) + [e for e in extras if e not in deal_map]


# ---------- memory + LLM helpers ----------
def recall_context(query, max_tokens=3000, budget="mid", tags=None):
    kwargs = dict(bank_id=BANK, query=query, max_tokens=max_tokens, budget=budget)
    if tags:
        kwargs["tags"] = tags
        kwargs["tags_match"] = "all_strict"
    memories = hindsight.recall(**kwargs)
    if getattr(memories, "text", None):
        return memories.text
    if hasattr(memories, "results"):
        return "\n".join(r.text for r in memories.results)
    return str(memories)


def ask_llm(prompt):
    try:
        r = groq.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}],
                                         reasoning_effort="low", max_completion_tokens=1500)
        return r.choices[0].message.content
    except Exception as e:
        return f"⚠️ The language model hit a limit ({type(e).__name__}). Wait about a minute and try again."


def get_brief(company):
    ctx = recall_context(f"{company} deal history, objections, stakeholders", tags=[f"company:{company}"])
    if not ctx.strip():
        return "No memories found for this company yet.", ctx
    return ask_llm(f"Deal history:\n\n{ctx}\n\nWrite a short pre-call brief: what's happened, key objections, "
                   "stakeholders, and one specific piece of advice for the next call."), ctx


def get_pattern_insight():
    ctx = recall_context("pricing objections, rep approach and deal outcomes across all deals", max_tokens=3500, budget="high")
    return ask_llm(f"Notes from many past deals:\n\n{ctx}\n\nIdentify which objection-handling approaches correlated with won "
                   "vs lost/stuck deals. Cite specific deal names as evidence. Give one clear recommendation."), ctx


def simulate_new_deal(note):
    ctx = recall_context(note, max_tokens=3000, budget="high")
    return ask_llm(f"A rep just logged this NEW call note:\n\n\"{note}\"\n\nWhat similar past deals show:\n\n{ctx}\n\n"
                   "Based on what has worked before in similar situations, give specific, actionable advice for the "
                   "rep's next move. Keep it under 250 words."), ctx


def show_memory(ctx, key):
    with st.expander("🧠 What Hindsight recalled (raw memory used for this answer)"):
        st.text_area("recalled", ctx, height=260, disabled=True, key=key, label_visibility="collapsed")


# ---------- callbacks ----------
def fill_example():
    st.session_state["note_input"] = EXAMPLE_NOTE
    st.session_state["company_input"] = "Helix Robotics"


def save_to_memory():
    company = st.session_state.get("advice_company")
    note = st.session_state.get("advice_note")
    try:
        hindsight.retain(bank_id=BANK, content=f"Deal: {company}. New call note: {note}", tags=[f"company:{company}"])
        current = load_extra()
        if company not in current and company not in deal_map:
            current.append(company)
            save_extra(current)
        st.session_state["brief_company"] = company
        st.session_state["save_msg"] = ("ok", f"Saved. Hindsight now remembers {company}. Open the Pre-Call Brief tab to see it.")
    except Exception as e:
        st.session_state["save_msg"] = ("err", f"Could not save: {e}")


def log_call():
    ss = st.session_state
    choice = ss.get("log_choice")
    company = ss.get("log_new_name", "").strip() if choice == NEW_OPT else choice
    note = ss.get("log_note", "").strip()
    if not company or not note:
        ss["log_msg"] = ("err", "A company name and a call note are required.")
        return
    content = (f"Deal: {company} (${int(ss.get('log_size', 0)):,}, stage: {ss.get('log_stage')}). "
               f"Call logged {date.today()} with {ss.get('log_who', '').strip() or 'the prospect'}: {note} "
               f"[Objection: {ss.get('log_obj')}]")
    try:
        hindsight.retain(bank_id=BANK, content=content,
                         tags=[f"company:{company}", f"objection:{ss.get('log_obj')}"])
        current = load_extra()
        if company not in current and company not in deal_map:
            current.append(company)
            save_extra(current)
        ss["brief_company"] = company
        ss["log_note"] = ""
        ss["log_msg"] = ("ok", f"Logged. Hindsight has one more memory for {company}. Open Pre-Call Brief to see it.")
    except Exception as e:
        ss["log_msg"] = ("err", f"Could not save: {e}")


# ---------- sidebar ----------
with st.sidebar:
    st.header("How memory works here")
    st.markdown('<div class="step"><b>1. Retain</b><br>Every call note is stored in Hindsight, tagged by company.</div>'
                '<div class="step"><b>2. Recall</b><br>The agent pulls only the relevant memories for each question.</div>'
                '<div class="step"><b>3. Reason</b><br>The LLM turns recalled memory into advice.</div>'
                '<div class="step"><b>4. Learn</b><br>New calls saved live are remembered instantly.</div>', unsafe_allow_html=True)
    st.divider()
    st.caption(f"Memory bank: `{BANK}`")
    st.caption(f"{len(deals)} seed deals + {len(extras)} saved live")

# ---------- main ----------
st.markdown('<div class="hero"><h1>🧠 Deal Intelligence Agent</h1>'
            '<p>A sales agent that remembers every call, spots what wins, and gets smarter with every deal. '
            'Powered by Hindsight memory.</p></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Pre-Call Brief", "🔍 Pattern Insight", "🆕 New Deal Simulator", "📊 Win-Rate Data", "➕ Log Deal / Call"])

with tab1:
    company = st.selectbox("Choose a deal", companies, key="brief_company")
    deal = deal_map.get(company)
    if deal:
        m1, m2, m3 = st.columns(3)
        try:
            m1.metric("Deal size", f"${int(deal['deal_size']):,}")
        except (ValueError, TypeError):
            m1.metric("Deal size", str(deal["deal_size"]))
        m2.metric("Stage", STAGE.get(deal["stage"], deal["stage"]))
        m3.metric("Calls logged", len(deal["call_notes"]))
    else:
        st.info("This deal was saved live in this session. Its memory lives in Hindsight.")
    if st.button("Generate pre-call brief", type="primary"):
        with st.spinner("Recalling this deal from Hindsight..."):
            answer, ctx = get_brief(company)
        st.markdown(answer)
        show_memory(ctx, "ctx_brief")

with tab2:
    st.write("The agent searches memory across **all** deals and finds what actually wins.")
    if st.button("Analyze patterns across all deals", type="primary"):
        with st.spinner("Recalling every deal and looking for patterns..."):
            answer, ctx = get_pattern_insight()
        st.markdown(answer)
        show_memory(ctx, "ctx_pattern")

with tab3:
    st.write("Paste a brand-new call note. The agent recalls similar past deals, advises, and can save the call to memory.")
    st.button("✨ Use example note", on_click=fill_example)
    st.text_input("Company name", key="company_input", placeholder="e.g. Helix Robotics")
    st.text_area("New call note", key="note_input", height=130,
                 placeholder="e.g. CFO said the price is 20% over budget and mentioned a competitor...")
    if st.button("Get advice", type="primary"):
        note = st.session_state.get("note_input", "").strip()
        if not note:
            st.warning("Paste a call note first.")
        else:
            with st.spinner("Recalling similar past deals..."):
                answer, ctx = simulate_new_deal(note)
            st.session_state.update(advice=answer, advice_ctx=ctx, advice_note=note,
                                    advice_company=st.session_state.get("company_input", "").strip() or "Unnamed deal",
                                    save_msg=None)
    if "advice" in st.session_state:
        st.markdown(st.session_state["advice"])
        show_memory(st.session_state["advice_ctx"], "ctx_sim")
        st.button("💾 Save this call to memory", on_click=save_to_memory)
        msg = st.session_state.get("save_msg")
        if msg:
            (st.success if msg[0] == "ok" else st.error)(msg[1])

with tab4:
    rows = []
    for d in deals:
        approaches = {c.get("approach") for c in d["call_notes"] if c.get("objection_type") == "pricing"}
        label = "ROI framing" if "roi_framing" in approaches else "Discount only" if "discount_only" in approaches else None
        if label:
            rows.append({"Deal": d["company_name"], "Approach": label, "Outcome": d["stage"], "Won": d["stage"] == "closed_won"})
    df = pd.DataFrame(rows)
    if df.empty:
        st.info("No approach data found. Run rebuild_data.py first.")
    else:
        summary = df.groupby("Approach").agg(Deals=("Deal", "count"), Won=("Won", "sum")).reset_index()
        summary["Win rate (%)"] = (summary["Won"] / summary["Deals"] * 100).round(0)
        st.subheader("How the rep handled the pricing objection vs. the outcome")
        cols = st.columns(len(summary))
        for col, (_, row) in zip(cols, summary.iterrows()):
            col.metric(row["Approach"], f"{int(row['Win rate (%)'])}% win rate")
            col.caption(f"{int(row['Won'])} of {int(row['Deals'])} deals won")
        st.bar_chart(summary.set_index("Approach")["Win rate (%)"])
        st.dataframe(df.drop(columns="Won"), hide_index=True)
        st.caption(f"Computed directly from {len(df)} synthetic deals, no LLM involved.")

with tab5:
    st.write("Add a new company, or log another call on an existing deal. Everything is stored in Hindsight memory.")
    st.selectbox("Company", [NEW_OPT] + companies, key="log_choice")
    if st.session_state.get("log_choice", NEW_OPT) == NEW_OPT:
        st.text_input("New company name", key="log_new_name", placeholder="e.g. Orion Pharma")
    c1, c2, c3 = st.columns(3)
    c1.number_input("Deal size (USD)", min_value=0, value=50000, step=10000, key="log_size")
    c2.selectbox("Stage", ["prospecting", "negotiation", "closed_won", "closed_lost"], key="log_stage")
    c3.selectbox("Objection raised", ["none", "pricing", "competitor", "timing", "authority"], key="log_obj")
    st.text_input("Stakeholder on the call", key="log_who", placeholder="e.g. CFO")
    st.text_area("Call note", key="log_note", height=120, placeholder="What was discussed, promised, or objected to...")
    st.button("💾 Save to memory", type="primary", on_click=log_call, key="log_save")
    msg = st.session_state.get("log_msg")
    if msg:
        (st.success if msg[0] == "ok" else st.error)(msg[1])