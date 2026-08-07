# CADGen AI Platform

**Text-to-3D CAD Platform** — Generate parametric 3D models from natural language prompts using LLMs and CadQuery.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Chat      │  │ 3D Viewport  │  │ Parametric Controls    │  │
│  │ Sidebar   │  │ (R3F + Three)│  │ + Code Drawer          │  │
│  └─────┬─────┘  └──────┬───────┘  └───────────┬───────────┘  │
│        │               │                      │              │
│        └───────────────┴──────────────────────┘              │
│                        AppContext                            │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │ /api/v1/       │  │ SessionManager  │  │ ExportPipeline│  │
│  │ generate       │  │ (in-memory)     │  │ (STEP/STL/   │  │
│  │ recompile      │  └────────┬────────┘  │  GLTF)       │  │
│  │ export         │           │           └──────┬───────┘  │
│  └────────┬───────┘           │                  │           │
│           │            ┌──────▼──────┐           │           │
│           │            │ LLMPipeline │           │           │
│           │            │ (repair +   │           │           │
│           │            │  code gen)  │           │           │
│           │            └──────┬──────┘           │           │
│           │                   │                  │           │
│  ┌────────▼───────────────────▼──────────────────▼─────────┐ │
│  │              CadQuerySandbox                             │ │
│  │  (subprocess or remote worker — executes Python/CadQuery)│ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

- **Text-to-3D Generation**: Describe a model in natural language; the LLM generates executable CadQuery Python code.
- **Parametric Sliders**: Numeric parameters are auto-extracted from generated code and exposed as interactive sliders.
- **Live Code Viewer**: Monaco-powered code drawer with read-only view of generated CadQuery scripts.
- **Auto-Repair**: If CadQuery execution fails, the LLM automatically repairs the code (up to 3 retries) with targeted OpenCascade error hints.
- **Revision History**: Chat-based interaction preserves previous generations for comparison and rollback.
- **Multi-format Export**: Download models as STEP, STL, or GLTF.
- **Display Modes**: Shaded, wireframe, normals, and overhang angle visualization for 3D print readiness.

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker & Docker Compose | Latest | Recommended for full-stack local development |
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ (20 recommended) | Frontend runtime |
| CUDA GPU (optional) | — | Faster local LLM inference (Ollama/vLLM) |

## Quick Start (Docker Compose)

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd cadgen-ai-platform

# 2. Copy environment file
cp .env.example .env

# 3. Start all services
docker compose -f docker-compose.prod.yml up --build

# 4. Open the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Sandbox API: http://localhost:8001
```

## Local Development

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
pip install pytest httpx ruff  # dev dependencies

# Run the API server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
pytest

# Lint
ruff check .
```

### Frontend Setup

```bash
# From project root
npm install

# Start dev server
npm run dev
# → http://localhost:3000

# Run tests
npm test

# Lint
npm run lint

# Build for production
npm run build
npm start
```

### Running with Docker Compose

```bash
docker compose -f docker-compose.prod.yml up --build
```

Services:
- **Frontend** — `http://localhost:3000` (Next.js)
- **Backend** — `http://localhost:8000` (FastAPI)
- **Sandbox** — `http://localhost:8001` (CadQuery worker)

## LLM Configuration

The platform uses any **OpenAI-compatible chat completions API**. Configure via environment variables:

### Ollama (Local)

```bash
# Install and start Ollama
ollama serve

# Pull a code-capable model
ollama pull qwen2.5-coder:32b

# Set environment variables
export LLM_API_URL=http://localhost:11434/v1
export LLM_API_KEY=ollama
export LLM_MODEL=qwen2.5-coder:32b
```

### OpenAI

```bash
export LLM_API_URL=https://api.openai.com/v1
export LLM_API_KEY=sk-...
export LLM_MODEL=gpt-4o
```

### Anthropic (via compatible proxy)

```bash
export LLM_API_URL=https://api.anthropic.com/v1
export LLM_API_KEY=sk-ant-...
export LLM_MODEL=claude-3-5-sonnet-20240620
```

