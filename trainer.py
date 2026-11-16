#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hot100 本地训练器命令行入口。

常用：
    python trainer.py serve            启动仪表盘与提醒
    python trainer.py status           查看今日计划
    python trainer.py start 1          开始第 1 题
    python trainer.py finish 1 done    标记完成
    python trainer.py check 1          用官方样例自测
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import webbrowser
from datetime import date, datetime, timedelta

from hot100 import checker, materials, notify, planner, server
from hot100.bank import BANK
from hot100.config import LOGS, ROOT, ensure_dirs, load_config, save_config
from hot100.store import RESULT_LABEL, Store

TASK_NAME = "Hot100Trainer"
RESULT_ALIAS = {
    "done": "done", "完成": "done", "独立": "done", "独立完成": "done",
    "hinted": "hinted", "提示": "hinted", "借提示": "hinted", "借提示完成": "hinted",
    "rewritten": "rewritten", "复现": "rewritten", "看题解后复现": "rewritten",
    "unfinished": "unfinished", "未完成": "unfinished",
}
WEEK = "一二三四五六日"


def _console() -> None:
    """Windows 控制台尽量切到 UTF-8，避免中文乱码。"""
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def say(text: str = "") -> None:
    try:
        if sys.stdout:
            print(text)
    except Exception:
        pass


def _load(store: Store | None = None) -> tuple[Store, list[dict], dict, dict[int, dict]]:
    cfg = load_config()
    data = materials.load_problems()
    problems = data["problems"]
    store = store or Store()
    store.sync_problems(problems)
    return store, problems, cfg, {p["id"]: p for p in problems}


def _item_for(store: Store, day: str, pid: int):
    for item in store.plan(day):
        if item["problem_id"] == pid:
            return item
    return None


def _limit(item, cfg: dict) -> int:
    return cfg["new_slot_minutes"] if item["kind"] == "new" else cfg["review_slot_minutes"]


def _status_line(item, by_id: dict[int, dict], states: dict) -> str:
    p = by_id.get(item["problem_id"], {})
    st = states.get(item["problem_id"])
    hints = st["hints_used"] if st else 0
    viewed = st["viewed_reference"] if st else 0
    tag = "新题" if item["kind"] == "new" else "复习"
    labels = {
        "pending": "未开始", "doing": "进行中", "done": "已完成",
        "unfinished": "未完成", "expired": "已过期",
    }
    extra = []
    if hints:
        extra.append(f"提示{hints}/2")
    if viewed:
        extra.append("看过参考")
    tail = (" · " + " · ".join(extra)) if extra else ""
    return (
        f"{item['planned_start']}-{item['planned_end']}  [{tag}] "
        f"#{item['problem_id']} {p.get('title', '')}  "
        f"{labels.get(item['status'], item['status'])}{tail}"
    )


def cmd_status(args) -> int:
    store, problems, cfg, by_id = _load()
    day = args.day or date.today().isoformat()
    summary = planner.ensure_day(store, problems, cfg, day)
    progress = summary["progress"]
    items = summary["items"]
    states = store.problems()
    done_today = sum(1 for i in items if i["status"] == "done")
    new_count = sum(1 for i in items if i["kind"] == "new")
    review_count = sum(1 for i in items if i["kind"] == "review")
    weekday = WEEK[date.fromisoformat(day).weekday()]
    say(f"{day} 周{weekday} · 距截止 {summary['days_left']} 天 · 截止 {cfg['deadline']}")
    say(
        f"总进度 {progress['done']}/{progress['total']} · 剩余 {progress['remaining']} · "
        f"今日完成 {done_today}/{len(items)} · 今日 {progress['minutes_today']} 分钟"
    )
    say(
        f"新题 {new_count} 道、复习 {review_count} 道，预计 "
        f"{new_count * cfg['new_slot_minutes'] + review_count * cfg['review_slot_minutes']} 分钟"
        f"（{cfg['session_start']}–{cfg['session_end']}）"
    )
    if summary["warnings"]:
        say("")
        for warning in summary["warnings"]:
            say("⚠ " + warning)
    say("")
    if not items:
        say("今天没有待办。")
    for item in items:
        say(_status_line(item, by_id, states))
    active = store.active_session()
    if active:
        say("")
        say(f"正在计时：#{active['problem_id']} {by_id.get(active['problem_id'], {}).get('title', '')}"
            f"（开始于 {active['started_at']}）")
    say("")
    say(f"文件：solutions/  problems/  reference/    仪表盘：http://127.0.0.1:{cfg['port']}/")
    return 0


