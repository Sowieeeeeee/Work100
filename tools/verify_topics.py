"""P2 验收：专题分组 / extra 加练 / delete_day_plan 保留 extra / 同题去重。

用法：python -m tools.verify_topics
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hot100 import planner  # noqa: E402
from hot100.materials import load_problems  # noqa: E402
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
    tmp = Path(tempfile.mkdtemp(prefix="hot100-topic-"))
    store = Store(tmp / "state.db")
    problems = load_problems()["problems"]
    store.sync_problems(problems)
    cfg = {
        "deadline": "2099-12-31", "session_start": "09:00", "session_end": "22:00",
        "new_slot_minutes": 25, "review_slot_minutes": 15,
        "max_new_per_day": 3, "max_reviews_per_day": 2,
    }
    day = "2099-01-01"

    print("== ensure_day + add_extra_item")
    summary = planner.ensure_day(store, problems, cfg, day)
    planned_ids = {r["problem_id"] for r in summary["items"]}
    target = next(p["id"] for p in problems if p["id"] not in planned_ids)

    s2 = planner.add_extra_item(store, problems, cfg, day, target)
    extras = [r for r in s2["items"] if r["kind"] == "extra"]
    check(len(extras) == 1, "加练生成一条 extra")
    check(extras[0]["problem_id"] == target, "extra 指向目标题")
    check(planner.slot_limit_minutes(extras[0], cfg) == 25, "extra 按 25 分钟一档")

    print("== 同题去重")
    try:
        planner.add_extra_item(store, problems, cfg, day, target)
        check(False, "同题重复加练应被拒绝")
    except ValueError:
        check(True, "同题重复加练被拒绝")

    print("== delete_day_plan 保留 extra")
    before = len(store.plan(day))
    store.delete_day_plan(day)
    remain = store.plan(day)
    check(all(r["kind"] == "extra" for r in remain), "重建后仅剩 extra 行")
    check(any(r["problem_id"] == target for r in remain), "extra 未被删除")
    check(len(remain) < before, "new/review 待办行被清掉")

    print("== 专题分组（server.topics 逻辑）")
    import threading
    from hot100.config import load_config
    from hot100.server import App
    app = App.__new__(App)
    app.cfg = load_config()
    app.problems = problems
    app.by_id = {p["id"]: p for p in problems}
    app.port = int(app.cfg["port"])
    app.lock = threading.Lock()
    app.store = store
    g = app.topics("group")
    o = app.topics("official")
    check(g["view"] == "group" and len(g["topics"]) > 0, f"分组视图有 {len(g['topics'])} 组")
    check(all("problems" in t and "done" in t and "count" in t for t in g["topics"]), "分组字段完整")
    total_g = sum(t["count"] for t in g["topics"])
    check(total_g == len(problems), f"分组视图覆盖全部 {total_g} 题")
    total_o = sum(t["count"] for t in o["topics"])
    check(total_o >= total_g, f"标签视图 {total_o} 条（含多标签重复）≥ 分组 {total_g}")
    check(o["view"] == "official", "标签视图标记 official")
    app.week()  # 只读，确保不抛异常
    check(True, "week() 只读可调用")

    print(f"\nP2 检查项：{CHECKS}，失败：{len(FAILS)}")
    for item in FAILS:
        print(f"  - {item}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