### vLLM

```bash
export LLM_API_URL=http://localhost:8000/v1
export LLM_API_KEY=EMPTY
export LLM_MODEL=<your-model-name>
```

### Fine-Tuned Model

If you have fine-tuned a model on the CADGen dataset, point `LLM_MODEL` to your model name. The backend sends the same OpenAI-compatible chat completion request format:

```json
{
  "model": "<your-fine-tuned-model>",
  "messages": [
    {"role": "system", "content": "You are a CadQuery code generation assistant..."},
    {"role": "user", "content": "Create a rectangular box with length 80..."}
  ],
  "temperature": 0.2,
  "max_tokens": 2048
}
```

## Usage Guide

### Generate a 3D Model from Text

1. Open the app at `http://localhost:3000`.
2. In the **Chat Sidebar** (left panel), type a description of the model you want.
3. Press Enter or click send. The backend:
   - Sends your prompt to the LLM.
   - Receives executable CadQuery Python code.
   - Runs the code in the CadQuery sandbox.
   - Returns the generated STEP, STL, and GLTF files.
4. The 3D viewport (center) displays the GLTF model.

### Adjust Parameters with Sliders

After generation, the **Parametric Panel** (right sidebar) shows sliders for each numeric variable in the generated code (length, width, fillet_radius, etc.).

- Drag a slider to change a value.
- The frontend recompiles the code by substituting parameter values.
- The model re-renders in the viewport automatically.

### View Generated Code

1. Click the **"View Code"** button in the right panel.
2. A Monaco Editor drawer opens showing the full CadQuery Python script.
3. Variables are syntax-highlighted; the drawer is read-only by default.

### Export Models

Use the export buttons in the top-right toolbar of the viewport:

| Format | Use Case |
|--------|----------|
| **STEP** | CAD interchange, manufacturing |
| **STL** | 3D printing, mesh processing |
| **GLTF** | Web display, Three.js rendering |

Click the format button to download the file. The export triggers a recompilation with current parameter values and returns the binary file.

## Dataset Generation & Model Fine-Tuning

### Generate a Synthetic Dataset

```bash
cd backend

# Generate 120 default entries
python -m dataset.generate_dataset --count 120 --output dataset/dataset.jsonl

# Generate beginner-only entries
python -m dataset.generate_dataset --count 50 --difficulty beginner --output dataset/beginner.jsonl

# Generate expert-only entries
python -m dataset.generate_dataset --count 30 --difficulty expert --output dataset/expert.jsonl
```

Output format (JSONL):

```json
{
  "instruction": "Create a rectangular box with length 80, width 60, and height 10.",
  "code": "import cadquery as cq\n\nlength: float = 80\nwidth: float = 60\nheight: float = 10\n\nresult = cq.Workplane(\"XY\").box(length, width, height)\n\ncq.exporters.export(result, \"output.step\")\ncq.exporters.export(result, \"output.stl\")\ncq.exporters.export(result, \"output.gltf\")\n",
  "metadata": {
    "template_id": "box",
    "difficulty": "beginner",
    "params": {"length": 80, "width": 60, "height": 10},
    "param_specs": [...]
  }
}
```

### Validation

Every generated script is statically validated (syntax, required imports, required exports). If static validation fails, it falls back to subprocess execution with CadQuery. Only valid, executable scripts are written to the dataset.

### Fine-Tuning

Use the generated `dataset.jsonl` to fine-tune an LLM. The platform expects a standard **instruction-response** format:

- **Instruction**: Natural language prompt describing the CAD model.
- **Response**: Executable CadQuery Python code with parametric variables and export statements.

Scale the dataset to 10k+ entries by increasing `--count`. The 12 built-in templates cover beginner, intermediate, and expert difficulty levels:

