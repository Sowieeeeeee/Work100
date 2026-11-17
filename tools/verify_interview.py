"""P4 验收：手撕面试三段式 + 锁定项 + 不污染。

用法：python -m tools.verify_interview

覆盖：
- start → outline（口述锁定）→ run（空代码 0 分）→ submit（印象分 + interview_done XP）；
- 锁定：面试壳 DOM 里不存在 #wsReset / #wsStatement / #wsModes（模式切换/提示/参考/重置全隐藏）；
- abandon 不发 XP；report/history 可读；全程不写 code_runs。
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hot100 import dashboard  # noqa: E402
from hot100.server import App  # noqa: E402
from hot100.store import Store  # noqa: E402

FAILS: list[str] = []
CHECKS = 0


def check(cond: bool, label: str, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if cond:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{(' — ' + detail) if detail else ''}")
        FAILS.append(label)


def main() -> int:
    app = App()
    tmp = Path(tempfile.mkdtemp(prefix="hot100-iv-"))
    app.store = Store(tmp / "state.db")

    def code_runs_count() -> int:
        with app.store.conn() as c:
            return int(c.execute("SELECT COUNT(*) AS n FROM code_runs").fetchone()["n"])

    before_runs = code_runs_count()

    print("== start → outline → run → submit")
    start = app.interview_start({"minutes": 35, "difficulty": "mixed"})
    check("interview_id" in start and start["problem"], f"返回 interview_id={start['interview_id']}")
    check("statement_html" in start["problem"], "有 statement_html")
    iv_id = start["interview_id"]
    pid = start["problem"]["id"]

    app.interview_outline({"interview_id": iv_id, "outline_text": "哈希表记录前缀和，O(n) 时间 O(n) 空间，边界空数组。", "outline_sec": 120})
    iv_row = app.store.interview_get(iv_id)
    check(bool(iv_row["outline_text"]), "口述已锁定")

    run = app.interview_run({"interview_id": iv_id, "code": ""})
    check(run["passed"] == 0 and run["total"] > 0, "空代码 0 通过")
    check(code_runs_count() == before_runs, "interview_run 不写 code_runs")

    sub = app.interview_submit({"interview_id": iv_id, "code": ""})
    check(sub["passed"] == 0, "submit 判 0 通过")
    check("impression" in sub and 0 <= sub["impression"] <= 100, f"印象分 {sub['impression']}")
    check(sub["xp_gained"] >= 35, f"interview_done XP >= 35（实际 {sub['xp_gained']}）")

    print("== report / history")
    rep = app.interview_report(iv_id)
    check(rep["interview_id"] == iv_id and "impression" in rep, "report 可读")
    hist = app.interview_history()
    check(any(i["id"] == iv_id for i in hist["interviews"]), "history 包含本场")

    print("== abandon 不发 XP")
    xp_before = app.store.xp_total()
    start2 = app.interview_start({"minutes": 30})
    app.interview_abandon({"interview_id": start2["interview_id"]})
    check(app.store.xp_total() == xp_before, "abandon 不发 XP")

    print("== DOM 锁定项（无 #wsReset/#wsStatement/#wsModes）")
    page = dashboard.PAGE
    mark = 'id="interviewShell"'
    shell = page[page.index(mark): page.index('id="toast"')]
    for forbidden in ("wsReset", "wsStatement", "wsModes"):
        check(forbidden not in shell, f"面试壳 DOM 不含 {forbidden}")

    print(f"\nP4 检查项：{CHECKS}，失败：{len(FAILS)}")
    for item in FAILS:
        print(f"  - {item}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
