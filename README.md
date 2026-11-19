# LitterCam

A camera system that watches roads and spots people littering or driving unsafely. It uses AI to look at video feeds, read number plates, and flag violations for review.

Live demo: https://littercam.vercel.app/

## How It Works

A camera feed goes through several steps. First, YOLO detects vehicles and tracks them. Then motion heuristics look for suspicious activity. An AI model (your choice of Gemini, OpenAI, Claude, or a local Ollama model) classifies what it sees. Finally, OCR reads number plates and everything is packaged up for review in a Streamlit dashboard.

## Getting Started

Install the dependencies:

```bash
pip install -r requirements.txt
```

Pick an AI backend and set your API key:

```bash
set AI_BACKEND=gemini
set GEMINI_API_KEY=your-key-here
```

Start the server:

```bash
uvicorn services.api.main:app --reload
```

You can also run it with Ollama for a fully local setup, or use just the heuristic mode with no AI key at all.

## Dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard lets you pick your AI provider and review flagged violations.

## Performance

Handles about 193 requests per second with 95% of responses under 700ms.