| Template | Difficulty | Description |
|----------|-----------|-------------|
| `box` | Beginner | Simple rectangular box |
| `l_bracket` | Beginner | L-shaped bracket with mounting holes |
| `hollow_cylinder` | Beginner | Pipe / tube |
| `fillet_box` | Beginner | Box with rounded edges |
| `chamfer_box` | Beginner | Box with chamfered edges |
| `flange` | Intermediate | Circular flange with bolt holes |
| `base_plate` | Intermediate | Plate with hole grid |
| `cylinder_holes` | Intermediate | Cylinder with radial holes |
| `shaft_coupling` | Intermediate | Shaft coupling |
| `bearing_housing` | Expert | Bearing housing with bore and bolts |
| `pulley_wheel` | Expert | Wheel with rim and hub |
| `rod_end` | Expert | Rod end fitting |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL (frontend) |
| `LLM_API_URL` | `http://localhost:1234/v1` | OpenAI-compatible LLM endpoint |
| `LLM_API_KEY` | *(empty)* | API key for LLM provider (empty for local Ollama) |
| `LLM_MODEL` | `qwen2.5-coder-32b-instruct` | Model name served by the LLM endpoint |
| `CADGEN_OUTPUT_DIR` | `/tmp/cadgen_outputs` | Directory for generated CAD files |
| `CADGEN_SANDBOX_URL` | *(empty)* | Remote sandbox URL; empty = use local sandbox service |
| `CORS_ORIGINS` | `http://localhost:3000,http://frontend:3000` | Comma-separated allowed CORS origins |
| `CADGEN_VALIDATE_TIMEOUT` | `60` | Dataset validation timeout in seconds (backend) |

### Backend Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .
COPY . .
RUN apt-get update && apt-get install -y --no-cache curl
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", 8000]
```

## API Reference

### Generate a Model

```bash
POST /api/v1/generate
Content-Type: application/json

{
  "prompt": "Create a rectangular box with length 80, width 60, and height 10.",
  "parameters": {}
}
```

**Response:**

```json
{
  "step_url": "http://localhost:8000/outputs/<session-id>/output.step",
  "stl_url": "http://localhost:8000/outputs/<session-id>/output.stl",
  "gltf_url": "http://localhost:8000/outputs/<session-id>/output.gltf",
  "parameters": [
    {"name": "length", "value": 80, "min": 0, "max": 200, "step": 1},
    {"name": "width", "value": 60, "min": 0, "max": 200, "step": 1},
    {"name": "height", "value": 10, "min": 0, "max": 100, "step": 1}
  ],
  "code": "import cadquery as cq\n\nlength: float = 80\n...",
  "logs": "...",
  "message": "Generated model: Create a rectangular box...",
  "revisionId": "<uuid>",
  "retry_count": 0,
  "max_retries": 3,
  "error_type": null,
  "repair_hints": null
}
```

### Recompile with New Parameters

```bash
POST /api/v1/recompile
Content-Type: application/json

{
  "parameters": {"length": 100, "width": 80, "height": 15}
}
```

### Export a Model

```bash
POST /api/v1/export?format=stl&session_id=<uuid>&tolerance=0.01
```

Returns a binary file stream with `Content-Disposition: attachment`.

### Health Check

```bash
GET /health
GET /api/v1/health
```

## Testing

### Backend Tests (pytest)

```bash
cd backend
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_llm_pipeline.py
```

Test files:
- `tests/test_llm_pipeline.py` — LLM code generation, repair, parameter extraction
- `tests/test_cadquery_sandbox.py` — Sandbox execution and parameter substitution
- `tests/test_export_pipeline.py` — Export pipeline (STEP, STL, GLTF)
- `tests/test_session.py` — Session manager

### Frontend Tests (Jest + React Testing Library)

```bash
npm test