def cmd_plan(args) -> int:
    return cmd_status(args)


def cmd_text(args) -> int:
    """纯文字模式：不启动服务，只打印今日计划和一道题的题面。"""
    store, problems, cfg, by_id = _load()
    day = args.day or date.today().isoformat()
    summary = planner.ensure_day(store, problems, cfg, day)
    items = summary["items"]
    states = store.problems()
    progress = summary["progress"]
    weekday = WEEK[date.fromisoformat(day).weekday()]
    done_today = sum(1 for i in items if i["status"] == "done")
    say(f"{day} 周{weekday} · 距截止 {summary['days_left']} 天 · 截止 {cfg['deadline']}")
    say(
        f"总进度 {progress['done']}/{progress['total']} · 剩余 {progress['remaining']} · "
        f"今日完成 {done_today}/{len(items)} · 今日 {progress['minutes_today']} 分钟"
    )
    if summary["warnings"]:
        for warning in summary["warnings"]:
            say("⚠ " + warning)
    say("")
    for item in items:
        say(_status_line(item, by_id, states))
    say("")

    pid = args.problem
    if pid is None:
        active = store.active_session()
        if active:
            pid = active["problem_id"]
        else:
            for item in items:
                if item["status"] in ("pending", "doing"):
                    pid = item["problem_id"]
                    break
    if pid is None:
        say("今天的题都完成了。")
        return 0

    problem = by_id.get(pid)
    if not problem:
        say(f"没有 #{pid} 这道题。")
        return 1
    paths = materials.problem_paths(problem["id"], problem["slug"])
    if not paths["statement"].exists():
        materials.ensure_problem(problem, create_solution=True)

    st = states.get(pid)
    hints = st["hints_used"] if st else 0
    viewed = st["viewed_reference"] if st else 0
    tags = [problem.get("difficulty", "")]
    if hints:
        tags.append(f"提示 {hints}/2")
    if viewed:
        tags.append("已看过参考")
    say("=" * 58)
    say(f"#{pid} {problem['title']} · " + " · ".join(t for t in tags if t))
    say("=" * 58)
    say(paths["statement"].read_text(encoding="utf-8").rstrip())
    say("")
    say(f"题解文件：{paths['solution'].relative_to(ROOT)}")
    say(f"计时：python trainer.py start {pid}    自测：python trainer.py check {pid}")
    say(f"提示：python trainer.py hint {pid}    参考：python trainer.py reference {pid}")
    return 0


def cmd_ensure(args) -> int:
    store, problems, cfg, _ = _load()
    materials.ensure_all(create_solutions=True)
    day = args.day or date.today().isoformat()
    summary = planner.ensure_day(store, problems, cfg, day)
    say(f"已生成 {len(problems)} 道题的题面、模板和参考题解。")
    say(f"{day} 计划：{len(summary['items'])} 项（新题 {summary['target_new']}，"
        f"复习 {min(summary['review_backlog'], cfg['max_reviews_per_day'])}）。")
    return 0


