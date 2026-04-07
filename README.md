# Vehicle Littering AI MVP

This project is a focused MVP for detecting candidate littering events from moving vehicles.

## MVP Scope

Included:
- Vehicle detection and tracking from recorded traffic video
- Candidate litter-event detection using motion and proximity heuristics
- Number plate extraction with OCR
- Evidence package generation (image + clip + metadata)
- Human review workflow via API and dashboard

Excluded (Phase 2):
- Automatic fining
- Noise pollution detection
- Rash driving detection

## Project Structure

- `services/inference`: video processing pipeline and litter-event logic
- `services/api`: FastAPI backend for storing and reviewing events
- `dashboard`: Streamlit review interface
- `data/raw`: input videos
- `data/evidence`: generated frames and metadata
- `data/clips`: generated event clips

## Quick Start

1. Create virtual environment and install dependencies.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Start API server.

```powershell
uvicorn services.api.main:app --reload --port 8000
```

3. Run video pipeline on a recorded traffic video.

```powershell
python -m services.inference.run_offline --video data/raw/traffic.mp4 --api-url http://127.0.0.1:8000
```

Optional: generate a local demo clip if you do not have footage yet.

```powershell
python scripts/generate_demo_video.py
```

4. Start review dashboard.

```powershell
streamlit run dashboard/app.py
```

## One-Command Helper Scripts (Windows PowerShell)

From project root:

```powershell
.\scripts\bootstrap.ps1
.\scripts\run_api.ps1
.\scripts\run_pipeline.ps1 -Video data/raw/traffic.mp4
.\scripts\run_dashboard.ps1
.\scripts\run_stress.ps1 -Requests 1000 -Concurrency 50
```

## Load Testing

Standard high-load run:

```powershell
python scripts/stress_test_api.py --base-url http://127.0.0.1:8000 --requests 1000 --concurrency 50 --timeout 8
```

Extreme run:

```powershell
python scripts/stress_test_api.py --base-url http://127.0.0.1:8000 --requests 3000 --concurrency 120 --timeout 8
```

## Environment Variables

Optional variables:
- `LITTER_DB_URL` default: `sqlite:///./litter_events.db`
- `EVIDENCE_DIR` default: `data/evidence`
- `CLIPS_DIR` default: `data/clips`
- `VEHICLE_MODEL` default: `yolov8n.pt`
- `LITTER_MODEL` default: empty (uses motion-only fallback)

## Important Safety Note

This MVP creates candidate violations only. Human review is required before enforcement actions.
