"""本地 HTTP 服务：仪表盘 API、计时状态与桌面提醒调度。"""
from __future__ import annotations

import ast
import html
import json
import logging
import re
import socket
import threading
import webbrowser
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import dashboard, judge, materials, motivation, notify, official, planner
from .bank import BANK
from .config import ROOT, load_config, save_config
from .store import RESULT_LABEL, Store

log = logging.getLogger("hot100")

WEEK = "一二三四五六日"
CONFIG_FIELDS = (
    "deadline", "session_start", "session_end", "new_slot_minutes",
    "review_slot_minutes", "max_reviews_per_day", "max_new_per_day",
    "port", "notify", "open_dashboard",
)


# ---------------------------------------------------------------- Markdown
def _link(match: re.Match) -> str:
    text, href = match.group(1), match.group(2)
    if href.startswith("../"):
        return text
    if href.startswith(("http://", "https://")):
        return f'<a href="{href}" target="_blank" rel="noreferrer">{text}</a>'
    return text


def inline_md(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", _link, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def markdown_to_html(text: str) -> str:
    out: list[str] = []
    code: list[str] | None = None
    in_list = False
    para: list[str] = []

    def flush_para() -> None:
        if para:
            out.append("<p>" + inline_md(" ".join(para)) + "</p>")
            para.clear()

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            if code is None:
                flush_para()
                close_list()
                code = []
            else:
                out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
                code = None
            continue
        if code is not None:
            code.append(raw)
            continue
        if not line.strip():
            flush_para()
            close_list()
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)$", line)
        if heading:
            flush_para()
            close_list()
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline_md(heading.group(2))}</h{level}>")
            continue
        if line.lstrip().startswith("- "):
            flush_para()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>" + inline_md(line.lstrip()[2:]) + "</li>")
            continue
        close_list()
        para.append(line.strip())
    flush_para()
    close_list()
    return "\n".join(out)


