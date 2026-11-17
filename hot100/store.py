"""SQLite 状态存储。"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from .config import db_path

COMPLETE = {"done", "hinted", "rewritten"}
RESULT_LABEL = {
    "done": "独立完成",
    "hinted": "借提示完成",
    "rewritten": "看题解后复现",
    "unfinished": "未完成",
}


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def today_iso() -> str:
    return datetime.now().date().isoformat()


class Store:
    def __init__(self, path: Path | None = None):
        self.path = path or db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    @contextmanager
    def conn(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init(self) -> None:
        with self.conn() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS problems (
                    id INTEGER PRIMARY KEY,
                    order_idx INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'todo',
                    hints_used INTEGER NOT NULL DEFAULT 0,
                    viewed_reference INTEGER NOT NULL DEFAULT 0,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    retry INTEGER NOT NULL DEFAULT 0,
                    completed_at TEXT,
                    note TEXT
                );
                CREATE TABLE IF NOT EXISTS plan_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    day TEXT NOT NULL,
                    problem_id INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    slot INTEGER NOT NULL,
                    planned_start TEXT NOT NULL,
                    planned_end TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    review_id INTEGER,
                    created_at TEXT NOT NULL,
                    UNIQUE(day, problem_id, kind)
                );
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    problem_id INTEGER NOT NULL,
                    due_date TEXT NOT NULL,
                    done INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    UNIQUE(problem_id, due_date)
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    day TEXT NOT NULL,
                    problem_id INTEGER NOT NULL,
                    plan_item_id INTEGER,
                    kind TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    elapsed_sec INTEGER NOT NULL DEFAULT 0,
                    limit_minutes INTEGER NOT NULL DEFAULT 25,
                    result TEXT,
                    hints_used INTEGER NOT NULL DEFAULT 0,
                    viewed_reference INTEGER NOT NULL DEFAULT 0,
                    note TEXT
                );
                CREATE TABLE IF NOT EXISTS notifications (
                    key TEXT PRIMARY KEY,
                    sent_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS code_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    problem_id INTEGER NOT NULL,
                    mode TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    total INTEGER NOT NULL,
                    errors INTEGER NOT NULL DEFAULT 0,
                    pass_rate REAL NOT NULL,
                    total_ms REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS code_mode (
                    problem_id INTEGER PRIMARY KEY,
                    mode TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS xp_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    ref_id INTEGER NOT NULL,
                    xp INTEGER NOT NULL,
                    day TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(kind, ref_id)
                );
                CREATE TABLE IF NOT EXISTS achievements (
                    id TEXT PRIMARY KEY,
                    unlocked_at TEXT NOT NULL,
                    day TEXT NOT NULL
                );
                """
            )

    # ---------- 写代码工作台 ----------
    def record_run(self, problem_id: int, mode: str, metrics: dict) -> None:
        with self.conn() as c:
            c.execute(
                "INSERT INTO code_runs(problem_id, mode, passed, total, errors, pass_rate, total_ms, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    problem_id, mode, metrics["passed"], metrics["total"], metrics["errors"],
                    metrics["pass_rate"], metrics["total_ms"], now_iso(),
                ),
            )
            c.execute(
                "DELETE FROM code_runs WHERE problem_id=? AND mode=? AND id NOT IN "
                "(SELECT id FROM code_runs WHERE problem_id=? AND mode=? ORDER BY id DESC LIMIT 40)",
                (problem_id, mode, problem_id, mode),
            )

    def best_run(self, problem_id: int, mode: str) -> dict | None:
        with self.conn() as c:
            row = c.execute(
                "SELECT * FROM code_runs WHERE problem_id=? AND mode=? "
                "ORDER BY pass_rate DESC, total_ms ASC, id DESC LIMIT 1",
                (problem_id, mode),
            ).fetchone()
            return dict(row) if row else None

    def run_count(self, problem_id: int, mode: str) -> int:
        with self.conn() as c:
            return c.execute(
                "SELECT COUNT(*) AS n FROM code_runs WHERE problem_id=? AND mode=?",
                (problem_id, mode),
            ).fetchone()["n"]

    def last_mode(self, problem_id: int) -> str:
        with self.conn() as c:
            row = c.execute(
                "SELECT mode FROM code_mode WHERE problem_id=?", (problem_id,)
            ).fetchone()
            return row["mode"] if row else "acm"

    def set_mode(self, problem_id: int, mode: str) -> None:
        with self.conn() as c:
            c.execute(
                "INSERT INTO code_mode(problem_id, mode) VALUES (?, ?) "
                "ON CONFLICT(problem_id) DO UPDATE SET mode=excluded.mode",
                (problem_id, mode),
            )

    # ---------- 题库同步 ----------
    def sync_problems(self, problems: Iterable[dict]) -> None:
        with self.conn() as c:
            for p in problems:
                c.execute(
                    "INSERT INTO problems(id, order_idx) VALUES (?, ?) "
                    "ON CONFLICT(id) DO UPDATE SET order_idx=excluded.order_idx",
                    (p["id"], p["order"]),
                )

    def reset_problems(self) -> None:
        with self.conn() as c:
            c.execute("DELETE FROM plan_items")
            c.execute("DELETE FROM reviews")
            c.execute("DELETE FROM sessions")
            c.execute("DELETE FROM notifications")
            c.execute("DELETE FROM problems")
            c.execute("DELETE FROM meta")

    def problems(self) -> dict[int, sqlite3.Row]:
        with self.conn() as c:
            return {row["id"]: row for row in c.execute("SELECT * FROM problems")}

    def problem(self, pid: int) -> sqlite3.Row | None:
        with self.conn() as c:
            return c.execute("SELECT * FROM problems WHERE id=?", (pid,)).fetchone()

    # ---------- 状态 ----------
    def mark_hint(self, pid: int, level: int) -> dict:
        level = max(1, min(2, int(level)))
        with self.conn() as c:
            row = c.execute("SELECT hints_used FROM problems WHERE id=?", (pid,)).fetchone()
            used = max(level, row["hints_used"] if row else 0)
            c.execute("UPDATE problems SET hints_used=? WHERE id=?", (used, pid))
            active = c.execute(
                "SELECT id FROM sessions WHERE problem_id=? AND ended_at IS NULL ORDER BY id DESC LIMIT 1",
                (pid,),
            ).fetchone()
            if active:
                c.execute("UPDATE sessions SET hints_used=? WHERE id=?", (used, active["id"]))
        return {"hints_used": used}

    def mark_reference(self, pid: int) -> dict:
        with self.conn() as c:
            c.execute("UPDATE problems SET viewed_reference=1 WHERE id=?", (pid,))
            active = c.execute(
                "SELECT id FROM sessions WHERE problem_id=? AND ended_at IS NULL ORDER BY id DESC LIMIT 1",
                (pid,),
            ).fetchone()
            if active:
                c.execute("UPDATE sessions SET viewed_reference=1 WHERE id=?", (active["id"],))
            viewed = c.execute("SELECT viewed_reference FROM problems WHERE id=?", (pid,)).fetchone()
        return {"viewed_reference": bool(viewed["viewed_reference"]) if viewed else False}

    # ---------- 计划 ----------
    def plan(self, day: str) -> list[sqlite3.Row]:
        with self.conn() as c:
            return c.execute(
                "SELECT * FROM plan_items WHERE day=? ORDER BY slot, id", (day,)
            ).fetchall()

    def plan_item(self, item_id: int) -> sqlite3.Row | None:
        with self.conn() as c:
            return c.execute("SELECT * FROM plan_items WHERE id=?", (item_id,)).fetchone()

    def plan_item_by_problem(self, day: str, pid: int, kind: str) -> sqlite3.Row | None:
        with self.conn() as c:
            return c.execute(
                "SELECT * FROM plan_items WHERE day=? AND problem_id=? AND kind=?",
                (day, pid, kind),
            ).fetchone()

    def insert_plan_items(self, day: str, items: list[dict]) -> None:
        stamp = now_iso()
        with self.conn() as c:
            for item in items:
                c.execute(
                    "INSERT OR IGNORE INTO plan_items"
                    "(day, problem_id, kind, slot, planned_start, planned_end, status, review_id, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)",
                    (
                        day,
                        item["problem_id"],
                        item["kind"],
                        item["slot"],
                        item["planned_start"],
                        item["planned_end"],
                        item.get("review_id"),
                        stamp,
                    ),
                )

    def expire_before(self, day: str) -> None:
        with self.conn() as c:
            # 先关闭跨天遗留的计时，否则旧会话会一直占用“正在计时”。
            stale = c.execute(
                "SELECT * FROM sessions WHERE ended_at IS NULL AND day<?", (day,)
            ).fetchall()
            for row in stale:
                started = datetime.fromisoformat(row["started_at"])
                limit = int(row["limit_minutes"] or 25) * 60
                elapsed = min(limit, max(0, int((datetime.now() - started).total_seconds())))
                c.execute(
                    "UPDATE sessions SET ended_at=?, elapsed_sec=?, result=? WHERE id=?",
                    (now_iso(), elapsed, "unfinished", row["id"]),
                )
                current = c.execute(
                    "SELECT status FROM problems WHERE id=?", (row["problem_id"],)
                ).fetchone()
                # 如果这题后来已经完成，不要把它退回未完成。
                if current and current["status"] not in COMPLETE:
                    c.execute(
                        "UPDATE problems SET status='todo', attempts=attempts+1, retry=1 WHERE id=?",
                        (row["problem_id"],),
                    )
            c.execute(
                "UPDATE plan_items SET status='expired' WHERE day<? AND status IN ('pending','doing')",
                (day,),
            )

    def delete_day_plan(self, day: str) -> None:
        with self.conn() as c:
            done = c.execute(
                "SELECT COUNT(*) AS n FROM plan_items WHERE day=? AND status IN ('done','doing')",
                (day,),
            ).fetchone()["n"]
            if done:
                raise ValueError("今天已经有开始或完成的题目，不能重建计划")
            c.execute("DELETE FROM plan_items WHERE day=?", (day,))

    def next_slot_index(self, day: str) -> int:
        with self.conn() as c:
            row = c.execute("SELECT MAX(slot) AS s FROM plan_items WHERE day=?", (day,)).fetchone()
        return -1 if row["s"] is None else int(row["s"])

    # ---------- 计时与完成 ----------
    def active_session(self, day: str | None = None) -> sqlite3.Row | None:
        """当前正在计时的会话；默认只看今天，避免跨天旧会话挂着。"""
        day = day or today_iso()
        with self.conn() as c:
            return c.execute(
                "SELECT * FROM sessions WHERE ended_at IS NULL AND day=? ORDER BY id DESC LIMIT 1",
                (day,),
            ).fetchone()

    def start_item(self, item_id: int, limit_minutes: int) -> dict:
        item = self.plan_item(item_id)
        if not item:
            raise ValueError("计划项不存在")
        if item["status"] == "done":
            raise ValueError("这道题已经完成")
        active = self.active_session()
        if active:
            if active["plan_item_id"] == item_id:
                return {"session_id": active["id"], "already": True}
            raise ValueError("还有一题正在计时，先完成或标记上一题")
        stamp = now_iso()
        with self.conn() as c:
            cur = c.execute(
                "INSERT INTO sessions(day, problem_id, plan_item_id, kind, started_at, limit_minutes) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (item["day"], item["problem_id"], item_id, item["kind"], stamp, limit_minutes),
            )
            c.execute("UPDATE plan_items SET status='doing' WHERE id=?", (item_id,))
            return {"session_id": cur.lastrowid, "started_at": stamp, "already": False}

    def finish_item(self, item_id: int, result: str, note: str = "", limit_minutes: int = 25) -> dict:
        if result not in RESULT_LABEL:
            raise ValueError("未知完成状态")
        item = self.plan_item(item_id)
        if not item:
            raise ValueError("计划项不存在")
        pid = item["problem_id"]
        stamp = now_iso()
        with self.conn() as c:
            session = c.execute(
                "SELECT * FROM sessions WHERE plan_item_id=? AND ended_at IS NULL ORDER BY id DESC LIMIT 1",
                (item_id,),
            ).fetchone()
            if not session:
                cur = c.execute(
                    "INSERT INTO sessions(day, problem_id, plan_item_id, kind, started_at, limit_minutes) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (item["day"], pid, item_id, item["kind"], stamp, limit_minutes),
                )
                session_id = cur.lastrowid
                elapsed = 0
                hints_used = c.execute("SELECT hints_used FROM problems WHERE id=?", (pid,)).fetchone()["hints_used"]
                viewed = c.execute("SELECT viewed_reference FROM problems WHERE id=?", (pid,)).fetchone()["viewed_reference"]
            else:
                session_id = session["id"]
                started = datetime.fromisoformat(session["started_at"])
                elapsed = max(0, int((datetime.now() - started).total_seconds()))
                current = c.execute(
                    "SELECT hints_used, viewed_reference FROM problems WHERE id=?", (pid,)
                ).fetchone()
                hints_used = max(session["hints_used"], current["hints_used"] if current else 0)
                viewed = bool(session["viewed_reference"] or (current["viewed_reference"] if current else 0))
            if result == "done" and hints_used:
                result = "hinted"
            if viewed and result != "unfinished":
                result = "rewritten"
            c.execute(
                "UPDATE sessions SET ended_at=?, elapsed_sec=?, result=?, note=? WHERE id=?",
                (stamp, elapsed, result, note, session_id),
            )
            c.execute("UPDATE plan_items SET status=? WHERE id=?", ("done" if result != "unfinished" else "unfinished", item_id))
            if result == "unfinished":
                c.execute(
                    "UPDATE problems SET status='todo', attempts=attempts+1, retry=1, note=? WHERE id=?",
                    (note, pid),
                )
            else:
                c.execute(
                    "UPDATE problems SET status=?, attempts=attempts+1, retry=0, completed_at=?, note=? WHERE id=?",
                    (result, stamp, note, pid),
                )
            if item["kind"] == "review" and item["review_id"]:
                if result == "unfinished":
                    tomorrow = (datetime.now().date() + timedelta(days=1)).isoformat()
                    c.execute("UPDATE reviews SET due_date=? WHERE id=?", (tomorrow, item["review_id"]))
                else:
                    c.execute("UPDATE reviews SET done=1 WHERE id=?", (item["review_id"],))
        if item["kind"] == "new" and result in {"hinted", "rewritten"}:
            offset = 1 if result == "hinted" else 1
            self.add_review(pid, (datetime.now().date() + timedelta(days=offset)).isoformat())
            second = 5 if result == "hinted" else 4
            self.add_review(pid, (datetime.now().date() + timedelta(days=second)).isoformat())
        return {
            "result": result,
            "elapsed_sec": elapsed,
            "hints_used": hints_used,
            "viewed_reference": bool(viewed),
        }

    # ---------- 复习 ----------
    def add_review(self, pid: int, due_date: str) -> None:
        with self.conn() as c:
            c.execute(
                "INSERT OR IGNORE INTO reviews(problem_id, due_date, created_at) VALUES (?, ?, ?)",
                (pid, due_date, now_iso()),
            )

    def due_reviews(self, day: str) -> list[sqlite3.Row]:
        with self.conn() as c:
            return c.execute(
                "SELECT r.*, p.status AS problem_status FROM reviews r "
                "JOIN problems p ON p.id=r.problem_id "
                "WHERE r.done=0 AND r.due_date<=? ORDER BY r.due_date, r.id",
                (day,),
            ).fetchall()

    def review_backlog(self, day: str) -> int:
        with self.conn() as c:
            return c.execute(
                "SELECT COUNT(*) AS n FROM reviews WHERE done=0 AND due_date<=?", (day,)
            ).fetchone()["n"]

    # ---------- 通知 ----------
    def notification_sent(self, key: str) -> bool:
        with self.conn() as c:
            return c.execute("SELECT 1 FROM notifications WHERE key=?", (key,)).fetchone() is not None

    def mark_notification(self, key: str) -> None:
        with self.conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO notifications(key, sent_at) VALUES (?, ?)",
                (key, now_iso()),
            )

    # ---------- 元数据 ----------
    def get_meta(self, key: str, default: str | None = None) -> str | None:
        with self.conn() as c:
            row = c.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_meta(self, key: str, value: str) -> None:
        with self.conn() as c:
            c.execute(
                "INSERT INTO meta(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    # ---------- 统计 ----------
    def progress(self) -> dict:
        with self.conn() as c:
            rows = c.execute("SELECT status, COUNT(*) AS n FROM problems GROUP BY status").fetchall()
            counts = {row["status"]: row["n"] for row in rows}
            total = c.execute("SELECT COUNT(*) AS n FROM problems").fetchone()["n"]
            sessions = c.execute("SELECT COUNT(*) AS n, COALESCE(SUM(elapsed_sec),0) AS sec FROM sessions").fetchone()
            today = c.execute(
                "SELECT COUNT(*) AS n, COALESCE(SUM(elapsed_sec),0) AS sec FROM sessions WHERE day=? AND ended_at IS NOT NULL",
                (today_iso(),),
            ).fetchone()
            hints = c.execute("SELECT COALESCE(SUM(hints_used),0) AS n FROM problems").fetchone()["n"]
            refs = c.execute("SELECT COUNT(*) AS n FROM problems WHERE viewed_reference=1").fetchone()["n"]
        done = sum(counts.get(s, 0) for s in COMPLETE)
        return {
            "total": total,
            "done": done,
            "remaining": total - done,
            "by_status": {s: counts.get(s, 0) for s in ("todo", "done", "hinted", "rewritten")},
            "hints_used": hints,
            "reference_views": refs,
            "sessions_total": sessions["n"],
            "minutes_total": round(sessions["sec"] / 60),
            "sessions_today": today["n"],
            "minutes_today": round(today["sec"] / 60),
        }

    def latest_sessions(self, limit: int = 10) -> list[sqlite3.Row]:
        with self.conn() as c:
            return c.execute(
                "SELECT * FROM sessions WHERE ended_at IS NOT NULL ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()

    # ---------- 激励（P1） ----------
    def grant_xp(self, kind: str, ref_id: int, xp: int, day: str | None = None) -> tuple[bool, int]:
        """同 kind+ref 只发一次；返回 (是否新发, 实际 XP)。"""
        day = day or today_iso()
        with self.conn() as c:
            cur = c.execute(
                "INSERT OR IGNORE INTO xp_events(kind, ref_id, xp, day, created_at) VALUES (?, ?, ?, ?, ?)",
                (kind, int(ref_id), int(xp), day, now_iso()),
            )
            return (cur.rowcount > 0, int(xp) if cur.rowcount > 0 else 0)

    def xp_total(self) -> int:
        with self.conn() as c:
            return int(c.execute("SELECT COALESCE(SUM(xp),0) AS n FROM xp_events").fetchone()["n"] or 0)

    def xp_by_kind(self) -> dict[str, int]:
        with self.conn() as c:
            rows = c.execute("SELECT kind, COALESCE(SUM(xp),0) AS n FROM xp_events GROUP BY kind").fetchall()
        return {row["kind"]: int(row["n"]) for row in rows}

    def active_days(self) -> set[str]:
        """有完成记录的活跃日（sessions 已结束才计数；exams/interviews 表在 P3/P4 加入）。"""
        days: set[str] = set()
        with self.conn() as c:
            for row in c.execute("SELECT DISTINCT day FROM sessions WHERE ended_at IS NOT NULL"):
                days.add(row["day"])
            if self._has_table(c, "exams"):
                for row in c.execute("SELECT DISTINCT created_at FROM exams WHERE status != 'running'"):
                    days.add(row["created_at"][:10])
            if self._has_table(c, "interviews"):
                for row in c.execute("SELECT DISTINCT created_at FROM interviews WHERE status != 'running'"):
                    days.add(row["created_at"][:10])
        return days

    def _has_table(self, c, name: str) -> bool:
        row = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        return row is not None

    def unlocked_achievements(self) -> set[str]:
        with self.conn() as c:
            return {row["id"] for row in c.execute("SELECT id FROM achievements")}

    def unlock_achievement(self, badge_id: str, day: str | None = None) -> bool:
        day = day or today_iso()
        with self.conn() as c:
            cur = c.execute(
                "INSERT OR IGNORE INTO achievements(id, unlocked_at, day) VALUES (?, ?, ?)",
                (badge_id, now_iso(), day),
            )
            return cur.rowcount > 0

    def full_run_count(self) -> int:
        with self.conn() as c:
            return int(c.execute("SELECT COUNT(*) AS n FROM code_runs WHERE pass_rate >= 100").fetchone()["n"] or 0)

    def night_owl(self) -> bool:
        with self.conn() as c:
            row = c.execute(
                "SELECT COUNT(*) AS n FROM sessions WHERE ended_at IS NOT NULL "
                "AND CAST(substr(ended_at, 12, 2) AS INTEGER) >= 22"
            ).fetchone()
        return int(row["n"] or 0) > 0

    def exam_best_score(self) -> float:
        with self.conn() as c:
            if not self._has_table(c, "exams"):
                return 0.0
            row = c.execute("SELECT MAX(score) AS m FROM exams WHERE status='finished'").fetchone()
        return float(row["m"] or 0.0) if row else 0.0

    def interview_count(self) -> int:
        with self.conn() as c:
            if not self._has_table(c, "interviews"):
                return 0
            row = c.execute("SELECT COUNT(*) AS n FROM interviews WHERE status='finished'").fetchone()
        return int(row["n"] or 0) if row else 0

    def interview_best_rate(self) -> float:
        with self.conn() as c:
            if not self._has_table(c, "interviews"):
                return 0.0
            row = c.execute("SELECT MAX(pass_rate) AS m FROM interviews WHERE status='finished'").fetchone()
        return float(row["m"] or 0.0) if row else 0.0

    def topic_mastered(self) -> bool:
        return self.get_meta("topic_master") == "1"

    def last_session_for_item(self, item_id: int) -> sqlite3.Row | None:
        with self.conn() as c:
            return c.execute(
                "SELECT * FROM sessions WHERE plan_item_id=? ORDER BY id DESC LIMIT 1", (item_id,)
            ).fetchone()

    def review_dates(self, pid: int) -> list[str]:
        with self.conn() as c:
            return [
                row["due_date"]
                for row in c.execute(
                    "SELECT due_date FROM reviews WHERE problem_id=? AND done=0 ORDER BY due_date", (pid,)
                )
            ]