def cmd_start(args) -> int:
    store, problems, cfg, by_id = _load()
    day = date.today().isoformat()
    planner.ensure_day(store, problems, cfg, day)
    item = _item_for(store, day, args.problem)
    if not item:
        say(f"今天的计划里没有 #{args.problem}。先运行 python trainer.py status 查看，或 rebuild 重排。")
        return 1
    if item["status"] == "done":
        say("这题今天已经完成了。")
        return 1
    try:
        result = store.start_item(item["id"], _limit(item, cfg))
    except ValueError as exc:
        say(str(exc))
        return 1
    if result.get("already"):
        say("这题已经在计时。")
    else:
        say(f"开始 #{args.problem} {by_id[args.problem]['title']}，上限 {_limit(item, cfg)} 分钟。")
        say(f"写代码：solutions/{args.problem:04d}-{by_id[args.problem]['slug']}.py")
        say(f"完成后：python trainer.py finish {args.problem} done")
    return 0


def cmd_finish(args) -> int:
    store, problems, cfg, by_id = _load()
    result = RESULT_ALIAS.get(args.result.lower() if args.result.isascii() else args.result)
    if not result:
        say("状态应为 done / hinted / rewritten / unfinished（也可用中文）。")
        return 1
    day = date.today().isoformat()
    planner.ensure_day(store, problems, cfg, day)
    item = _item_for(store, day, args.problem)
    if not item:
        say(f"今天的计划里没有 #{args.problem}。")
        return 1
    try:
        detail = store.finish_item(item["id"], result, args.note or "", _limit(item, cfg))
    except ValueError as exc:
        say(str(exc))
        return 1
    minutes = max(0, round(detail["elapsed_sec"] / 60))
    say(f"已记录：{RESULT_LABEL[detail['result']]} · 用时 {minutes} 分钟")
    if detail["result"] == "rewritten":
        say("明天会安排一次闭卷重写。")
    elif detail["result"] == "hinted":
        say("1 天和 5 天后会各安排一次复习。")
    elif detail["result"] == "unfinished":
        say("明天会优先重新排入这题。")
    return 0


def cmd_hint(args) -> int:
    store, problems, cfg, by_id = _load()
    pid = args.problem
    entry = BANK.get(pid)
    if not entry:
        say("这道题没有准备提示。")
        return 1
    level = max(1, min(len(entry["hints"]), args.level))
    store.mark_hint(pid, level)
    say(f"#{pid} {by_id.get(pid, {}).get('title', '')} · 提示 {level}/{len(entry['hints'])}")
    say(entry["hints"][level - 1])
    return 0


def cmd_reference(args) -> int:
    store, problems, cfg, by_id = _load()
    problem = by_id.get(args.problem)
    if not problem:
        say("没有这道题。")
        return 1
    paths = materials.problem_paths(problem["id"], problem["slug"])
    if not paths["reference"].exists():
        materials.ensure_problem(problem, create_solution=False)
    store.mark_reference(problem["id"])
    say(f"#{problem['id']} {problem['title']} · 参考题解（已记录“看过参考”）")
    say("")
    say(paths["reference"].read_text(encoding="utf-8"))
    return 0


def cmd_check(args) -> int:
    store, problems, cfg, by_id = _load()
    problem = by_id.get(args.problem)
    if not problem:
        say("没有这道题。")
        return 1
    paths = materials.problem_paths(problem["id"], problem["slug"])
    if not paths["solution"].exists():
        materials.ensure_problem(problem, create_solution=True)
    say(f"运行 {paths['solution'].relative_to(ROOT)}")
    results = checker.check_file(problem, paths["solution"])
    if not results:
        say("这道题没有官方样例。")
        return 0
    failed = 0
    for row in results:
        mark = "PASS" if row["ok"] else "FAIL"
        say(f"  样例 {row['sample']}: {mark}")
        if not row["ok"]:
            failed += 1
            say("    " + (row.get("detail") or "").replace("\n", "\n    "))
    say(f"结果：{len(results) - failed}/{len(results)} 通过")
    return 0 if failed == 0 else 1


def cmd_rebuild(args) -> int:
    store, problems, cfg, _ = _load()
    day = args.day or date.today().isoformat()
    try:
        planner.rebuild_day(store, problems, cfg, day)
    except ValueError as exc:
        say(str(exc))
        return 1
    say("已按当前配置重排。")
    return cmd_status(args)


