from __future__ import annotations

import operator
from pathlib import Path
from typing import TypedDict, List, Optional, Literal, Annotated

from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_tavily import TavilySearch

import os
from dotenv import load_dotenv
# override=False: .env will NOT overwrite vars already set by app.py at runtime
load_dotenv(override=False)

# ── User config bridge (set by app.py via os.environ before each run) ─────────
from ace_config import cfg   # reads os.environ at property-access time → always fresh


# ═════════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ═════════════════════════════════════════════════════════════════════════════

class Task(BaseModel):
    id: int
    title: str
    goal: str = Field(
        ...,
        description="One sentence describing what the reader should be able to do/understand after this section."
    )
    bullets: List[str] = Field(
        ...,
        min_length=3,
        max_length=6,
        description="2-3 concrete, non-overlapping subpoints to cover in this section.",
    )
    target_words: str = Field(..., description="Target word count for this section (30-50).")
    tags: List[str] = Field(default_factory=list)
    requires_research: bool = False
    requires_citations: bool = False
    requires_code: bool = False


class Plan(BaseModel):
    blog_title: str
    audience: str
    tone: str
    blog_kind: Literal["explainer", "tutorial", "news_roundup", "comparison", "system_design"] = "explainer"
    constraints: List[str] = Field(default_factory=list)
    tasks: List[Task]


class RouterDecision(BaseModel):
    needs_research: bool
    mode: Literal["closed_book", "hybrid", "open_book"]
    queries: List[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None
    snippet: Optional[str] = None
    source: Optional[str] = None


class EvidencePack(BaseModel):
    evidence: List[EvidenceItem] = Field(default_factory=list)


# ═════════════════════════════════════════════════════════════════════════════
# STATE
# ═════════════════════════════════════════════════════════════════════════════

class State(TypedDict):
    topic: str
    mode: str
    needs_research: bool
    queries: List[str]
    evidence: List[EvidenceItem]
    plan: Optional[Plan]
    sections: Annotated[List[tuple[int, str]], operator.add]
    final: str


# ═════════════════════════════════════════════════════════════════════════════
# LLM  — re-initialised each call so a fresh API key is always used
# ═════════════════════════════════════════════════════════════════════════════

def get_llm() -> ChatGoogleGenerativeAI:
    """Return an LLM instance using the current API key.
    Priority: user key in Settings UI → GOOGLE_API_KEY in .env → GEMINI_API_KEY in .env
    Key is resolved explicitly so LangChain never falls back to a stale cached env read.
    """
    key = (
        cfg.gemini_api_key                          # user's own key saved in MongoDB
        or os.environ.get("GOOGLE_API_KEY", "")     # server key set by app.py / .env
        or os.environ.get("GEMINI_API_KEY", "")     # legacy alias
    ).strip()
    if not key:
        raise ValueError(
            "No Google API key found. Add your key in Settings → API Key, "
            "or set GOOGLE_API_KEY in your .env file."
        )
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=key,
    )


# ═════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═════════════════════════════════════════════════════════════════════════════

ROUTER_SYSTEM = """
You are a routing module for a content planner.

Decide whether web research is needed BEFORE planning.

Modes:
- closed_book (needs_research=false):
  Evergreen topics where correctness does not depend on recent facts (concepts, fundamentals).
- hybrid (needs_research=true):
  Mostly evergreen but needs up-to-date examples/tools/models to be useful.
- open_book (needs_research=true):
  Mostly volatile: weekly roundups, "this week", "latest", rankings, pricing, policy/regulation.

If needs_research=true:
- Output 2-3 high-signal queries.
- Queries should be scoped and specific (avoid generic queries like just "AI" or "LLM").
- If user asked for "last week/this week/latest", reflect that constraint IN THE QUERIES.
"""


