# Deal Intelligence Agent

An AI-powered deal intelligence prototype that uses persistent memory to turn previous sales conversations into useful context for future customer calls.

The system stores deal interactions in **Hindsight**, retrieves relevant historical context, and uses **Groq** to generate pre-call briefings and cross-deal pattern insights.

> **Note:** This project uses synthetic B2B sales data for experimentation. The results are intended to demonstrate the memory and retrieval workflow, not to establish real-world sales conclusions.

---

## Overview

Sales conversations often contain valuable information about:

* Customer objections
* Pricing discussions
* Competitors
* Stakeholder concerns
* Deal stages
* Unresolved issues
* Previous approaches and outcomes

The problem is that this information is spread across multiple conversations.

A salesperson preparing for a new call may need to reconstruct the history manually.

The **Deal Intelligence Agent** addresses this by maintaining persistent deal memory and retrieving the right context when it is needed.

The core workflow is:

```text
Previous Sales Conversations
            |
            v
      Hindsight Memory
            |
            v
     Relevant Retrieval
            |
       +----+----+
       |         |
       v         v
Pre-Call Brief  Pattern Insight
       |         |
       +----+----+
            |
            v
        Groq LLM
            |
            v
     Useful Deal Context
            |
            v
      New Call Logged
            |
            v
    Stored in Hindsight
```

---

## Why Hindsight?

The main engineering challenge was not simply generating text with an LLM.

The important question was:

> **Which previous information should the agent retrieve for the current situation?**

For example, two different companies may have discussed pricing.

A broad search could retrieve both conversations.

But when preparing a briefing for one company, information belonging to another company should not appear in the briefing.

This is why the project uses **company-scoped retrieval** for pre-call briefings.

For broader analysis, the system can retrieve across the deal history to identify recurring patterns.

This makes retrieval scope an important part of the agent's intelligence.

Hindsight provides the persistent memory layer for this workflow.

* **Retain:** store deal conversations and context.
* **Recall:** retrieve relevant historical information.
* **Groq:** reason over the retrieved context and generate the final output.

Learn more:

