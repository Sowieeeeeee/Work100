"""激励系统（P1）：XP / 等级 / 连击 / 徽章，只奖不罚。

所有写入走 `store.grant_xp`（`UNIQUE(kind, ref_id)` 判重），所以同一事件重复触发
也只发一次 XP。徽章解锁走 `store.unlock_achievement`（`INSERT OR IGNORE`）。
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from .store import COMPLETE, Store, today_iso

# ---------------------------------------------------------------- XP 规则
XP = {
    "ac_new": 30,       # 新题独立完成
    "ac_hinted": 20,    # 新题借提示完成
    "ac_rewritten": 15,  # 新题看题解后复现
    "review_done": 10,  # 复习完成（任何非 unfinished 结果）
    "topic_ac": 10,     # 专题自由练习全过
    "hard_bonus": 25,   # hard 题首次全过（额外）
    "exam_pass": 40,    # 考试提交且 score >= 60
    "interview_done": 35,  # 面试提交（无论通过率）
}


def streak_bonus_xp(streak: int) -> int:
    return 5 * min(streak, 7)


def _cumulative(level: int) -> int:
    """升到第 level 级所需累计 XP（level 1 从 0 开始）。"""
    if level <= 1:
        return 0
    return sum(100 + (i - 1) * 60 for i in range(1, level))


def level_cost(level: int) -> int:
    """从 level 升到 level+1 需要的 XP。"""
    return 100 + (level - 1) * 60


def level_of(xp: int) -> int:
    level = 1
    while xp >= _cumulative(level + 1):
        level += 1
    return level


def level_progress(xp: int) -> dict:
    level = level_of(xp)
    base = _cumulative(level)
    return {"level": level, "level_xp": xp - base, "level_need": level_cost(level)}


def streak_of(store: Store) -> int:
    """连续活跃天数；今天没活跃则允许从上一天往前数。"""
    active = store.active_days()
    today = date.today()
    if today.isoformat() not in active:
        today -= timedelta(days=1)
    streak = 0
    while today.isoformat() in active:
        streak += 1
        today -= timedelta(days=1)
    return streak


# ---------------------------------------------------------------- 徽章
def _stats(store: Store) -> dict:
    progress = store.progress()
    return {
        "done": progress["done"],
        "total": progress["total"],
        "streak": streak_of(store),
        "full_runs": store.full_run_count(),
        "night_owl": store.night_owl(),
        "hard_done": store.xp_by_kind().get("hard_bonus", 0) > 0,
        "exam_best": store.exam_best_score(),
        "interview_count": store.interview_count(),
        "interview_best": store.interview_best_rate(),
        "topic_mastered": store.topic_mastered(),
    }


BADGES: list[dict] = [
    {"id": "first_ac", "name": "首杀", "desc": "完成第一道题",
     "check": lambda s: s["done"] >= 1},
    {"id": "streak7", "name": "七日连击", "desc": "连续 7 天活跃",
     "check": lambda s: s["streak"] >= 7},
    {"id": "streak30", "name": "月度坚持", "desc": "连续 30 天活跃",
     "check": lambda s: s["streak"] >= 30},
    {"id": "hard_first", "name": "硬骨头", "desc": "首次全过一道困难题",
     "check": lambda s: s["hard_done"]},
    {"id": "exam_pass", "name": "考官认可", "desc": "模拟考试得分 ≥ 80",
     "check": lambda s: s["exam_best"] >= 80},
    {"id": "exam_full", "name": "满分考官", "desc": "模拟考试得分 = 100",
     "check": lambda s: s["exam_best"] >= 100},
    {"id": "interview_debut", "name": "面试首秀", "desc": "完成第一次手撕面试",
     "check": lambda s: s["interview_count"] >= 1},
    {"id": "interview_full", "name": "面试通关", "desc": "面试一次全过",
     "check": lambda s: s["interview_best"] >= 100},
    {"id": "topic_master", "name": "专题征服", "desc": "任一专题全部完成",
     "check": lambda s: s["topic_mastered"]},
    {"id": "night_owl", "name": "夜猫", "desc": "22:00 后完成一次练习",
     "check": lambda s: s["night_owl"]},
    {"id": "century", "name": "百炼", "desc": "累计 100 次全过运行",
     "check": lambda s: s["full_runs"] >= 100},
    {"id": "conqueror", "name": "题库征服者", "desc": "88 题全部完成",
     "check": lambda s: s["total"] > 0 and s["done"] >= s["total"]},
]


def check_achievements(store: Store) -> list[dict]:
    """跑一遍徽章判定，返回**本次新解锁**的徽章（含 id/name/desc）。"""
    stats = _stats(store)
    already = store.unlocked_achievements()
    fresh: list[dict] = []
    for badge in BADGES:
        if badge["id"] in already:
            continue
        try:
            if badge["check"](stats):
                if store.unlock_achievement(badge["id"]):
                    fresh.append({"id": badge["id"], "name": badge["name"], "desc": badge["desc"]})
        except Exception:
            # 徽章判定绝不影响主流程（数据缺失时静默跳过）。
            continue
    return fresh


def award(store: Store, kind: str, ref_id: int, xp: int | None = None) -> dict:
    """发放一次 XP + 当日 streak 奖励 + 检查徽章。返回增量结果。"""
    gained = 0
    value = XP.get(kind, xp or 0)
    ok, got = store.grant_xp(kind, ref_id, value)
    if ok:
        gained += got

    # streak 奖励：按“当天”判重，每天首次事件补发一次（streak>=1 才发，
    # 避免“当天第一次事件时 streak 还是 0”把当天的奖励槽位浪费掉）。
    streak = streak_of(store)
    if streak >= 1:
        day_key = int(today_iso().replace("-", ""))
        ok2, got2 = store.grant_xp("streak_bonus", day_key, streak_bonus_xp(streak))
        if ok2:
            gained += got2

    badges = check_achievements(store)
    return {"xp_gained": gained, "new_badges": badges}


def motivation_state(store: Store) -> dict:
    """注入 `/api/state` 的 motivation 块（保持轻量：不含徽章明细）。"""
    xp = store.xp_total()
    progress = store.progress()
    streak = streak_of(store)
    today = today_iso()
    today_done = store.progress()["sessions_today"]
    return {
        "xp": xp,
        **level_progress(xp),
        "streak": streak,
        "today": {"done": today_done, "planned": 0},  # planned 由 server 补上
        "badge_count": len(store.unlocked_achievements()),
    }


def badges(store: Store) -> list[dict]:
    """徽章墙：全部徽章 + 解锁状态。"""
    unlocked = store.unlocked_achievements()
    result = []
    for badge in BADGES:
        row = dict(badge)
        row["unlocked"] = badge["id"] in unlocked
        row.pop("check", None)
        result.append(row)
    return result