# Run with coverage
npm test -- --coverage
```

Test files:
- `src/components/__tests__/LiveSync.test.ts` — Parameter extraction and substitution utilities
- `src/components/__tests__/CodeDrawer.test.tsx` — Code drawer component
- `src/components/__tests__/ParametricPanel.test.tsx` — Parametric control panel
- `src/components/__tests__/ChatSidebar.test.tsx` — Chat sidebar and revision history
- `src/contexts/__tests__/AppContext.test.tsx` — App context state management

## Project Structure

```
.
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── sandbox_api.py             # Standalone sandbox worker (port 8001)
│   ├── pyproject.toml             # Python project config
│   ├── Dockerfile                 # Backend container image
│   ├── api/v1/
│   │   ├── router.py              # API route aggregation
│   │   └── endpoints/
│   │       ├── generate.py        # POST /generate — LLM + sandbox execution
│   │       ├── recompile.py       # POST /recompile — parameter substitution + rerun
│   │       └── export_endpoint.py # POST /export — file download
│   ├── models/
│   │   └── schemas.py             # Pydantic request/response models
│   ├── services/
│   │   ├── llm_pipeline.py        # LLM client, code generation, repair, parameter helpers
│   │   ├── cadquery_sandbox.py    # Sandbox execution (local subprocess or remote)
│   │   ├── export_pipeline.py     # STEP/STL/GLTF export orchestration
│   │   └── session.py             # In-memory session management
│   ├── dataset/
│   │   ├── generate_dataset.py    # Dataset generation orchestrator
│   │   ├── prompt_templates.py    # 12 parametric CAD prompt/script templates
│   │   ├── validate_scripts.py    # Static + subprocess script validator
│   │   └── README.md              # Dataset pipeline documentation
│   └── tests/                     # Backend pytest suite
├── src/
│   ├── app/
│   │   └── page.tsx               # Main app layout (viewport, chat, controls)
│   ├── components/
│   │   ├── chat/                  # ChatSidebar, PromptInput, MessageList, RevisionHistory
│   │   ├── controls/              # ParametricPanel
│   │   ├── editor/                # CodeDrawer, MonacoWrapper, LiveSync
│   │   ├── viewport/              # CADViewport, Scene, DisplayModes, ClippingPlane
│   │   ├── ui/                    # Button, LoadingSpinner, Toast
│   │   └── GlobalErrorBoundary.tsx
│   ├── contexts/
│   │   └── AppContext.tsx         # Global state: generation, recompilation, revisions
│   ├── hooks/
│   │   ├── useApi.ts              # API request hooks
│   │   ├── useThree.ts            # Three.js / R3F hooks
│   │   └── useDebounce.ts         # Debounce utility
│   └── lib/
│       ├── api/
│       │   ├── client.ts          # ApiService (generate, recompile, export)
│       │   └── index.ts
│       ├── types/                 # TypeScript types (errors, etc.)
│       └── utils/                 # Icons, formatting
├── public/                        # Static assets
├── Dockerfile                     # Multi-stage Next.js production image
├── docker-compose.prod.yml        # Production compose (frontend, backend, sandbox)
├── package.json                   # Node dependencies & scripts
├── next.config.js                 # Next.js config (standalone output)
├── tailwind.config.js
├── tsconfig.json
├── jest.config.js                 # Jest config (jsdom environment)
├── .env.example                   # Environment variable template
└── README.md                      # This file
```

## Troubleshooting

### LLM connection fails

- Verify `LLM_API_URL` is reachable from the backend container/process.
- For Ollama, ensure `ollama serve` is running and the model is pulled (`ollama list`).
- Check that `LLM_MODEL` exactly matches the model name served by your endpoint.

### CadQuery execution fails

- Ensure `cadquery>=2.4.0` is installed in the backend environment.
- Check that `CADGEN_OUTPUT_DIR` is writable.
- Review logs returned in the `logs` field of the API response.
- The platform auto-repairs code on failure (up to 3 retries); check `retry_count` and `repair_hints` in the response.

### Frontend cannot reach backend

- Confirm `NEXT_PUBLIC_API_URL` matches the backend address.
- Verify CORS origins in `CORS_ORIGINS` include the frontend origin.
- Check that the backend health endpoint returns `{"status": "ok"}`.

### Docker volumes not persisting

- The `cadgen_outputs` named volume stores generated files. Remove it with `docker compose down -v` to reset.

## License

MIT