* [Hindsight GitHub](https://github.com/vectorize-io/hindsight)
* [Hindsight Documentation](https://hindsight.vectorize.io/)
* [What is Agent Memory?](https://vectorize.io/what-is-agent-memory)

---

## Key Features

### 1. Persistent Deal Memory

Sales calls and deal information are retained in Hindsight instead of being treated as temporary conversation data.

Stored information can include:

* Company
* Deal size
* Deal stage
* Stakeholder
* Call notes
* Objection
* Approach
* Deal metadata

---

### 2. Company-Scoped Pre-Call Briefing

The agent can retrieve historical information for a specific company and turn it into a concise pre-call briefing.

The goal is to answer questions such as:

* What happened in previous conversations?
* What objections were raised?
* Which stakeholders were involved?
* What concerns remain unresolved?
* What should the salesperson know before the next call?

The retrieval scope is kept specific to the selected company.

---

### 3. Cross-Deal Pattern Insight

The system also provides a broader retrieval path for looking across multiple deals.

This can be used to explore recurring:

* Objections
* Responses
* Approaches
* Outcomes
* Deal patterns

This is intentionally different from company-specific briefing retrieval.

```text
Company Briefing
      |
      v
Strict company-scoped recall

Pattern Analysis
      |
      v
Broader cross-deal recall
```

---

### 4. Deal / Call Logging

New deal information and call notes can be added through the application.

The information is then retained in Hindsight so that later interactions can use the accumulated history.

This creates a memory loop:

```text
New Call
   |
   v
Retain
   |
   v
Recall Later
   |
   v
Generate Briefing
   |
   v
New Call
   |
   +------> Retain Again
```

---

### 5. Synthetic Deal Dataset

The project includes a prepared synthetic B2B sales dataset for testing the memory and retrieval workflow.

The dataset is deliberately structured to contain different deal approaches and outcomes so that the application can surface patterns.

These experiments are **not real-world sales evidence**.

They are used to test the application's retrieval and analysis behavior.

---

## Technology Stack

| Technology | Purpose                         |
| ---------- | ------------------------------- |
| Python     | Application logic               |
| Streamlit  | Web interface                   |
| Hindsight  | Persistent agent memory         |
| Groq       | LLM inference                   |
| JSON       | Synthetic deal dataset          |
| dotenv     | Environment variable management |

---

## Architecture

The application separates memory, retrieval, and reasoning responsibilities.

```text
                    +------------------+
                    |  Streamlit UI   |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | Application Logic|
                    +--------+---------+
                             |
                  +----------+----------+
                  |                     |
                  v                     v
          +---------------+      +-------------+
          |   Hindsight   |      |    Groq     |
          | Persistent    |      |     LLM     |
          | Memory        |      | Reasoning   |
          +-------+-------+      +------+------+
                  |                     |
                  +----------+----------+
                             |
                             v
                  Pre-Call Brief /
                  Pattern Insight
```

### Memory flow

```text
Call Notes
    |
    v
Hindsight Retain
    |
    v
Persistent Deal Memory
    |
    +----------------------+
    |                      |
    v                      v
Company Recall       Cross-Deal Recall
    |                      |
    v                      v
Pre-Call Brief       Pattern Insight
```

---

## Hindsight Integration

The project uses Hindsight as the persistent memory layer.

A simplified version of the retention flow is:

```python
hindsight.retain(
    bank_id=BANK,
    content=content,
    tags=[
        f"company:{company}",
        f"objection:{objection}"
    ]
)
```

The company tag provides the context needed for company-specific retrieval.

For recall, the application can apply a strict tag scope:

```python
if tags:
    kwargs["tags"] = tags
    kwargs["tags_match"] = "all_strict"

memories = hindsight.recall(**kwargs)
```

This distinction is important:

```text
Store everything
      |
      v
Retrieve only what belongs to the current context
      |
      v
Give retrieved context to the LLM
      |
      v
Generate useful output
```

---

## Project Structure

```text
deal-intelligence-agent/
│
├── app.py
│   └── Streamlit application interface
│
├── check_memory.py
│   └── Utility for checking memory state
│
├── rebuild_data.py
│   └── Generates/rebuilds the prepared deal dataset
│      and populates the Hindsight memory bank
│
├── deals_data.json
│   └── Synthetic deal data
│
├── requirements.txt
│   └── Python dependencies
│
├── .env.example
│   └── Example environment-variable configuration
│
└── .gitignore
    └── Files excluded from version control
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/ghaneeshkumar83-lab/deal-intelligence-agent.git
```

```bash
cd deal-intelligence-agent
```

---

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

Linux / macOS:

```bash
python3 -m venv venv
```

```bash
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure environment variables

Create a `.env` file based on `.env.example`.

Add the required API credentials used by the application.

Example structure:

```env
GROQ_API_KEY=your_groq_api_key
HINDSIGHT_API_KEY=your_hindsight_api_key
```

Do **not** commit your real API keys to GitHub.

The repository includes `.env.example` so the expected configuration can be understood without exposing secrets.

---

### 5. Prepare the dataset and memory

The project includes `rebuild_data.py` for preparing the synthetic deal dataset and populating the Hindsight memory bank.

Run:

```bash
python rebuild_data.py
```

The prepared memory bank used by the project is:

```text
deals-demo-v2
```

Because Hindsight is persistent, memory state can outlive a particular code run. When testing from a clean state, use the project's rebuild process and verify the resulting memory state.

---

### 6. Run the application

Start Streamlit with:

```bash
streamlit run app.py
```

The application will open in your browser.

---

## Application Workflow

The application is organized around several workflows.

### Pre-Call Brief

Select a company and retrieve its relevant historical context.

```text
Company
   |
   v
Company-scoped Hindsight Recall
   |
   v
Historical Deal Context
   |
   v
Groq
   |
   v
Pre-Call Brief
```

---

### Pattern Insight

Use broader deal history to identify recurring patterns across multiple deals.

```text
Multiple Deals
      |
      v
Broader Hindsight Recall
      |
      v
Historical Patterns
      |
      v
Groq
      |
      v
Pattern Insight
```

---

### Log Deal / Call

Record a new interaction.

```text
Company
Deal Size
Stage
Stakeholder
Objection
Call Notes
      |
      v
Hindsight Retain
      |
      v
Available for Future Retrieval
```

---

## Experiment

The project includes synthetic deal data designed to test how historical deal information can be recalled and analyzed.

One experiment compares two structured approaches:

* Discount-only
* ROI framing

The dataset used for the experiment contains:

* **36 synthetic seed deals**
* **18 discount-only**
* **18 ROI-framing**

The captured experiment showed:

| Approach      | Won | Total | Observed Win Rate |
| ------------- | --: | ----: | ----------------: |
| Discount-only |   0 |    18 |                0% |
| ROI framing   |  12 |    18 |               67% |

### Important limitation

These numbers come from a deliberately constructed synthetic dataset.

They should **not** be interpreted as evidence that ROI framing causes a higher real-world sales win rate.

The purpose of the experiment is to demonstrate that the agent can retrieve and surface patterns from its stored deal history.

---

## What I Learned

### 1. Memory is an application-design problem

Adding persistent memory is not enough.

The application still has to decide:

* What should be retained?
* What context should be attached?
* What should be recalled?
* How broad should retrieval be?

---

### 2. Retrieval is part of the intelligence

The LLM can only reason over the information it receives.

If the retrieval layer returns irrelevant or incorrect historical context, the generated answer can still look convincing while being based on the wrong information.

---

### 3. A briefing is different from a summary

A summary describes what happened.

A briefing selects the parts of previous conversations that are useful for the next conversation.

That difference influenced the design of the application.

---

### 4. Stateful systems need reproducible data

Persistent memory means that state can remain even after code changes.

The `rebuild_data.py` workflow exists to make the prepared dataset and memory state easier to reproduce.

---

### 5. Small datasets require careful interpretation

Synthetic data is useful for testing application behavior.

It is not enough to establish general conclusions about real-world sales performance.

---

## Limitations

This project is a prototype and has several limitations:

* The dataset is synthetic.
* The experiments are relatively small.
* The results should not be treated as real sales research.
* Retrieval quality needs more systematic evaluation.
* Persistent memory introduces state-management considerations.
* Generated insights depend on the quality and scope of retrieved context.
* Real CRM integration has not been implemented in this prototype.

---

## Future Improvements

Possible next steps include:

* Automated retrieval-quality evaluation
* Negative tests for cross-company memory leakage
* More realistic CRM data
* Integration with real CRM systems
* Better deal-history visualization
* Retrieval evaluation metrics
* More robust memory management
* Additional deal-stage analysis
* Human feedback on generated briefings
* Evaluation of whether recalled context is actually useful to the salesperson

---

## Article

Read the complete engineering write-up:

**[Hindsight Memory Only Helped Once I Fixed Retrieval Scope](https://dev.to/g_haneeshkumar_874892a2b/hindsight-memory-only-helped-once-i-fixed-retrieval-scope-1c33)**

The article explains the retrieval-scope problem, Hindsight integration, experiments, and lessons learned while building the project.

---

## Hindsight Resources

* **Hindsight GitHub:** https://github.com/vectorize-io/hindsight
* **Hindsight Documentation:** https://hindsight.vectorize.io/
* **Agent Memory:** https://vectorize.io/what-is-agent-memory

---

## Repository

**GitHub:**
https://github.com/ghaneeshkumar83-lab/deal-intelligence-agent

---

## Disclaimer

This project is an engineering prototype built using synthetic B2B sales data.

The deal outcomes and win-rate experiment are intended to demonstrate persistent memory, retrieval, and pattern-analysis workflows. They should not be interpreted as statistically valid evidence about real-world sales strategies or customer behavior.

---

## Author

**G Haneesh Kumar**

Built with:

* Python
* Streamlit
* Hindsight
* Groq
* Persistent agent memory