def cmd_config(args) -> int:
    cfg = load_config()
    changed = False
    for key in ("deadline", "session_start", "session_end", "port"):
        value = getattr(args, key, None)
        if value is not None:
            cfg[key] = value if key in {"deadline", "session_start", "session_end"} else int(value)
            changed = True
    for key in ("new_slot_minutes", "review_slot_minutes", "max_new_per_day", "max_reviews_per_day"):
        value = getattr(args, key, None)
        if value is not None:
            cfg[key] = int(value)
            changed = True
    if changed:
        try:
            server._validate_config(cfg)
        except ValueError as exc:
            say(str(exc))
            return 1
        save_config(cfg)
        say("配置已保存。改动时段或截止日期后，运行 python trainer.py rebuild 重排今天。")
    say(f"截止 {cfg['deadline']} · 时段 {cfg['session_start']}–{cfg['session_end']} · "
        f"新题 {cfg['new_slot_minutes']} 分钟 · 复习 {cfg['review_slot_minutes']} 分钟")
    say(f"每日新题上限 {cfg['max_new_per_day']} · 每日复习上限 {cfg['max_reviews_per_day']} · 端口 {cfg['port']}")
    return 0


def cmd_reset(args) -> int:
    if not args.yes:
        say("这会清空全部进度、计划和复习记录。确认请加 --yes。")
        return 1
    store = Store()
    store.reset_problems()
    _load(store)
    say("进度已清空，题目文件保留。")
    return 0


def _task_action() -> str:
    pythonw = notify.pythonw()
    script = ROOT / "trainer.py"
    return f'"{pythonw}" "{script}" serve --no-browser'


def _task_time(cfg: dict) -> str:
    start = datetime.strptime(cfg["session_start"], "%H:%M") - timedelta(minutes=5)
    return start.strftime("%H:%M")


def _decode_console(data: bytes | None) -> str:
    if not data:
        return ""
    for encoding in ("utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "replace")


def _run_task_command(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True)
    return proc.returncode, _decode_console(proc.stdout), _decode_console(proc.stderr)


def cmd_install_task(args) -> int:
    cfg = load_config()
    when = args.time or _task_time(cfg)
    action = _task_action()
    cmd = [
        "schtasks", "/Create", "/TN", TASK_NAME, "/TR", action,
        "/SC", "DAILY", "/ST", when, "/F",
    ]
    try:
        code, out, err = _run_task_command(cmd)
    except FileNotFoundError:
        say("找不到 schtasks，确认这是 Windows 系统。")
        return 1
    if code != 0:
        say("创建计划任务失败：")
        say((out + err).strip())
        say("可以改用管理员 PowerShell 手动创建，命令：")
        say(" ".join(cmd))
        return 1
    say(f"已创建计划任务 {TASK_NAME}，每天 {when} 启动训练器（登录状态下运行）。")
    say("如果启动时提示端口被占用，说明训练器已经在运行，可直接打开仪表盘。")
    return 0


def cmd_uninstall_task(args) -> int:
    try:
        code, out, err = _run_task_command(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"])
    except FileNotFoundError:
        say("找不到 schtasks，确认这是 Windows 系统。")
        return 1
    if code != 0:
        say("没有找到可删除的计划任务，或删除失败：")
        say((out + err).strip())
        return 1
    say(f"已删除计划任务 {TASK_NAME}。")
    return 0


def cmd_task_status(args) -> int:
    try:
        code, out, err = _run_task_command(["schtasks", "/Query", "/TN", TASK_NAME, "/FO", "LIST"])
    except FileNotFoundError:
        say("找不到 schtasks，确认这是 Windows 系统。")
        return 1
    say((out or err).strip())
    return 0 if code == 0 else 1


def cmd_open(args) -> int:
    cfg = load_config()
    url = f"http://127.0.0.1:{cfg['port']}/"
    if not server.port_open(int(cfg["port"])):
        say(f"训练器还没启动。先运行 python trainer.py serve，或安装计划任务。")
        return 1
    webbrowser.open(url)
    say(f"已打开 {url}")
    return 0


def cmd_serve(args) -> int:
    ensure_dirs()
    LOGS.mkdir(parents=True, exist_ok=True)
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(LOGS / "server.log", encoding="utf-8")],
    )
    open_browser = args.browser
    try:
        return server.serve(port=args.port, open_browser=open_browser)
    except Exception:
        logging.getLogger("hot100").exception("训练器启动失败")
        return 1