# ---------------------------------------------------------------- 应用
class App:
    def __init__(self) -> None:
        self.cfg = load_config()
        data = materials.load_problems()
        self.problems: list[dict] = data["problems"]
        self.by_id: dict[int, dict] = {p["id"]: p for p in self.problems}
        self.store = Store()
        self.store.sync_problems(self.problems)
        materials.ensure_all(create_solutions=True)
        self.port = int(self.cfg["port"])
        self.lock = threading.Lock()

    # ---- 基础
    def reload_config(self) -> dict:
        self.cfg = load_config()
        return self.cfg

    def summary(self, day: str | None = None) -> dict:
        day = day or date.today().isoformat()
        return planner.ensure_day(self.store, self.problems, self.cfg, day)

    def problem_brief(self, pid: int) -> dict:
        p = self.by_id.get(pid, {})
        return {
            "id": pid,
            "title": p.get("title", f"题目 {pid}"),
            "slug": p.get("slug", ""),
            "difficulty": p.get("difficulty", ""),
            "group": p.get("group", ""),
        }

    def resolve_item(self, payload: dict):
        item_id = payload.get("item_id")
        if item_id:
            row = self.store.plan_item(int(item_id))
            if row:
                return row
        pid = payload.get("problem_id")
        if pid:
            for row in self.store.plan(date.today().isoformat()):
                if row["problem_id"] == int(pid):
                    return row
        return None

    def resolve_problem(self, payload: dict) -> dict | None:
        pid = payload.get("problem_id")
        if pid:
            return self.by_id.get(int(pid))
        row = self.resolve_item(payload)
        return self.by_id.get(row["problem_id"]) if row else None

    # ---- 状态
    def state(self) -> dict:
        day = date.today().isoformat()
        summary = self.summary(day)
        problem_rows = self.store.problems()
        active = self.store.active_session()
        items = []
        for row in summary["items"]:
            pid = row["problem_id"]
            brief = self.problem_brief(pid)
            pstate = problem_rows.get(pid)
            session = self.store.last_session_for_item(row["id"])
            limit = self.cfg["new_slot_minutes"] if row["kind"] == "new" else self.cfg["review_slot_minutes"]
            items.append({
                **brief,
                "problem_id": pid,
                "item_id": row["id"],
                "id": row["id"],
                "kind": row["kind"],
                "slot": row["slot"],
                "planned_start": row["planned_start"],
                "planned_end": row["planned_end"],
                "status": row["status"],
                "hints_used": pstate["hints_used"] if pstate else 0,
                "viewed_reference": bool(pstate["viewed_reference"]) if pstate else False,
                "review_dates": self.store.review_dates(pid),
                "limit_minutes": limit,
                "note": (session["note"] if session else "") or ((pstate["note"] if pstate else "") or ""),
                "session": dict(session) if session else None,
            })
        items.sort(key=lambda i: (i["slot"], i["item_id"]))

        recent = []
        for row in self.store.latest_sessions(8):
            brief = self.problem_brief(row["problem_id"])
            recent.append({
                **brief,
                "problem_id": row["problem_id"],
                "day": row["day"],
                "kind": row["kind"],
                "result": row["result"],
                "elapsed_sec": row["elapsed_sec"],
                "ended_at": row["ended_at"],
            })

        new_count = sum(1 for i in items if i["kind"] == "new")
        review_count = sum(1 for i in items if i["kind"] == "review")
        planned = new_count * self.cfg["new_slot_minutes"] + review_count * self.cfg["review_slot_minutes"]
        today = date.today()
        mot = motivation.motivation_state(self.store)
        mot["today"]["planned"] = len(items)
        return {
            "day": day,
            "day_week": f"{day} 周{WEEK[today.weekday()]}",
            "deadline": self.cfg["deadline"],
            "days_left": summary["days_left"],
            "target_new": summary["target_new"],
            "review_backlog": summary["review_backlog"],
            "warnings": summary["warnings"],
            "progress": summary["progress"],
            "items": items,
            "current_item_id": active["plan_item_id"] if active and active["plan_item_id"] else None,
            "current_session_id": active["id"] if active else None,
            "recent": recent,
            "planned_minutes": planned,
            "session_start": self.cfg["session_start"],
            "session_end": self.cfg["session_end"],
            "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "motivation": mot,
            "config": {k: self.cfg.get(k) for k in CONFIG_FIELDS},
        }

    def badge_list(self) -> dict:
        return {"badges": motivation.badges(self.store)}

    # ---- 动作
    def start(self, payload: dict) -> dict:
        item = self.resolve_item(payload)
        if not item:
            raise ValueError("找不到今天的计划项，请先重排计划")
        limit = self.cfg["new_slot_minutes"] if item["kind"] == "new" else self.cfg["review_slot_minutes"]
        result = self.store.start_item(item["id"], limit)
        return {"item_id": item["id"], **result}

    def finish(self, payload: dict) -> dict:
        item = self.resolve_item(payload)
        if not item:
            raise ValueError("找不到今天的计划项")
        result = payload.get("result", "")
        if result not in RESULT_LABEL:
            raise ValueError("未知完成状态")
        limit = self.cfg["new_slot_minutes"] if item["kind"] == "new" else self.cfg["review_slot_minutes"]
        detail = self.store.finish_item(item["id"], result, str(payload.get("note", "")), limit)
        award_kind = None
        if item["kind"] in ("new", "extra"):
            award_kind = {"done": "ac_new", "hinted": "ac_hinted", "rewritten": "ac_rewritten"}.get(detail["result"])
        elif item["kind"] == "review" and detail["result"] != "unfinished":
            award_kind = "review_done"
        xp = motivation.award(self.store, award_kind, item["id"]) if award_kind else {"xp_gained": 0, "new_badges": []}
        return {"item_id": item["id"], **detail, **xp}

    def hint(self, payload: dict) -> dict:
        problem = self.resolve_problem(payload)
        if not problem:
            raise ValueError("找不到对应题目")
        entry = BANK.get(problem["id"])
        if not entry or not entry["hints"]:
            raise ValueError("这道题没有准备提示")
        level = max(1, min(len(entry["hints"]), int(payload.get("level", 1))))
        self.store.mark_hint(problem["id"], level)
        return {
            "problem_id": problem["id"],
            "level": level,
            "total": len(entry["hints"]),
            "hint": entry["hints"][level - 1],
        }

    def reference(self, payload: dict) -> dict:
        problem = self.resolve_problem(payload)
        if not problem:
            raise ValueError("找不到对应题目")
        paths = materials.problem_paths(problem["id"], problem["slug"])
        if not paths["reference"].exists():
            materials.ensure_problem(problem, create_solution=False)
        self.store.mark_reference(problem["id"])
        return {
            "problem_id": problem["id"],
            "code": paths["reference"].read_text(encoding="utf-8"),
        }

    def check(self, payload: dict) -> dict:
        """兼容旧入口：按最近使用的模式跑全部官方用例。"""
        problem = self.resolve_problem(payload)
        if not problem:
            raise ValueError("找不到对应题目")
        mode = payload.get("mode") or self.store.last_mode(problem["id"])
        return self.run({**payload, "mode": mode})

    def _ensure_code_file(self, problem: dict, mode: str):
        paths = materials.problem_paths(problem["id"], problem["slug"])
        path = paths["core"] if mode == "core" else paths["solution"]
        if not path.exists():
            materials.ensure_problem(problem, create_solution=True)
        return path

    def code(self, pid: int, mode: str | None = None) -> dict:
        """读取整份可编辑代码（ACM 完整程序 / 核心代码脚手架）。"""
        problem = self.by_id.get(pid)
        if not problem:
            raise ValueError("找不到题目")
        mode = mode if mode in judge.MODES else self.store.last_mode(pid)
        path = self._ensure_code_file(problem, mode)
        cases = official.official_cases(problem)
        preview = [
            {
                "index": c["index"],
                "input": c["input_acm"] if mode == "acm" else c["input_lc"],
                "expected": c["expected_acm"] if mode == "acm" else c["expected_lc"],
                "note": c.get("note", ""),
                "source": c["source"],
            }
            for c in cases
        ]
        best = self.store.best_run(pid, mode)
        return {
            "problem_id": pid,
            "title": problem["title"],
            "mode": mode,
            "file": str(path.relative_to(ROOT)).replace("\\", "/"),
            "code": path.read_text(encoding="utf-8"),
            "cases": preview,
            "best": {
                "pass_rate": best["pass_rate"],
                "passed": best["passed"],
                "total": best["total"],
                "runs": self.store.run_count(pid, mode),
            } if best else None,
        }

    def save_code(self, payload: dict) -> dict:
        """整份文件写回：main、辅助函数、签名都允许用户删改，只校验语法。"""
        problem = self.resolve_problem(payload)
        if not problem:
            raise ValueError("找不到对应题目")
        mode = payload.get("mode") or self.store.last_mode(problem["id"])
        if mode not in judge.MODES:
            raise ValueError(f"未知模式 {mode}")
        code = payload.get("code")
        if not isinstance(code, str):
            raise ValueError("代码必须是字符串")
        if len(code) > 200_000:
            raise ValueError("代码太长")
        code = code.replace("\r\n", "\n").replace("\r", "\n")
        try:
            ast.parse(code)
        except SyntaxError as exc:
            raise ValueError(f"语法错误：第 {exc.lineno or '?'} 行 {exc.msg}") from exc
        path = self._ensure_code_file(problem, mode)
        tmp = path.parent / (path.name + ".tmp")
        tmp.write_text(code, encoding="utf-8", newline="\n")
        tmp.replace(path)
        self.store.set_mode(problem["id"], mode)
        return {
            "problem_id": problem["id"],
            "mode": mode,
            "file": str(path.relative_to(ROOT)).replace("\\", "/"),
        }

    def precompile(self, payload: dict) -> dict:
        code = payload.get("code")
        if not isinstance(code, str):
            raise ValueError("代码必须是字符串")
        # 语法错误是正常诊断结果，不是接口失败：ok 恒为 True，诊断放在 compile 里。
        return {"compile": judge.precompile(code.replace("\r\n", "\n"), "<editor>")}

    def run(self, payload: dict) -> dict:
        problem = self.resolve_problem(payload)
        if not problem:
            raise ValueError("找不到对应题目")
        mode = payload.get("mode") or self.store.last_mode(problem["id"])
        if mode not in judge.MODES:
            raise ValueError(f"未知模式 {mode}")
        if isinstance(payload.get("code"), str):
            self.save_code({**payload, "mode": mode})
        path = self._ensure_code_file(problem, mode)
        code = path.read_text(encoding="utf-8")
        try:
            result = judge.run(problem, mode, code, str(path))
        except SyntaxError as exc:
            raise ValueError(f"语法错误：第 {exc.lineno or '?'} 行 {exc.msg}") from exc
        self.store.record_run(problem["id"], mode, result["metrics"])
        self.store.set_mode(problem["id"], mode)
        best = self.store.best_run(problem["id"], mode)
        return {
            "problem_id": problem["id"],
            "mode": mode,
            "file": str(path.relative_to(ROOT)).replace("\\", "/"),
            **result,
            "best": {
                "pass_rate": best["pass_rate"],
                "passed": best["passed"],
                "total": best["total"],
                "runs": self.store.run_count(problem["id"], mode),
            } if best else None,
        }

    def run_detached(self, problem: dict, mode: str, code: str) -> dict:
        """考试/面试判题：不落盘、不记 code_runs、不切模式（DESIGN_v3 §2.3）。"""
        if mode not in judge.MODES:
            raise ValueError(f"未知模式 {mode}")
        if not isinstance(code, str):
            raise ValueError("代码必须是字符串")
        code = code.replace("\r\n", "\n").replace("\r", "\n")
        try:
            ast.parse(code)
        except SyntaxError as exc:
            raise ValueError(f"语法错误：第 {exc.lineno or '?'} 行 {exc.msg}") from exc
        cases = official.official_cases(problem)
        return judge.run_cases(problem, mode, code, "<detached>", cases)

    def reset_code(self, payload: dict) -> dict:
        """把当前模式的文件恢复为预生成模板。"""
        problem = self.resolve_problem(payload)
        if not problem:
            raise ValueError("找不到对应题目")
        mode = payload.get("mode") or self.store.last_mode(problem["id"])
        if mode not in judge.MODES:
            raise ValueError(f"未知模式 {mode}")
        path = self._ensure_code_file(problem, mode)
        text = materials.generate_core(problem) if mode == "core" else materials.generate_practice(problem)
        tmp = path.parent / (path.name + ".tmp")
        tmp.write_text(text, encoding="utf-8", newline="\n")
        tmp.replace(path)
        return {"problem_id": problem["id"], "mode": mode, "code": text}

    def statement(self, pid: int) -> dict:
        problem = self.by_id.get(pid)
        if not problem:
            raise ValueError("找不到题目")
        paths = materials.problem_paths(pid, problem["slug"])
        if not paths["statement"].exists():
            materials.ensure_problem(problem, create_solution=False)
        return {
            "problem_id": pid,
            "title": problem["title"],
            "html": markdown_to_html(paths["statement"].read_text(encoding="utf-8")),
        }

    def update_config(self, payload: dict) -> dict:
        cfg = load_config()
        for key in CONFIG_FIELDS:
            if key not in payload:
                continue
            value = payload[key]
            if key in {"new_slot_minutes", "review_slot_minutes", "max_reviews_per_day",
                       "max_new_per_day", "port"}:
                cfg[key] = int(value)
            elif key in {"notify", "open_dashboard"}:
                cfg[key] = bool(value)
            else:
                cfg[key] = str(value)
        _validate_config(cfg)
        save_config(cfg)
        self.cfg = cfg
        return {"config": {k: cfg.get(k) for k in CONFIG_FIELDS}}

    def replan(self, payload: dict) -> dict:
        day = payload.get("day") or date.today().isoformat()
        planner.rebuild_day(self.store, self.problems, self.cfg, day)
        return {"day": day}


