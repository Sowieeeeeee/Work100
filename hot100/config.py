"""运行时常量：路径与默认配置。"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SESSIONS = ROOT / "sessions"
SOLUTIONS = ROOT / "solutions"
CORE = ROOT / "core"
REFERENCE = ROOT / "reference"
LOGS = ROOT / "logs"

DEFAULT_CONFIG = {
    "dataset": "hot100",
    "deadline": "2026-12-07",
    "session_start": "19:30",
    "session_end": "23:00",
    "new_slot_minutes": 25,
    "review_slot_minutes": 15,
    "max_reviews_per_day": 2,
    "max_new_per_day": 7,
    "port": 8765,
    "notify": True,
    "open_dashboard": True,
}


def ensure_dirs() -> None:
    for path in (DATA, SESSIONS, SOLUTIONS, CORE, REFERENCE, LOGS):
        path.mkdir(parents=True, exist_ok=True)


def config_path() -> Path:
    return DATA / "config.json"


def load_config() -> dict:
    ensure_dirs()
    path = config_path()
    if path.exists():
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            saved = {}
        cfg = {**DEFAULT_CONFIG, **saved}
    else:
        cfg = dict(DEFAULT_CONFIG)
        save_config(cfg)
    return cfg


def save_config(cfg: dict) -> None:
    ensure_dirs()
    path = config_path()
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def db_path() -> Path:
    return DATA / "state.db"


def problems_path() -> Path:
    return DATA / "problems.json"
