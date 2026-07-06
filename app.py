import html as _html
import base64
import json
import os
import re
import secrets as _secrets
from copy import deepcopy
from datetime import datetime
from typing import Any, Optional

import streamlit as st

try:
    import pdfplumber as _pdfplumber
except ImportError:
    _pdfplumber = None  # type: ignore

APP_TITLE = "MedQuiz: NEET PG Prep"
ADMIN_QUERY_TOKEN = "admin"
PUBLIC_QUERY_TOKEN = "public"
HISTORY_QUERY_TOKEN = "history"
ATTEMPTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quiz_attempts.json")
QUIZZES_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quizzes.json")
USER_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data.json")
FEEDBACK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quiz_feedback.json")
_LOCAL_ENV_CACHE: Optional[dict[str, str]] = None
NEET_SUBJECTS = [
    "Anatomy",
    "Physiology",
    "Biochemistry",
    "Pathology",
    "Pharmacology",
    "Microbiology",
    "Forensic Medicine",
    "Community Medicine / PSM",
    "Medicine",
    "Dermatology",
    "Psychiatry",
    "Pediatrics",
    "Surgery",
    "Orthopedics",
    "Anesthesia",
    "Radiology",
    "Obstetrics and Gynecology",
    "Ophthalmology",
    "ENT",
]


def get_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default
    return os.getenv(name, value)


def _load_local_env_values() -> dict[str, str]:
    global _LOCAL_ENV_CACHE
    if _LOCAL_ENV_CACHE is not None:
        return _LOCAL_ENV_CACHE

    values: dict[str, str] = {}
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for filename in (".env",):
        path = os.path.join(base_dir, filename)
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r") as env_file:
                for raw_line in env_file:
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key:
                        values[key] = value
        except Exception:
            pass

    _LOCAL_ENV_CACHE = values
    return values


