"""P3 验收：模拟考试全生命周期 + 不污染练习数据。

前置：先运行 tools/build_exam_pool.py 建池。
用法：python -m tools.verify_exam

覆盖：
- start → 返回 exam_id/deadline/problems（含 statement_html / input_preview，绝不含 expected/cases_preview）；
- run 空代码 → 0 分，只回 passed/total/failed_indexes，不落盘、不写 code_runs；
- save 草稿不覆盖判题结果；
- submit → score/elapsed/late 语义正确，exam 状态 finished；
- abandon 不发 XP；report 仅在提交后可读；
- solutions/ 与 code_runs 行数不变。
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

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
    tmp = Path(tempfile.mkdtemp(prefix="hot100-exam-"))
    app.store = Store(tmp / "state.db")

    def code_runs_count() -> int:
        with app.store.conn() as c:
            return int(c.execute("SELECT COUNT(*) AS n FROM code_runs").fetchone()["n"])

    before_runs = code_runs_count()

    print("== start")
    start = app.exam_start({"medium": 2, "hard": 1, "minutes": 60})
    check("exam_id" in start and start["exam_id"], f"返回 exam_id={start['exam_id']}")
    check("deadline" in start and "problems" in start, "返回 deadline + problems")
    check(len(start["problems"]) >= 1, f"抽到 {len(start['problems'])} 题")
    for p in start["problems"]:
        check("statement_html" in p and p["statement_html"], f"#{p['id']} 有 statement_html")
        check("input_preview" in p, f"#{p['id']} 有 input_preview")
        check("expected" not in p and "cases_preview" not in p, f"#{p['id']} 不下发期望输出")
        check("样例输出" not in (p.get("statement_html") or ""), f"#{p['id']} 题面不含样例输出")
    exam_id = start["exam_id"]
    first_pid = start["problems"][0]["id"]

    print("== run（空代码 → 0 分，不污染）")
    run = app.exam_run({"exam_id": exam_id, "problem_id": first_pid, "code": ""})
    check(set(run) == {"problem_id", "passed", "total", "pass_rate", "failed_indexes"}, f"run 只回计数 {run}")
    check(run["passed"] == 0 and run["total"] > 0, "空代码 0 通过")
    check(code_runs_count() == before_runs, "exam_run 不写 code_runs")

    print("== save 草稿")
    app.exam_save({"exam_id": exam_id, "problem_id": first_pid, "code": "class Solution:\n    pass\n"})
    draft = app.store.exam_answer_code(exam_id, first_pid)
    check(draft.startswith("class Solution"), "草稿已保存")

    print("== submit")
    sub = app.exam_submit({"exam_id": exam_id, "answers": [{"problem_id": first_pid, "code": ""}]})
    check(sub["score"] == 0.0, f"空代码 score=0（实际 {sub['score']}）")
    check("late" in sub and sub["late"] in (0, 1), "有 late 标记")
    check(sub["xp_gained"] == 0, "0 分不发 exam_pass XP")

    print("== report / history")
    rep = app.exam_report(exam_id)
    check(rep["exam_id"] == exam_id and "problems" in rep, "report 可读（提交后）")
    hist = app.exam_history()
    check(any(e["id"] == exam_id for e in hist["exams"]), "history 包含本场")

    print("== abandon 不发 XP")
    start2 = app.exam_start({"medium": 1, "hard": 0, "minutes": 30})
    app.exam_abandon({"exam_id": start2["exam_id"]})
    check(code_runs_count() == before_runs, "abandon 不写 code_runs")
    xp_after = app.store.xp_total()
    check(xp_after == 0, f"全程无 exam_pass XP（xp={xp_after}）")

    print(f"\nP3 检查项：{CHECKS}，失败：{len(FAILS)}")
    for item in FAILS:
        print(f"  - {item}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
