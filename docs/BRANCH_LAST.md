# Branch last — technical documentation

This page documents the application as implemented on the Git branch named **last**. It covers the React studio, Python API, multi-agent graph, setup, runtime configuration, and user-visible behavior.

## 1. What this branch contains

The primary application runs as two local processes:

1. **Web process** — Next.js App Router, React, TypeScript, and Three.js. It renders the studio, streams progress, and displays and exports the final report.
2. **Planner process** — Python FastAPI and LangGraph. It validates the project brief, runs the agents, and returns progress events and the final plan.

The web server proxies browser requests to the planner API. The browser normally communicates with same-origin Next.js routes and does not need direct access to port 8000.

The root-level **app.py** is a retained Streamlit interface from the earlier implementation. It is not the recommended entry point for this branch; use the React studio commands below.

## 2. Features

- React studio with project-brief examples, input validation, pipeline progress, error messages, retry, and reset.
- Six pipeline roles: Supervisor, Researcher, Knowledge Base, Architect, Reviewer, and Planner.
- Three.js medallion displaying the icon-only Planorai mark, rotating one full turn every nine seconds. The pause control and the operating system's reduced-motion preference pause the scene.
- Responsive final report with overview, architecture, dataset, model, roadmap, risks, skills, recommended tools, sources, timeline, and success metrics.
- PDF export through the Python API, browser print/save as a fallback, and JSON download of the final plan.
- Hugging Face dataset discovery, optional Tavily web search, a local ChromaDB knowledge base, and optional LangSmith tracing.

## 3. Architecture and request flow

~~~text
Browser
  └─ Next.js / React (port 3000)
       ├─ /api/health      ──proxy──> FastAPI GET  /health
       ├─ /api/build       ──proxy──> FastAPI POST /build (NDJSON stream)
       └─ /api/export-pdf  ──proxy──> FastAPI POST /export/pdf
                                      └─ LangGraph pipeline
                                           ├─ Supervisor
                                           ├─ Research
                                           ├─ RAG
                                           ├─ Architect
                                           ├─ Critic ── revise ──> Research or Architect
                                           └─ Report
~~~

### Pipeline stages

1. **Supervisor** validates the brief and converts it into structured project requirements.
2. **Researcher** searches for relevant sources and candidate datasets. Tavily web search is used when configured; Hugging Face dataset discovery is also available.
3. **Knowledge Base** retrieves related passages from local ChromaDB and prepares context for the design stage. If the store is unavailable or empty, the graph continues with fallback context.
4. **Architect** creates the technical architecture, dataset strategy, and model strategy.
5. **Reviewer** evaluates the proposed plan. A pass advances to the report stage. A revision can route back to Researcher or Architect, subject to the configured maximum.
6. **Planner** assembles the validated user-facing plan.

The internal graph state is a ProjectState containing the brief, requirements, research results and sources, retrieved context, design strategies, review feedback, revision state, and final report. The Python definitions in app/graph/state.py and app/graph/workflow.py are the source of truth for state and routing.

## 4. Agent trace and user-visible data

The backend builds detailed trace snapshots in api.py using app/services/agent_trace.py. A snapshot can contain each step's input, output, and accumulated internal state. These trace objects are held by the backend request handler and are not included in the browser event stream.

The web client receives only:

- the event type;
- the completed agent/node name and small progress fields;
- the final report after the Planner finishes; or
- a user-readable error message.

The JSON export button downloads the **final project report**. It does not download the internal agent trace. LangSmith tracing is a separate, optional backend integration controlled by environment settings.

## 5. API reference

The FastAPI application object is api:api in the repository-root api.py.

### GET /health

Returns service status, selected model, whether the Google API key is configured, and whether LangSmith tracing is enabled. The configured flag checks the Google key; it does not verify that an external provider is reachable.

Example:

~~~json
{
  "ok": true,
  "model": "gemini-2.5-flash",
  "configured": true,
  "langsmith_tracing": false
}
~~~

### POST /build

Request body:

~~~json
{ "idea": "Describe the AI project you want to plan in at least five words." }
~~~

The brief must contain at least 20 characters, at least five words, and no more than 2,000 characters. A valid request returns a newline-delimited JSON stream with content type application/x-ndjson.

Event contract:

- **started** — the run was accepted and started.
- **step** — one graph node completed; contains node, revision_count, critic_status, and next_agent.
- **complete** — contains report, the final ProjectReport.
- **error** — contains a readable message.

Each event is one JSON object followed by a newline. Internal trace snapshots and run state are not part of this event contract.

Relevant HTTP errors include 422 for invalid project ideas, 503 when GOOGLE_API_KEY is missing, and 502 from the Next.js proxy when the Python API cannot be reached.

### POST /export/pdf

Accepts the final report JSON and returns a PDF file. The Next.js route /api/export-pdf proxies the request and forwards the download filename. The report UI falls back to browser print/save if PDF export fails.

### Next.js browser-facing routes