def cmd_notify_window(args) -> int:
    notify.show_window(args.title, args.body, args.url)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hot100 本地训练器")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("serve", help="启动仪表盘和提醒")
    p.add_argument("--port", type=int)
    p.add_argument("--browser", dest="browser", action="store_true", help="强制打开浏览器")
    p.add_argument("--no-browser", dest="browser", action="store_false", help="不自动打开浏览器")
    p.set_defaults(browser=None, func=cmd_serve)

    for name, func, help_text in (
        ("status", cmd_status, "查看今日计划"),
        ("plan", cmd_plan, "查看今日计划"),
        ("text", cmd_text, "纯文字模式：打印今日计划和题面"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--day")
        if name == "text":
            p.add_argument("problem", type=int, nargs="?", help="题号，默认取当前未完成的第一题")
        p.set_defaults(func=func)

    p = sub.add_parser("ensure", help="生成题面、模板和参考题解")
    p.add_argument("--day")
    p.set_defaults(func=cmd_ensure)

    p = sub.add_parser("start", help="开始一道题")
    p.add_argument("problem", type=int)
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("finish", help="标记完成状态")
    p.add_argument("problem", type=int)
    p.add_argument("result", help="done / hinted / rewritten / unfinished 或中文")
    p.add_argument("-m", "--note", default="")
    p.set_defaults(func=cmd_finish)

    p = sub.add_parser("hint", help="查看分级提示")
    p.add_argument("problem", type=int)
    p.add_argument("level", type=int, nargs="?", default=1)
    p.set_defaults(func=cmd_hint)

    p = sub.add_parser("reference", help="查看参考题解并记录")
    p.add_argument("problem", type=int)
    p.set_defaults(func=cmd_reference)

    p = sub.add_parser("check", help="用官方样例自测 solutions 里的代码")
    p.add_argument("problem", type=int)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("rebuild", help="按当前配置重排今日计划")
    p.add_argument("--day")
    p.set_defaults(func=cmd_rebuild)

    p = sub.add_parser("config", help="查看或修改配置")
    p.add_argument("--deadline")
    p.add_argument("--session-start", dest="session_start")
    p.add_argument("--session-end", dest="session_end")
    p.add_argument("--new-slot-minutes", dest="new_slot_minutes", type=int)
    p.add_argument("--review-slot-minutes", dest="review_slot_minutes", type=int)
    p.add_argument("--max-new-per-day", dest="max_new_per_day", type=int)
    p.add_argument("--max-reviews-per-day", dest="max_reviews_per_day", type=int)
    p.add_argument("--port", type=int)
    p.set_defaults(func=cmd_config)

    p = sub.add_parser("reset", help="清空进度（保留题目文件）")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_reset)

    p = sub.add_parser("install-task", help="安装 Windows 每日计划任务")
    p.add_argument("--time", help="启动时间 HH:MM，默认练习开始前 5 分钟")
    p.set_defaults(func=cmd_install_task)

    p = sub.add_parser("uninstall-task", help="删除计划任务")
    p.set_defaults(func=cmd_uninstall_task)

    p = sub.add_parser("task-status", help="查看计划任务状态")
    p.set_defaults(func=cmd_task_status)

    p = sub.add_parser("open", help="打开仪表盘")
    p.set_defaults(func=cmd_open)

    p = sub.add_parser("notify-window", help=argparse.SUPPRESS)
    p.add_argument("title")
    p.add_argument("body")
    p.add_argument("url", nargs="?")
    p.set_defaults(func=cmd_notify_window)

    return parser


def main(argv: list[str] | None = None) -> int:
    _console()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    ensure_dirs()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