def _get_env_config(*names: str) -> str:
    local_values = _load_local_env_values()
    for name in names:
        value = os.getenv(name) or local_values.get(name, "")
        if value:
            return value
    return ""


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #050003;
            --surface: #0f0108;
            --surface-strong: #1a020b;
            --ink: #f8f0f0;
            --muted: #c4a0a8;
            --line: rgba(220, 20, 60, 0.18);
            --primary: #dc143c;
            --primary-dark: #a50e2d;
            --accent: #ff6b6b;
            --soft: rgba(220, 20, 60, 0.12);
            --danger: #ff3366;
        }

        html, body, [class*="css"] {
            font-family: "Aptos", "Segoe UI", sans-serif;
            color: var(--ink);
        }

        .stApp {
            background:
                radial-gradient(circle at 18% 8%, rgba(220, 20, 60, 0.22), transparent 28rem),
                radial-gradient(circle at 86% 18%, rgba(180, 10, 50, 0.16), transparent 25rem),
                linear-gradient(180deg, #050003 0%, #0c0006 48%, #040002 100%);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 1.5rem;
            padding-bottom: 4rem;
        }

        header[data-testid="stHeader"],
        div[data-testid="stDecoration"],
        #MainMenu { display: none; }

        h1, h2, h3 {
            letter-spacing: 0;
            color: var(--ink);
        }

        div[data-testid="stToolbar"] { display: none; }

        .top-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
            gap: 1rem;
        }

        .brand-mark {
            color: var(--ink);
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-size: 0.86rem;
        }

        .top-nav-spacer { flex: 1; }

        .hero {
            background: linear-gradient(135deg, #173f35 0%, #245244 54%, #74512e 100%);
            color: #fffaf0;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 18px 45px rgba(40, 33, 22, 0.18);
            margin-bottom: 1.25rem;
        }

        .hero h1 {
            color: #fffaf0;
            font-size: clamp(2rem, 4vw, 3.5rem);
            line-height: 1.04;
            margin-bottom: 0.65rem;
        }

        .hero p {
            color: rgba(255, 250, 240, 0.82);
            max-width: 760px;
            font-size: 1.05rem;
            line-height: 1.6;
        }

        .dashboard-shell {
            position: relative;
            overflow: hidden;
            min-height: 580px;
            border: 1px solid var(--line);
            border-radius: 14px;
            background:
                radial-gradient(circle at 76% 24%, rgba(220, 20, 60, 0.22), transparent 17rem),
                radial-gradient(circle at 88% 72%, rgba(180, 10, 50, 0.16), transparent 18rem),
                linear-gradient(135deg, rgba(15, 1, 8, 0.96), rgba(5, 0, 3, 0.92));
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.05), 0 30px 80px rgba(0,0,0,0.35);
            padding: 3.2rem 2.25rem 2rem;
        }

        .dashboard-panel {
            position: relative;
            z-index: 2;
            width: min(680px, 62%);
            padding: 1rem 0 1.6rem;
        }

        .dashboard-panel h1 {
            font-size: clamp(2.8rem, 7vw, 5.8rem);
            line-height: 0.95;
            margin: 0 0 0.85rem;
            max-width: 780px;
        }

        .dashboard-panel p {
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.65;
            max-width: 660px;
        }

        .dashboard-copy {
            margin-top: 1rem;
            color: var(--muted);
            max-width: 700px;
            line-height: 1.65;
        }

        .eyebrow {
            color: var(--primary);
            font-weight: 800;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            font-size: 0.78rem;
            margin-bottom: 0.9rem;
        }

        .landing-metrics {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            max-width: 720px;
            margin: 1.35rem 0 0;
        }

        .landing-metric {
            background: rgba(255,255,255,0.055);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.75rem;
        }

        .landing-metric strong {
            color: var(--ink);
            display: block;
            font-size: 1.1rem;
            margin-bottom: 0.18rem;
        }

        .landing-metric span {
            color: var(--muted);
            font-size: 0.88rem;
        }

        .motion-stage {
            position: absolute;
            inset: 0;
            pointer-events: none;
        }

        .med-orbit {
            position: absolute;
            right: 7%;
            top: 12%;
            width: min(360px, 34vw);
            aspect-ratio: 1;
            border-radius: 50%;
            border: 1px solid rgba(220, 20, 60, 0.20);
            background:
                radial-gradient(circle at 50% 48%, rgba(220, 20, 60, 0.16) 0 18%, transparent 19%),
                conic-gradient(from 20deg, rgba(220,20,60,0.08), rgba(180,10,50,0.22), rgba(220,20,60,0.08));
            filter: drop-shadow(0 24px 80px rgba(0,0,0,0.38));
            animation: slowSpin 28s linear infinite;
        }

        .doctor-figure {
            position: absolute;
            right: 16%;
            top: 28%;
            width: 92px;
            height: 150px;
            animation: floatDrift 7s ease-in-out infinite;
        }

        .doctor-figure::before {
            content: "";
            position: absolute;
            left: 28px;
            top: 0;
            width: 42px;
            height: 42px;
            border-radius: 50%;
            background: #f0c39a;
            box-shadow: 0 48px 0 18px #f8f3ec, 0 102px 0 12px #202437;
        }

        .doctor-figure::after {
            content: "";
            position: absolute;
            left: 41px;
            top: 64px;
            width: 22px;
            height: 22px;
            background:
                linear-gradient(#d44848, #d44848) center / 100% 34% no-repeat,
                linear-gradient(#d44848, #d44848) center / 34% 100% no-repeat;
            border-radius: 3px;
        }

        .leaf {
            position: absolute;
            width: 64px;
            height: 30px;
            border-radius: 64px 6px 64px 6px;
            background: linear-gradient(135deg, rgba(220, 60, 80, 0.90), rgba(140, 10, 35, 0.72));
            transform-origin: 10% 50%;
            box-shadow: 0 12px 36px rgba(0,0,0,0.32);
            animation: leafFloat 9s ease-in-out infinite;
        }

        .leaf-one { right: 34%; top: 18%; transform: rotate(-28deg); animation-delay: -1s; }
        .leaf-two { right: 7%; top: 61%; transform: rotate(20deg); animation-delay: -4s; }
        .leaf-three { right: 26%; bottom: 13%; transform: rotate(-8deg); animation-delay: -6s; }

        .flower {
            position: absolute;
            width: 72px;
            height: 72px;
            border-radius: 50%;
            background:
                radial-gradient(circle, #ff8080 0 16%, transparent 17%),
                radial-gradient(circle at 50% 0%, rgba(220,20,60,0.92) 0 18%, transparent 19%),
                radial-gradient(circle at 100% 50%, rgba(200,10,50,0.88) 0 18%, transparent 19%),
                radial-gradient(circle at 50% 100%, rgba(220,20,60,0.92) 0 18%, transparent 19%),
                radial-gradient(circle at 0% 50%, rgba(200,10,50,0.88) 0 18%, transparent 19%);
            animation: flowerBob 8s ease-in-out infinite;
        }

        .flower-one { right: 6%; top: 18%; }
        .flower-two { right: 31%; bottom: 18%; animation-delay: -3s; transform: scale(0.75); }

        .pulse-node {
            position: absolute;
            width: 9px;
            height: 9px;
            border-radius: 999px;
            background: var(--primary);
            box-shadow: 0 0 0 0 rgba(220,20,60,0.55);
            animation: pulseNode 2.8s ease-out infinite;
        }

        .node-one { left: 12%; top: 28%; }
        .node-two { right: 28%; top: 38%; animation-delay: -1.1s; }
        .node-three { right: 8%; bottom: 28%; animation-delay: -2s; }

        .feature-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
            margin-top: 1.25rem;
        }

        .feature-tile {
            background: rgba(17, 24, 39, 0.86);
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: 1rem;
        }

        .feature-tile h3 {
            font-size: 1rem;
            margin-bottom: 0.4rem;
        }

        .feature-tile p {
            color: var(--muted);
            line-height: 1.5;
            margin: 0;
        }

        .app-topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
            padding: 0.2rem 0.1rem;
        }

        .app-brand {
            color: rgba(248,240,240,0.92);
            font-weight: 900;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            font-size: 0.78rem;
        }

        .app-nav-link {
            color: rgba(248,240,240,0.58);
            font-size: 0.78rem;
            text-decoration: none;
            border: 1px solid rgba(220,20,60,0.22);
            padding: 0.34rem 0.8rem;
            border-radius: 6px;
            background: rgba(255,255,255,0.035);
            letter-spacing: 0.04em;
            white-space: nowrap;
        }

        .user-hero {
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(220,20,60,0.22);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 1rem;
            background:
                linear-gradient(115deg, rgba(20,2,10,0.96), rgba(6,0,4,0.94) 54%, rgba(76,7,23,0.62)),
                radial-gradient(circle at 84% 18%, rgba(255,107,107,0.18), transparent 18rem);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.055), 0 28px 70px rgba(0,0,0,0.30);
        }

        .user-hero::after {
            content: "";
            position: absolute;
            right: -7rem;
            top: -9rem;
            width: 26rem;
            height: 26rem;
            border-radius: 50%;
            border: 1px solid rgba(220,20,60,0.25);
            background: conic-gradient(from 30deg, rgba(220,20,60,0.02), rgba(220,20,60,0.18), rgba(220,20,60,0.02));
            pointer-events: none;
        }

        .user-hero-content {
            position: relative;
            z-index: 1;
            max-width: 760px;
        }

        .user-hero h1 {
            font-size: clamp(2rem, 5vw, 4.2rem);
            line-height: 0.98;
            margin: 0.25rem 0 0.55rem;
        }

        .user-hero p {
            color: var(--muted);
            margin: 0;
            line-height: 1.6;
        }

        .section-kicker {
            color: var(--primary);
            font-size: 0.72rem;
            font-weight: 850;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin: 1.25rem 0 0.3rem;
        }

        .section-title {
            margin: 0 0 0.7rem;
            font-size: 1.22rem;
            letter-spacing: 0;
        }

        .insight-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.055), rgba(255,255,255,0.025));
            border: 1px solid rgba(220,20,60,0.18);
            border-radius: 10px;
            padding: 1rem;
            min-height: 100%;
        }

        .insight-card strong {
            display: block;
            margin-bottom: 0.65rem;
            color: var(--ink);
            font-size: 0.98rem;
        }

        .progress-row {
            display: grid;
            grid-template-columns: minmax(110px, 170px) 1fr minmax(44px, auto);
            align-items: center;
            gap: 0.7rem;
            padding: 0.42rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.055);
            font-size: 0.86rem;
        }

        .progress-track {
            height: 8px;
            border-radius: 999px;
            background: rgba(255,255,255,0.08);
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            border-radius: inherit;
        }

        .recent-row {
            display: grid;
            grid-template-columns: 1fr auto auto;
            align-items: center;
            gap: 0.7rem;
            padding: 0.52rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.055);
            font-size: 0.86rem;
        }

        .portal-hero {
            display: flex;
            justify-content: space-between;
            align-items: end;
            gap: 1rem;
            padding: 1.35rem 1.4rem;
            border: 1px solid rgba(220,20,60,0.18);
            border-radius: 10px;
            background: linear-gradient(135deg, rgba(20,2,10,0.92), rgba(6,0,4,0.88));
            margin-bottom: 1rem;
        }

        .portal-hero h1 {
            margin: 0.18rem 0 0.35rem;
            font-size: clamp(1.7rem, 4vw, 3rem);
        }

        .portal-hero p { margin: 0; color: var(--muted); }

        .quiz-card {
            transition: border-color 160ms ease, transform 160ms ease, box-shadow 160ms ease;
        }

        .quiz-card:hover {
            border-color: rgba(220,20,60,0.38);
            transform: translateY(-2px);
            box-shadow: 0 18px 45px rgba(0,0,0,0.22);
        }

        .quiz-card h3 {
            margin: 0 0 0.4rem;
            font-size: 1.12rem;
        }

        .quiz-card .muted { margin-bottom: 0.2rem; }

        .quiz-topline {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.9rem;
            margin-bottom: 0.7rem;
            padding: 0.7rem 0.9rem;
            border: 1px solid rgba(220,20,60,0.16);
            border-radius: 9px;
            background: rgba(255,255,255,0.035);
        }

        .feedback-panel {
            border: 1px solid rgba(220,20,60,0.20);
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
            background: linear-gradient(180deg, rgba(255,255,255,0.052), rgba(255,255,255,0.025));
        }

        @keyframes floatDrift {
            0%, 100% { transform: translate3d(0, 0, 0) rotate(-1deg); }
            50% { transform: translate3d(0, -18px, 0) rotate(1deg); }
        }

        @keyframes slowSpin {
            to { transform: rotate(360deg); }
        }

        @keyframes leafFloat {
            0%, 100% { translate: 0 0; rotate: 0deg; }
            50% { translate: 0 -22px; rotate: 7deg; }
        }

        @keyframes flowerBob {
            0%, 100% { translate: 0 0; rotate: 0deg; }
            50% { translate: 0 16px; rotate: 12deg; }
        }

        @keyframes pulseNode {
            0% { box-shadow: 0 0 0 0 rgba(220,20,60,0.55); transform: scale(1); }
            70% { box-shadow: 0 0 0 22px rgba(220,20,60,0); transform: scale(1.15); }
            100% { box-shadow: 0 0 0 0 rgba(220,20,60,0); transform: scale(1); }
        }

        .card, .vignette-card, .result-card, .quiz-card {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 12px 30px rgba(55, 45, 31, 0.08);
            padding: 1.15rem 1.25rem;
            margin: 0.7rem 0;
        }

        .vignette-card {
            border-left: 5px solid var(--primary);
        }

        .diagram-card {
            background: rgba(56, 217, 169, 0.09);
            border: 1px dashed rgba(56, 217, 169, 0.45);
            border-radius: 8px;
            padding: 1rem;
            margin: 0.8rem 0;
        }

        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 0.7rem 0 0.2rem;
        }

        .pill {
            border: 1px solid rgba(17, 97, 73, 0.22);
            border-radius: 999px;
            background: var(--soft);
            color: var(--primary);
            padding: 0.22rem 0.65rem;
            font-size: 0.84rem;
            font-weight: 650;
        }

        .muted {
            color: var(--muted);
            line-height: 1.55;
        }

        .mnemonic {
            background: rgba(244, 192, 106, 0.13);
            border-left: 4px solid var(--primary);
            border-radius: 8px;
            padding: 0.9rem 1rem;
            margin-top: 0.85rem;
            color: var(--ink);
        }
        .mnemonic strong { color: var(--primary); }

        .danger-pill {
            background: rgba(255,107,122,0.14);
            border-color: rgba(255,107,122,0.3);
            color: var(--danger);
        }

        /* ── Clinical diagram frames ── */
        .diag-frame {
            margin: 1rem 0;
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid var(--line);
            background: var(--surface-strong);
        }
        .diag-title-bar {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            padding: 0.42rem 0.75rem;
            background: rgba(255,255,255,0.05);
            border-bottom: 1px solid var(--line);
        }
        .diag-badge {
            font-size: 0.68rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            padding: 0.15rem 0.48rem;
            border-radius: 3px;
        }
        .diag-badge-ecg  { background:#0d2e14; color:#33ff88; border:1px solid rgba(51,255,136,0.4); }
        .diag-badge-lab  { background:#0d1e38; color:#60a5fa; border:1px solid rgba(96,165,250,0.4); }
        .diag-badge-film { background:#222;    color:#bbb;    border:1px solid rgba(187,187,187,0.3); }
        .diag-badge-us   { background:#071e0e; color:#44cc77; border:1px solid rgba(68,204,119,0.4); }
        .diag-badge-histo{ background:#200838; color:#c084fc; border:1px solid rgba(192,132,252,0.4); }
        .diag-badge-dflt { background:var(--soft); color:var(--primary); border:1px solid rgba(244,192,106,0.35); }
        .diag-badge-info { font-size:0.71rem; color:var(--muted); letter-spacing:0.05em; }
        .diag-footer {
            padding: 0.48rem 0.82rem;
            font-size: 0.81rem;
            color: var(--muted);
            border-top: 1px solid var(--line);
            line-height: 1.5;
        }
        .lab-table { width:100%; border-collapse:collapse; font-size:0.9rem; }
        .lab-table th {
            background: rgba(255,255,255,0.06);
            padding: 0.42rem 0.8rem;
            text-align: left;
            font-size: 0.74rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--muted);
            border-bottom: 1px solid var(--line);
        }
        .lab-table td { padding:0.38rem 0.8rem; border-bottom:1px solid rgba(255,242,224,0.07); }
        .lab-val { font-weight:700; color:var(--primary); font-family:monospace; font-size:0.96rem; }

        .stButton > button {
            background: var(--primary);
            border: 1px solid var(--primary);
            color: #ffffff;
            border-radius: 5px;
            padding: 0.32rem 0.82rem;
            font-size: 0.86rem;
            font-weight: 700;
            min-height: 2rem;
            transition: background 140ms ease, border 140ms ease, transform 140ms ease;
        }

        .stButton > button:hover {
            background: var(--primary-dark);
            border-color: var(--primary-dark);
            color: #ffffff;
            transform: translateY(-1px);
        }

        @media (max-width: 820px) {
            .dashboard-shell { min-height: auto; padding: 2.2rem 1rem; }
            .dashboard-panel { width: 100%; }
            .landing-metrics, .feature-strip { grid-template-columns: 1fr; }
            .motion-stage { opacity: 0.25; }
            .med-orbit, .doctor-figure, .leaf, .flower { display: none; }
        }

        @media (min-width: 821px) and (max-width: 1100px) {
            .feature-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }

        .stButton > button:focus:not(:active) {
            border-color: var(--accent);
            box-shadow: 0 0 0 0.18rem rgba(182, 95, 42, 0.22);
        }

        /* Sign-in ghost link — same-tab navigation, styled as outline button */
        a.cta-signin-link {
            display: block;
            text-align: center;
            text-decoration: none;
            background: transparent;
            border: 1.5px solid rgba(220, 20, 60, 0.55);
            color: #f8f0f0;
            font-size: 1rem;
            font-weight: 600;
            padding: 0.65rem 2rem;
            letter-spacing: 0.06em;
            border-radius: 6px;
            transition: background 140ms ease, border-color 140ms ease, transform 140ms ease;
            margin: 0.35rem 0;
        }
        a.cta-signin-link:hover {
            background: rgba(220, 20, 60, 0.12);
            border-color: var(--primary);
            color: #ffffff;
            transform: translateY(-1px);
        }

        div[data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 8px 24px rgba(55, 45, 31, 0.07);
        }

        section[data-testid="stSidebar"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def default_questions() -> list[dict[str, Any]]:
    return [
        {
            "id": "med-medium-acs-001",
            "specialty": "Medicine",
            "difficulty": "Medium",
            "question": "A 58-year-old man with diabetes and smoking history presents with crushing retrosternal chest pain for 40 minutes, diaphoresis, and nausea. ECG shows ST elevation in leads II, III, and aVF with reciprocal ST depression in I and aVL. Blood pressure is 104/68 mmHg and oxygen saturation is 96% on room air. Which drug should be given immediately if there is no contraindication while arranging reperfusion?",
            "options": ["Aspirin", "Warfarin", "Digoxin", "Verapamil"],
            "answer": "Aspirin",
            "rationale": "Inferior-wall STEMI requires immediate antiplatelet therapy while reperfusion is arranged. Chewed aspirin rapidly inhibits thromboxane-mediated platelet aggregation.",
            "memory_tip": "MONA-BASH keeps ACS first steps ordered: Morphine, Oxygen if hypoxic, Nitrates, Aspirin, Beta blocker, Anticoagulation, Statin, Heparin.",
            "red_flags": ["Crushing chest pain", "ST elevation", "Inferior leads II, III, aVF"],
        },
        {
            "id": "pharm-medium-sludge-002",
            "specialty": "Pharmacology",
            "difficulty": "Medium",
            "question": "A farm worker is brought after pesticide exposure with sweating, pinpoint pupils, wheeze, vomiting, bradycardia, excessive salivation, and fasciculations. His clothes smell strongly of chemicals and his oxygen saturation improves after suctioning secretions. Which antidote should be prioritized first to reverse the life-threatening muscarinic features?",
            "options": ["Atropine", "Flumazenil", "Naloxone", "Vitamin K"],
            "answer": "Atropine",
            "rationale": "Organophosphate poisoning causes muscarinic excess. Atropine reverses life-threatening bronchorrhea, bronchospasm, and bradycardia.",
            "memory_tip": "SLUDGE flags cholinergic toxicity: Salivation, Lacrimation, Urination, Defecation, Gastrointestinal distress, Emesis.",
            "red_flags": ["Pesticide exposure", "Pinpoint pupils", "Secretions and bradycardia"],
        },
        {
            "id": "obg-medium-pph-003",
            "specialty": "Obstetrics and Gynecology",
            "difficulty": "Medium",
            "question": "A woman has heavy bleeding immediately after vaginal delivery of a macrosomic baby following prolonged labor. The placenta appears complete, the cervix is not visibly torn, and the uterus is soft, enlarged, and boggy on palpation despite ongoing fundal massage. What is the most likely cause of this primary postpartum hemorrhage?",
            "options": ["Uterine atony", "Cervical tear", "Placenta accreta", "Coagulopathy"],
            "answer": "Uterine atony",
            "rationale": "A soft, boggy uterus after delivery indicates failure of myometrial contraction, the most common cause of primary postpartum hemorrhage.",
            "memory_tip": "The 4 Ts of PPH are Tone, Trauma, Tissue, Thrombin. A boggy uterus is Tone until proven otherwise.",
            "red_flags": ["Immediate postpartum bleeding", "Soft boggy uterus"],
        },
        {
            "id": "med-medium-dka-004",
            "specialty": "Medicine",
            "difficulty": "Medium",
            "question": "A 19-year-old with type 1 diabetes presents with abdominal pain, Kussmaul breathing, glucose 480 mg/dL, pH 7.14, bicarbonate 9 mEq/L, and serum potassium 3.1 mEq/L. What is the next best step?",
            "options": ["Start IV insulin immediately", "Give potassium before insulin", "Give sodium bicarbonate", "Restrict IV fluids"],
            "answer": "Give potassium before insulin",
            "rationale": "This is DKA, but insulin drives potassium into cells and can precipitate fatal hypokalemia. Potassium must be corrected before insulin when K+ is below 3.3 mEq/L.",
            "memory_tip": "DKA potassium rule: K less than 3.3, hold insulin and replace K; 3.3 to 5.2, insulin plus K; above 5.2, insulin and monitor.",
            "red_flags": ["DKA physiology", "Kussmaul breathing", "Potassium 3.1"],
            "visual_type": "lab_table",
            "diagram_prompt": "Render a compact ABG/electrolyte table showing glucose 480 mg/dL, pH 7.14, bicarbonate 9 mEq/L, and potassium 3.1 mEq/L.",
        },
        {
            "id": "surg-medium-appy-005",
            "specialty": "Surgery",
            "difficulty": "Medium",
            "question": "A 23-year-old has periumbilical pain that migrated to the right iliac fossa with fever, anorexia, leukocytosis, and rebound tenderness. What is the most appropriate definitive management after resuscitation and antibiotics?",
            "options": ["Appendectomy", "Colonoscopy", "Oral metronidazole alone", "Immediate steroid therapy"],
            "answer": "Appendectomy",
            "rationale": "Migratory pain to the right iliac fossa with localized peritonism is acute appendicitis. Definitive treatment is appendectomy after stabilization and antibiotics.",
            "memory_tip": "MANTRELS supports appendicitis scoring: Migration, Anorexia, Nausea/vomiting, Tenderness, Rebound, Elevation of temperature, Leukocytosis, Shift left.",
            "red_flags": ["Migratory pain", "Right iliac fossa rebound", "Fever and leukocytosis"],
        },
        {
            "id": "obg-medium-preeclampsia-006",
            "specialty": "OBGYN",
            "difficulty": "Medium",
            "question": "A 30-year-old primigravida at 34 weeks has BP 168/112 mmHg, headache, visual blurring, proteinuria, and brisk reflexes. Which medication prevents the most feared acute neurologic complication?",
            "options": ["Magnesium sulfate", "Methyldopa", "Furosemide", "Warfarin"],
            "answer": "Magnesium sulfate",
            "rationale": "Severe pre-eclampsia can progress to eclampsia. Magnesium sulfate is used for seizure prophylaxis and treatment.",
            "memory_tip": "MAG for maternal seizures: Magnesium sulfate protects the brain; antihypertensives protect vessels; delivery cures the disease.",
            "red_flags": ["Severe BP", "Headache and visual symptoms", "Proteinuria"],
        },
        {
            "id": "med-hard-tb-hiv-007",
            "specialty": "Medicine",
            "difficulty": "Hard",
            "question": "A 36-year-old man with untreated HIV presents with 4 weeks of fever, weight loss, night sweats, and cough. Chest radiograph shows diffuse reticulonodular infiltrates rather than a classic upper-lobe cavity. Sputum CBNAAT detects Mycobacterium tuberculosis with rifampicin sensitivity. CD4 count is 72 cells/mm3, LFTs are normal, and he has no signs of meningitis. After starting standard antitubercular therapy, when should antiretroviral therapy generally be initiated?",
            "options": ["Within 2 weeks", "After completing intensive phase", "After completing all TB therapy", "Only if viral load remains detectable after TB cure"],
            "answer": "Within 2 weeks",
            "rationale": "In TB-HIV coinfection with CD4 below 50 to 100 and no TB meningitis, early ART after ATT initiation reduces mortality, while monitoring for IRIS.",
            "memory_tip": "TB-HIV timing anchor: low CD4 means early ART; TB meningitis is the major reason to delay because CNS inflammation is dangerous.",
            "red_flags": ["HIV with CD4 72", "Confirmed rifampicin-sensitive TB", "No meningitis"],
        },
        {
            "id": "surg-hard-trauma-008",
            "specialty": "Surgery",
            "difficulty": "Hard",
            "question": "A 28-year-old motorcyclist arrives after blunt abdominal trauma. He is confused, pale, and diaphoretic with pulse 138/min and BP 78/46 mmHg. Airway is patent after cervical stabilization, oxygen is being given, and two large-bore IV lines are placed. FAST shows free intraperitoneal fluid. Despite rapid crystalloid and packed red cell transfusion, he remains hypotensive. What is the next best management step?",
            "options": ["Emergency exploratory laparotomy", "CT abdomen with contrast", "Diagnostic peritoneal lavage", "Observation with serial abdominal exams"],
            "answer": "Emergency exploratory laparotomy",
            "rationale": "Hemodynamic instability with positive FAST after blunt trauma indicates ongoing intra-abdominal hemorrhage. The patient should go directly to operative control of bleeding, not CT.",
            "memory_tip": "ATLS decision hook: unstable plus positive FAST equals laparotomy; stable plus positive FAST can go to CT.",
            "red_flags": ["Shock", "Positive FAST", "No response to resuscitation"],
            "visual_type": "diagram",
            "diagram_prompt": "Show a simplified FAST ultrasound panel with free fluid marked in Morrison pouch and pelvis.",
        },
        {
            "id": "obg-hard-ectopic-009",
            "specialty": "OBGYN",
            "difficulty": "Hard",
            "question": "A 27-year-old with 7 weeks of amenorrhea presents with lower abdominal pain and spotting. She is dizzy, pulse is 126/min, BP is 86/54 mmHg, and abdomen is tender with guarding. Urine pregnancy test is positive. Transvaginal ultrasound shows an empty uterus with complex adnexal mass and free fluid in the pouch of Douglas. What is the most appropriate management?",
            "options": ["Immediate laparoscopy or laparotomy", "Single-dose methotrexate", "Repeat beta-hCG in 48 hours", "Misoprostol for missed abortion"],
            "answer": "Immediate laparoscopy or laparotomy",
            "rationale": "This is ruptured ectopic pregnancy with hemodynamic instability and hemoperitoneum. Surgical management is required urgently; methotrexate is for stable selected cases.",
            "memory_tip": "Ectopic triad: amenorrhea, pain, bleeding. Shock or free fluid moves the answer from methotrexate to surgery.",
            "red_flags": ["Positive pregnancy test", "Empty uterus", "Shock with free fluid"],
            "visual_type": "ultrasound_prompt",
            "diagram_prompt": "Transvaginal ultrasound description: empty uterus, complex right adnexal mass, and free fluid in pouch of Douglas.",
        },
    ]


def initialize_state() -> None:
    defaults = {
        "stage": "landing",
        "role": "guest",
        "admin_authenticated": False,
        "quizzes": load_quizzes(),
        "active_quiz_id": None,
        "current_question_index": 0,
        "score": 0,
        "responses": [],
        "incorrect": [],
        "user_details": {},
        "draft_questions": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = deepcopy(value)

    st.session_state.quizzes = [
        quiz for quiz in st.session_state.quizzes if quiz.get("id") != "neet-pg-clinical-core"
    ]
    if st.session_state.active_quiz_id == "neet-pg-clinical-core":
        st.session_state.active_quiz_id = None

    # ─ Process Clerk OAuth callback ───────────────────────────────────────────────────
    if st.query_params.get("error"):
        desc = st.query_params.get("error_description", st.query_params.get("error", "Unknown OAuth error"))
        st.session_state["_clerk_error"] = desc
        st.query_params.clear()
        st.rerun()

    # When Clerk redirects back with ?code=... exchange it immediately.
    if not st.session_state.get("clerk_user") and st.query_params.get("code"):
        expected_state = st.session_state.get("_clerk_oauth_state", "")
        returned_state = st.query_params.get("state", "")
        if expected_state and returned_state != expected_state:
            st.session_state["_clerk_error"] = "OAuth state mismatch. Please try signing in again."
            st.query_params.clear()
            st.rerun()
        with st.spinner("Verifying your identity…"):
            user = _clerk_exchange_code(st.query_params.get("code", ""))
        st.query_params.clear()
        if user:
            st.session_state.pop("_clerk_oauth_state", None)
            st.rerun()
        # If user is None, _clerk_exchange_code stored the error in _clerk_error.

    view = st.query_params.get("view")
    quiz_id = st.query_params.get("quiz_id")
    public_stages = {"public_dashboard", "registration", "quiz_active", "results"}
    admin_stages = {"admin_login", "admin_dashboard"}
    if view == HISTORY_QUERY_TOKEN:
        st.session_state.role = "guest"
        st.session_state.stage = "user_history" if _get_auth_user() else "landing"
    elif view == PUBLIC_QUERY_TOKEN and st.session_state.stage not in public_stages:
        st.session_state.role = "guest"
        st.session_state.stage = "public_dashboard"
        if quiz_id:
            st.session_state.active_quiz_id = quiz_id
    elif view == ADMIN_QUERY_TOKEN and st.session_state.stage not in admin_stages:
        st.session_state.stage = "admin_login"


def set_stage(stage: str) -> None:
    st.session_state.stage = stage


def navigate(stage: str, **params: str) -> None:
    set_stage(stage)
    st.query_params.clear()
    if stage in {"public_dashboard", "registration", "quiz_active", "results"}:
        st.query_params["view"] = PUBLIC_QUERY_TOKEN
        quiz_id = params.get("quiz_id") or st.session_state.get("active_quiz_id")
        if quiz_id:
            st.query_params["quiz_id"] = quiz_id
    elif stage in {"admin_login", "admin_dashboard"}:
        st.query_params["view"] = ADMIN_QUERY_TOKEN
    elif stage == "user_history":
        st.query_params["view"] = HISTORY_QUERY_TOKEN


def reset_attempt() -> None:
    st.session_state.current_question_index = 0
    st.session_state.score = 0
    st.session_state.responses = []
    st.session_state.incorrect = []
    st.session_state["result_saved"] = False
    st.session_state["attempt_id"] = None
    st.session_state["feedback_submitted"] = False


def start_registration(quiz_id: str) -> None:
    reset_attempt()
    st.session_state.active_quiz_id = quiz_id
    navigate("registration", quiz_id=quiz_id)


def get_active_quiz() -> Optional[dict[str, Any]]:
    for quiz in st.session_state.quizzes:
        if quiz["id"] == st.session_state.active_quiz_id:
            return quiz
    return None


def validate_question(raw: dict[str, Any], index: int) -> dict[str, Any]:
    required = ["specialty", "difficulty", "question", "options", "answer", "rationale", "memory_tip"]
    for field in required:
        if field not in raw:
            raise ValueError(f"Question {index + 1} is missing {field}.")
    if not isinstance(raw["options"], list) or len(raw["options"]) != 4:
        raise ValueError(f"Question {index + 1} must have exactly four options.")
    if raw["answer"] not in raw["options"]:
        raise ValueError(f"Question {index + 1} answer must match one option exactly.")
    difficulty = str(raw["difficulty"]).title()
    if difficulty not in {"Easy", "Medium", "Hard"}:
        raise ValueError(f"Question {index + 1} difficulty must be Easy, Medium, or Hard.")

    return {
        "id": raw.get("id") or f"generated-{index + 1:03d}",
        "specialty": str(raw["specialty"]),
        "difficulty": difficulty,
        "question": str(raw["question"]),
        "options": [str(option) for option in raw["options"]],
        "answer": str(raw["answer"]),
        "rationale": str(raw["rationale"]),
        "memory_tip": str(raw["memory_tip"]),
        "red_flags": raw.get("red_flags", []),
        "visual_type": raw.get("visual_type", "none"),
        "diagram_prompt": raw.get("diagram_prompt", ""),
        "diagram_image": raw.get("diagram_image", ""),
    }


def _database_url() -> str:
    return get_secret("DATABASE_URL", "")


def _db_connect():
    import psycopg
    return psycopg.connect(_database_url())


def _db_available() -> bool:
    return bool(_database_url())


def _ensure_db_schema() -> None:
    if not _db_available():
        return
    with _db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id BIGSERIAL PRIMARY KEY,
                    quiz_id TEXT NOT NULL,
                    quiz_title TEXT NOT NULL,
                    candidate TEXT NOT NULL,
                    email TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    max_score INTEGER NOT NULL,
                    accuracy DOUBLE PRECISION NOT NULL,
                    correct INTEGER NOT NULL,
                    incorrect INTEGER NOT NULL,
                    total INTEGER NOT NULL,
                    subject_accuracy JSONB NOT NULL DEFAULT '{}'::jsonb,
                    completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    payload JSONB NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS quiz_feedback (
                    id BIGSERIAL PRIMARY KEY,
                    attempt_id BIGINT REFERENCES quiz_attempts(id) ON DELETE SET NULL,
                    quiz_id TEXT NOT NULL,
                    quiz_title TEXT NOT NULL,
                    candidate TEXT NOT NULL,
                    email TEXT NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                    comments TEXT NOT NULL DEFAULT '',
                    next_quiz TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_quiz_attempts_email ON quiz_attempts (LOWER(email))")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_quiz_feedback_email ON quiz_feedback (LOWER(email))")


def _load_attempts_from_db() -> list:
    from psycopg.rows import dict_row

    _ensure_db_schema()
    with _db_connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT payload, id FROM quiz_attempts ORDER BY completed_at DESC, id DESC")
            attempts = []
            for row in cur.fetchall():
                payload = dict(row["payload"])
                payload.setdefault("id", row["id"])
                attempts.append(payload)
            return attempts


def _save_attempt_to_db(attempt: dict) -> Optional[int]:
    from psycopg.types.json import Jsonb

    _ensure_db_schema()
    with _db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO quiz_attempts (
                    quiz_id, quiz_title, candidate, email, score, max_score, accuracy,
                    correct, incorrect, total, subject_accuracy, completed_at, payload
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    attempt.get("quiz_id", ""),
                    attempt.get("quiz_title", "Quiz"),
                    attempt.get("candidate", ""),
                    attempt.get("email", ""),
                    int(attempt.get("score", 0)),
                    int(attempt.get("max_score", 0)),
                    float(attempt.get("accuracy", 0)),
                    int(attempt.get("correct", 0)),
                    int(attempt.get("incorrect", 0)),
                    int(attempt.get("total", 0)),
                    Jsonb(attempt.get("subject_accuracy", {})),
                    attempt.get("completed_at") or datetime.now().isoformat(timespec="seconds"),
                    Jsonb(attempt),
                ),
            )
            row = cur.fetchone()
            return int(row[0]) if row else None


def _load_feedback_from_db() -> list:
    from psycopg.rows import dict_row

    _ensure_db_schema()
    with _db_connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT attempt_id, quiz_id, quiz_title, candidate, email,
                       rating, comments, next_quiz, created_at
                FROM quiz_feedback
                ORDER BY created_at DESC, id DESC
                """
            )
            return [dict(row) for row in cur.fetchall()]


def load_attempts() -> list:
    """Load all quiz attempt records from the configured database or local fallback file."""
    if _db_available():
        try:
            return _load_attempts_from_db()
        except Exception as exc:
            st.warning(f"Database read failed; using local fallback. {exc}")
    try:
        if os.path.exists(ATTEMPTS_FILE):
            with open(ATTEMPTS_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_attempt(attempt: dict) -> Optional[int]:
    """Append a quiz attempt record to the configured database or local fallback file."""
    if _db_available():
        try:
            return _save_attempt_to_db(attempt)
        except Exception as exc:
            st.warning(f"Database write failed; using local fallback. {exc}")
    try:
        records = load_attempts()
        records.append(attempt)
        with open(ATTEMPTS_FILE, "w") as f:
            json.dump(records, f, indent=2)
        return len(records)
    except Exception:
        return None


def save_feedback(feedback: dict) -> bool:
    """Persist quiz feedback to the database, or to a local fallback JSON file."""
    if _db_available():
        try:
            _ensure_db_schema()
            with _db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO quiz_feedback (
                            attempt_id, quiz_id, quiz_title, candidate, email,
                            rating, comments, next_quiz, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            feedback.get("attempt_id"),
                            feedback.get("quiz_id", ""),
                            feedback.get("quiz_title", "Quiz"),
                            feedback.get("candidate", ""),
                            feedback.get("email", ""),
                            int(feedback.get("rating", 0)),
                            feedback.get("comments", ""),
                            feedback.get("next_quiz", ""),
                            feedback.get("created_at") or datetime.now().isoformat(timespec="seconds"),
                        ),
                    )
            return True
        except Exception as exc:
            st.warning(f"Database feedback write failed; using local fallback. {exc}")

    try:
        records = []
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, "r") as f:
                records = json.load(f)
        records.append(feedback)
        with open(FEEDBACK_FILE, "w") as f:
            json.dump(records, f, indent=2)
        return True
    except Exception:
        return False


def load_feedback() -> list:
    """Load quiz feedback from the configured database or local fallback file."""
    if _db_available():
        try:
            return _load_feedback_from_db()
        except Exception as exc:
            st.warning(f"Database feedback read failed; using local fallback. {exc}")
    try:
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def load_quizzes() -> list:
    """Load all published/draft quizzes from disk, normalising question fields for backwards-compat."""
    try:
        if os.path.exists(QUIZZES_FILE):
            with open(QUIZZES_FILE, "r") as f:
                data = json.load(f)
            for quiz in data:
                for q in quiz.get("questions", []):
                    q.setdefault("visual_type",   "none")
                    q.setdefault("diagram_prompt", "")
                    q.setdefault("diagram_image",  "")
                    q.setdefault("rationale",      "")
                    q.setdefault("memory_tip",     "Review this topic in your NEET PG notes.")
                    q.setdefault("red_flags",      [])
            return data
    except Exception:
        pass
    return []


def save_quizzes(quizzes: list) -> None:
    """Persist the full quiz list to disk so every new session sees it."""
    try:
        with open(QUIZZES_FILE, "w") as f:
            json.dump(quizzes, f, indent=2)
    except Exception:
        pass


# ── Clerk / OIDC authentication helpers ──────────────────────────────────────

def _clerk_fapi_url_from_publishable_key(publishable_key: str) -> str:
    if not publishable_key:
        return ""
    encoded = re.sub(r"^pk_(?:test|live)_", "", publishable_key).strip()
    try:
        padded = encoded + "=" * (-len(encoded) % 4)
        decoded = base64.b64decode(padded).decode("utf-8").rstrip("$")
        return f"https://{decoded}" if decoded else ""
    except Exception:
        return ""


def _clerk_config() -> dict[str, str]:
    try:
        clerk = st.secrets.get("clerk", {})
    except Exception:
        clerk = {}

    client_secret = _get_env_config("CLERK_CLIENT_SECRET", "CLERK_OAUTH_CLIENT_SECRET")
    secret_key = _get_env_config("CLERK_SECRET_KEY")
    if not client_secret and secret_key and not secret_key.startswith(("sk_test_", "sk_live_")):
        client_secret = secret_key

    fapi_url = (
        _get_env_config("CLERK_FAPI_URL", "CLERK_FRONTEND_API_URL")
        or clerk.get("fapi_url", "")
        or _clerk_fapi_url_from_publishable_key(
            _get_env_config("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "CLERK_PUBLISHABLE_KEY")
        )
    )

    return {
        "client_id": _get_env_config("CLERK_CLIENT_ID", "CLERK_OAUTH_CLIENT_ID") or clerk.get("client_id", ""),
        "client_secret": client_secret or clerk.get("client_secret", ""),
        "redirect_uri": _get_env_config("CLERK_REDIRECT_URI", "CLERK_OAUTH_REDIRECT_URI") or clerk.get("redirect_uri", "http://localhost:8501"),
        "fapi_url": fapi_url.rstrip("/"),
    }


def _clerk_oauth_state() -> str:
    state = st.session_state.get("_clerk_oauth_state", "")
    if len(state) < 8:
        state = _secrets.token_urlsafe(24)
        st.session_state["_clerk_oauth_state"] = state
    return state


def _clerk_request_headers(extra: Optional[dict[str, str]] = None) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }
    if extra:
        headers.update(extra)
    return headers

def _clerk_auth_available() -> bool:
    """True when Clerk OAuth config is available from secrets or env-style keys."""
    clerk = _clerk_config()
    return bool(clerk["client_id"] and clerk["client_secret"] and clerk["fapi_url"])


def _clerk_base_url() -> str:
    """Return the Clerk Frontend API base URL."""
    return _clerk_config()["fapi_url"]


def _clerk_build_auth_url() -> str:
    """
    Build the Clerk OAuth2 authorization URL.
    prompt=login forces Clerk to show the sign-in form even when the user
    already has an active Clerk browser session.
    """
    try:
        import urllib.parse
        clerk  = _clerk_config()
        redir  = clerk["redirect_uri"]
        base   = _clerk_base_url()
        params = urllib.parse.urlencode({
            "client_id":     clerk["client_id"],
            "redirect_uri":  redir,
            "response_type": "code",
            "scope":         "openid email profile",
            "state":         _clerk_oauth_state(),
            "prompt":        "login",   # always show the sign-in form
        })
        return f"{base}/oauth/authorize?{params}"
    except Exception:
        return ""


def _clerk_exchange_code(code: str) -> Optional[dict]:
    """
    Exchange an OAuth authorization code for user info.
    Returns {name, email, id} on success, None on any error.
    Stores a human-readable error in session_state['_clerk_error'] on failure.
    """
    import urllib.request, urllib.parse
    try:
        clerk  = _clerk_config()
        redir  = clerk["redirect_uri"]
        base   = _clerk_base_url()

        # Step 1 — exchange code for tokens
        token_data = urllib.parse.urlencode({
            "grant_type":    "authorization_code",
            "code":          code,
            "redirect_uri":  redir,
            "client_id":     clerk["client_id"],
            "client_secret": clerk["client_secret"],
        }).encode()
        req = urllib.request.Request(
            f"{base}/oauth/token",
            data=token_data,
            headers=_clerk_request_headers({"Content-Type": "application/x-www-form-urlencoded"}),
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                tokens = json.loads(resp.read())
        except urllib.error.HTTPError as http_err:
            body = http_err.read().decode("utf-8", errors="replace")
            st.session_state["_clerk_error"] = f"Token exchange failed ({http_err.code}): {body[:300]}"
            return None

        access_token = tokens.get("access_token", "")
        if not access_token:
            st.session_state["_clerk_error"] = f"No access_token in Clerk response: {str(tokens)[:200]}"
            return None

        # Step 2 — fetch user info
        req2 = urllib.request.Request(
            f"{base}/oauth/userinfo",
            headers=_clerk_request_headers({"Authorization": f"Bearer {access_token}"}),
        )
        with urllib.request.urlopen(req2, timeout=10) as resp:
            info = json.loads(resp.read())

        email = info.get("email", "")
        name  = info.get("name", "") or email.split("@")[0]
        user  = {"name": name, "email": email, "id": info.get("sub", email)}
        st.session_state["clerk_user"] = user
        return user
    except Exception:
        return None


def _clerk_sign_out() -> None:
    """Sign the user out by clearing the Clerk session cache."""
    st.session_state.pop("clerk_user", None)
    st.query_params.clear()


def _get_auth_user() -> Optional[dict]:
    """Return current signed-in user from session cache."""
    return st.session_state.get("clerk_user")


def _is_admin_email() -> bool:
    """
    Return True when the signed-in Clerk user's email matches ADMIN_EMAIL.
    Falls back to True when password-based admin is authenticated.
    """
    if st.session_state.get("admin_authenticated"):
        return True
    admin_email = get_secret("ADMIN_EMAIL", "")
    user = _get_auth_user()
    return bool(admin_email and user and user["email"].lower() == admin_email.lower())


# ── PDF parsing helpers ──────────────────────────────────────────────────────

def _extract_pdf_text(file_bytes: bytes) -> str:
    """Extract all text from a PDF given its raw bytes."""
    if _pdfplumber is None:
        raise RuntimeError("pdfplumber is not installed. Run: python3 -m pip install pdfplumber")
    import io
    pages = []
    with _pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
    return "\n".join(pages)


def _clean_pdf_text(text: str) -> str:
    """Normalise common PDF extraction artefacts."""
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\nPage \d+ of \d+\n?", "\n", text)  # strip page markers
    text = re.sub(r"\n{3,}", "\n\n", text)              # collapse blank lines
    return text.strip()


def _parse_neet_question_paper(text: str) -> list:
    """
    Parse 'Question N / Type / Difficulty / vignette / options / Hint' format.
    Extracts difficulty, diagram flag, and hint for each question.
    """
    questions = []
    parts = re.split(r"(?:^|\n)Question\s+(\d+)\s*\n", text, flags=re.MULTILINE)
    i = 1
    while i + 1 < len(parts):
        q_num = int(parts[i])
        body = parts[i + 1].strip()
        i += 2

        # Difficulty from header line
        diff_match = re.search(r"Difficulty:\s*(TOUGH|HARD|MEDIUM|EASY)", body, re.IGNORECASE)
        difficulty = "Hard" if diff_match and diff_match.group(1).upper() in ("TOUGH", "HARD") else "Medium"

        # Remove Type/Difficulty header line
        body = re.sub(r"Type:.*?(?:\n|$)", "", body, count=1)

        # Diagram flag
        has_diagram = bool(re.search(r"\[diagram available", body, re.IGNORECASE))
        body = re.sub(r"\[Diagram available[^\]]*\]\n?", "", body, flags=re.IGNORECASE)

        # Hint (remove from body, save separately)
        hint = ""
        hint_m = re.search(r"\nHint:\s*(.+?)$", body, re.DOTALL)
        if hint_m:
            hint = re.sub(r"\s+", " ", hint_m.group(1)).strip()
            body = body[: hint_m.start()].strip()

        # Options: A. / B. / C. / D. (may have spurious spaces like "C . ")
        opt_re = re.compile(
            r"\n\s*([A-D])\s*\.\s+(.+?)(?=\n\s*[A-D]\s*\.\s+|\Z)",
            re.DOTALL,
        )
        opts = opt_re.findall(body)
        if len(opts) == 4:
            first = opt_re.search(body)
            stem = body[: first.start()].strip() if first else body
            stem = re.sub(r"\s{2,}", " ", stem).strip()
            options = [re.sub(r"\s+", " ", v).strip() for _, v in opts]
            questions.append({
                "num": q_num,
                "question": stem,
                "options": options,
                "difficulty": difficulty,
                "hint": hint,
                "has_diagram": has_diagram,
            })
    return questions


def _parse_numbered_question_paper(text: str) -> list:
    """Parse legacy '1. question ... A. opt ...' format (backward compatibility)."""
    questions = []
    parts = re.split(r"(?:^|\n)\s*(?:Q[\. ]?)?\s*(\d+)\s*[.):][ \t]+", text, flags=re.MULTILINE)
    i = 1
    while i + 1 < len(parts):
        q_num = int(parts[i])
        body = parts[i + 1].strip()
        i += 2
        opt_re = re.compile(
            r"(?:^|\n)\s*[\(\[]?([A-Da-d])[\)\].:][ \t]+"
            r"(.+?)(?=(?:^|\n)\s*[\(\[]?[A-Da-d][\)\].:][ \t]+|\Z)",
            re.DOTALL,
        )
        opts = opt_re.findall(body)
        if len(opts) == 4:
            first = opt_re.search(body)
            stem = body[: first.start()].strip() if first else body
            stem = re.sub(r" {2,}", " ", stem).strip()
            options = [re.sub(r"\s+", " ", v).strip() for _, v in opts]
            questions.append({
                "num": q_num,
                "question": stem,
                "options": options,
                "difficulty": "Medium",
                "hint": "",
                "has_diagram": False,
            })
    return questions


def _parse_question_paper(text: str) -> list:
    """Dispatcher: detect format and call the correct parser."""
    text = _clean_pdf_text(text)
    if re.search(r"(?:^|\n)Question\s+\d+\s*\n", text):
        return _parse_neet_question_paper(text)
    return _parse_numbered_question_paper(text)


def _parse_neet_answer_key(text: str) -> dict:
    """
    Parse NEET answer key format:
      [CORRECT] A. option text   ← correct answer marker
      Correct Answer: A          ← fallback
      Explanation: ...           ← rationale
      Memory Tip: ...            ← memory tip
    Returns {q_num: (answer_letter, memory_tip, rationale)}
    """
    answers: dict = {}
    parts = re.split(r"(?:^|\n)Question\s+(\d+)\s*\n", text, flags=re.MULTILINE)
    i = 1
    while i + 1 < len(parts):
        q_num = int(parts[i])
        body = parts[i + 1].strip()
        i += 2

        # Correct answer: prefer [CORRECT] marker, fallback to "Correct Answer: X"
        correct_opt = re.search(r"\[CORRECT\]\s+([A-D])\s*\.", body)
        ca_line     = re.search(r"Correct Answer:\s*([A-D])", body)
        ans_letter  = (correct_opt.group(1) if correct_opt else
                       ca_line.group(1)     if ca_line     else "")

        # Rationale (Explanation field)
        exp_m = re.search(
            r"Explanation:\s*(.+?)(?=\nMemory Tip:|\nExpected Answer|\nSource:|\Z)",
            body, re.DOTALL,
        )
        rationale = re.sub(r"\s+", " ", exp_m.group(1)).strip() if exp_m else ""

        # Memory Tip
        tip_m = re.search(
            r"Memory Tip:\s*(.+?)(?=\nExpected Answer|\nSource:|\Z)",
            body, re.DOTALL,
        )
        memory_tip = re.sub(r"\s+", " ", tip_m.group(1)).strip() if tip_m else ""
        # Remove any trailing Source/Expected content that leaked in
        memory_tip = re.split(r"Source:|Expected Answer", memory_tip)[0].strip()

        if ans_letter:
            answers[q_num] = (ans_letter, memory_tip, rationale)
    return answers


def _parse_simple_answer_key(text: str) -> dict:
    """Parse legacy simple answer-key formats (1. A / table / pipe-separated)."""
    answers: dict = {}
    # Table-style
    table_rows = re.findall(r"(\d+)\s*[|\t]\s*([A-Da-d])\s*[|\t]?\s*(.*?)(?=\n|\Z)", text)
    if table_rows:
        for num_s, ans, tip in table_rows:
            answers[int(num_s)] = (ans.upper(), tip.strip(), "")
        return answers
    # Line-style
    line_re = re.compile(
        r"(?:^|\n)\s*(?:Q[\. ]?)?\s*(\d+)\s*[.):]?\s*([A-Da-d])\b"
        r"(?:\s*[-\u2013\u2014|:]\s*(.+?))?(?=\n\s*(?:Q[\. ]?)?\s*\d+\s*[.):]?\s*[A-Da-d]|\Z)",
        re.DOTALL,
    )
    for m in line_re.finditer(text):
        q_num = int(m.group(1))
        ans   = m.group(2).upper()
        rest  = re.sub(r"\s+", " ", m.group(3) or "").strip()
        if "|" in rest:
            parts = [p.strip() for p in rest.split("|", 1)]
            answers[q_num] = (ans, parts[1] if len(parts) > 1 else "", parts[0])
        else:
            answers[q_num] = (ans, rest, "")
    return answers


def _parse_answer_key(text: str) -> dict:
    """Dispatcher: detect format and call the correct parser."""
    text = _clean_pdf_text(text)
    if re.search(r"\[CORRECT\]", text) or re.search(r"Memory Tip:", text):
        return _parse_neet_answer_key(text)
    if re.search(r"(?:^|\n)Question\s+\d+\s*\n", text):
        return _parse_neet_answer_key(text)
    return _parse_simple_answer_key(text)


def _merge_pdf_questions(parsed_qs: list, answers: dict, subjects: list, default_difficulty: str = "Medium") -> tuple:
    """
    Merge parsed questions with answer key.
    Uses per-question difficulty from the question paper.
    Uses hint as memory_tip fallback if answer key provides none.
    Sets visual_type=clinical_image for questions that had a diagram marker.
    Rotates through `subjects` when assigning specialty.
    """
    merged = []
    unmatched = []
    sub_count = len(subjects)
    for idx_q, q in enumerate(parsed_qs):
        num = q["num"]
        specialty  = subjects[idx_q % sub_count] if sub_count else "Medicine"
        difficulty = q.get("difficulty", default_difficulty)
        has_diagram = q.get("has_diagram", False)
        hint = q.get("hint", "")

        if num in answers:
            ans_letter, memory_tip, rationale = answers[num]
            idx = ord(ans_letter) - ord("A")
            answer_text = q["options"][idx] if 0 <= idx < len(q["options"]) else ""
        else:
            answer_text = ""
            memory_tip  = ""
            rationale   = ""
            unmatched.append(num)

        merged.append({
            "id": f"pdf-{num:03d}-{datetime.now().strftime('%H%M%S')}",
            "specialty": specialty,
            "difficulty": difficulty,
            "question": q["question"],
            "options": q["options"],
            "answer": answer_text,
            "rationale": rationale,
            "memory_tip": memory_tip or "Review this topic in your NEET PG notes.",
            "red_flags": [],
            "visual_type": "clinical_image" if has_diagram else "none",
            "diagram_prompt": (
                "See the clinical diagram/image referenced in this question for additional visual context."
                if has_diagram else ""
            ),
            "diagram_image": q.get("diagram_image", ""),
        })
    return merged, unmatched


# ── PDF image extraction helpers ─────────────────────────────────────────────

def _extract_pdf_pages(file_bytes: bytes) -> list:
    """Return [(page_text, page_object), ...] for every page in the PDF."""
    if _pdfplumber is None:
        raise RuntimeError("pdfplumber is not installed.")
    import io
    result = []
    with _pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            result.append((page.extract_text() or "", page))
    return result


def _extract_diagram_from_page(page: Any) -> str:
    """
    Extract the diagram region from a PDF page as a base64 PNG data URI.
    Strategy 1 — embedded raster images (via page.images).
    Strategy 2 — text-position crop: find [Diagram available] Y, crop to first option.
    Returns data:image/png;base64,... or empty string.
    """
    import io, base64

    def _b64(pil_img: Any) -> str:
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    RES = 150
    scale = RES / 72

    # Strategy 1: largest embedded image object on the page
    if page.images:
        try:
            pil = page.to_image(resolution=RES).original
            best = max(
                page.images,
                key=lambda i: (i.get("x1", 0) - i.get("x0", 0)) * (i.get("bottom", 0) - i.get("top", 0)),
            )
            x0 = max(0, best.get("x0", 0) * scale - 8)
            y0 = max(0, best.get("top", 0) * scale - 8)
            x1 = min(pil.width,  best.get("x1", pil.width / scale) * scale + 8)
            y1 = min(pil.height, best.get("bottom", pil.height / scale) * scale + 8)
            if (x1 - x0) > 20 and (y1 - y0) > 20:
                return _b64(pil.crop((int(x0), int(y0), int(x1), int(y1))))
        except Exception:
            pass

    # Strategy 2: text-guided crop (catches vector / drawn diagrams)
    try:
        words = page.extract_words()
        diag_y: Optional[float] = None
        for w in words:
            if "diagram" in w.get("text", "").lower():
                diag_y = float(w.get("top", 0))
                break
        if diag_y is not None:
            opts_y: Optional[float] = None
            for w in words:
                if re.match(r"^[A-D]$", w.get("text", "")) and float(w.get("top", 0)) > diag_y + 10:
                    opts_y = float(w.get("top", 0))
                    break
            end_y = (opts_y - 5) if opts_y else min(diag_y + 260, float(page.height))
            bbox = (0.0, diag_y + 14, float(page.width), end_y)
            pil = page.crop(bbox).to_image(resolution=RES).original
            if pil.width > 20 and pil.height > 20:
                return _b64(pil)
    except Exception:
        pass

    return ""


def _assign_diagrams_to_questions(parsed_qs: list, pages: list) -> None:
    """
    For each question with has_diagram=True, extract the real image from the
    corresponding PDF page and store it as 'diagram_image' (data URI or '').
    Modifies parsed_qs in place.
    """
    q_page: dict = {}
    for page_idx, (page_text, _) in enumerate(pages):
        for q_str in re.findall(r"Question\s+(\d+)", page_text):
            q_page[int(q_str)] = page_idx

    for q in parsed_qs:
        if not q.get("has_diagram"):
            q["diagram_image"] = ""
            continue
        page_idx = q_page.get(q["num"])
        if page_idx is None:
            q["diagram_image"] = ""
            continue
        _, page_obj = pages[page_idx]
        q["diagram_image"] = _extract_diagram_from_page(page_obj)


# ── Diagram rendering helpers (SVG / text-based fallback) ────────────────────

def _parse_lab_rows(text: str) -> list:
    pairs = []
    pattern = r'([A-Za-z][A-Za-z0-9\s/]+?)\s+([\d.]+\s*(?:mg/dL|mEq/L|mmol/L|g/dL|IU/L|cells/mm3|%|mL|kPa|mmHg|mm Hg)?)'
    for m in re.finditer(pattern, text):
        name = m.group(1).strip().rstrip(',').strip()
        val = m.group(2).strip()
        if 2 < len(name) < 35:
            pairs.append((name.title(), val))
    return pairs or [("Finding", text[:90])]


def _ecg_svg() -> str:
    b = 90

    def one_complex(ox: int) -> list:
        return [
            (ox, b), (ox + 10, b),
            (ox + 12, b - 2), (ox + 16, b - 11), (ox + 19, b - 2), (ox + 22, b),
            (ox + 30, b), (ox + 31, b + 5),
            (ox + 33, b - 62), (ox + 35, b + 16), (ox + 38, b),
            (ox + 54, b - 3),
            (ox + 58, b - 8), (ox + 64, b - 20), (ox + 71, b - 8), (ox + 76, b - 3), (ox + 80, b),
            (ox + 200, b),
        ]

    def pts_to_d(pts: list) -> str:
        return " ".join(("M" if i == 0 else "L") + str(x) + "," + str(y) for i, (x, y) in enumerate(pts))

    all_pts = one_complex(0) + one_complex(200)[1:] + one_complex(400)[1:]
    path_d = pts_to_d(all_pts)

    grid_mh = "".join('<line x1="0" y1="' + str(y) + '" x2="600" y2="' + str(y) + '" stroke="rgba(0,200,100,0.13)" stroke-width="0.5"/>' for y in range(0, 181, 20))
    grid_mv = "".join('<line x1="' + str(x) + '" y1="0" x2="' + str(x) + '" y2="180" stroke="rgba(0,200,100,0.13)" stroke-width="0.5"/>' for x in range(0, 601, 20))
    grid_Mh = "".join('<line x1="0" y1="' + str(y) + '" x2="600" y2="' + str(y) + '" stroke="rgba(0,200,100,0.28)" stroke-width="0.9"/>' for y in range(0, 181, 100))
    grid_Mv = "".join('<line x1="' + str(x) + '" y1="0" x2="' + str(x) + '" y2="180" stroke="rgba(0,200,100,0.28)" stroke-width="0.9"/>' for x in range(0, 601, 200))

    return (
        '<svg viewBox="0 0 600 180" xmlns="http://www.w3.org/2000/svg" '
        'style="width:100%;height:155px;display:block;background:#040d06;">'
        + grid_mh + grid_mv + grid_Mh + grid_Mv
        + '<path d="' + path_d + '" stroke="#33ff88" stroke-width="2" fill="none" stroke-linejoin="round"/>'
        + '</svg>'
    )


def _film_svg(modality: str, prompt: str) -> str:
    cfgs = {
        "xray": ("#111", "#ccc"),
        "ct":   ("#0a0a0a", "#8ab4c8"),
        "mri":  ("#080810", "#b09ad8"),
    }
    bg, col = cfgs.get(modality, ("#111", "#aaa"))
    labels = {"xray": "Chest X-Ray · PA", "ct": "CT Scan · Axial", "mri": "MRI · Coronal"}
    label = labels.get(modality, modality.upper())
    if modality == "xray":
        body = ('<ellipse cx="300" cy="100" rx="140" ry="88" fill="none" stroke="#444" stroke-width="0.8"/>'
                '<ellipse cx="265" cy="82" rx="50" ry="65" fill="rgba(60,60,60,0.35)" stroke="#555" stroke-width="0.6"/>'
                '<ellipse cx="335" cy="82" rx="50" ry="65" fill="rgba(60,60,60,0.35)" stroke="#555" stroke-width="0.6"/>'
                '<ellipse cx="300" cy="86" rx="23" ry="74" fill="rgba(85,85,85,0.45)" stroke="#666" stroke-width="0.5"/>')
    elif modality == "ct":
        body = ('<circle cx="300" cy="110" r="104" fill="rgba(14,24,34,0.7)" stroke="#334" stroke-width="1"/>'
                '<ellipse cx="300" cy="110" rx="74" ry="68" fill="rgba(24,44,64,0.5)" stroke="#446" stroke-width="0.7"/>'
                '<circle cx="300" cy="110" r="28" fill="rgba(44,64,90,0.4)" stroke="#558" stroke-width="0.5"/>')
    else:
        body = ('<circle cx="300" cy="105" r="94" fill="rgba(14,14,30,0.7)" stroke="#333" stroke-width="1"/>'
                '<ellipse cx="300" cy="86" rx="66" ry="78" fill="rgba(28,28,64,0.5)" stroke="#446" stroke-width="0.7"/>'
                '<ellipse cx="300" cy="86" rx="30" ry="36" fill="rgba(54,54,95,0.4)" stroke="#558" stroke-width="0.5"/>')
    safe = prompt[:82] + ("..." if len(prompt) > 82 else "")
    return (
        '<svg viewBox="0 0 600 218" xmlns="http://www.w3.org/2000/svg" '
        'style="width:100%;height:190px;display:block;background:' + bg + ';">'
        '<rect width="600" height="218" fill="' + bg + '"/>'
        + body
        + '<text x="10" y="17" fill="' + col + '" font-size="8" font-family="monospace" opacity="0.65">' + label + '</text>'
        + '<text x="10" y="212" fill="' + col + '" font-size="7.5" font-family="monospace" opacity="0.5">' + safe + '</text>'
        + '</svg>'
    )


def _us_svg(prompt: str) -> str:
    speckles = "".join(
        '<circle cx="' + str(80 + (i * 71) % 440) + '" cy="' + str(28 + (i * 43) % 158)
        + '" r="' + str(round(0.6 + (i % 4) * 0.35, 1))
        + '" fill="rgba(160,200,160,' + str(round(0.05 + (i % 9) * 0.023, 3)) + ')"/>'
        for i in range(260)
    )
    safe = prompt[:82] + ("..." if len(prompt) > 82 else "")
    return (
        '<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" '
        'style="width:100%;height:175px;display:block;background:#030904;">'
        '<path d="M300,5 L58,195 L542,195 Z" fill="rgba(0,22,5,0.55)" stroke="rgba(0,175,80,0.22)" stroke-width="0.8"/>'
        + speckles
        + '<text x="10" y="17" fill="#44aa66" font-size="8" font-family="monospace" opacity="0.8">ULTRASOUND · B-MODE</text>'
        + '<text x="10" y="193" fill="#44aa66" font-size="7.5" font-family="monospace" opacity="0.5">' + safe + '</text>'
        + '</svg>'
    )


def _histo_svg(prompt: str) -> str:
    cells = "".join(
        '<ellipse cx="' + str(28 + (i * 89) % 544) + '" cy="' + str(22 + (i * 67) % 168)
        + '" rx="' + str(8 + i % 5) + '" ry="' + str(6 + i % 4)
        + '" fill="rgba(' + str(155 + i % 38) + ',' + str(98 + i % 42) + ',200,0.30)"'
        + ' stroke="rgba(100,58,152,0.38)" stroke-width="0.7"/>'
        for i in range(52)
    )
    nuclei = "".join(
        '<ellipse cx="' + str(30 + (i * 89) % 544) + '" cy="' + str(24 + (i * 67) % 168)
        + '" rx="' + str(3 + i % 2) + '" ry="' + str(2 + i % 2) + '" fill="rgba(46,12,88,0.75)"/>'
        for i in range(52)
    )
    safe = prompt[:82] + ("..." if len(prompt) > 82 else "")
    return (
        '<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" '
        'style="width:100%;height:175px;display:block;background:#f4eefb;">'
        + cells + nuclei
        + '<text x="8" y="15" fill="#3d0b60" font-size="8" font-family="monospace" opacity="0.68">HISTOLOGY · H&amp;E STAIN · 40×</text>'
        + '<text x="8" y="194" fill="#3d0b60" font-size="7.5" font-family="monospace" opacity="0.58">' + safe + '</text>'
        + '</svg>'
    )


def render_diagram(visual_type: str, prompt: str) -> None:
    """Render a clinical diagram/investigation as a styled SVG or table."""
    if not visual_type or visual_type == "none" or not prompt:
        return
    vt = visual_type.lower()

    if vt == "lab_table":
        rows = _parse_lab_rows(prompt)
        tbody = "".join("<tr><td>" + k + "</td><td class='lab-val'>" + v + "</td></tr>" for k, v in rows)
        html = (
            '<div class="diag-frame">'
            '<div class="diag-title-bar"><span class="diag-badge diag-badge-lab">LAB RESULTS</span></div>'
            '<table class="lab-table"><thead><tr><th>Parameter</th><th>Value</th></tr></thead>'
            '<tbody>' + tbody + '</tbody></table>'
            '<div class="diag-footer">' + prompt + '</div></div>'
        )
    elif vt == "ecg":
        html = (
            '<div class="diag-frame">'
            '<div class="diag-title-bar"><span class="diag-badge diag-badge-ecg">ECG STRIP</span>'
            '<span class="diag-badge-info">&nbsp;25 mm/s &nbsp;·&nbsp; 10 mm/mV</span></div>'
            + _ecg_svg()
            + '<div class="diag-footer">' + prompt + '</div></div>'
        )
    elif vt in ("xray", "ct", "mri"):
        labels = {"xray": "X-RAY", "ct": "CT SCAN", "mri": "MRI"}
        html = (
            '<div class="diag-frame">'
            '<div class="diag-title-bar"><span class="diag-badge diag-badge-film">' + labels[vt] + '</span></div>'
            + _film_svg(vt, prompt)
            + '<div class="diag-footer">' + prompt + '</div></div>'
        )
    elif vt in ("ultrasound", "ultrasound_prompt", "diagram"):
        html = (
            '<div class="diag-frame">'
            '<div class="diag-title-bar"><span class="diag-badge diag-badge-us">ULTRASOUND</span>'
            '<span class="diag-badge-info">&nbsp;B-MODE</span></div>'
            + _us_svg(prompt)
            + '<div class="diag-footer">' + prompt + '</div></div>'
        )
    elif vt == "histology":
        html = (
            '<div class="diag-frame">'
            '<div class="diag-title-bar"><span class="diag-badge diag-badge-histo">HISTOLOGY</span>'
            '<span class="diag-badge-info">&nbsp;H&amp;E Stain</span></div>'
            + _histo_svg(prompt)
            + '<div class="diag-footer">' + prompt + '</div></div>'
        )
    else:
        html = (
            '<div class="diag-frame">'
            '<div class="diag-title-bar"><span class="diag-badge diag-badge-dflt">' + visual_type.upper() + '</span></div>'
            '<div style="padding:1rem;color:var(--muted);font-size:0.9rem">' + prompt + '</div></div>'
        )

    st.markdown(html, unsafe_allow_html=True)


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>NEET PG Clinical Vignette Dashboard</h1>
            <p>Attempt published NEET PG clinical drills or sign in as admin to prepare medium and hard vignette-based quizzes.</p>
            <div class="pill-row">
                <span class="pill">Medium + hard only</span>
                <span class="pill">Long clinical stems</span>
                <span class="pill">Diagram-style items</span>
                <span class="pill">Published quizzes</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    return


def _compute_user_stats(email: str) -> Optional[dict]:
    """
    Aggregate all quiz attempts for a user and return a stats dict used
    by the personalised landing dashboard.
    Returns None if the user has no recorded attempts.
    """
    all_attempts = load_attempts()
    my  = [a for a in all_attempts if a.get("email", "").lower() == email.lower()]
    if not my:
        return None

    total_quizzes     = len(my)
    avg_accuracy      = sum(a.get("accuracy", 0) for a in my) / total_quizzes
    best_accuracy     = max(a.get("accuracy", 0) for a in my)
    total_questions   = sum(a.get("total",    0) for a in my)
    total_correct     = sum(a.get("correct",  0) for a in my)

    # Aggregate subject accuracy across all attempts
    subj_pool: dict[str, list] = {}
    for a in my:
        for subj, pct in a.get("subject_accuracy", {}).items():
            subj_pool.setdefault(subj, []).append(pct)
    subj_avg = {s: round(sum(v) / len(v)) for s, v in subj_pool.items()}

    # Weak subjects: accuracy below 65 % or below the user's own average
    threshold = min(65, avg_accuracy - 5)
    weak = sorted(
        [(s, p) for s, p in subj_avg.items() if p < threshold],
        key=lambda x: x[1],
    )
    strong = sorted(
        [(s, p) for s, p in subj_avg.items() if p >= threshold],
        key=lambda x: -x[1],
    )

    return {
        "total_quizzes":    total_quizzes,
        "avg_accuracy":     round(avg_accuracy, 1),
        "best_accuracy":    best_accuracy,
        "total_questions":  total_questions,
        "total_correct":    total_correct,
        "subject_avg":      subj_avg,
        "weak_subjects":    weak,
        "strong_subjects":  strong,
        "recent_attempts":  sorted(my, key=lambda x: x.get("completed_at", ""), reverse=True)[:5],
    }


def render_landing() -> None:
    auth_user = _get_auth_user() if _clerk_auth_available() else None

    # ── TOP NAV (always rendered) ─────────────────────────────────────────────────────────
    admin_href = (
        '?view=admin' if not (_is_admin_email() and auth_user)
        else '?view=admin'
    )
    st.markdown(
        f"""
        <div class="app-topbar">
            <span class="app-brand">QuizRepo</span>
            <a href="{admin_href}" target="_self" class="app-nav-link">Admin &rarr;</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── LOGGED-IN: PERSONALISED DASHBOARD ──────────────────────────────────────────────
    if auth_user:
        stats = _compute_user_stats(auth_user["email"])

        st.markdown(
            f"""
            <div class="user-hero">
                <div class="user-hero-content">
                    <div class="eyebrow">Welcome back</div>
                    <h1>{_html.escape(auth_user['name'])}</h1>
                    <p>{_html.escape(auth_user['email'])} · Your progress, weak areas, and recent attempts stay synced across sessions.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Action buttons
        ca, cb, cc = st.columns([2, 1, 1])
        with ca:
            if st.button("📚  Browse & Attempt Quizzes", use_container_width=True):
                navigate("public_dashboard")
                st.rerun()
        with cb:
            if st.button("My Full History", use_container_width=True):
                navigate("user_history")
                st.rerun()
        with cc:
            if st.button("Sign out", use_container_width=True):
                _clerk_sign_out()
                st.rerun()

        if not stats:
            st.info("You haven't completed any quizzes yet. Click **Browse & Attempt Quizzes** to get started.")
            return

        # Summary metrics
        st.markdown('<div class="section-kicker">Performance</div><h2 class="section-title">Your study dashboard</h2>', unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Quizzes taken",     stats["total_quizzes"])
        m2.metric("Avg accuracy",      f"{stats['avg_accuracy']}%")
        m3.metric("Best accuracy",     f"{stats['best_accuracy']}%")
        m4.metric("Questions answered",stats["total_questions"])

        # Weak areas + strong areas
        perf_col, recent_col = st.columns([1, 1])
        with perf_col:
            st.markdown('<div class="insight-card"><strong>Subject signal</strong>', unsafe_allow_html=True)
            if stats["weak_subjects"]:
                for subj, pct in stats["weak_subjects"]:
                    colour = "#dc143c" if pct < 50 else "#e06030"
                    st.markdown(
                        f'<div class="progress-row">'
                        f'<span>{_html.escape(subj)}</span>'
                        f'<div class="progress-track"><div class="progress-fill" style="width:{pct}%;background:{colour}"></div></div>'
                        f'<span style="color:var(--muted)">{pct}%</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            if stats["strong_subjects"]:
                for subj, pct in stats["strong_subjects"][:3]:
                    st.markdown(
                        f'<div class="progress-row">'
                        f'<span>{_html.escape(subj)}</span>'
                        f'<div class="progress-track"><div class="progress-fill" style="width:{pct}%;background:#22c55e"></div></div>'
                        f'<span style="color:var(--muted)">{pct}%</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            st.markdown('</div>', unsafe_allow_html=True)

        with recent_col:
            st.markdown('<div class="insight-card"><strong>Recent attempts</strong>', unsafe_allow_html=True)
            for att in stats["recent_attempts"]:
                acc    = att.get("accuracy", 0)
                colour = "#22c55e" if acc >= 70 else ("#e06030" if acc >= 50 else "#dc143c")
                st.markdown(
                    f'<div class="recent-row">'
                    f'<span>{_html.escape(att.get("quiz_title","Quiz"))}</span>'
                    f'<span style="color:{colour};font-weight:700">{acc}%</span>'
                    f'<span style="color:var(--muted)">{att.get("completed_at","")[:10]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)

        # Improvement suggestions
        if stats["weak_subjects"]:
            worst = stats["weak_subjects"][:2]
            suggestions = ", ".join(s for s, _ in worst)
            st.info(
                f"👉 Focus on **{suggestions}** in your next session. "
                f"Quiz yourself on dedicated {suggestions.split(',')[0]} paper to push past the plateau."
            )
        return

    # ── NOT LOGGED IN: CLERK SIGN-IN CALL TO ACTION ────────────────────────────────
    # Show any auth error from the last code-exchange attempt
    clerk_err = st.session_state.pop("_clerk_error", None)
    if clerk_err:
        st.error(f"Sign-in error (share with developer): {clerk_err}")

    st.markdown(
        """
        <div class="dashboard-shell">
            <div class="motion-stage" aria-hidden="true">
                <div class="med-orbit"></div>
                <div class="doctor-figure"></div>
                <div class="leaf leaf-one"></div>
                <div class="leaf leaf-two"></div>
                <div class="leaf leaf-three"></div>
                <div class="flower flower-one"></div>
                <div class="flower flower-two"></div>
                <div class="pulse-node node-one"></div>
                <div class="pulse-node node-two"></div>
                <div class="pulse-node node-three"></div>
            </div>
            <div class="dashboard-panel">
                <div class="eyebrow">NEET PG Practice Platform</div>
                <h1>QuizRepo</h1>
                <p>Attempt high-quality clinical vignette quizzes, track your progress per subject,
                   and get personalised improvement insights after every quiz.</p>
                <div class="landing-metrics">
                    <div class="landing-metric"><strong>Medium / Hard</strong><span>No easy one-liners</span></div>
                    <div class="landing-metric"><strong>Tracked progress</strong><span>Subject-wise analytics</span></div>
                    <div class="landing-metric"><strong>+4 / -1</strong><span>Exam-style marking</span></div>
                </div>
            </div>
        </div>
        <div class="feature-strip">
            <div class="feature-tile"><h3>Clinical stems</h3><p>Long vignette-style questions with investigations, red flags, and next-best-step logic.</p></div>
            <div class="feature-tile"><h3>Smart progress</h3><p>Every attempt is saved to your profile so you can track improvement over time.</p></div>
            <div class="feature-tile"><h3>Weak-area alerts</h3><p>After each quiz the dashboard highlights the subjects you need to work on most.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Sign-in CTA
    auth_url = _clerk_build_auth_url() if _clerk_auth_available() else ""
    if auth_url:
        st.markdown(
            f"""
            <div style="text-align:center;margin:1.4rem 0 0.5rem">
                <a href="{auth_url}"
                   style="display:inline-block;text-decoration:none;
                          background:transparent;
                          border:1px solid rgba(220,20,60,0.5);
                          color:#ede0e0;
                          font-family:'Segoe UI',sans-serif;
                          font-size:0.86rem;
                          font-weight:600;
                          padding:0.44rem 1.6rem;
                          border-radius:5px;
                          letter-spacing:0.06em;"
                >Sign In</a>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        _, cta_mid, _ = st.columns([1.5, 1, 1.5])
        with cta_mid:
            if st.button("Sign In", use_container_width=True):
                st.info("⚠\ufe0f Fill in Clerk credentials in `.streamlit/secrets.toml`.")
    st.caption("Sign in to track your scores and get personalised improvement insights.")


def render_admin_login() -> None:
    # If Clerk is configured and the logged-in user's email matches ADMIN_EMAIL, bypass the form
    if _clerk_auth_available() and _is_admin_email() and _get_auth_user():
        st.session_state.admin_authenticated = True
        st.session_state.role = "admin"
        navigate("admin_dashboard")
        st.rerun()

    st.title("Admin Login")
    st.markdown('<p class="muted">Only an administrator can prepare, draft, or publish quizzes.</p>', unsafe_allow_html=True)
    password = st.text_input("Password", type="password")
    expected_password = get_secret("ADMIN_PASSWORD", "")
    if not expected_password:
        st.error("Admin password is not configured. Set ADMIN_PASSWORD in Streamlit secrets.")
        return
    login_col, back_col = st.columns(2)
    with login_col:
        login_clicked = st.button("Login", use_container_width=True)
    with back_col:
        if st.button("Back to Dashboard", use_container_width=True):
            navigate("landing")
            st.rerun()
    if login_clicked:
        if password == expected_password:
            st.session_state.admin_authenticated = True
            st.session_state.role = "admin"
            navigate("admin_dashboard")
            st.rerun()
        else:
            st.error("You really thought you can hack my system? Stop trying, kindly attempt the quiz and study 😄")


def render_admin_dashboard() -> None:
    if not st.session_state.admin_authenticated:
        navigate("admin_login")
        st.rerun()

    col_t, col_o = st.columns([5, 1])
    with col_t:
        st.title("Admin Dashboard")
    with col_o:
        if st.button("Sign out", use_container_width=True):
            st.session_state.admin_authenticated = False
            st.session_state.role = "guest"
            navigate("landing")
            st.rerun()

    if not os.path.exists(QUIZZES_FILE):
        st.info("⚠️ **Ephemeral storage notice** — On Streamlit Cloud, quizzes are stored in a file that resets when the server restarts. Use the ‘Load sample quiz\u2019 button or re-upload your PDFs after a restart. For permanent storage, configure a database connection.")

    tab_build, tab_lib, tab_att, tab_feedback = st.tabs(["Build Quiz", "Quiz Library", "Attempts", "Feedback"])

    # ── TAB 1: BUILD QUIZ ───────────────────────────────────────────────
    with tab_build:
        st.markdown('<p class="muted">Upload a question paper PDF and an answer key PDF to build a quiz instantly. Manual entry and JSON paste are also available as fallback options.</p>', unsafe_allow_html=True)

        with st.container(border=True):
            st.subheader("Quiz details")
            q_title  = st.text_input("Quiz title", placeholder="e.g. Surgery High-Yield MCQs 2026", key="bld_title")
            q_desc   = st.text_input("Short description (optional)", key="bld_desc")
            q_subjs  = st.multiselect("Subjects covered", NEET_SUBJECTS, key="bld_subjects")
            q_status = st.radio("Status after saving", ["draft", "published"], horizontal=True, key="bld_status")

        draft = st.session_state.setdefault("draft_questions", [])
        st.caption(f"{len(draft)} question(s) in current draft.")

        in_pdf, in_manual, in_json = st.tabs(["PDF Upload", "Manual entry", "Paste JSON"])

        # ─ PDF UPLOAD ────────────────────────────────────────────────────────
        with in_pdf:
            # One-click demo loader
            SAMPLE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_quiz.json")
            if os.path.exists(SAMPLE_FILE):
                st.markdown("**Demo available** — load the 30-question NEET PG sample (Pathology · Pharmacology · Microbiology) to test the full quiz flow instantly.")
                if st.button("Load sample quiz into draft", use_container_width=True):
                    try:
                        with open(SAMPLE_FILE) as f:
                            sample = json.load(f)
                        qs = sample.get("questions", [])
                        for q in qs:
                            q.setdefault("rationale", "")
                            q.setdefault("memory_tip", "Review this topic in your NEET PG notes.")
                            q.setdefault("red_flags", [])
                            q.setdefault("visual_type", "none")
                            q.setdefault("diagram_prompt", "")
                        draft.extend(qs)
                        if not st.session_state.get("bld_title"):
                            st.session_state["bld_title"] = sample.get("title", "NEET PG Sample Quiz")
                        if not st.session_state.get("bld_subjects"):
                            st.session_state["bld_subjects"] = sample.get("subjects", [])
                        st.success(f"Loaded {len(qs)} questions into draft. Fill in the quiz title and click Save quiz.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not load sample: {e}")
                st.divider()

            if _pdfplumber is None:
                st.warning("pdfplumber not installed. Run `python3 -m pip install pdfplumber` then restart the app.")
            else:
                col_paper, col_key = st.columns(2)
                with col_paper:
                    paper_file = st.file_uploader(
                        "Question paper PDF",
                        type=["pdf"],
                        key="paper_pdf",
                        help="PDF with numbered questions and A/B/C/D options.",
                    )
                with col_key:
                    key_file = st.file_uploader(
                        "Answer key PDF",
                        type=["pdf"],
                        key="key_pdf",
                        help="PDF with answers per question number, optionally with memory tips after a dash.",
                    )
                pdf_subjs = st.multiselect(
                        "Subjects in this paper",
                        NEET_SUBJECTS,
                        default=["Medicine"],
                        key="pdf_subjs",
                        help="Select all subjects present. Questions are distributed across subjects in order — edit individual questions in the draft to reassign.",
                    )

                with st.expander("Supported answer key formats"):
                    st.code("""# Format 1 – plain list
1. A
2. C - SLUDGE mnemonic for cholinergic toxicity
3. B

# Format 2 – rationale pipe memory tip
1. A - Inferior STEMI pattern | MONA-BASH mnemonic

# Format 3 – table (Q.No | Answer | Memory Tip)
1 | A | MONA-BASH
2 | C | SLUDGE""", language="text")

                if st.button("Parse PDFs and add to draft", use_container_width=True):
                    if not paper_file:
                        st.error("Upload the question paper PDF.")
                    elif not key_file:
                        st.error("Upload the answer key PDF.")
                    elif not pdf_subjs:
                        st.error("Select at least one subject.")
                    else:
                        with st.spinner("Extracting and parsing PDFs…"):
                            try:
                                paper_bytes = paper_file.read()
                                pdf_pages   = _extract_pdf_pages(paper_bytes)
                                q_text = "\n".join(t for t, _ in pdf_pages)
                                a_text = _extract_pdf_text(key_file.read())
                                parsed_qs = _parse_question_paper(q_text)
                                with st.spinner("Extracting diagram images from PDF\u2026"):
                                    _assign_diagrams_to_questions(parsed_qs, pdf_pages)
                                answers   = _parse_answer_key(a_text)
                                merged, unmatched = _merge_pdf_questions(
                                    parsed_qs, answers, pdf_subjs
                                )
                                valid    = [q for q in merged if len(q["options"]) == 4 and q["answer"]]
                                no_ans   = [q for q in merged if not q["answer"]]
                                draft.extend(valid)
                                if valid:
                                    st.success(
                                        f"Added {len(valid)} question(s) to draft." +
                                        (f" {len(no_ans)} had no matching answer and were skipped." if no_ans else "")
                                    )
                                else:
                                    st.error(
                                        "No parseable questions found. Make sure the question paper uses numbered "
                                        "questions with A/B/C/D options and the answer key has matching numbers."
                                    )
                                if unmatched:
                                    shown = ", ".join(map(str, sorted(unmatched[:10])))
                                    st.warning(f"No answer found for question(s): {shown}" + ("…" if len(unmatched) > 10 else ""))
                            except Exception as exc:
                                st.error(f"Parse error: {exc}")

        # ─ MANUAL ENTRY ──────────────────────────────────────────────────────
        with in_manual:
            with st.form("q_form", clear_on_submit=True):
                q_text = st.text_area("Question text (clinical vignette or stem)", height=120)
                c1, c2 = st.columns(2)
                with c1:
                    oa = st.text_input("Option A")
                    oc = st.text_input("Option C")
                with c2:
                    ob = st.text_input("Option B")
                    od = st.text_input("Option D")
                r1, r2, r3 = st.columns(3)
                with r1:
                    correct_label = st.selectbox("Correct option", ["A", "B", "C", "D"])
                with r2:
                    diff = st.selectbox("Difficulty", ["Medium", "Hard", "Easy"])
                with r3:
                    subj = st.selectbox("Subject", NEET_SUBJECTS)
                mem = st.text_input("Memory tip / mnemonic (optional)")
                rat = st.text_area("Rationale / explanation (optional)", height=68)
                add_clicked = st.form_submit_button("Add question to draft")

            if add_clicked:
                opts = [oa, ob, oc, od]
                label_map = {"A": oa, "B": ob, "C": oc, "D": od}
                ans_text = label_map[correct_label]
                if not q_text.strip() or not all(o.strip() for o in opts):
                    st.error("Fill in the question stem and all four options.")
                else:
                    qid = f"manual-{len(draft)+1:03d}-{datetime.now().strftime('%H%M%S')}"
                    draft.append({
                        "id": qid,
                        "specialty": subj,
                        "difficulty": diff,
                        "question": q_text.strip(),
                        "options": [o.strip() for o in opts],
                        "answer": ans_text.strip(),
                        "rationale": rat.strip(),
                        "memory_tip": mem.strip() or "Review this topic in your NEET PG notes.",
                        "red_flags": [],
                        "visual_type": "none",
                        "diagram_prompt": "",
                    })
                    st.success(f"Q{len(draft)} added: {q_text.strip()[:70]}…")

        # ─ PASTE JSON ────────────────────────────────────────────────────────
        with in_json:
            st.markdown("Paste a **JSON array** `[...]` of question objects. Each object needs: `question`, `options` (4 items), `answer` (exact text or letter A-D).")
            TEMPLATE = json.dumps([{
                "question": "A 45-year-old man presents with...",
                "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
                "answer": "Option A text",
                "subject": "Medicine",
                "difficulty": "Hard",
                "memory_tip": "Optional mnemonic (shown only for wrong answers)",
                "rationale": "Optional explanation shown in results"
            }], indent=2)
            with st.expander("JSON format — click to see template"):
                st.code(TEMPLATE, language="json")
                st.caption("'answer' can be the letter \"A\"/\"B\"/\"C\"/\"D\" or the exact option text.  Use \"subject\" or \"specialty\" interchangeably.")
            raw_json = st.text_area("Paste JSON here", height=220, key="json_paste",
                                    placeholder='[{"question": "...", "options": [...], "answer": "..."}]')
            if st.button("Import questions", use_container_width=True):
                if not raw_json.strip():
                    st.error("Paste a JSON array first.")
                else:
                    try:
                        parsed = json.loads(raw_json)
                        if isinstance(parsed, dict) and "questions" in parsed:
                            parsed = parsed["questions"]
                        if not isinstance(parsed, list):
                            st.error("JSON must be an array [...] of question objects.")
                        else:
                            imported, errors = [], []
                            for i, raw in enumerate(parsed):
                                try:
                                    if "subject" in raw and "specialty" not in raw:
                                        raw["specialty"] = raw.pop("subject")
                                    raw.setdefault("specialty", "Medicine")
                                    raw.setdefault("difficulty", "Medium")
                                    raw.setdefault("rationale", "")
                                    raw.setdefault("memory_tip", "Review this topic in your NEET PG notes.")
                                    raw.setdefault("red_flags", [])
                                    raw.setdefault("visual_type", "none")
                                    raw.setdefault("diagram_prompt", "")
                                    ans = raw.get("answer", "")
                                    if isinstance(ans, str) and ans.strip().upper() in ("A", "B", "C", "D"):
                                        idx = ord(ans.strip().upper()) - ord("A")
                                        raw["answer"] = raw["options"][idx]
                                    q = validate_question(raw, i)
                                    imported.append(q)
                                except Exception as e:
                                    errors.append(f"Q{i+1}: {e}")
                            draft.extend(imported)
                            msg = f"Imported {len(imported)} question(s)."
                            if errors:
                                msg += f" Skipped {len(errors)}: " + " | ".join(errors[:3])
                                st.warning(msg)
                            elif imported:
                                st.success(msg)
                            else:
                                st.error("No questions could be imported. Check the format and try again.")
                    except json.JSONDecodeError as e:
                        st.error(f"Invalid JSON — {e}")

        if draft:
            st.divider()
            st.subheader(f"Draft — {len(draft)} question(s)")
            diag_edit_id = st.session_state.get("diag_edit_id")
            DIAG_TYPES = [
                "ecg", "xray", "ct", "mri", "ultrasound", "histology",
                "lab_table", "flowchart", "pedigree", "clinical_image",
                "public_health_chart",
            ]
            for i, q in enumerate(list(draft)):
                has_diag = q.get("visual_type", "none") != "none"
                diag_badge = f" • [{q['visual_type'].upper()}]" if has_diag else ""
                label = f"Q{i+1} · {q['difficulty']} · {q['specialty']}{diag_badge} · {q['question'][:55]}…"
                with st.expander(label):
                    for j, opt in enumerate(q["options"]):
                        marker = "✓ " if opt == q["answer"] else "   "
                        st.write(f"{marker}{chr(65+j)}. {opt}")
                    if q.get("rationale"):
                        st.caption(f"Rationale: {q['rationale'][:130]}")
                    if q.get("memory_tip") and q["memory_tip"] != "Review this topic in your NEET PG notes.":
                        st.caption(f"Memory tip: {q['memory_tip']}")

                    # Diagram status badge
                    if has_diag:
                        st.markdown(
                            f'<div class="diag-title-bar" style="margin:0.5rem 0;border-radius:6px">'
                            f'<span class="diag-badge diag-badge-dflt">{q["visual_type"].upper()}</span>'
                            f'<span class="diag-badge-info">&nbsp;{q["diagram_prompt"][:80]}</span></div>',
                            unsafe_allow_html=True,
                        )

                    # Action row
                    act1, act2, act3 = st.columns(3)
                    with act1:
                        diag_label = "Edit diagram" if has_diag else "Attach diagram"
                        if st.button(diag_label, key=f"diag-open-{q['id']}"):
                            st.session_state["diag_edit_id"] = q["id"] if diag_edit_id != q["id"] else None
                            st.rerun()
                    with act2:
                        if has_diag and st.button("Remove diagram", key=f"diag-rm-{q['id']}"):
                            draft[i]["visual_type"] = "none"
                            draft[i]["diagram_prompt"] = ""
                            if diag_edit_id == q["id"]:
                                st.session_state["diag_edit_id"] = None
                            st.rerun()
                    with act3:
                        if st.button("Remove question", key=f"rm-{q['id']}"):
                            draft.pop(i)
                            if diag_edit_id == q["id"]:
                                st.session_state["diag_edit_id"] = None
                            st.rerun()

                    # Inline diagram editor — shown only for the question being edited
                    if diag_edit_id == q["id"]:
                        st.markdown("---")
                        st.markdown("**Attach diagram to this question**")
                        type_opts = ["(select type)"] + DIAG_TYPES
                        cur_type = q.get("visual_type", "none")
                        cur_idx  = DIAG_TYPES.index(cur_type) + 1 if cur_type in DIAG_TYPES else 0
                        chosen_type = st.selectbox(
                            "Diagram / investigation type",
                            type_opts,
                            index=cur_idx,
                            key=f"diag-type-{q['id']}",
                            help="ECG strip · X-ray · CT · MRI · Ultrasound · Histology · Lab table · Flowchart · Pedigree · Clinical photo · Public-health chart",
                        )
                        chosen_prompt = st.text_area(
                            "Describe what the image/diagram shows",
                            value=q.get("diagram_prompt", ""),
                            height=90,
                            key=f"diag-prompt-{q['id']}",
                            placeholder="e.g. ECG strip showing ST elevation in leads II, III, aVF with reciprocal changes in I and aVL",
                        )
                        col_save_d, col_cancel_d = st.columns(2)
                        with col_save_d:
                            if st.button("Save diagram", key=f"diag-save-{q['id']}"):
                                if chosen_type == "(select type)":
                                    st.error("Select a diagram type first.")
                                elif not chosen_prompt.strip():
                                    st.error("Describe what the diagram shows.")
                                else:
                                    draft[i]["visual_type"]   = chosen_type
                                    draft[i]["diagram_prompt"] = chosen_prompt.strip()
                                    st.session_state["diag_edit_id"] = None
                                    st.rerun()
                        with col_cancel_d:
                            if st.button("Cancel", key=f"diag-cancel-{q['id']}"):
                                st.session_state["diag_edit_id"] = None
                                st.rerun()

            col_sv, col_cl = st.columns(2)
            with col_sv:
                if st.button("Save quiz", use_container_width=True):
                    title = st.session_state.get("bld_title", "").strip()
                    if not title:
                        st.error("Enter a quiz title before saving.")
                    else:
                        subjs  = st.session_state.get("bld_subjects") or []
                        status = st.session_state.get("bld_status", "draft")
                        desc   = st.session_state.get("bld_desc", "").strip() or f"{len(draft)}-question NEET PG quiz."
                        slug   = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
                        new_quiz = {
                            "id": f"{slug}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            "title": title,
                            "description": desc,
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "source": "Admin upload",
                            "subjects": subjs,
                            "status": status,
                            "questions": list(draft),
                        }
                        st.session_state.quizzes.insert(0, new_quiz)
                        save_quizzes(st.session_state.quizzes)
                        st.session_state.draft_questions = []
                        st.success(f"Saved \u2018{title}\u2019 with {len(new_quiz['questions'])} questions as {status}.")
                        st.rerun()
            with col_cl:
                if st.button("Clear draft", use_container_width=True):
                    st.session_state.draft_questions = []
                    st.rerun()

    # ── TAB 2: QUIZ LIBRARY ─────────────────────────────────────────────
    with tab_lib:
        if not st.session_state.quizzes:
            st.info("No quizzes yet. Build one in the \u2018Build Quiz\u2019 tab.")
        for index, quiz in enumerate(st.session_state.quizzes):
            quiz.setdefault("status", "published")
            quiz.setdefault("subjects", [])
            public_link = f"?view={PUBLIC_QUERY_TOKEN}&quiz_id={quiz['id']}"
            status_class = "pill" if quiz["status"] == "published" else "pill danger-pill"
            subjects_text = ", ".join(quiz.get("subjects", [])) or "Mixed subjects"
            st.markdown(
                f"""
                <div class="quiz-card">
                    <h3>{quiz['title']}</h3>
                    <p class="muted">{quiz['description']}</p>
                    <div class="pill-row">
                        <span class="{status_class}">{quiz['status'].title()}</span>
                        <span class="pill">{len(quiz['questions'])} questions</span>
                        <span class="pill">{subjects_text}</span>
                        <span class="pill">{quiz.get('source', 'Admin upload')}</span>
                        <span class="pill">{quiz['created_at']}</span>
                    </div>
                    <p class="muted">Share path: <code>{public_link}</code></p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_s, col_p, col_d = st.columns([1, 3, 1])
            with col_s:
                if quiz["status"] == "published":
                    if st.button("Unpublish", key=f"unp-{quiz['id']}", use_container_width=True):
                        st.session_state.quizzes[index]["status"] = "draft"
                        save_quizzes(st.session_state.quizzes)
                        st.rerun()
                else:
                    if st.button("Publish", key=f"pub-{quiz['id']}", use_container_width=True):
                        st.session_state.quizzes[index]["status"] = "published"
                        save_quizzes(st.session_state.quizzes)
                        st.rerun()
            with col_p:
                with st.expander(f"Preview: {quiz['title']}"):
                    diffs: dict[str, int] = {}
                    for q in quiz["questions"]:
                        d = q.get("difficulty", "Medium")
                        diffs[d] = diffs.get(d, 0) + 1
                    st.write("  ·  ".join(f"{d}: {n}" for d, n in sorted(diffs.items())))
                    diag_n = sum(1 for q in quiz["questions"] if q.get("visual_type", "none") != "none")
                    if diag_n:
                        st.write(f"Diagram questions: {diag_n}")
            with col_d:
                if st.button("Delete", key=f"del-{quiz['id']}", use_container_width=True):
                    st.session_state.quizzes.pop(index)
                    save_quizzes(st.session_state.quizzes)
                    st.rerun()

    # ── TAB 3: ATTEMPTS ───────────────────────────────────────────────────
    with tab_att:
        all_attempts = load_attempts()
        if not all_attempts:
            st.info("No quiz attempts recorded yet. Results appear here once candidates complete a quiz.")
        else:
            quiz_map = {q["id"]: q["title"] for q in st.session_state.quizzes}
            by_quiz: dict[str, list] = {}
            for att in all_attempts:
                by_quiz.setdefault(att.get("quiz_id", "unknown"), []).append(att)
            for qid, atts in by_quiz.items():
                title = quiz_map.get(qid, qid)
                with st.expander(f"{title}  —  {len(atts)} attempt(s)"):
                    for att in sorted(atts, key=lambda x: x.get("completed_at", ""), reverse=True):
                        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
                        c1.write(f"**{att.get('candidate', '—')}** · {att.get('email', '—')}")
                        c2.metric("Score", f"{att.get('score', 0)}/{att.get('max_score', 0)}")
                        c3.metric("Accuracy", f"{att.get('accuracy', 0)}%")
                        c4.metric("Correct", att.get("correct", 0))
                        c5.write(att.get("completed_at", "")[:10])
                        st.divider()

    # ── TAB 4: FEEDBACK ───────────────────────────────────────────────────
    with tab_feedback:
        feedback_rows = load_feedback()
        if not feedback_rows:
            st.info("No quiz feedback submitted yet.")
        else:
            for row in feedback_rows:
                created_at = str(row.get("created_at", ""))[:19]
                label = f"{row.get('quiz_title', 'Quiz')}  —  {row.get('rating', '—')}/5  —  {created_at}"
                with st.expander(label):
                    st.write(f"**Student:** {row.get('candidate', '—')} · {row.get('email', '—')}")
                    st.write(f"**Rating:** {row.get('rating', '—')}/5")
                    comments = row.get("comments") or "—"
                    next_quiz = row.get("next_quiz") or "—"
                    st.write(f"**How was the test:** {comments}")
                    st.write(f"**Wanted for next quiz:** {next_quiz}")


def render_public_dashboard() -> None:
    auth_user = _get_auth_user() if _clerk_auth_available() else None
    published_quizzes = [quiz for quiz in st.session_state.quizzes if quiz.get("status", "published") == "published"]
    st.markdown(
        f"""
        <div class="portal-hero">
            <div>
                <div class="section-kicker" style="margin:0">Practice library</div>
                <h1>Candidate Quiz Portal</h1>
                <p>{len(published_quizzes)} published quiz{'zes' if len(published_quizzes) != 1 else ''} available · progress saved to your profile</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if auth_user:
        c1, c2 = st.columns([4, 1])
        c1.markdown(f'<p class="muted">Welcome back, <strong>{_html.escape(auth_user["name"])}</strong>! Choose a quiz below.</p>', unsafe_allow_html=True)
        with c2:
            if st.button("My History", use_container_width=True):
                navigate("user_history")
                st.rerun()
    else:
        st.markdown('<p class="muted">Choose a quiz below. Sign in is required before the first vignette.</p>', unsafe_allow_html=True)
    selected_id = st.session_state.active_quiz_id

    if not published_quizzes:
        st.info("No quizzes are published yet. Please check back after the admin publishes a quiz.")
        if st.button("Back"):
            navigate("landing")
            st.rerun()
        return

    for quiz in published_quizzes:
        subjects_text = ", ".join(quiz.get("subjects", [])) or "Mixed subjects"
        st.markdown(
            f"""
            <div class="quiz-card">
                <h3>{quiz['title']}</h3>
                <p class="muted">{quiz['description']}</p>
                <div class="pill-row">
                    <span class="pill">Published</span>
                    <span class="pill">{len(quiz['questions'])} questions</span>
                    <span class="pill">{subjects_text}</span>
                    <span class="pill">+4 / -1</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        label = "Attempt selected quiz" if selected_id == quiz["id"] else "Attempt quiz"
        if st.button(label, key=f"attempt-{quiz['id']}"):
            start_registration(quiz["id"])
            st.rerun()


def render_registration() -> None:
    quiz = get_active_quiz()
    if not quiz:
        st.error("Quiz not found.")
        navigate("public_dashboard")
        return

    # ─ Clerk path: skip the manual form entirely ─────────────────────────────────
    if _clerk_auth_available():
        auth_user = _get_auth_user()
        if not auth_user:
            st.title("Sign in to attempt this quiz")
            st.markdown(
                f'<div class="card"><h3>{_html.escape(quiz["title"])}</h3>'
                '<p class="muted">Create a free account or sign in to track your scores and attempt history.</p></div>',
                unsafe_allow_html=True,
            )
            if st.button("Sign in / Create account", use_container_width=True):
                auth_url = _clerk_build_auth_url()
                if auth_url:
                    st.markdown(
                        f'<a href="{auth_url}" class="cta-signin-link">Sign In</a>',
                        unsafe_allow_html=True,
                    )
            if st.button("Back", use_container_width=True):
                navigate("public_dashboard")
                st.rerun()
            return
        # Use Clerk identity — jump straight into the quiz
        st.session_state.user_details = {
            "name":       auth_user["name"],
            "email":      auth_user["email"],
            "started_at": datetime.now().isoformat(timespec="seconds"),
        }
        navigate("quiz_active")
        st.rerun()
        return

    # ─ Manual registration form (Clerk not configured) ───────────────────────
    st.title("Candidate Registration")
    st.markdown(f'<div class="card"><h3>{_html.escape(quiz["title"])}</h3><p class="muted">Submit details to unlock the first clinical vignette.</p></div>', unsafe_allow_html=True)
    name    = st.text_input("Full name")
    email   = st.text_input("Email")
    consent = st.checkbox("I confirm this is a self-assessment practice test and not medical advice.")

    if st.button("Start quiz", use_container_width=True):
        if not name.strip() or not email.strip() or "@" not in email:
            st.error("Enter a valid name and email before starting.")
            return
        if not consent:
            st.error("Confirm the practice-test disclaimer before starting.")
            return
        st.session_state.user_details = {
            "name":       name.strip(),
            "email":      email.strip(),
            "started_at": datetime.now().isoformat(timespec="seconds"),
        }
        navigate("quiz_active")
        st.rerun()


def submit_answer(question: dict[str, Any], selected: str) -> None:
    is_correct = selected == question["answer"]
    st.session_state.score += 4 if is_correct else -1
    response = {
        "question_id": question["id"],
        "question": question["question"],
        "selected": selected,
        "answer": question["answer"],
        "is_correct": is_correct,
        "rationale": question["rationale"],
        "memory_tip": question["memory_tip"],
        "red_flags": question.get("red_flags", []),
        "difficulty": question["difficulty"],
        "specialty": question["specialty"],
    }
    st.session_state.responses.append(response)
    if not is_correct:
        st.session_state.incorrect.append(response)

    st.session_state.current_question_index += 1
    quiz = get_active_quiz()
    if quiz and st.session_state.current_question_index >= len(quiz["questions"]):
        navigate("results")


def render_quiz() -> None:
    quiz = get_active_quiz()
    if not quiz:
        st.error("Quiz not found.")
        navigate("public_dashboard")
        return
    if not st.session_state.user_details:
        navigate("registration")
        st.rerun()

    total = len(quiz["questions"])
    index = st.session_state.current_question_index
    question = quiz["questions"][index]
    progress = (index + 1) / total

    st.markdown(
        f"""
        <div class="quiz-topline">
            <span>Candidate: <strong>{_html.escape(st.session_state.user_details['name'])}</strong></span>
            <span style="color:var(--muted)">Question {index + 1} of {total}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _, exit_col = st.columns([5, 1])
    with exit_col:
        if st.button("Exit quiz", use_container_width=True):
            reset_attempt()
            st.session_state.user_details = {}
            navigate("public_dashboard")
            st.rerun()
    st.progress(progress, text=f"Question {index + 1} of {total}")
    st.markdown(
        f"""
        <div class="vignette-card">
            <div class="pill-row">
                <span class="pill">{_html.escape(question['specialty'])}</span>
                <span class="pill">{_html.escape(question['difficulty'])}</span>
                <span class="pill">+4 / -1</span>
            </div>
            <h3>Clinical Vignette</h3>
            <p>{_html.escape(question['question'])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Show real image extracted from PDF (takes priority over SVG fallback)
    if question.get("diagram_image"):
        st.markdown(
            '<div class="diag-frame">'
            '<div class="diag-title-bar">'
            '<span class="diag-badge diag-badge-dflt">CLINICAL DIAGRAM</span>'
            '</div>'
            f'<img src="{question["diagram_image"]}" '
            'style="max-width:100%;display:block;border-radius:0 0 8px 8px;"/>'
            '</div>',
            unsafe_allow_html=True,
        )
    elif question.get("visual_type", "none") != "none" and question.get("diagram_prompt"):
        render_diagram(question["visual_type"], question["diagram_prompt"])
    selected = st.radio("Choose the single best answer", question["options"], index=None)
    if st.button("Submit answer", use_container_width=True):
        if selected is None:
            st.error("Select an answer before submitting.")
            return
        submit_answer(question, selected)
        st.rerun()


def render_results() -> None:
    quiz = get_active_quiz()
    if not quiz:
        st.error("Quiz not found.")
        navigate("public_dashboard")
        return

    total = len(quiz["questions"])
    correct = sum(1 for response in st.session_state.responses if response["is_correct"])
    attempted = len(st.session_state.responses)
    accuracy = (correct / attempted * 100) if attempted else 0
    max_score = total * 4
    possible_min = total * -1
    percentage_of_max = (st.session_state.score / max_score * 100) if max_score else 0
    subject_summary: dict[str, dict[str, int]] = {}
    difficulty_summary: dict[str, dict[str, int]] = {}
    for response in st.session_state.responses:
        for bucket, key in ((subject_summary, response["specialty"]), (difficulty_summary, response["difficulty"])):
            bucket.setdefault(key, {"correct": 0, "total": 0})
            bucket[key]["total"] += 1
            if response["is_correct"]:
                bucket[key]["correct"] += 1

    st.title("Results Dashboard")
    st.markdown(f'<p class="muted">{quiz["title"]} | {st.session_state.user_details.get("name", "Candidate")}</p>', unsafe_allow_html=True)

    # Persist attempt once per session so admin can review it
    if not st.session_state.get("result_saved"):
        # Compute subject-level accuracy for the personalized dashboard
        subj_acc = {
            subj: round(data["correct"] / data["total"] * 100)
            for subj, data in subject_summary.items()
        }
        attempt = {
            "quiz_id":        st.session_state.active_quiz_id,
            "quiz_title":     quiz["title"],
            "candidate":      st.session_state.user_details.get("name", ""),
            "email":          st.session_state.user_details.get("email", ""),
            "score":          st.session_state.score,
            "max_score":      max_score,
            "accuracy":       round(accuracy, 1),
            "correct":        correct,
            "incorrect":      len(st.session_state.incorrect),
            "total":          total,
            "subject_accuracy": subj_acc,
            "completed_at":   datetime.now().isoformat(timespec="seconds"),
        }
        st.session_state["attempt_id"] = save_attempt(attempt)
        st.session_state["result_saved"] = True

    score_col, accuracy_col, correct_col, missed_col = st.columns(4)
    score_col.metric("Score", f"{st.session_state.score}/{max_score}", help=f"Minimum possible score: {possible_min}")
    accuracy_col.metric("Accuracy", f"{accuracy:.1f}%")
    correct_col.metric("Correct", correct)
    missed_col.metric("Incorrect", len(st.session_state.incorrect))

    st.subheader("Performance Breakdown")
    subject_col, difficulty_col = st.columns(2)
    with subject_col:
        st.markdown('<div class="card"><h3>By subject</h3>', unsafe_allow_html=True)
        for subject, data in sorted(subject_summary.items()):
            percent = data["correct"] / data["total"] * 100
            st.write(f"{subject}: {data['correct']}/{data['total']} correct ({percent:.0f}%)")
        st.markdown("</div>", unsafe_allow_html=True)
    with difficulty_col:
        st.markdown('<div class="card"><h3>By difficulty</h3>', unsafe_allow_html=True)
        for difficulty, data in sorted(difficulty_summary.items()):
            percent = data["correct"] / data["total"] * 100
            st.write(f"{difficulty}: {data['correct']}/{data['total']} correct ({percent:.0f}%)")
        st.write(f"Percent of maximum marks: {percentage_of_max:.1f}%")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Complete answer review"):
        for number, item in enumerate(st.session_state.responses, start=1):
            verdict = "Correct" if item["is_correct"] else "Incorrect"
            st.write(f"Q{number}. {verdict} | {item['specialty']} | {item['difficulty']}")
            st.write(f"Your answer: {item['selected']}")
            st.write(f"Correct answer: {item['answer']}")
            st.write(item["rationale"])

    st.markdown(
        '<div class="feedback-panel"><div class="section-kicker" style="margin:0 0 0.25rem">Feedback</div>'
        '<h2 class="section-title">Test Feedback</h2>'
        '<p class="muted" style="margin:0">Help shape the next quiz set with a quick note after reviewing your results.</p></div>',
        unsafe_allow_html=True,
    )
    if st.session_state.get("feedback_submitted"):
        st.success("Thanks for the feedback. It has been saved.")
    else:
        with st.form("quiz_feedback_form"):
            rating = st.slider("Overall test experience", 1, 5, 4)
            comments = st.text_area("How was this test?", height=90)
            next_quiz = st.text_area("What would you want in the next quiz?", height=90)
            submitted = st.form_submit_button("Submit feedback", use_container_width=True)
        if submitted:
            saved = save_feedback({
                "attempt_id": st.session_state.get("attempt_id"),
                "quiz_id": st.session_state.active_quiz_id,
                "quiz_title": quiz["title"],
                "candidate": st.session_state.user_details.get("name", ""),
                "email": st.session_state.user_details.get("email", ""),
                "rating": rating,
                "comments": comments.strip(),
                "next_quiz": next_quiz.strip(),
                "created_at": datetime.now().isoformat(timespec="seconds"),
            })
            if saved:
                st.session_state["feedback_submitted"] = True
                st.rerun()
            else:
                st.error("Could not save feedback. Please try again.")

    st.subheader("Error Analysis")
    if not st.session_state.incorrect:
        st.success("No incorrect answers. Memory tips are intentionally reserved for missed items.")
    for item in st.session_state.incorrect:
        flags = "".join(f'<span class="pill">{_html.escape(str(flag))}</span>' for flag in item.get("red_flags", []))
        q_text   = _html.escape(item["question"]).replace("\n", " ")
        selected = _html.escape(item["selected"])
        correct  = _html.escape(item["answer"])
        rationale = _html.escape(item["rationale"]).replace("\n", " ")
        mem_tip  = _html.escape(item["memory_tip"])
        st.markdown(
            f"""
            <div class="result-card">
                <div class="pill-row">
                    <span class="pill">{_html.escape(item['specialty'])}</span>
                    <span class="pill">{_html.escape(item['difficulty'])}</span>
                    {flags}
                </div>
                <p><strong>Question:</strong> {q_text}</p>
                <p><strong>Your answer:</strong> {selected}</p>
                <p><strong>Correct answer:</strong> {correct}</p>
                <p><strong>Rationale:</strong> {rationale}</p>
                <div class="mnemonic"><strong>Memory tip:</strong> {mem_tip}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col_retry, col_home = st.columns(2)
    with col_retry:
        if st.button("Retry this quiz", use_container_width=True):
            reset_attempt()
            navigate("registration")
            st.rerun()
    with col_home:
        if st.button("Back to public dashboard", use_container_width=True):
            reset_attempt()
            st.session_state.user_details = {}
            navigate("public_dashboard")
            st.rerun()


def render_user_history() -> None:
    """Show all quiz attempts for the current Clerk-authenticated user."""
    auth_user = _get_auth_user()
    if not auth_user:
        navigate("landing")
        st.rerun()

    st.title("My Quiz History")
    st.caption(f"Signed in as {auth_user['email']}")

    all_attempts = load_attempts()
    my_attempts = [
        a for a in all_attempts
        if a.get("email", "").lower() == auth_user["email"].lower()
    ]

    if not my_attempts:
        st.info("You haven't completed any quizzes yet. Attempt a published quiz to see your history here.")
    else:
        total_quizzes = len(my_attempts)
        avg_acc = sum(a.get("accuracy", 0) for a in my_attempts) / total_quizzes
        best_acc = max(a.get("accuracy", 0) for a in my_attempts)
        m1, m2, m3 = st.columns(3)
        m1.metric("Quizzes taken", total_quizzes)
        m2.metric("Average accuracy", f"{avg_acc:.1f}%")
        m3.metric("Best accuracy", f"{best_acc:.1f}%")
        st.divider()

        quiz_titles = {q["id"]: q["title"] for q in st.session_state.quizzes}
        for att in sorted(my_attempts, key=lambda x: x.get("completed_at", ""), reverse=True):
            title = att.get("quiz_title") or quiz_titles.get(att.get("quiz_id", ""), "Quiz")
            label = f"{title}  —  {att.get('completed_at', '')[:10]}  |  {att.get('score', 0)}/{att.get('max_score', 0)} pts  |  {att.get('accuracy', 0)}%"
            with st.expander(label):
                c1, c2, c3 = st.columns(3)
                c1.metric("Score", f"{att.get('score', 0)}/{att.get('max_score', 0)}")
                c2.metric("Accuracy", f"{att.get('accuracy', 0)}%")
                c3.metric("Correct", f"{att.get('correct', 0)}/{att.get('total', 0)}")

    if st.button("Back to Quiz Portal", use_container_width=True):
        navigate("public_dashboard")
        st.rerun()


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="NP", layout="wide")
    inject_css()
    initialize_state()
    render_sidebar()

    # State machine routing: landing -> dashboard/login -> registration -> quiz -> results.
    routes = {
        "landing":          render_landing,
        "admin_login":      render_admin_login,
        "admin_dashboard":  render_admin_dashboard,
        "public_dashboard": render_public_dashboard,
        "registration":     render_registration,
        "quiz_active":      render_quiz,
        "results":          render_results,
        "user_history":     render_user_history,
    }
    routes.get(st.session_state.stage, render_landing)()


if __name__ == "__main__":
    main()