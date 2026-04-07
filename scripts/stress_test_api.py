from __future__ import annotations

import argparse
import random
import statistics
import string
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


STATUS_CODES = ["PENDING", "APPROVED", "REJECTED"]


def random_plate() -> str:
    letters = "".join(random.choices(string.ascii_uppercase, k=2))
    digits = "".join(random.choices(string.digits, k=2))
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{letters}{digits}{suffix}"


def make_payload(i: int) -> dict:
    now_ms = int(time.time() * 1000)
    event_id = f"stress_{now_ms}_{i}_{random.randint(1000, 9999)}"
    return {
        "event_id": event_id,
        "violation_type": "LITTERING_CANDIDATE",
        "vehicle_track_id": random.randint(1, 99999),
        "plate_text": random_plate(),
        "plate_confidence": round(random.uniform(0.5, 0.99), 3),
        "detection_confidence": round(random.uniform(0.5, 0.98), 3),
        "timestamp_ms": now_ms,
        "camera_id": "stress-cam-01",
        "source_video": "stress_test",
        "image_path": "data/evidence/stress.jpg",
        "clip_path": "data/clips/stress.mp4",
        "metadata_json": {"mode": "stress", "sequence": i},
    }


def post_event(base_url: str, i: int, timeout: float) -> tuple[bool, float, str]:
    payload = make_payload(i)
    t0 = time.perf_counter()
    try:
        resp = requests.post(f"{base_url}/violations", json=payload, timeout=timeout)
        ok = 200 <= resp.status_code < 300
        return ok, (time.perf_counter() - t0) * 1000, payload["event_id"]
    except Exception:
        return False, (time.perf_counter() - t0) * 1000, payload["event_id"]


def patch_status(base_url: str, event_id: str, timeout: float) -> tuple[bool, float]:
    body = {
        "status": random.choice(STATUS_CODES),
        "review_note": "stress-check",
    }
    t0 = time.perf_counter()
    try:
        resp = requests.patch(f"{base_url}/violations/{event_id}/status", json=body, timeout=timeout)
        ok = 200 <= resp.status_code < 300
        return ok, (time.perf_counter() - t0) * 1000
    except Exception:
        return False, (time.perf_counter() - t0) * 1000


def get_list(base_url: str, timeout: float) -> tuple[bool, float]:
    t0 = time.perf_counter()
    try:
        resp = requests.get(f"{base_url}/violations", params={"limit": 100}, timeout=timeout)
        ok = 200 <= resp.status_code < 300
        return ok, (time.perf_counter() - t0) * 1000
    except Exception:
        return False, (time.perf_counter() - t0) * 1000


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = max(0, min(len(sorted_vals) - 1, int(round((p / 100) * (len(sorted_vals) - 1)))))
    return sorted_vals[idx]


def main() -> None:
    parser = argparse.ArgumentParser(description="Stress test for Littering MVP API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=1000)
    parser.add_argument("--concurrency", type=int, default=40)
    parser.add_argument("--timeout", type=float, default=6.0)
    args = parser.parse_args()

    print(f"Starting POST load: requests={args.requests}, concurrency={args.concurrency}")

    post_latencies = []
    post_ok = 0
    event_ids: list[str] = []

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(post_event, args.base_url, i, args.timeout) for i in range(args.requests)]
        for fut in as_completed(futures):
            ok, latency, event_id = fut.result()
            post_latencies.append(latency)
            if ok:
                post_ok += 1
                event_ids.append(event_id)

    post_elapsed = time.perf_counter() - start

    patch_latencies = []
    patch_ok = 0
    patch_sample = min(len(event_ids), max(1, args.requests // 4))
    with ThreadPoolExecutor(max_workers=max(8, args.concurrency // 2)) as pool:
        futures = [pool.submit(patch_status, args.base_url, eid, args.timeout) for eid in event_ids[:patch_sample]]
        for fut in as_completed(futures):
            ok, latency = fut.result()
            patch_latencies.append(latency)
            if ok:
                patch_ok += 1

    get_latencies = []
    get_ok = 0
    get_rounds = max(20, args.requests // 40)
    with ThreadPoolExecutor(max_workers=max(8, args.concurrency // 2)) as pool:
        futures = [pool.submit(get_list, args.base_url, args.timeout) for _ in range(get_rounds)]
        for fut in as_completed(futures):
            ok, latency = fut.result()
            get_latencies.append(latency)
            if ok:
                get_ok += 1

    throughput = args.requests / post_elapsed if post_elapsed > 0 else 0.0

    print("\n=== STRESS TEST SUMMARY ===")
    print(f"POST success: {post_ok}/{args.requests} ({(post_ok / args.requests) * 100:.2f}%)")
    print(f"POST throughput: {throughput:.2f} req/s")
    print(f"POST latency ms: avg={statistics.mean(post_latencies):.2f}, p95={percentile(post_latencies, 95):.2f}, p99={percentile(post_latencies, 99):.2f}")

    print(f"PATCH success: {patch_ok}/{patch_sample} ({(patch_ok / max(patch_sample, 1)) * 100:.2f}%)")
    if patch_latencies:
        print(f"PATCH latency ms: avg={statistics.mean(patch_latencies):.2f}, p95={percentile(patch_latencies, 95):.2f}")

    print(f"GET success: {get_ok}/{get_rounds} ({(get_ok / max(get_rounds, 1)) * 100:.2f}%)")
    if get_latencies:
        print(f"GET latency ms: avg={statistics.mean(get_latencies):.2f}, p95={percentile(get_latencies, 95):.2f}")


if __name__ == "__main__":
    main()
