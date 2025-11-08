# Figma-to-Code AI Agent (Gemini + LangChain)

## Demo (Selected Screenshots)

### 1) Input: Figma Frame
Shows the source design with the frame and layers selected (ground truth for the export).
  
![Figma frame](docs/screenshots/01_input_figma_frame.png)

### 2) Output: Folder Tree
Static export / generated code artifacts (e.g., `exported-web/` or `generated-ui/`) and key files.
  
![Output folder tree](docs/screenshots/04_output_folder_tree.png)

### 3) UI Schema (Excerpt)
Normalized JSON the tool builds from Figma (positions, fills/gradients/images, strokes, radii, text styles, effects).
  
![ui-schema.json snippet](docs/screenshots/08_schema_json_snippet.png)

### 4) React Code Components (AI Path)
Generated React + TSX components (LLM path) that compose the page, ready to run with Vite dev server.
  
![React components](docs/screenshots/10_react_code_components.png)


> **One-command pipeline** that turns **Figma designs** into runnable **React + TypeScript + Tailwind** code using **Google Gemini** with **LangChain**.  
> Includes an offline sample, clear CLI, and a pluggable writer architecture.

---

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [How It Works](#how-it-works)
- [Figma Setup](#figma-setup)
- [LLM & Prompting](#llm--prompting)
- [Output Project (React + Tailwind)](#output-project-react--tailwind)
- [Troubleshooting](#troubleshooting)
- [Testing](#testing)
- [Extending & Customization](#extending--customization)
- [Security & Privacy](#security--privacy)
- [Cost & Rate Limits](#cost--rate-limits)
- [Roadmap](#roadmap)
- [FAQ](#faq)
- [License](#license)

---

## Features
- 🔌 **Figma ingestion**: Pulls Figma file JSON via REST API (or load included sample for offline demo).
- 🧩 **Schema normalization**: Converts Figma nodes to a compact, typed UI schema (Pydantic).
- 🧠 **AI codegen with Gemini**: Uses LangChain + Google Gemini to synthesize React components.
- 🧱 **Scaffolded app**: Generates a Vite + React + Tailwind project in `generated-ui/`.
- 🧪 **Tests**: Minimal PyTest sanity checks for schema and pipeline basics.
- 🧰 **Pluggable writers**: Easily swap in other target frameworks (Vue/Svelte/Native) via `agent/writers`.
- 🧯 **Offline mode**: `--sample` runs end-to-end without any network or API keys.

---

## Architecture
```
[Figma File] --(REST API)--> [Ingestion]
                           -> [UI Schema (Pydantic)]
                           -> [Prompt Builder]
                           -> [Gemini (LangChain)]
                           -> [LLM Output Parser: fenced files]
                           -> [Writer] --> generated-ui/ (Vite+React+Tailwind)
```

- **Ingestion**: `agent/figma_api.py` fetches file JSON.
- **Schema**: `agent/schema.py` defines minimal Node/Bounds/TextStyle models.
- **Prompting**: `agent/prompt.py` provides system & user messages.
- **LLM**: `agent/codegen.py` wraps `ChatGoogleGenerativeAI` and parses fenced code blocks.
- **Writer**: `agent/writers/react_writer.py` creates the scaffold and writes files.

---

## Folder Structure
```
agent/
  __init__.py
  config.py              # env + settings
  figma_api.py           # Figma REST client
  schema.py              # UI schema (Pydantic)
  prompt.py              # system + user prompts
  codegen.py             # Gemini via LangChain + fenced file parser
  main.py                # CLI entrypoint
  utils/
    __init__.py
    logging.py
  writers/
    __init__.py
    react_writer.py      # Vite + React + Tailwind scaffold + file writer
  tests/
    test_schema.py
generated-ui/            # Output (created/overwritten by the agent)
samples/
  figma_sample.json      # Offline demo data
README.md
requirements.txt
.env.example
LICENSE
```

---

## Prerequisites
- **Python** 3.10+
- **Node.js** 18+ and **npm** (for running the generated app)
- A **Google Gemini API key** (for real codegen) – optional if using `--sample`
- A **Figma Personal Access Token** and **file key** – optional if using `--sample`

---

## Installation
```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

---

## Configuration
Copy `.env.example` ➜ `.env` and fill in:
```
GEMINI_API_KEY=your_google_gemini_key
FIGMA_TOKEN=your_figma_personal_access_token
FIGMA_FILE_ID=your_figma_file_key
# Optional overrides
MODEL_NAME=gemini-1.5-flash
HTTP_TIMEOUT=30
```

- `GEMINI_API_KEY`: Create at Google AI Studio / Google Cloud Generative AI (depending on your account).
- `FIGMA_TOKEN`: Create a Personal Access Token in Figma (Profile → Settings → Personal access tokens).
- `FIGMA_FILE_ID`: The part after `/file/` in your Figma URL:  
  `https://www.figma.com/file/<FILE_KEY>/Your-File-Name`

> Never commit real secrets. `.env` is git-ignored.

---

## Quick Start
**Online (Figma + Gemini):**
```bash
python -m agent.main run --file-id $FIGMA_FILE_ID --out generated-ui --framework react
cd generated-ui
npm install
npm run dev
```

**Offline (Sample only):**
```bash
python -m agent.main run --sample --out generated-ui --framework react
cd generated-ui
npm install
npm run dev
```

---

## CLI Reference
```
python -m agent.main run [OPTIONS]

Options:
  --file-id TEXT    Figma file key (overrides FIGMA_FILE_ID).
  --out TEXT        Output directory (default: generated-ui).
  --framework TEXT  Target framework (currently: react).
  --sample          Use bundled sample instead of calling Figma/Gemini.
```
Examples:
```bash
# Use env vars
python -m agent.main run

# Explicit file
python -m agent.main run --file-id AbCdEf123 --out generated-ui

# Offline
python -m agent.main run --sample
```

---

## How It Works
1. **Ingest**  
   `FigmaAPI.get_file(file_id)` fetches the file JSON. (Offline mode loads `samples/figma_sample.json`.)

2. **Normalize**  
   `main._figma_to_schema` walks Figma nodes → simplified `UISchema`. Current demo mapping includes:
   - Frames, Groups → container nodes
   - Text → text nodes (partial style parsing)
   - Rectangle/Ellipse/Image/Instance → basic nodes (limited properties)
   > This is intentionally minimal so you can extend it.

3. **Synthesize**  
   `CodeGen.generate(schema)` builds a chat prompt and calls Gemini via `langchain-google-genai`.
   The LLM **must** return **fenced file blocks** like:
   ```
   ```file:src/components/Hero.tsx
   export default function Hero(){ ... }
   ```
   ```

4. **Write**  
   The writer scaffolds a **Vite + React + Tailwind** app and writes each fenced file to disk.

---

## Figma Setup
1. **Token**: In Figma, open your profile → **Settings** → **Personal access tokens** → **Create new token**.
2. **Permissions**: Your token inherits your account/file access. Ensure you can **view** the target file.
3. **File Key**: Copy from the Figma URL: `https://www.figma.com/file/<FILE_KEY>/...`.
4. **Rate limits**: Figma enforces rate limits; if you hit 429, retry after a short delay.

---

## LLM & Prompting
- **Model**: default `gemini-1.5-flash` (fast, cost-effective). Change via `MODEL_NAME`.
- **System Prompt**: Demands React + Tailwind, functional components, valid TSX, no external deps.
- **User Prompt**: Injects the **UI Schema JSON** plus assembly instructions.
- **Output Contract**: LLM must produce fenced blocks prefixed with `file:` and then the relative path.

If the LLM fails to return files, we fall back to a safe `src/App.tsx` stub to avoid breaking the build.

---

## Output Project (React + Tailwind)
- Scaffold includes: `vite`, `typescript`, `tailwindcss`, `postcss`, and a sensible `tsconfig`.
- Start the app:
  ```bash
  cd generated-ui
  npm install
  npm run dev
  ```
- The agent may **overwrite** `generated-ui/src/App.tsx` each run. Commit it in a separate repo if needed.

---

## Troubleshooting
**1) `RuntimeError: GEMINI_API_KEY is required`**  
Set `GEMINI_API_KEY` in `.env` or run with `--sample`.

**2) `RuntimeError: FIGMA_TOKEN and a file id are required`**  
Set `FIGMA_TOKEN` and `FIGMA_FILE_ID`, or pass `--file-id`, or use `--sample`.

**3) Figma 401/403**  
- Token invalid/expired or no permission to the file. Regenerate token or request access.

**4) Empty LLM output**  
- Model throttle or prompt too large. The agent prints a warning and writes a stub `App.tsx`.
- Retry, or reduce schema size (e.g., process a single frame).

**5) Node/Yarn issues**  
- Use Node 18+. Delete `node_modules` and reinstall if you see strange Vite errors.

---

## Testing
Run unit tests:
```bash
pytest -q
```

---

## Extending & Customization
- **Better Figma mapping** (`agent/main.py::_figma_to_schema`): add auto-layout, constraints, variants, images.
- **Design tokens** (`schema.tokens`): wire your color/spacing/typography into the prompt.
- **Writers**: add `writers/vue_writer.py` or `writers/svelte_writer.py`; expose via `--framework`.
- **Prompt tuning**: customize `agent/prompt.py` to match your design system and code style rules.
- **Chunking**: large files → split by frames/pages and generate components incrementally.
- **Images**: call `FigmaAPI.get_images` for node IDs and write them into `/public` + `<img>`/`<Image/>`.

---

## Security & Privacy
- Keep secrets in `.env` (git-ignored). Regenerate tokens if compromised.
- Be mindful of sending proprietary design data to external LLMs. Check your org’s compliance rules.

---

## Cost & Rate Limits
- **Gemini**: billed per input/output tokens. `-flash` is cheaper/faster; `-pro` yields higher quality for complex UIs.
- **Figma**: subject to API rate limits; cache file JSON locally during development to save calls.

---

## Roadmap
- Rich auto-layout → Flex/Grid mapping
- Variant/Instance support
- Image export & asset pipeline
- Design tokens → Tailwind theme injection
- Additional writers (Vue, Svelte, React Native)
- Deterministic multi-pass generation with tests

---

## FAQ
**Q: Can I run without any keys?**  
A: Yes. Use `--sample` to run fully offline; it writes a small demo UI.

**Q: My org requires SSO—will the Figma token work?**  
A: As long as your user can access the file normally, the PAT should work. Otherwise, export the JSON or use `--sample`.

**Q: How stable is the output?**  
A: LLM output can vary. The prompt enforces a file contract; consider validating the fenced blocks and re-prompting on errors.

---

## License
MIT – see [LICENSE](LICENSE).

