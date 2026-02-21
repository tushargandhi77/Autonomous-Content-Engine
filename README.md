# Autonomous Content Engine (ACE)

An agentic, multi-stage content generation system that plans, researches, and writes long-form structured Markdown using LangGraph + Gemini, with a full Streamlit UI, user authentication, and MongoDB-backed persistence.

## What This Project Does

ACE generates content from a topic prompt through a staged pipeline:

1. Router chooses strategy (`closed_book`, `hybrid`, `open_book`).
2. Research (optional) gathers web evidence via Tavily.
3. Orchestrator builds a structured plan (title + sections + constraints).
4. Worker writes each section in parallel.
5. Reducer merges sections into final Markdown.

The Streamlit app adds:

- User sign-up/sign-in with hashed passwords (`bcrypt`)
- Session management with token persistence
- Per-user settings (output type, tone, depth, section length, API keys)
- History of generated outputs in MongoDB
- Downloadable Markdown outputs

## Tech Stack

- Python 3.11+
- Streamlit
- LangGraph
- LangChain
- Gemini (`langchain-google-genai`)
- Tavily search (`langchain-tavily`)
- MongoDB (`pymongo`)
- Pydantic
- python-dotenv

## Repository Structure

```text
.
|-- streamlit_app.py         # Main UI app + auth + settings + history + pipeline streaming
|-- ACE_backend.py           # LangGraph pipeline (router/research/orchestrator/worker/reducer)
|-- ace_config.py            # Runtime config bridge via environment variables
|-- requirements.txt
|-- pyproject.toml
|-- Notebooks/               # Iterative notebook builds and experiments
|-- main.py                  # Minimal entrypoint placeholder
```

## Setup

### 1) Create and activate virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) Configure environment variables

Create or update `.env` in project root.

```env
# Required for Streamlit app database
MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>/<db>?retryWrites=true&w=majority

# At least one Gemini key path should be available
GOOGLE_API_KEY=<your_gemini_key>
# or
GEMINI_API_KEY=<your_gemini_key>

# Optional: enables web evidence gathering in research mode
TAVILY_API_KEY=<your_tavily_key>

# Optional runtime defaults (UI can override these per user)
ACE_OUTPUT_TYPE=Study Guide
ACE_SECTION_COUNT=5
ACE_WORDS_PER_SECTION=300
ACE_DEPTH_LEVEL=Balanced
ACE_TONE=Educational
ACE_EXTRA_INSTRUCTION=
```

## Run the App

```powershell
streamlit run streamlit_app.py
```

Then open the local URL shown in terminal (usually `http://localhost:8501`).

## How Generation Works (Runtime Flow)

1. User enters topic in `streamlit_app.py`.
2. App maps settings -> environment variables (`ACE_*`, `GOOGLE_API_KEY`, etc.).
3. App imports `ACE_backend.app` and streams graph updates.
4. UI displays live stage progress (Router -> Research -> Planner -> Writer -> Assembler).
5. Final Markdown is saved to MongoDB `blogs` collection and shown in UI.

## Output Controls in UI

Per-user settings include:

- `Output Type`: Study Guide, Blog Post, Deep Research, Quick Summary
- `Length`: section count + words per section
- `Depth`: Quick, Balanced, Deep, Exhaustive
- `Tone`: Educational, Academic, Casual, Professional, Socratic
- Custom instruction string injected into worker/orchestrator prompting
- Personal Gemini/Tavily API keys (stored in user settings)

## Data Model (MongoDB)

Collections used by `streamlit_app.py`:

- `users`: account records (`name`, `email`, `password_hash`, `created_at`)
- `sessions`: auth tokens with TTL expiry (`expires_at` indexed)
- `blogs`: generated output history per user
- `user_settings`: persisted user preferences and API keys

Indexes created at startup include unique email and session token indexes.

## Notebook Guide (Detailed)

The `Notebooks/` folder captures the evolution of the pipeline from basic orchestration to research-grounded and image-augmented workflows.

### Recommended notebook execution order

1. `practice_001.ipynb`
2. `001_ACE_basic.ipynb`
3. `002_ACE_promptiing.ipynb`
4. `tavily_test.ipynb`
5. `003_ACE_Research.ipynb`
6. `004_ACE_Image.ipynb`

### Notebook-by-notebook breakdown

#### `Notebooks/practice_001.ipynb`

- Earliest minimal LangGraph prototype.
- Demonstrates `orchestrator -> worker -> reducer` flow.
- Uses simple `Plan/Task/State` schema.
- Best for understanding core fan-out/fan-in mechanics before extra complexity.

#### `Notebooks/001_ACE_basic.ipynb`

- Basic end-to-end structured content generator.
- Introduces stronger typed schema and markdown assembly.
- Focused on foundational multi-agent decomposition without external research.

#### `Notebooks/002_ACE_promptiing.ipynb`

- Prompt-engineering-focused iteration (filename keeps original spelling).
- Adds richer plan fields (`audience`, `tone`, constraints in prompts).
- Good reference for improving orchestration prompt quality and section-level instructions.

#### `Notebooks/tavily_test.ipynb`

- Isolated Tavily connectivity and result-format test.
- Minimal sanity check to validate `TAVILY_API_KEY` and query behavior.
- Run this first when troubleshooting research failures.

#### `Notebooks/003_ACE_Research.ipynb`

- Full research-capable graph prototype.
- Adds explicit RouterDecision + Evidence schemas.
- Implements mode-based routing (`closed_book/hybrid/open_book`).
- Uses Tavily + LLM evidence normalization/dedup before planning and writing.
- Closest conceptual predecessor of `ACE_backend.py`.

#### `Notebooks/004_ACE_Image.ipynb`

- Extends research pipeline with image planning/generation scaffolding.
- Adds `ImageSpec` and markdown placeholder workflow.
- Demonstrates content + image co-generation pipeline design.
- If image generation quota is low, you may see 429/resource-exhausted errors in generated markdown outputs.

### Markdown artifacts in `Notebooks/`

You also have generated content examples as `.md` files, including:

- `Demystifying Self-Attention in Transformer Architectures.md`
- `Unpacking Self-Attention in Transformer Architectures.md`
- `unlocking_context_a_deep_dive_into_self-attention_for_developers.md`
- `the_state_of_multimodal_llms_in_2026_a_developers_outlook.md`

These are useful for reviewing final output style, structure, citation formatting, and failure modes (like image quota errors embedded in output).

## Troubleshooting

- `MONGO_URI not set`: add `MONGO_URI` in `.env` (or Streamlit secrets).
- `No Google API key found`: set `GOOGLE_API_KEY` or `GEMINI_API_KEY`, or save key in sidebar settings.
- Research stage returns empty evidence: verify `TAVILY_API_KEY` and run `Notebooks/tavily_test.ipynb`.
- Image generation quota errors: expected on limited/free tiers; rerun later or upgrade quota.

## Security Notes

- Passwords are hashed with `bcrypt`.
- Session tokens are random and stored server-side with TTL expiry.
- API keys are stored per user in MongoDB settings; protect database access and backups.

## Next Improvement Ideas

- Add automated tests for pipeline nodes and schema validation.
- Add structured citation section in final reducer output.
- Add notebook-to-production mapping docs per function.
- Add Docker compose for one-command local startup (Streamlit + Mongo).
