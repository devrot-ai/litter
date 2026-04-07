 Built a traffic-side littering detection MVP that tracks vehicles, flags throw events, reads plates, and saves evidence ready for human review.

Tech:
- YOLOv8 + ByteTrack for vehicle detection/tracking
- EasyOCR for number plate extraction
- OpenCV for video pipeline and motion-based litter heuristics
- FastAPI + SQLAlchemy for violation APIs
- Streamlit for reviewer dashboard
- SQLite (WAL mode) for MVP storage

Challenge:
- Hardest part was not just detection, it was reliability under load.
- Early stress runs caused API failures (response validation issues + DB pool timeouts) when traffic spiked.

Solution:
- Built an end-to-end pipeline: video -> detection/tracking -> litter candidate logic -> OCR -> evidence package (image, clip, metadata).
- Added reviewer-first workflow (PENDING / APPROVED / REJECTED) instead of auto enforcement.
- Fixed API response serialization and tuned DB concurrency settings (pool sizing, SQLite WAL, busy timeout).
- Added repeatable stress testing scripts to validate real pressure behavior before shipping.

Impact:
- Stable under heavy load after fixes:
- 3000 requests at concurrency 120
- 100% POST success, 100% PATCH success, 100% GET success
- ~193 requests/sec throughput
- POST p95 latency ~701 ms (p99 ~765 ms)

Code:
- GitHub Repo: https://github.com/your-username/your-repo

What would you improve?
