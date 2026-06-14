https://littercam.vercel.app/

# LitterCam — AI Traffic Intelligence System

AI-powered traffic monitoring for real-world violations. Detect littering, unsafe driving, and public violations in real-time using computer vision.

## Tech Stack

- **Object Detection**: YOLOv8 + ByteTrack for vehicle detection/tracking
- **OCR**: EasyOCR for number plate extraction
- **Video Pipeline**: OpenCV for video processing and motion-based litter heuristics
- **AI Vision**: Multi-LLM support (Gemini, OpenAI, Claude, Ollama) for intelligent litter classification
- **Backend**: FastAPI + SQLAlchemy for violation APIs
- **Dashboard**: Streamlit for reviewer dashboard
- **Database**: SQLite (WAL mode) for MVP storage

## Quick Start

### Option A: Cloud API (Recommended)

Use any major LLM provider for AI-powered litter detection. No GPU required.

```bash
pip install -r requirements.txt

# Pick ONE provider and set its key:
set GEMINI_API_KEY=your-key-here       # Google Gemini
# set OPENAI_API_KEY=your-key-here     # OpenAI GPT-4o
# set ANTHROPIC_API_KEY=your-key-here  # Anthropic Claude

set AI_BACKEND=gemini   # or: openai, claude

uvicorn services.api.main:app --reload
```

### Option B: Local with Ollama (Private & Offline)

Run AI models entirely on your own hardware. No cloud dependency.

```bash
# Install Ollama from https://ollama.ai
ollama pull llava

pip install -r requirements.txt

set AI_BACKEND=ollama
set OLLAMA_URL=http://localhost:11434
set OLLAMA_MODEL=llava

uvicorn services.api.main:app --reload
```

### Option C: Heuristic Only (No AI Key Needed)

Use only YOLO object detection + motion heuristics. Basic detection, no API key needed.

```bash
pip install -r requirements.local.txt

# AI_BACKEND defaults to "heuristic" if not set
uvicorn services.api.main:app --reload
```

## Supported AI Providers

| Provider | API Key Env Var | Default Model | Example Models |
|----------|----------------|---------------|----------------|
| Google Gemini | `GEMINI_API_KEY` | gemini-2.0-flash | gemini-2.5-pro, gemini-2.5-flash |
| OpenAI | `OPENAI_API_KEY` | gpt-4o-mini | gpt-4o, gpt-4.1 |
| Anthropic Claude | `ANTHROPIC_API_KEY` | claude-sonnet-4-20250514 | claude-haiku, claude-opus-4-20250514 |
| Ollama (Local) | — | llava | llama3.2-vision, bakllava, moondream |
| Heuristic | — | yolov8n | — |

## AI Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ai/status` | GET | Check current AI backend status |
| `/ai/providers` | GET | List all supported providers |
| `/ai/configure` | POST | Set provider + API key at runtime |
| `/ai/analyze` | POST | Analyze a base64-encoded frame |
| `/ai/analyze-upload` | POST | Upload and analyze an image file |
| `/ai/ollama/models` | GET | List models available on Ollama |

## Running the Streamlit Dashboard

```bash
pip install -r requirements.local.txt
streamlit run dashboard/app.py
```

The dashboard sidebar lets you pick your AI provider and enter your API key before processing videos.

## Architecture

```
Camera Feed → YOLO Object Detection → Motion Heuristic Engine → AI Vision LLM (2nd stage) → OCR Plate Reader → Evidence Package → Violation API → Dashboard Review
```

## Performance

- 3000 requests at concurrency 120
- 100% POST/PATCH/GET success rate
- ~193 requests/sec throughput
- POST p95 latency ~701 ms (p99 ~765 ms)

## What would you improve?

Suggestions welcome — built for the ruckus caused by overpopulation and poor road management, to make life a bit easier.