- GET /api/health — browser health check and API proxy.
- POST /api/build — browser plan-generation route and NDJSON proxy.
- POST /api/export-pdf — browser PDF-export route.

The upstream planner URL defaults to http://127.0.0.1:8000. Set PLANNER_API_URL in the web server environment only if the API is hosted elsewhere.

## 6. Final report shape

ProjectReport is declared in web/lib/types.ts; the corresponding Pydantic output model is FinalProjectPlan in app/models/report_models.py. The final plan includes:

- project title and executive summary;
- objectives;
- technical architecture;
- dataset plan and optional dataset recommendations;
- model plan;
- implementation roadmap;
- risks and mitigations;
- success metrics;
- estimated timeline in weeks;
- required skills and recommended tools;
- review-cycle count and source URLs.

The report view supports section navigation, PDF download, browser print, JSON download, and starting a new plan. Report data is held in the current browser session; this branch does not add a user account or report-history database.

## 7. Requirements

- Git.
- Python 3.11 or newer and pip.
- Node.js LTS and npm compatible with the installed Next.js version.
- Internet access for installing dependencies and using configured model/search services.
- A [Google AI Studio API key](https://aistudio.google.com/app/apikey) for plan generation.

Optional integrations:

- **[OpenAI API key](https://platform.openai.com/api-keys)** — uses OpenAI text-embedding-3-small embeddings. Without this key, the embedding service falls back to local Hugging Face sentence-transformer embeddings.
- **[Tavily API key](https://app.tavily.com)** — enables live web search. Without it, that search path is skipped.
- **LangSmith API key and tracing flag** — sends pipeline traces to the configured LangSmith project when enabled.

When using local embeddings without an OpenAI key, install the Hugging Face LangChain integration if it is not already installed:

~~~powershell
.\.venv\Scripts\python.exe -m pip install langchain-huggingface
~~~

The sentence-transformer model is downloaded on first use. An OpenAI key avoids that local model download.

## 8. First-time setup — Windows PowerShell

Run these commands from PowerShell. If the repository is already cloned, start at the virtual-environment step.

~~~powershell
git clone -b last https://github.com/EmadAnwerNaguib465/Planorai.git
cd Planorai
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
~~~

In the root .env file, replace the Google key placeholder:

~~~dotenv
GOOGLE_API_KEY=your_google_ai_studio_key
~~~

The .env.example file also lists OpenAI, Tavily, embedding, model, RAG, graph, and application settings. Keep secrets in the root .env; do not put provider keys in web/.env, browser code, or a NEXT_PUBLIC_* variable. The root .env is ignored by Git.

Install web packages from the web directory:

~~~powershell
cd web
npm ci
~~~

### Prepare the knowledge base

The five source documents are already in data/knowledge_base/. The ChromaDB database under data/chroma/ is local generated data and is not committed. Ingest the documents once per fresh checkout to enable local RAG retrieval:

~~~powershell
cd ..
.\.venv\Scripts\python.exe scripts/ingest_documents.py
~~~

Use --force to rebuild after changing source documents, or --dry-run to inspect the ingestion inputs. The application can still proceed without a populated database, but the Knowledge Base stage will use fallback context.

## 9. Start the application

Keep the backend and web server in separate terminals. Do not launch a second server on a port that is already in use.

**Terminal 1 — Python API, from the repository root:**

~~~powershell
cd "D:\Courses\NTI - ETA (AI)\Graduation Project\Planorai"
.\.venv\Scripts\python.exe -m uvicorn api:api --host 127.0.0.1 --port 8000
~~~

**Terminal 2 — React/Next.js, from the web directory:**

~~~powershell
cd "D:\Courses\NTI - ETA (AI)\Graduation Project\Planorai\web"
npm run dev -- --hostname 127.0.0.1 --port 3000
~~~

Open [http://localhost:3000](http://localhost:3000/). The backend health endpoint is [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

Stop each process with Ctrl+C in its terminal.

### Production web build

Build and serve the Next.js app from web/; the Python API must still run separately:

~~~powershell
npm run build
npm run start
~~~

The start script uses Next.js production-server defaults. Use the PORT environment variable or Next.js server options to select another port when needed.

## 10. Environment settings

Settings are loaded by Pydantic Settings from the repository-root .env. Values in the file override Python defaults.

| Variable | Purpose | Behavior |
|---|---|---|
| GOOGLE_API_KEY | Gemini model calls | Required to generate plans |
| LLM_MODEL | Gemini model identifier | .env.example supplies gemini-2.0-flash; the Python default is gemini-2.5-flash |
| LLM_TEMPERATURE | Model sampling | Default/template: 0.7 |
| LLM_MAX_TOKENS | Model output limit | Default/template: 8192 |
| OPENAI_API_KEY | OpenAI embeddings | Optional; local embeddings are used when unavailable |
| EMBEDDING_PROVIDER | Embedding selection | OpenAI is used only when set to openai and an OpenAI key exists |
| EMBEDDING_MODEL | OpenAI embedding model | Template: text-embedding-3-small |
| TAVILY_API_KEY | Live web search | Optional; web search is skipped without it |
| LANGSMITH_TRACING | Enable LangSmith tracing | Defaults to disabled |
| LANGSMITH_API_KEY | LangSmith authentication | Required for tracing to activate |
| LANGSMITH_PROJECT | LangSmith project name | Defaults to planorai |
| LANGSMITH_ENDPOINT | LangSmith endpoint | Defaults to the public LangSmith API |
| CHROMA_PERSIST_DIR | Local vector-store path | Template: ./data/chroma |
| KNOWLEDGE_BASE_DIR | Source document directory | Template: ./data/knowledge_base |
| RAG_TOP_K | Number of retrieved passages | Default/template: 5 |
| CHUNK_SIZE / CHUNK_OVERLAP | Document chunking settings | Defaults/template: 1000 / 200 |
| MAX_REVISIONS | Maximum critic revision cycles | Default/template: 2 |
| PLANNER_API_URL | API upstream for Next.js proxy | Web-server setting; defaults to http://127.0.0.1:8000 |

Do not commit .env or expose API keys to the browser. No key is required for opening the UI, but a valid Google key is required to generate a plan.

## 11. Repository structure

~~~text
.
├── api.py                         FastAPI app: health, plan stream, PDF export
├── app.py                         Legacy Streamlit entry point
├── requirements.txt               Python dependencies
├── .env.example                   Backend configuration template
├── app/
│   ├── agents/                    Six LangGraph node implementations
│   ├── config/settings.py         Pydantic Settings and defaults
│   ├── graph/state.py             Internal ProjectState TypedDict
│   ├── graph/workflow.py          Compiled graph and stream API
│   ├── models/                    Pydantic agent/report schemas
│   ├── prompts/                   Per-agent prompt templates
│   ├── rag/                       Loader, splitter, embeddings, ChromaDB
│   ├── services/                  LLM, trace, search, report, and PDF services
│   ├── tools/                     Web search, dataset search, calculator
│   └── utils/                     Validation, logging, and helpers
├── data/
│   ├── knowledge_base/            Five curated Markdown guides
│   └── chroma/                    Local generated vector store (git-ignored)
├── docs/BRANCH_LAST.md            This branch-specific guide
├── scripts/                       Ingestion, evaluation, conversion utilities
├── tests/                         Python tests and report fixture
└── web/
    ├── app/                       Pages, styling, and API proxy handlers
    ├── components/                Three.js scene and report view
    ├── lib/types.ts               Agent, event, and report TypeScript types
    └── public/                    Logos, fonts, and static assets
~~~

## 12. Useful development commands

Run from the indicated directory:

~~~powershell
# Repository root: Python tests
.\.venv\Scripts\python.exe -m pytest

# web/: production compile and type validation
npm run build
npm run typecheck

# web/: ESLint
npm run lint
~~~

## 13. Troubleshooting

### EADDRINUSE on port 3000 or 8000

Another process already owns the port. Reuse the running app if it is responsive, or stop the old process with Ctrl+C in its terminal before starting another copy. To identify the listener in PowerShell:

~~~powershell
Get-NetTCPConnection -LocalPort 3000 -State Listen |
  Select-Object LocalAddress, LocalPort, OwningProcess
~~~

Replace 3000 with 8000 to inspect the Python API port. To use another Next.js port, start with npm run dev -- --hostname 127.0.0.1 --port 3001.

### UI says “Service offline”

Confirm the Python API is running in its own terminal and responds at http://127.0.0.1:8000/health. If the API is hosted elsewhere, set PLANNER_API_URL in the environment used by Next.js and restart the web process.

### Plan generation says the Google key is missing

Check that .env is in the repository root beside api.py, that GOOGLE_API_KEY contains a real key, and that the API process was restarted after editing it. Do not include quotation marks around the value unless they are part of the key.

### Knowledge retrieval falls back or local embeddings fail

Run document ingestion once. If using local embeddings, install langchain-huggingface and ensure the machine can download the sentence-transformer model on first use. If the ChromaDB store was built with OpenAI embeddings, continue using the same embedding provider/model when loading it; otherwise rebuild with scripts/ingest_documents.py --force.

### npm ci or Next.js startup fails

Confirm Node.js and npm are installed, run commands from web/, and use npm ci to install dependencies from the committed lockfile. The repository contains a root npm lockfile as well, so always run frontend package commands from the web directory.

## 14. Implementation references

- Web page and request/event handling: web/app/page.tsx
- Report rendering and export: web/components/report-view.tsx
- 3D icon scene and fallback: web/components/pipeline-scene.tsx
- TypeScript event/report contracts: web/lib/types.ts
- Next.js API proxy routes: web/app/api/
- FastAPI endpoints and internal trace assembly: api.py
- Agent trace snapshots: app/services/agent_trace.py
- Graph topology and stream API: app/graph/workflow.py
- Shared internal state: app/graph/state.py
- User brief validation: app/utils/validators.py
- Final report schema: app/models/report_models.py