def router_node(state: State) -> dict:
    topic = state["topic"]

    # ── User depth override: Quick → always closed_book, no research ──────────
    if cfg.depth_level == "Quick":
        return {"needs_research": False, "mode": "closed_book", "queries": []}

    # ── Exhaustive → always force open_book with research ─────────────────────
    if cfg.depth_level == "Exhaustive":
        hint = cfg.router_hint()
        # Still ask LLM for good queries but force mode
        decider = get_llm().with_structured_output(RouterDecision)
        decision = decider.invoke([
            SystemMessage(content=ROUTER_SYSTEM),
            HumanMessage(content=f"Topic: {topic}"),
        ])
        return {
            "needs_research": True,
            "mode": hint["mode"],
            "queries": decision.queries or [topic],
        }

    # ── Default: let LLM decide (Balanced / Deep) ─────────────────────────────
    decider = get_llm().with_structured_output(RouterDecision)
    decision = decider.invoke([
        SystemMessage(content=ROUTER_SYSTEM),
        HumanMessage(content=f"Topic: {topic}"),
    ])
    return {
        "needs_research": decision.needs_research,
        "mode": decision.mode,
        "queries": decision.queries,
    }


def route_next(state: State) -> str:
    return "research" if state["needs_research"] else "orchestrator"


# ═════════════════════════════════════════════════════════════════════════════
# RESEARCH
# ═════════════════════════════════════════════════════════════════════════════

def _tavily_search(query: str, max_results: int = 2) -> List[dict]:
    tool = TavilySearch(max_results=max_results)
    response = tool.invoke({"query": query})
    results = response.get("results", []) if isinstance(response, dict) else []
    normalized: List[dict] = []
    for r in results or []:
        if not isinstance(r, dict):
            continue
        normalized.append({
            "title":        r.get("title") or "",
            "url":          r.get("url") or "",
            "snippet":      r.get("content") or r.get("snippet") or "",
            "published_at": r.get("published_date") or r.get("published_at"),
            "source":       r.get("source"),
        })
    return normalized


RESEARCH_SYSTEM = """You are a research synthesizer for technical writing.

Given raw web search results, produce a deduplicated list of EvidenceItem objects.

Rules:
- Only include items with a non-empty url.
- Prefer relevant + authoritative sources (company blogs, docs, reputable outlets).
- If a published date is explicitly present in the result payload, keep it as YYYY-MM-DD.
  If missing or unclear, set published_at=null. Do NOT guess.
- Keep snippets short.
- Deduplicate by URL.
"""


def research_node(state: State) -> dict:
    queries = state.get("queries", []) or []

    # Scale search results with depth
    max_results_per_query = {
        "Balanced":   2,
        "Deep":       3,
        "Exhaustive": 4,
    }.get(cfg.depth_level, 2)

    raw_results: List[dict] = []
    for q in queries:
        raw_results.extend(_tavily_search(q, max_results=max_results_per_query))

    if not raw_results:
        return {"evidence": []}

    extractor = get_llm().with_structured_output(EvidencePack)
    pack = extractor.invoke([
        SystemMessage(content=RESEARCH_SYSTEM),
        HumanMessage(content=f"Raw Results:\n{raw_results}"),
    ])

    dedup = {}
    for e in pack.evidence:
        if e.url:
            dedup[e.url] = e

    return {"evidence": list(dedup.values())}


# ═════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR  — now driven by user output_type + section count
# ═════════════════════════════════════════════════════════════════════════════

