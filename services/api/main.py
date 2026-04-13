from __future__ import annotations

import json

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import ViolationEvent
from .schemas import ViolationCreate, ViolationRead, ViolationUpdateStatus


app = FastAPI(title="Littering MVP API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def root() -> str:
        return """
        <!doctype html>
        <html lang="en">
            <head>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <title>LitterCam | AI Traffic Intelligence</title>
                <style>
                    :root {
                        --bg: #070c14;
                        --bg-soft: #0f1826;
                        --glass: rgba(18, 28, 44, 0.58);
                        --glass-border: rgba(151, 179, 215, 0.24);
                        --text: #f4f8ff;
                        --muted: #a8b6cb;
                        --accent: #25d38e;
                        --accent-2: #1bb06d;
                        --warning: #ffbb4b;
                        --danger: #ff6f7f;
                        --shadow: rgba(0, 0, 0, 0.35);
                    }

                    * {
                        box-sizing: border-box;
                    }

                    html,
                    body {
                        margin: 0;
                        min-height: 100%;
                        background: radial-gradient(circle at top, #101d31 0%, var(--bg) 62%);
                        color: var(--text);
                        font-family: Candara, "Trebuchet MS", sans-serif;
                        scroll-behavior: smooth;
                    }

                    .container {
                        width: min(1160px, 94vw);
                        margin: 0 auto;
                    }

                    .glass {
                        background: var(--glass);
                        border: 1px solid var(--glass-border);
                        backdrop-filter: blur(10px);
                        box-shadow: 0 20px 42px var(--shadow);
                        border-radius: 16px;
                    }

                    .topbar {
                        position: sticky;
                        top: 10px;
                        z-index: 20;
                        margin: 10px auto 14px;
                        padding: 10px 14px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        gap: 14px;
                    }

                    .brand {
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        font-weight: 700;
                        letter-spacing: 0.02em;
                    }

                    .brand-chip {
                        width: 28px;
                        height: 28px;
                        border-radius: 8px;
                        display: grid;
                        place-items: center;
                        background: linear-gradient(140deg, #1cbf77, #22d59a);
                        color: #04110a;
                        font-size: 0.8rem;
                        font-weight: 800;
                    }

                    .top-links {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        flex-wrap: wrap;
                    }

                    .top-links a {
                        color: var(--muted);
                        text-decoration: none;
                        border: 1px solid rgba(154, 178, 209, 0.2);
                        border-radius: 9px;
                        padding: 8px 10px;
                        font-size: 0.86rem;
                        transition: all 150ms ease;
                    }

                    .top-links a:hover {
                        color: var(--text);
                        border-color: rgba(37, 211, 142, 0.45);
                    }

                    .hero {
                        position: relative;
                        overflow: hidden;
                        min-height: 74vh;
                        border-radius: 22px;
                        display: flex;
                        align-items: center;
                        margin-bottom: 18px;
                    }

                    .hero video {
                        position: absolute;
                        inset: 0;
                        width: 100%;
                        height: 100%;
                        object-fit: cover;
                        filter: blur(1px) brightness(0.42) saturate(1.05);
                        transform: scale(1.03);
                    }

                    .hero::before {
                        content: "";
                        position: absolute;
                        inset: 0;
                        background: linear-gradient(120deg, rgba(5, 10, 18, 0.87), rgba(11, 21, 36, 0.55));
                    }

                    .hero-content {
                        position: relative;
                        z-index: 2;
                        width: min(780px, 90%);
                        margin-left: 5%;
                    }

                    .tag {
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        border: 1px solid rgba(158, 184, 217, 0.3);
                        background: rgba(17, 30, 46, 0.44);
                        padding: 8px 12px;
                        border-radius: 999px;
                        color: #b9cadf;
                        font-size: 0.86rem;
                        margin-bottom: 16px;
                        animation: floatIn 650ms ease-out;
                    }

                    .hero h1 {
                        margin: 0;
                        font-size: clamp(1.9rem, 5vw, 3.4rem);
                        line-height: 1.06;
                        letter-spacing: 0.01em;
                        animation: floatIn 760ms ease-out;
                    }

                    .hero p {
                        margin: 14px 0 0;
                        color: #d9e4f5;
                        font-size: clamp(1rem, 2vw, 1.2rem);
                        max-width: 680px;
                        line-height: 1.5;
                        animation: floatIn 920ms ease-out;
                    }

                    .hero-cta {
                        margin-top: 22px;
                        display: flex;
                        flex-wrap: wrap;
                        gap: 10px;
                        animation: floatIn 1060ms ease-out;
                    }

                    .btn {
                        border: 1px solid transparent;
                        border-radius: 11px;
                        text-decoration: none;
                        font-weight: 700;
                        padding: 11px 15px;
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                    }

                    .btn.primary {
                        background: linear-gradient(130deg, var(--accent), #39f0ae);
                        color: #072314;
                    }

                    .btn.secondary {
                        border-color: rgba(177, 199, 228, 0.34);
                        color: var(--text);
                        background: rgba(19, 34, 53, 0.5);
                    }

                    .hero-metrics {
                        margin-top: 20px;
                        display: grid;
                        grid-template-columns: repeat(4, minmax(0, 1fr));
                        gap: 10px;
                        animation: floatIn 1220ms ease-out;
                    }

                    .metric {
                        background: rgba(12, 20, 34, 0.66);
                        border: 1px solid rgba(148, 173, 204, 0.25);
                        border-radius: 12px;
                        padding: 10px;
                    }

                    .metric .label {
                        color: #a5bad7;
                        font-size: 0.78rem;
                        text-transform: uppercase;
                        letter-spacing: 0.06em;
                    }

                    .metric .value {
                        margin-top: 6px;
                        font-size: 1.22rem;
                        font-weight: 700;
                    }

                    .section {
                        padding: 44px 0 16px;
                    }

                    .section h2 {
                        margin: 0;
                        font-size: clamp(1.45rem, 3vw, 2.25rem);
                    }

                    .section-sub {
                        margin: 10px 0 0;
                        color: var(--muted);
                        line-height: 1.6;
                        max-width: 860px;
                    }

                    .pipeline {
                        margin-top: 20px;
                        padding: 18px;
                    }

                    .pipeline-flow {
                        display: grid;
                        grid-template-columns: repeat(11, minmax(0, 1fr));
                        gap: 8px;
                        align-items: center;
                    }

                    .pipe-step {
                        grid-column: span 1;
                        min-height: 110px;
                        border-radius: 12px;
                        border: 1px solid rgba(149, 174, 204, 0.22);
                        background: rgba(10, 20, 33, 0.75);
                        padding: 10px;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        text-align: center;
                        gap: 7px;
                    }

                    .pipe-step .icon {
                        width: 30px;
                        height: 30px;
                        margin: 0 auto;
                        border-radius: 10px;
                        display: grid;
                        place-items: center;
                        background: rgba(37, 211, 142, 0.15);
                        color: #84f7c6;
                        font-size: 0.68rem;
                        font-weight: 800;
                    }

                    .pipe-step .title {
                        font-size: 0.78rem;
                        line-height: 1.25;
                        color: #deebfc;
                        font-weight: 600;
                    }

                    .pipe-arrow {
                        text-align: center;
                        color: #7ee9be;
                        font-size: 1.05rem;
                        font-weight: 700;
                    }

                    .how-grid {
                        margin-top: 16px;
                        display: grid;
                        grid-template-columns: repeat(3, minmax(0, 1fr));
                        gap: 10px;
                    }

                    .how-item {
                        padding: 14px;
                        border: 1px solid rgba(151, 177, 209, 0.2);
                        border-radius: 12px;
                        background: rgba(10, 18, 30, 0.76);
                    }

                    .how-item h3 {
                        margin: 0;
                        font-size: 0.98rem;
                    }

                    .how-item p {
                        margin: 8px 0 0;
                        color: var(--muted);
                        font-size: 0.9rem;
                        line-height: 1.45;
                    }

                    .demo-grid {
                        margin-top: 20px;
                        display: grid;
                        grid-template-columns: 1.45fr 0.95fr;
                        gap: 12px;
                    }

                    .panel {
                        padding: 16px;
                    }

                    .panel h3 {
                        margin: 0;
                        font-size: 1.02rem;
                    }

                    .video-wrap {
                        margin-top: 12px;
                        position: relative;
                        border-radius: 14px;
                        overflow: hidden;
                        border: 1px solid rgba(147, 172, 204, 0.24);
                        background: #02050b;
                    }

                    .video-wrap video {
                        width: 100%;
                        max-height: 360px;
                        background: #050a14;
                    }

                    .bbox {
                        position: absolute;
                        border: 2px solid #25d38e;
                        box-shadow: 0 0 0 1px rgba(37, 211, 142, 0.22);
                        border-radius: 8px;
                        animation: pulse 1.6s infinite;
                        pointer-events: none;
                    }

                    .bbox.one {
                        width: 28%;
                        height: 34%;
                        left: 18%;
                        top: 31%;
                    }

                    .bbox.two {
                        width: 20%;
                        height: 18%;
                        left: 58%;
                        top: 56%;
                        border-color: #ffbb4b;
                        box-shadow: 0 0 0 1px rgba(255, 187, 75, 0.3);
                    }

                    .overlay-tag {
                        position: absolute;
                        left: 18%;
                        top: 26%;
                        background: rgba(37, 211, 142, 0.88);
                        color: #052314;
                        font-size: 0.78rem;
                        font-weight: 700;
                        padding: 5px 8px;
                        border-radius: 8px;
                    }

                    .demo-controls {
                        margin-top: 10px;
                        display: flex;
                        flex-wrap: wrap;
                        gap: 10px;
                    }

                    .demo-controls input {
                        flex: 1 1 320px;
                        min-width: 240px;
                    }

                    .upload {
                        position: relative;
                        border-radius: 10px;
                        border: 1px solid rgba(156, 183, 216, 0.3);
                        padding: 10px 12px;
                        color: #d7e4f8;
                        cursor: pointer;
                        font-weight: 600;
                    }

                    .upload input {
                        position: absolute;
                        inset: 0;
                        opacity: 0;
                        cursor: pointer;
                    }

                    .integration-box {
                        margin-top: 12px;
                        padding: 12px;
                        border-radius: 12px;
                        border: 1px solid rgba(150, 175, 208, 0.2);
                        background: rgba(9, 18, 30, 0.72);
                    }

                    .integration-box h4 {
                        margin: 0 0 8px;
                        font-size: 0.92rem;
                    }

                    .token-row {
                        display: flex;
                        gap: 8px;
                        flex-wrap: wrap;
                        align-items: center;
                    }

                    .token-row input {
                        flex: 1 1 240px;
                        min-width: 180px;
                    }

                    .mini-note {
                        margin: 8px 0 0;
                        color: var(--muted);
                        font-size: 0.82rem;
                        line-height: 1.45;
                    }

                    .panel button,
                    .panel input,
                    .form-grid button,
                    .console button,
                    .console input,
                    .console select,
                    .form-grid input {
                        border-radius: 10px;
                        border: 1px solid rgba(154, 178, 210, 0.3);
                        background: rgba(18, 29, 45, 0.78);
                        color: var(--text);
                        font: inherit;
                        padding: 9px 10px;
                    }

                    .panel button,
                    .console button,
                    .form-grid button {
                        cursor: pointer;
                        font-weight: 700;
                    }

                    .panel button.primary,
                    .console button.primary,
                    .form-grid button.primary {
                        background: linear-gradient(120deg, var(--accent), #39f0ae);
                        color: #062214;
                        border-color: rgba(37, 211, 142, 0.7);
                    }

                    .console {
                        margin-top: 12px;
                        padding: 15px;
                    }

                    .console-head {
                        display: flex;
                        justify-content: space-between;
                        gap: 10px;
                        align-items: center;
                        flex-wrap: wrap;
                    }

                    .toolbar {
                        display: flex;
                        gap: 8px;
                        align-items: center;
                        flex-wrap: wrap;
                    }

                    .status-note {
                        margin: 8px 0 0;
                        color: var(--muted);
                        min-height: 1.2em;
                        font-size: 0.9rem;
                    }

                    .table-wrap {
                        overflow: auto;
                        margin-top: 10px;
                        border: 1px solid rgba(147, 174, 207, 0.18);
                        border-radius: 12px;
                    }

                    table {
                        width: 100%;
                        border-collapse: collapse;
                        min-width: 760px;
                    }

                    th,
                    td {
                        text-align: left;
                        padding: 10px 8px;
                        border-bottom: 1px solid rgba(137, 164, 196, 0.13);
                        font-size: 0.88rem;
                    }

                    th {
                        color: #9fb4d0;
                        text-transform: uppercase;
                        letter-spacing: 0.05em;
                        font-size: 0.75rem;
                    }

                    .row-actions {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 6px;
                    }

                    .row-actions button.warn {
                        color: var(--warning);
                    }

                    .row-actions button.danger {
                        color: var(--danger);
                    }

                    .form-grid {
                        margin-top: 10px;
                        display: grid;
                        grid-template-columns: repeat(6, minmax(0, 1fr));
                        gap: 8px;
                    }

                    .form-grid .wide {
                        grid-column: span 2;
                    }

                    .output {
                        margin-top: 12px;
                        display: grid;
                        gap: 8px;
                    }

                    .output-item {
                        border: 1px solid rgba(150, 176, 209, 0.2);
                        border-radius: 11px;
                        padding: 10px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        gap: 10px;
                        background: rgba(8, 16, 26, 0.78);
                    }

                    .output-item span {
                        color: var(--muted);
                    }

                    .output-item strong {
                        font-size: 0.95rem;
                    }

                    .cards {
                        margin-top: 18px;
                        display: grid;
                        grid-template-columns: repeat(4, minmax(0, 1fr));
                        gap: 10px;
                    }

                    .card-item {
                        padding: 16px;
                        border-radius: 14px;
                        border: 1px solid rgba(149, 173, 204, 0.22);
                        background: rgba(12, 21, 35, 0.74);
                    }

                    .card-item h3 {
                        margin: 0;
                        font-size: 1.02rem;
                    }

                    .card-item p,
                    .card-item li {
                        color: var(--muted);
                        margin: 8px 0 0;
                        line-height: 1.5;
                        font-size: 0.9rem;
                    }

                    .stack-grid {
                        margin-top: 16px;
                        display: grid;
                        grid-template-columns: repeat(3, minmax(0, 1fr));
                        gap: 10px;
                    }

                    .stack-grid .card-item ul {
                        padding-left: 18px;
                        margin: 8px 0 0;
                    }

                    .arch {
                        margin-top: 12px;
                        padding: 14px;
                        border-radius: 14px;
                        border: 1px solid rgba(145, 171, 203, 0.2);
                        background: rgba(10, 19, 31, 0.74);
                        display: flex;
                        flex-wrap: wrap;
                        gap: 8px;
                        align-items: center;
                        justify-content: center;
                    }

                    .arch-node {
                        padding: 9px 11px;
                        border-radius: 10px;
                        border: 1px solid rgba(148, 174, 206, 0.26);
                        background: rgba(18, 31, 49, 0.78);
                        font-size: 0.88rem;
                        font-weight: 700;
                    }

                    .arch-arrow {
                        color: #79edbd;
                        font-weight: 700;
                    }

                    .duo {
                        margin-top: 16px;
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 12px;
                    }

                    .chip-row {
                        margin-top: 12px;
                        display: flex;
                        flex-wrap: wrap;
                        gap: 8px;
                    }

                    .chip {
                        border: 1px solid rgba(150, 175, 206, 0.26);
                        border-radius: 999px;
                        padding: 8px 12px;
                        color: #cde0fb;
                        background: rgba(18, 30, 47, 0.72);
                        font-size: 0.86rem;
                        font-weight: 600;
                    }

                    .footer {
                        margin: 36px 0 26px;
                        color: #8499b8;
                        font-size: 0.86rem;
                        text-align: center;
                    }

                    @keyframes floatIn {
                        from {
                            opacity: 0;
                            transform: translateY(14px);
                        }
                        to {
                            opacity: 1;
                            transform: translateY(0);
                        }
                    }

                    @keyframes pulse {
                        0%,
                        100% {
                            opacity: 0.7;
                        }
                        50% {
                            opacity: 1;
                        }
                    }

                    @media (max-width: 980px) {
                        .hero-metrics {
                            grid-template-columns: repeat(2, minmax(0, 1fr));
                        }

                        .pipeline-flow {
                            grid-template-columns: repeat(3, minmax(0, 1fr));
                        }

                        .pipe-arrow {
                            display: none;
                        }

                        .pipe-step {
                            min-height: 96px;
                        }

                        .how-grid {
                            grid-template-columns: repeat(2, minmax(0, 1fr));
                        }

                        .demo-grid,
                        .duo,
                        .stack-grid,
                        .cards {
                            grid-template-columns: 1fr;
                        }

                        .form-grid {
                            grid-template-columns: repeat(2, minmax(0, 1fr));
                        }

                        .form-grid .wide {
                            grid-column: span 2;
                        }
                    }

                    @media (max-width: 640px) {
                        .topbar {
                            position: static;
                        }

                        .hero {
                            min-height: 68vh;
                        }

                        .hero-content {
                            margin: 0 auto;
                            width: 92%;
                        }

                        .form-grid {
                            grid-template-columns: 1fr;
                        }

                        .form-grid .wide {
                            grid-column: span 1;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <header class="topbar glass">
                        <div class="brand">
                            <span class="brand-chip">LC</span>
                            <span>LitterCam | AI Traffic Intelligence System</span>
                        </div>
                        <nav class="top-links">
                            <a href="#how-it-works">How It Works</a>
                            <a href="#demo">Live Demo</a>
                            <a href="#technology">Tech</a>
                            <a href="#ethics">Ethics</a>
                            <a href="/docs">API Docs</a>
                        </nav>
                    </header>

                    <section class="hero glass" id="hero">
                        <video autoplay muted loop playsinline>
                            <source src="https://samplelib.com/lib/preview/mp4/sample-5s.mp4" type="video/mp4" />
                        </video>
                        <div class="hero-content">
                            <span class="tag">Real-time civic enforcement intelligence</span>
                            <h1>AI-powered traffic monitoring for real-world violations</h1>
                            <p>Detect littering, unsafe driving, and public violations in real-time using computer vision. Built for smart cities, campuses, and enforcement systems.</p>
                            <div class="hero-cta">
                                <a class="btn primary" href="#demo">View Live Demo</a>
                                <a class="btn secondary" href="#how-it-works">See How It Works</a>
                            </div>
                            <div class="hero-metrics">
                                <article class="metric"><div class="label">Total Events</div><div class="value" id="mTotal">0</div></article>
                                <article class="metric"><div class="label">Pending Review</div><div class="value" id="mPending">0</div></article>
                                <article class="metric"><div class="label">Approved</div><div class="value" id="mApproved">0</div></article>
                                <article class="metric"><div class="label">Rejected</div><div class="value" id="mRejected">0</div></article>
                            </div>
                        </div>
                    </section>

                    <section class="section" id="how-it-works">
                        <h2>How It Works</h2>
                        <p class="section-sub">A deterministic pipeline designed for field reliability and auditability, not black-box magic.</p>
                        <div class="pipeline glass">
                            <div class="pipeline-flow">
                                <div class="pipe-step"><div class="icon">CAM</div><div class="title">Camera Feed</div></div>
                                <div class="pipe-arrow">-></div>
                                <div class="pipe-step"><div class="icon">DET</div><div class="title">Object Detection Model</div></div>
                                <div class="pipe-arrow">-></div>
                                <div class="pipe-step"><div class="icon">ACT</div><div class="title">Action Recognition Engine</div></div>
                                <div class="pipe-arrow">-></div>
                                <div class="pipe-step"><div class="icon">OCR</div><div class="title">License Plate Recognition</div></div>
                                <div class="pipe-arrow">-></div>
                                <div class="pipe-step"><div class="icon">VER</div><div class="title">Violation Verification Layer</div></div>
                                <div class="pipe-arrow">-></div>
                                <div class="pipe-step"><div class="icon">FINE</div><div class="title">Fine Generation System</div></div>
                            </div>
                        </div>
                        <div class="how-grid">
                            <article class="how-item glass"><h3>Camera Feed Input</h3><p>Real-time video streams from roadside or surveillance cameras.</p></article>
                            <article class="how-item glass"><h3>Object Detection</h3><p>Vehicles, people, and relevant objects are detected using trained CV models.</p></article>
                            <article class="how-item glass"><h3>Behavior Analysis</h3><p>Actions like litter throwing and rash movement patterns are identified over time.</p></article>
                            <article class="how-item glass"><h3>Number Plate Recognition</h3><p>OCR extraction maps events to vehicle identity for traceable enforcement.</p></article>
                            <article class="how-item glass"><h3>Verification Layer</h3><p>Human or AI-assisted validation happens before issuing a legal action.</p></article>
                            <article class="how-item glass"><h3>Fine Processing</h3><p>Violation reports are generated for integrated enforcement and dashboard systems.</p></article>
                        </div>
                    </section>

                    <section class="section" id="demo">
                        <h2>Live Demo Interaction</h2>
                        <p class="section-sub">People trust AI when they can see it working. Upload a clip, simulate detection, and monitor live events from the same screen.</p>
                        <div class="demo-grid">
                            <article class="panel glass">
                                <h3>Video Feed</h3>
                                <div class="video-wrap">
                                    <video id="demoVideo" controls muted playsinline>
                                        <source id="demoSource" src="https://filesamples.com/samples/video/mp4/sample_640x360.mp4" type="video/mp4" />
                                    </video>
                                    <div class="bbox one"></div>
                                    <div class="bbox two"></div>
                                    <div class="overlay-tag">LITTER DETECTED</div>
                                </div>
                                <div class="demo-controls">
                                    <label class="upload">Upload Demo Video
                                        <input id="videoUpload" type="file" accept="video/*" />
                                    </label>
                                    <input id="streamUrlInput" type="url" placeholder="https://your-cctv-gateway/live/cam-01.m3u8 or .mp4" />
                                    <button id="loadStreamBtn" type="button">Connect Live Stream</button>
                                    <button id="resetDemoVideoBtn" type="button">Use Default Feed</button>
                                    <button id="simulateBtn" class="primary" type="button">Run Detection Simulation</button>
                                    <a class="btn secondary" href="/docs">Try Endpoints</a>
                                </div>
                                <p class="mini-note">For CCTV integrations use HTTPS HLS or MP4 gateway URLs. Raw RTSP links are not directly playable in browsers.</p>
                            </article>
                            <article class="panel glass">
                                <h3>Detection Output</h3>
                                <div class="output">
                                    <div class="output-item"><span>Detected:</span><strong id="detectedLabel">Littering</strong></div>
                                    <div class="output-item"><span>Vehicle:</span><strong id="vehicleLabel">DL01AB1234</strong></div>
                                    <div class="output-item"><span>Confidence:</span><strong id="confidenceLabel">92%</strong></div>
                                    <div class="output-item"><span>Event ID:</span><strong id="eventLabel">-</strong></div>
                                    <div class="output-item"><span>Review Status:</span><strong id="reviewLabel">PENDING</strong></div>
                                </div>
                                <div class="integration-box">
                                    <h4>API Access Key</h4>
                                    <div class="token-row">
                                        <input id="apiKeyInput" type="password" placeholder="Enter your API key" />
                                        <button id="saveApiKeyBtn" class="primary" type="button">Save Key</button>
                                        <button id="resetApiKeyBtn" type="button">Use Default Key</button>
                                    </div>
                                    <p class="mini-note" id="apiKeyHint"></p>
                                </div>
                            </article>
                        </div>

                        <section class="console glass">
                            <div class="console-head">
                                <h3>Violation Console</h3>
                                <div class="toolbar">
                                    <label for="statusFilter">Status</label>
                                    <select id="statusFilter">
                                        <option value="">All</option>
                                        <option value="PENDING">Pending</option>
                                        <option value="APPROVED">Approved</option>
                                        <option value="REJECTED">Rejected</option>
                                    </select>
                                    <button id="refreshBtn" class="primary" type="button">Refresh</button>
                                </div>
                            </div>
                            <p class="status-note" id="statusText">Ready</p>
                            <div class="table-wrap">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Event ID</th>
                                            <th>Status</th>
                                            <th>Plate</th>
                                            <th>Violation</th>
                                            <th>Confidence</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="rows"></tbody>
                                </table>
                            </div>
                            <form id="createForm" class="form-grid">
                                <input id="eventId" placeholder="event_id (optional)" />
                                <input id="trackId" type="number" value="1" placeholder="vehicle_track_id" required />
                                <input id="detConf" type="number" step="0.01" value="0.92" placeholder="detection_confidence" required />
                                <input id="plateText" value="DL01AB1234" placeholder="plate_text" />
                                <input id="sourceVideo" class="wide" value="demo_feed.mp4" placeholder="source_video" required />
                                <input id="imagePath" class="wide" value="/tmp/frame.jpg" placeholder="image_path" required />
                                <button class="primary" type="submit">Create Test Violation</button>
                            </form>
                        </section>
                    </section>

                    <section class="section" id="technology">
                        <h2>Technology Behind LitterCam</h2>
                        <div class="stack-grid">
                            <article class="card-item glass">
                                <h3>Computer Vision</h3>
                                <ul>
                                    <li>YOLOv8 for object detection</li>
                                    <li>OpenCV for stream and frame operations</li>
                                </ul>
                            </article>
                            <article class="card-item glass">
                                <h3>Action Detection + OCR</h3>
                                <ul>
                                    <li>Temporal behavior logic for violations</li>
                                    <li>EasyOCR-based plate extraction</li>
                                </ul>
                            </article>
                            <article class="card-item glass">
                                <h3>Backend + Deployment</h3>
                                <ul>
                                    <li>FastAPI APIs with event lifecycle controls</li>
                                    <li>Edge + cloud-friendly deployment model</li>
                                </ul>
                            </article>
                        </div>
                        <div class="arch glass">
                            <span class="arch-node">Camera</span>
                            <span class="arch-arrow">-></span>
                            <span class="arch-node">Edge Processing</span>
                            <span class="arch-arrow">-></span>
                            <span class="arch-node">Cloud API</span>
                            <span class="arch-arrow">-></span>
                            <span class="arch-node">Dashboard</span>
                        </div>
                    </section>

                    <section class="section" id="use-cases">
                        <h2>Where This Can Be Used</h2>
                        <div class="cards">
                            <article class="card-item glass"><h3>Smart Cities</h3><p>Monitor littering and public behavior at scale with auditable workflows.</p></article>
                            <article class="card-item glass"><h3>Highways</h3><p>Detect unsafe driving patterns and improve traffic risk visibility.</p></article>
                            <article class="card-item glass"><h3>College Campuses</h3><p>Automate cleanliness and compliance operations with less manpower.</p></article>
                            <article class="card-item glass"><h3>Toll Booths</h3><p>Integrate with existing camera infrastructure for fast rollout.</p></article>
                        </div>
                    </section>

                    <section class="section" id="business">
                        <h2>Business Model</h2>
                        <div class="duo">
                            <article class="card-item glass">
                                <h3>Revenue Approach</h3>
                                <ul>
                                    <li>SaaS-based pricing per camera stream</li>
                                    <li>Integration with municipal fine systems</li>
                                    <li>API access for third-party platforms</li>
                                    <li>Analytics dashboard subscriptions for authorities</li>
                                </ul>
                                <p><strong>Indicative pricing:</strong> INR 500 to INR 2000 per camera per month.</p>
                            </article>
                            <article class="card-item glass" id="story">
                                <h3>Why I Built This</h3>
                                <p>Built after participating in multiple AI hackathons where it became clear that AI can solve civic problems beyond chatbot experiences. Littering and traffic violations are everywhere, while enforcement remains weak. This system is focused on practical automation with accountability.</p>
                            </article>
                        </div>
                    </section>

                    <section class="section" id="ethics">
                        <h2>Ethics and Compliance</h2>
                        <div class="cards">
                            <article class="card-item glass"><h3>Human Verification</h3><p>Every action can be reviewed before any fine is issued.</p></article>
                            <article class="card-item glass"><h3>Privacy First</h3><p>Data handling is designed for minimum exposure and operational necessity.</p></article>
                            <article class="card-item glass"><h3>No Unauthorized Face ID</h3><p>No facial recognition is used without explicit legal and consent frameworks.</p></article>
                            <article class="card-item glass"><h3>Government-Authorized Use</h3><p>Designed for authorized civic and enforcement use cases only.</p></article>
                        </div>
                    </section>

                    <section class="section" id="scale">
                        <h2>One system. Multiple violations. Real-time enforcement.</h2>
                        <p class="section-sub">Repositioned from single-use litter detection to an extensible AI Traffic Intelligence System.</p>
                        <div class="chip-row">
                            <span class="chip">Helmet Detection</span>
                            <span class="chip">Seatbelt Detection</span>
                            <span class="chip">Rash Driving Detection</span>
                            <span class="chip">Noise Pollution Monitoring</span>
                        </div>
                    </section>

                    <p class="footer">LitterCam MVP | Real-world civic intelligence built with computer vision and verifiable enforcement workflow.</p>
                </div>

                <script>
                    const rowsEl = document.getElementById("rows");
                    const statusText = document.getElementById("statusText");
                    const statusFilter = document.getElementById("statusFilter");
                    const refreshBtn = document.getElementById("refreshBtn");
                    const createForm = document.getElementById("createForm");
                    const simulateBtn = document.getElementById("simulateBtn");
                    const videoUpload = document.getElementById("videoUpload");
                    const demoVideo = document.getElementById("demoVideo");
                    const streamUrlInput = document.getElementById("streamUrlInput");
                    const loadStreamBtn = document.getElementById("loadStreamBtn");
                    const resetDemoVideoBtn = document.getElementById("resetDemoVideoBtn");
                    const apiKeyInput = document.getElementById("apiKeyInput");
                    const saveApiKeyBtn = document.getElementById("saveApiKeyBtn");
                    const resetApiKeyBtn = document.getElementById("resetApiKeyBtn");
                    const apiKeyHint = document.getElementById("apiKeyHint");
                    const DEFAULT_DEMO_VIDEO_URL = "https://filesamples.com/samples/video/mp4/sample_640x360.mp4";
                    const DEFAULT_API_KEY = "LITTERCAM_DEMO_KEY";
                    const API_KEY_STORAGE = "littercam_api_key";
                    let localRows = [];

                    function showStatus(message) {
                        statusText.textContent = message;
                    }

                    function currentApiKey() {
                        const key = String(apiKeyInput.value || "").trim();
                        return key || DEFAULT_API_KEY;
                    }

                    function updateApiKeyHint() {
                        const isDefault = currentApiKey() === DEFAULT_API_KEY;
                        apiKeyHint.textContent = isDefault
                            ? "Using default key for first-time access. Add your own key for private integrations."
                            : "Custom API key active for this browser session.";
                    }

                    function initializeApiKey() {
                        const storedKey = localStorage.getItem(API_KEY_STORAGE);
                        if (storedKey && String(storedKey).trim()) {
                            apiKeyInput.value = String(storedKey).trim();
                        } else {
                            apiKeyInput.value = DEFAULT_API_KEY;
                            localStorage.setItem(API_KEY_STORAGE, DEFAULT_API_KEY);
                        }
                        updateApiKeyHint();
                    }

                    function persistApiKey() {
                        localStorage.setItem(API_KEY_STORAGE, currentApiKey());
                        updateApiKeyHint();
                    }

                    async function apiFetch(url, options = {}) {
                        const nextOptions = { ...options };
                        nextOptions.headers = {
                            ...(options.headers || {}),
                            "x-api-key": currentApiKey(),
                        };
                        return fetch(url, nextOptions);
                    }

                    function randomPlate() {
                        const number = Math.floor(Math.random() * 9000) + 1000;
                        return "DL01AB" + String(number);
                    }

                    function toPercent(value) {
                        return Math.round(Number(value || 0) * 100) + "%";
                    }

                    function setMetrics(rows) {
                        const counts = { total: rows.length, PENDING: 0, APPROVED: 0, REJECTED: 0 };
                        rows.forEach((row) => {
                            const key = String(row.status || "").toUpperCase();
                            if (counts[key] !== undefined) {
                                counts[key] += 1;
                            }
                        });
                        document.getElementById("mTotal").textContent = String(counts.total);
                        document.getElementById("mPending").textContent = String(counts.PENDING);
                        document.getElementById("mApproved").textContent = String(counts.APPROVED);
                        document.getElementById("mRejected").textContent = String(counts.REJECTED);
                    }

                    function setDetectionOutput(row) {
                        if (!row) {
                            return;
                        }
                        const detected = row.violation_type || "LITTERING_CANDIDATE";
                        document.getElementById("detectedLabel").textContent = detected.replaceAll("_", " ");
                        document.getElementById("vehicleLabel").textContent = row.plate_text || "UNKNOWN";
                        document.getElementById("confidenceLabel").textContent = toPercent(row.detection_confidence || 0.0);
                        document.getElementById("eventLabel").textContent = row.event_id || "-";
                        document.getElementById("reviewLabel").textContent = row.status || "PENDING";
                    }

                    function normalizeRows(rows) {
                        return [...rows].sort((a, b) => Number(b.timestamp_ms || 0) - Number(a.timestamp_ms || 0));
                    }

                    function getVisibleRows() {
                        const selected = statusFilter.value;
                        if (!selected) {
                            return normalizeRows(localRows);
                        }
                        return normalizeRows(localRows.filter((row) => String(row.status || "").toUpperCase() === selected));
                    }

                    function renderRows(rows) {
                        rowsEl.innerHTML = "";
                        if (!rows.length) {
                            const tr = document.createElement("tr");
                            const td = document.createElement("td");
                            td.colSpan = 6;
                            td.textContent = "No violations found yet.";
                            tr.appendChild(td);
                            rowsEl.appendChild(tr);
                            return;
                        }

                        rows.forEach((row) => {
                            const tr = document.createElement("tr");

                            const eventId = document.createElement("td");
                            eventId.textContent = row.event_id;
                            tr.appendChild(eventId);

                            const status = document.createElement("td");
                            status.textContent = row.status;
                            tr.appendChild(status);

                            const plate = document.createElement("td");
                            plate.textContent = row.plate_text || "-";
                            tr.appendChild(plate);

                            const type = document.createElement("td");
                            type.textContent = (row.violation_type || "-").replaceAll("_", " ");
                            tr.appendChild(type);

                            const conf = document.createElement("td");
                            conf.textContent = toPercent(row.detection_confidence || 0.0);
                            tr.appendChild(conf);

                            const action = document.createElement("td");
                            const rowActions = document.createElement("div");
                            rowActions.className = "row-actions";

                            const approveBtn = document.createElement("button");
                            approveBtn.type = "button";
                            approveBtn.className = "primary";
                            approveBtn.textContent = "Approve";
                            approveBtn.onclick = () => updateStatus(row.event_id, "APPROVED");

                            const rejectBtn = document.createElement("button");
                            rejectBtn.type = "button";
                            rejectBtn.className = "danger";
                            rejectBtn.textContent = "Reject";
                            rejectBtn.onclick = () => updateStatus(row.event_id, "REJECTED");

                            const pendingBtn = document.createElement("button");
                            pendingBtn.type = "button";
                            pendingBtn.className = "warn";
                            pendingBtn.textContent = "Pending";
                            pendingBtn.onclick = () => updateStatus(row.event_id, "PENDING");

                            rowActions.appendChild(approveBtn);
                            rowActions.appendChild(rejectBtn);
                            rowActions.appendChild(pendingBtn);
                            action.appendChild(rowActions);
                            tr.appendChild(action);

                            tr.onclick = () => setDetectionOutput(row);
                            rowsEl.appendChild(tr);
                        });

                        setDetectionOutput(rows[0]);
                    }

                    async function fetchViolations() {
                        const status = statusFilter.value;
                        const query = status ? "?status=" + encodeURIComponent(status) + "&limit=200" : "?limit=200";
                        showStatus("Loading violations...");
                        try {
                            const response = await apiFetch("/violations" + query);
                            if (!response.ok) {
                                throw new Error("Unable to load violations");
                            }
                            const serverRows = await response.json();

                            if (serverRows.length) {
                                localRows = normalizeRows(serverRows);
                            }

                            const visibleRows = getVisibleRows();
                            renderRows(visibleRows);
                            setMetrics(localRows);
                            showStatus("Loaded " + visibleRows.length + " records.");
                        } catch (error) {
                            if (localRows.length) {
                                const visibleRows = getVisibleRows();
                                renderRows(visibleRows);
                                setMetrics(localRows);
                                showStatus("Using local session data. Sync error: " + error.message);
                            } else {
                                showStatus("Error: " + error.message);
                            }
                        }
                    }

                    async function updateStatus(eventId, nextStatus) {
                        showStatus("Updating " + eventId + "...");
                        try {
                            const response = await apiFetch("/violations/" + encodeURIComponent(eventId) + "/status", {
                                method: "PATCH",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ status: nextStatus, review_note: "updated from web console" }),
                            });
                            if (!response.ok) {
                                const text = await response.text();
                                throw new Error(text || "Status update failed");
                            }

                            localRows = localRows.map((row) => {
                                if (row.event_id === eventId) {
                                    return { ...row, status: nextStatus };
                                }
                                return row;
                            });

                            await fetchViolations();
                        } catch (error) {
                            showStatus("Update failed: " + error.message);
                        }
                    }

                    async function createViolation(payload) {
                        const response = await apiFetch("/violations", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify(payload),
                        });
                        if (!response.ok) {
                            const text = await response.text();
                            throw new Error(text || "Create request failed");
                        }
                        return response.json();
                    }

                    createForm.addEventListener("submit", async (event) => {
                        event.preventDefault();
                        const now = Date.now();
                        const eventId = document.getElementById("eventId").value || "web-" + now;
                        const payload = {
                            event_id: eventId,
                            violation_type: "LITTERING_CANDIDATE",
                            vehicle_track_id: Number(document.getElementById("trackId").value || 1),
                            plate_text: document.getElementById("plateText").value || "UNKNOWN",
                            plate_confidence: 0.0,
                            detection_confidence: Number(document.getElementById("detConf").value || 0.92),
                            timestamp_ms: now,
                            camera_id: "cam-web",
                            source_video: document.getElementById("sourceVideo").value || "demo_feed.mp4",
                            image_path: document.getElementById("imagePath").value || "/tmp/frame.jpg",
                            clip_path: "",
                            metadata_json: { created_from: "landing-page" },
                        };

                        showStatus("Creating violation event...");
                        try {
                            const result = await createViolation(payload);
                            localRows = normalizeRows([result, ...localRows.filter((row) => row.event_id !== result.event_id)]);
                            setDetectionOutput(result);
                            await fetchViolations();
                            showStatus("Violation created successfully.");
                        } catch (error) {
                            showStatus("Create failed: " + error.message);
                        }
                    });

                    simulateBtn.addEventListener("click", async () => {
                        const now = Date.now();
                        const payload = {
                            event_id: "sim-" + now,
                            violation_type: "LITTERING_CANDIDATE",
                            vehicle_track_id: 1,
                            plate_text: randomPlate(),
                            plate_confidence: 0.91,
                            detection_confidence: 0.92,
                            timestamp_ms: now,
                            camera_id: "cam-demo",
                            source_video: "simulation.mp4",
                            image_path: "/tmp/sim-frame.jpg",
                            clip_path: "",
                            metadata_json: { simulated: true },
                        };

                        showStatus("Running detection simulation...");
                        try {
                            const result = await createViolation(payload);
                            localRows = normalizeRows([result, ...localRows.filter((row) => row.event_id !== result.event_id)]);
                            setDetectionOutput(result);
                            await fetchViolations();
                            showStatus("Simulation completed and saved.");
                        } catch (error) {
                            showStatus("Simulation failed: " + error.message);
                        }
                    });

                    videoUpload.addEventListener("change", (event) => {
                        const file = event.target.files && event.target.files[0];
                        if (!file) {
                            return;
                        }
                        const objectUrl = URL.createObjectURL(file);
                        demoVideo.src = objectUrl;
                        streamUrlInput.value = "";
                        demoVideo.play().catch(() => {});
                        showStatus("Loaded local demo video: " + file.name);
                    });

                    loadStreamBtn.addEventListener("click", () => {
                        const streamUrl = String(streamUrlInput.value || "").trim();
                        if (!streamUrl) {
                            showStatus("Enter an HTTPS stream URL to connect CCTV feed.");
                            return;
                        }
                        const isHttpStream =
                            streamUrl.startsWith("https://") || streamUrl.startsWith("http://");
                        if (!isHttpStream) {
                            showStatus("Stream URL must start with http:// or https://.");
                            return;
                        }

                        demoVideo.src = streamUrl;
                        demoVideo.load();
                        demoVideo
                            .play()
                            .then(() => showStatus("Connected to live stream source."))
                            .catch(() => showStatus("Stream loaded. Press play if browser blocked autoplay."));
                    });

                    resetDemoVideoBtn.addEventListener("click", () => {
                        demoVideo.src = DEFAULT_DEMO_VIDEO_URL;
                        streamUrlInput.value = "";
                        demoVideo.load();
                        showStatus("Switched to default demo feed.");
                    });

                    saveApiKeyBtn.addEventListener("click", () => {
                        persistApiKey();
                        showStatus("API key saved for this browser.");
                    });

                    resetApiKeyBtn.addEventListener("click", () => {
                        apiKeyInput.value = DEFAULT_API_KEY;
                        persistApiKey();
                        showStatus("Reverted to default API key.");
                    });

                    apiKeyInput.addEventListener("input", updateApiKeyHint);

                    refreshBtn.addEventListener("click", fetchViolations);
                    statusFilter.addEventListener("change", fetchViolations);
                    initializeApiKey();
                    fetchViolations();
                </script>
            </body>
        </html>
        """


def _row_to_response(row: ViolationEvent) -> ViolationEvent:
    if isinstance(row.metadata_json, str):
        row.metadata_json = json.loads(row.metadata_json or "{}")
    return row


@app.post("/violations", response_model=ViolationRead)
def create_violation(payload: ViolationCreate, db: Session = Depends(get_db)):
    existing = db.query(ViolationEvent).filter(ViolationEvent.event_id == payload.event_id).first()
    if existing:
        return _row_to_response(existing)

    event = ViolationEvent(
        event_id=payload.event_id,
        violation_type=payload.violation_type,
        vehicle_track_id=payload.vehicle_track_id,
        plate_text=payload.plate_text,
        plate_confidence=payload.plate_confidence,
        detection_confidence=payload.detection_confidence,
        timestamp_ms=payload.timestamp_ms,
        camera_id=payload.camera_id,
        source_video=payload.source_video,
        image_path=payload.image_path,
        clip_path=payload.clip_path,
        metadata_json=json.dumps(payload.metadata_json),
        status="PENDING",
    )

    db.add(event)
    db.commit()
    db.refresh(event)
    return _row_to_response(event)


@app.get("/violations", response_model=list[ViolationRead])
def list_violations(
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(ViolationEvent)
    if status:
        query = query.filter(ViolationEvent.status == status.upper())

    rows = query.order_by(ViolationEvent.created_at.desc()).limit(limit).all()
    return [_row_to_response(row) for row in rows]


@app.patch("/violations/{event_id}/status", response_model=ViolationRead)
def update_status(event_id: str, payload: ViolationUpdateStatus, db: Session = Depends(get_db)):
    row = db.query(ViolationEvent).filter(ViolationEvent.event_id == event_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Violation not found")

    next_status = payload.status.upper()
    if next_status not in {"PENDING", "APPROVED", "REJECTED"}:
        raise HTTPException(status_code=400, detail="Invalid status")

    row.status = next_status
    row.review_note = payload.review_note
    db.commit()
    db.refresh(row)
    return _row_to_response(row)