def _validate_config(cfg: dict) -> None:
    try:
        date.fromisoformat(cfg["deadline"])
    except (KeyError, ValueError) as exc:
        raise ValueError("截止日期格式应为 YYYY-MM-DD") from exc
    for key in ("session_start", "session_end"):
        try:
            datetime.strptime(cfg[key], "%H:%M")
        except (KeyError, ValueError) as exc:
            raise ValueError("时间格式应为 HH:MM") from exc
    if cfg["session_end"] <= cfg["session_start"]:
        raise ValueError("结束时间必须晚于开始时间")
    if not 5 <= int(cfg["new_slot_minutes"]) <= 60:
        raise ValueError("新题分钟数应在 5–60 之间")
    if not 5 <= int(cfg["review_slot_minutes"]) <= 45:
        raise ValueError("复习分钟数应在 5–45 之间")
    if not 1 <= int(cfg["max_new_per_day"]) <= 12:
        raise ValueError("每日新题上限应在 1–12 之间")
    if not 0 <= int(cfg["max_reviews_per_day"]) <= 5:
        raise ValueError("每日复习上限应在 0–5 之间")
    if not 1024 <= int(cfg["port"]) <= 65535:
        raise ValueError("端口应在 1024–65535 之间")


# ---------------------------------------------------------------- 提醒调度
class Scheduler(threading.Thread):
    def __init__(self, app: App):
        super().__init__(daemon=True, name="hot100-scheduler")
        self.app = app
        self.stop = threading.Event()

    def run(self) -> None:
        while not self.stop.is_set():
            try:
                self.tick()
            except Exception:
                log.exception("提醒调度出错")
            self.stop.wait(20)

    def tick(self) -> None:
        app = self.app
        cfg = app.reload_config()
        now = datetime.now()
        day = now.date()
        day_key = day.isoformat()
        store = app.store

        summary = planner.ensure_day(store, app.problems, cfg, day_key)
        start = planner.at_time(day, cfg["session_start"])
        end = planner.at_time(day, cfg["session_end"])
        url = f"http://127.0.0.1:{app.port}/"

        # 自动打开仪表盘独立于桌面提醒开关
        if start <= now < end and cfg.get("open_dashboard"):
            open_key = f"open:{day_key}"
            if not store.notification_sent(open_key):
                try:
                    webbrowser.open(url)
                except Exception:
                    log.exception("打开仪表盘失败")
                store.mark_notification(open_key)

        if not cfg.get("notify"):
            return

        # 时段开始时提醒一次
        if start <= now < end:
            key = f"session:{day_key}"
            if not store.notification_sent(key):
                items = summary["items"]
                new_count = sum(1 for i in items if i["kind"] == "new")
                review_count = sum(1 for i in items if i["kind"] == "review")
                minutes = new_count * cfg["new_slot_minutes"] + review_count * cfg["review_slot_minutes"]
                notify.send(
                    "今晚训练开始",
                    f"新题 {new_count} 道，复习 {review_count} 道，预计 {minutes} 分钟。打开仪表盘开始第一题。",
                    url,
                )
                store.mark_notification(key)

        active = store.active_session()

        # 到点提醒：没有正在计时的题时，提醒下一题
        if start <= now < end and not active:
            for item in summary["items"]:
                if item["status"] not in ("pending",):
                    continue
                slot_start, slot_end = planner.item_times(item, cfg)
                if slot_start <= now < slot_end and (now - slot_start).total_seconds() <= 8 * 60:
                    if item["slot"] == 0 and (now - start).total_seconds() <= 8 * 60:
                        continue  # 开场提醒已覆盖第一题
                    key = f"slot:{day_key}:{item['id']}"
                    if not store.notification_sent(key):
                        title = f"{item['planned_start']} · {app.problem_brief(item['problem_id'])['title']}"
                        kind = "新题" if item["kind"] == "new" else "复习"
                        notify.send(title, f"{kind}时间到了，打开仪表盘开始计时。", url)
                        store.mark_notification(key)
                    break

        # 正在计时的题：15 分钟提示与超时提醒
        if active:
            started = datetime.fromisoformat(active["started_at"])
            elapsed = (now - started).total_seconds()
            if elapsed >= 15 * 60 and not active["hints_used"] and not active["viewed_reference"]:
                key = f"hint:{active['id']}"
                if not store.notification_sent(key):
                    notify.send(
                        "已经 15 分钟",
                        "卡住就看提示：先想清楚状态定义和边界，再动手写。",
                        url,
                    )
                    store.mark_notification(key)
            if elapsed >= active["limit_minutes"] * 60:
                key = f"timeup:{active['id']}"
                if not store.notification_sent(key):
                    notify.send(
                        "时间到",
                        f"这题已计时 {active['limit_minutes']} 分钟。可以先标记状态，明天优先重排。",
                        url,
                    )
                    store.mark_notification(key)

        # 收尾提醒
        if end <= now <= end + timedelta(minutes=30):
            key = f"end:{day_key}"
            if not store.notification_sent(key):
                done = sum(1 for i in summary["items"] if i["status"] == "done")
                notify.send("今晚收尾", f"今天已完成 {done} 道。记得在仪表盘标记未完成的题。", url)
                store.mark_notification(key)


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    app: App
    server_version = "Hot100Trainer/1.0"

    def log_message(self, fmt: str, *args) -> None:
        log.debug("%s - %s", self.address_string(), fmt % args)

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, data: dict, code: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send(code, raw, "application/json; charset=utf-8")

    def _html(self, text: str, code: int = 200) -> None:
        self._send(code, text.encode("utf-8"), "text/html; charset=utf-8")

    def _error(self, message: str, code: int = 400) -> None:
        self._json({"ok": False, "error": message}, code)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            if path in ("/", "/index.html"):
                self._html(dashboard.page())
            elif path == "/api/state":
                self._json({"ok": True, "state": self.app.state()})
            elif path == "/api/badges":
                self._json({"ok": True, **self.app.badge_list()})
            elif path == "/api/statement":
                query = parse_qs(parsed.query)
                pid = int((query.get("id") or ["0"])[0])
                self._json({"ok": True, **self.app.statement(pid)})
            elif path == "/api/code":
                query = parse_qs(parsed.query)
                pid = int((query.get("id") or ["0"])[0])
                mode = (query.get("mode") or [None])[0]
                self._json({"ok": True, **self.app.code(pid, mode)})
            elif path == "/health":
                self._send(200, b"ok", "text/plain; charset=utf-8")
            elif path == "/favicon.ico":
                self._send(204, b"", "image/x-icon")
            else:
                self._error("未知路径", 404)
        except ValueError as exc:
            self._error(str(exc), 400)
        except Exception as exc:  # pragma: no cover - 兜底
            log.exception("GET %s 失败", path)
            self._error(f"服务端错误：{exc}", 500)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length > 2_000_000:
                raise ValueError("请求体过大")
            raw = self.rfile.read(length) if length else b"{}"
            payload = json.loads(raw.decode("utf-8") or "{}")
            if not isinstance(payload, dict):
                raise ValueError("请求体应为 JSON 对象")
        except (ValueError, json.JSONDecodeError) as exc:
            self._error(f"请求格式错误：{exc}", 400)
            return
        try:
            if path in ("/api/run", "/api/check", "/api/precompile"):
                # 判题最长约 30 秒，不占用全局锁，避免阻塞仪表盘的状态轮询。
                if path == "/api/precompile":
                    data = self.app.precompile(payload)
                elif path == "/api/check":
                    data = self.app.check(payload)
                else:
                    data = self.app.run(payload)
                self._json({"ok": True, **data})
                return
            with self.app.lock:
                if path == "/api/start":
                    data = self.app.start(payload)
                elif path == "/api/finish":
                    data = self.app.finish(payload)
                elif path == "/api/hint":
                    data = self.app.hint(payload)
                elif path == "/api/reference":
                    data = self.app.reference(payload)
                elif path == "/api/code":
                    data = self.app.save_code(payload)
                elif path == "/api/reset_code":
                    data = self.app.reset_code(payload)
                elif path == "/api/config":
                    data = self.app.update_config(payload)
                elif path == "/api/replan":
                    data = self.app.replan(payload)
                else:
                    self._error("未知路径", 404)
                    return
            self._json({"ok": True, **data})
        except ValueError as exc:
            self._error(str(exc), 400)
        except Exception as exc:  # pragma: no cover - 兜底
            log.exception("POST %s 失败", path)
            self._error(f"服务端错误：{exc}", 500)


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.4):
            return True
    except OSError:
        return False


def serve(port: int | None = None, open_browser: bool | None = None) -> int:
    app = App()
    cfg = app.cfg
    port = int(port or cfg["port"])
    app.port = port
    url = f"http://127.0.0.1:{port}/"
    if port_open(port):
        log.info("服务已在运行：%s", url)
        if open_browser if open_browser is not None else cfg.get("open_dashboard"):
            webbrowser.open(url)
        log.info("训练器已在运行：%s", url)
        return 0

    handler = type("BoundHandler", (Handler,), {"app": app})
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError as exc:
        log.error("无法监听端口 %s：%s", port, exc)
        log.error("无法监听端口 %s：%s", port, exc)
        return 1
    httpd.daemon_threads = True
    Scheduler(app).start()
    if open_browser if open_browser is not None else cfg.get("open_dashboard"):
        try:
            webbrowser.open(url)
        except Exception:
            log.exception("打开浏览器失败")
    log.info("Hot100 训练台：%s（Ctrl+C 停止）", url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0