def _build_orch_system() -> str:
    """Build orchestrator system prompt dynamically from user config."""

    output_type = cfg.output_type
    n_sections  = cfg.section_count
    tone        = cfg.tone
    word_target = cfg.total_word_target

    # Per-section word budget (we leave a small overhead for title / glue)
    per_section_words = cfg.words_per_section

    # Output-type specific guidance
    output_guidance = {
        "Study Guide": (
            "Structure content as a STUDY GUIDE: definitions first, then concepts, "
            "then worked examples, then practice/review questions in a final section. "
            "Include a 'Key Takeaways' or 'Summary' section as the last task."
        ),
        "Blog Post": (
            "Structure content as a BLOG POST: compelling introduction section, "
            "2-N body sections with clear narrative flow, strong conclusion with takeaways. "
            "Use engaging subheadings."
        ),
        "Deep Research": (
            "Structure content as a RESEARCH DOCUMENT: abstract/overview first, "
            "then background, methodology/analysis, findings, and conclusions. "
            "Include a 'References & Further Reading' section as the last task."
        ),
        "Quick Summary": (
            "Keep it BRIEF. Produce only 3 sections max: Overview, Key Points, Takeaways. "
            "No tutorials, no deep dives. Bullets only, minimal prose."
        ),
    }.get(output_type, "")

    return f"""You are a senior technical writer and developer advocate.
Your job is to produce a highly actionable outline for a {output_type}.

{output_guidance}

Hard requirements:
- Create exactly {n_sections} sections (tasks).
- Each task must include:
  1) goal (1 sentence)
  2) 2-3 bullets that are concrete, specific, and non-overlapping
  3) target_words: "{per_section_words}" (string, this is the per-section word budget)
- Audience tone: {tone}

Quality bar:
- Assume the reader wants to understand deeply; use correct terminology.
- Bullets must be actionable: build/compare/measure/verify/debug/explain/summarise.
- Across all sections, include at least 2 of:
  * minimal code sketch / MWE (set requires_code=True)
  * edge cases / failure modes
  * performance / cost considerations
  * debugging / observability tips

Grounding rules:
- Mode closed_book : keep evergreen; do not depend on evidence.
- Mode hybrid      : use evidence for up-to-date examples; mark those sections requires_research=True.
- Mode open_book   : set blog_kind="news_roundup"; every section summarises events + implications.
  If evidence is empty, create a plan that transparently says "insufficient sources".

Output MUST strictly match the Plan schema.
"""


def orchestrator_node(state: State) -> dict:
    planner = get_llm().with_structured_output(Plan)
    evidence = state.get("evidence", [])
    mode     = state.get("mode", "closed_book")

    plan = planner.invoke([
        SystemMessage(content=_build_orch_system()),
        HumanMessage(content=(
            f"Topic: {state['topic']}\n"
            f"Mode: {mode}\n"
            f"Output type: {cfg.output_type}\n"
            f"Tone: {cfg.tone}\n"
            f"Total word target: {cfg.total_word_target} ({cfg.section_count} sections x {cfg.words_per_section} words each)\n\n"
            f"Evidence (ONLY use for fresh claims; may be empty):\n"
            f"{[e.model_dump() for e in evidence][:16]}"
        )),
    ])

    return {"plan": plan}


# ═════════════════════════════════════════════════════════════════════════════
# WORKER  — tone + output type + extra instructions flow in here
# ═════════════════════════════════════════════════════════════════════════════

def _build_worker_system() -> str:
    """Build worker system prompt from user config."""

    tone_guidance = {
        "Educational":  "Use clear, accessible language. Define jargon when introduced. Include analogies.",
        "Academic":     "Use formal language, precise terminology, and structured argumentation.",
        "Casual":       "Write conversationally. Use contractions. Keep sentences short and punchy.",
        "Professional": "Be precise and structured. Avoid filler. No marketing language.",
        "Socratic":     "Frame ideas as questions that lead the reader to the answer. Pose rhetorical questions.",
    }.get(cfg.tone, "Use clear, accessible language.")

    output_type_guidance = {
        "Study Guide":   "Include definitions, examples, and a mini-quiz or practice prompt at the end of each section.",
        "Blog Post":     "Write with narrative flow. Hook the reader in the first sentence of each section.",
        "Deep Research": "Cite evidence for every major claim. Be exhaustive. Prefer depth over breadth.",
        "Quick Summary": "Be as concise as possible. Bullet points preferred over prose. No padding.",
    }.get(cfg.output_type, "")

    extra = f"\nSPECIAL INSTRUCTIONS: {cfg.extra_instruction}" if cfg.extra_instruction else ""

    return f"""You are a senior technical writer and developer advocate.
Write ONE section of a {cfg.output_type} in Markdown.

TONE: {tone_guidance}
OUTPUT TYPE RULES: {output_type_guidance}{extra}

Hard constraints:
- Follow the provided Goal and cover ALL Bullets in order (do not skip or merge bullets).
- Stay close to Target words (±15%).
- Output ONLY the section content in Markdown (no blog title H1, no extra commentary).
- Start with a '## <Section Title>' heading.

Scope guard:
- If blog_kind == "news_roundup": focus on summarising events and implications only.
  Do NOT turn this into a how-to tutorial unless bullets explicitly ask for it.

Grounding policy:
- If mode == open_book:
  - Do NOT introduce any specific event/company/model/claim unless supported by provided Evidence.
  - Cite as Markdown links: ([Source](URL)). Only use URLs from Evidence.
  - If not supported: write "Not found in provided sources."
- If requires_citations == true: cite Evidence URLs for outside-world claims.

Code:
- If requires_code == true, include at least one minimal, correct, well-commented code snippet.

Style:
- Short paragraphs, bullets where helpful, code fences for code.
- Avoid fluff and marketing language. Be precise and implementation-oriented.
"""


