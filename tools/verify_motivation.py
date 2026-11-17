"""P1 验收：激励系统纯逻辑与幂等性（用临时库，不碰真实 state.db）。

用法：python -m tools.verify_motivation
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hot100 import motivation  # noqa: E402
from hot100.store import Store, now_iso, today_iso  # noqa: E402

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
    tmp = Path(tempfile.mkdtemp(prefix="hot100-mot-"))
    store = Store(tmp / "state.db")

    print("== 等级曲线")
    check(motivation.level_of(0) == 1, "0 XP 是 1 级")
    check(motivation.level_of(99) == 1, "99 XP 仍是 1 级")
    check(motivation.level_of(100) == 2, "100 XP 升 2 级")
    p = motivation.level_progress(100)
    check(p == {"level": 2, "level_xp": 0, "level_need": 160}, f"2 级进度正确 {p}")
    check(motivation.level_of(100 + 160 - 1) == 2, "259 XP 仍是 2 级")
    check(motivation.level_of(100 + 160) == 3, "260 XP 升 3 级")

    print("== XP 幂等")
    ok1, got1 = store.grant_xp("ac_new", 1, 30)
    ok2, got2 = store.grant_xp("ac_new", 1, 30)
    check(ok1 and got1 == 30, "首次发放 30")
    check((not ok2) and got2 == 0, "同 ref 重复发放被拒")
    check(store.xp_total() == 30, "XP 合计 30")

    print("== award 聚合")
    a1 = motivation.award(store, "ac_new", 2)
    a2 = motivation.award(store, "ac_new", 2)
    check(a1["xp_gained"] == 30, f"空库（streak=0）无 streak 奖励 {a1}")
    check(a2["xp_gained"] == 0, "同 ref 二次 award 为 0")

    # 造一条今天已结束的 session → 今天算活跃 → streak=1 → 补发 5 XP
    with store.conn() as c:
        c.execute(
            "INSERT INTO sessions(day, problem_id, kind, started_at, ended_at, elapsed_sec, limit_minutes) "
            "VALUES (?, 1, 'new', ?, ?, 60, 25)",
            (today_iso(), now_iso(), now_iso()),
        )
    check(motivation.streak_of(store) == 1, "有今日 session 后 streak=1")
    a3 = motivation.award(store, "ac_new", 3)
    check(a3["xp_gained"] == 30 + motivation.streak_bonus_xp(1), f"streak>=1 时补发 streak 奖励 {a3}")

    print("== 徽章墙与空库安全")
    wall = motivation.badges(store)
    check(len(wall) == 12, f"徽章共 12 枚（实际 {len(wall)}）")
    check(all("check" not in b for b in wall), "徽章墙不含 check 闭包")
    fresh = motivation.check_achievements(store)
    check(isinstance(fresh, list), "空库检查不崩")

    print("== motivation_state 结构")
    ms = motivation.motivation_state(store)
    for key in ("xp", "level", "level_xp", "level_need", "streak", "today", "badge_count"):
        check(key in ms, f"motivation_state 含 {key}")

    print(f"\nP1 检查项：{CHECKS}，失败：{len(FAILS)}")
    for item in FAILS:
        print(f"  - {item}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