def fanout(state: State):
    return [
        Send(
            "worker",
            {
                "task":     task.model_dump(),
                "topic":    state["topic"],
                "mode":     state["mode"],
                "plan":     state["plan"].model_dump(),
                "evidence": [e.model_dump() for e in state.get("evidence", [])],
            },
        )
        for task in state["plan"].tasks
    ]


def worker_node(payload: dict) -> dict:
    task     = Task(**payload["task"])
    plan     = Plan(**payload["plan"])
    evidence = [EvidenceItem(**e) for e in payload.get("evidence", [])]
    topic    = payload["topic"]
    mode     = payload.get("mode", "closed_book")

    bullets_text = "\n -" + "\n -".join(task.bullets)

    evidence_text = ""
    if evidence:
        evidence_text = "\n".join(
            f"- {e.title} | {e.url} | {e.published_at or 'date:unknown'}"
            for e in evidence[:20]
        )

    section_md = get_llm().invoke([
        SystemMessage(content=_build_worker_system()),
        HumanMessage(content=(
            f"Blog title: {plan.blog_title}\n"
            f"Audience: {plan.audience}\n"
            f"Tone: {plan.tone}\n"
            f"Blog kind: {plan.blog_kind}\n"
            f"Constraints: {plan.constraints}\n"
            f"Topic: {topic}\n"
            f"Mode: {mode}\n\n"
            f"Section title: {task.title}\n"
            f"Goal: {task.goal}\n"
            f"Target words: {task.target_words}\n"
            f"Tags: {task.tags}\n"
            f"requires_research: {task.requires_research}\n"
            f"requires_citations: {task.requires_citations}\n"
            f"requires_code: {task.requires_code}\n"
            f"Bullets:{bullets_text}\n\n"
            f"Evidence (ONLY use these URLs when citing):\n{evidence_text}\n"
        )),
    ]).content.strip()

    return {"sections": [(task.id, section_md)]}


# ═════════════════════════════════════════════════════════════════════════════
# REDUCER
# ═════════════════════════════════════════════════════════════════════════════

def reducer_node(state: State) -> dict:
    plan = state["plan"]
    ordered = [md for _, md in sorted(state["sections"], key=lambda x: x[0])]
    body = "\n\n".join(ordered).strip()
    final_md = f"# {plan.blog_title}\n\n{body}\n"

    filename = "".join(
        c if c.isalnum() or c in (" ", "_", "-") else "" for c in plan.blog_title
    )
    filename = filename.strip().lower().replace(" ", "_") + ".md"
    Path(filename).write_text(final_md, encoding="utf-8")

    return {"final": final_md}


# ═════════════════════════════════════════════════════════════════════════════
# GRAPH
# ═════════════════════════════════════════════════════════════════════════════

G = StateGraph(State)
G.add_node("router",       router_node)
G.add_node("research",     research_node)
G.add_node("orchestrator", orchestrator_node)
G.add_node("worker",       worker_node)
G.add_node("reducer",      reducer_node)

G.add_edge(START, "router")
G.add_conditional_edges("router", route_next, {"research": "research", "orchestrator": "orchestrator"})
G.add_edge("research", "orchestrator")
G.add_conditional_edges("orchestrator", fanout, ["worker"])
G.add_edge("worker", "reducer")
G.add_edge("reducer", END)

app = G.compile()