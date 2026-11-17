"""自适应日程与复习排期。"""
from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta

from .store import COMPLETE, Store

NEW = "new"
REVIEW = "review"


def parse_day(day: str | None = None) -> date:
    return date.fromisoformat(day) if day else date.today()


def deadline_date(cfg: dict) -> date:
    return date.fromisoformat(cfg["deadline"])


def days_left(day: date, cfg: dict) -> int:
    return max(1, (deadline_date(cfg) - day).days + 1)


def at_time(day: date, hhmm: str) -> datetime:
    hour, minute = map(int, hhmm.split(":"))
    return datetime.combine(day, time(hour, minute))


def target_new(remaining: int, left: int, max_new: int) -> int:
    if remaining <= 0:
        return 0
    return min(max_new, max(1, math.ceil(remaining / left)))


def plan_summary(store: Store, problems: list[dict], cfg: dict, day_str: str | None = None) -> dict:
    day = parse_day(day_str)
    left = days_left(day, cfg)
    rows = store.plan(day.isoformat())
    progress = store.progress()
    remaining = progress["remaining"]
    target = target_new(remaining, left, cfg["max_new_per_day"])
    backlog = store.review_backlog(day.isoformat())
    warnings = []
    if remaining and math.ceil(remaining / left) > cfg["max_new_per_day"]:
        warnings.append(
            f"按每天最多 {cfg['max_new_per_day']} 道新题，无法在 {cfg['deadline']} 前完成："
            f"还剩 {remaining} 道、{left} 天。建议延长练习时段、减少复习上限或调整截止日期。"
        )
    if day > deadline_date(cfg) and remaining:
        warnings.append("截止日期已过，计划会自动压缩到最后一天。")
    if backlog > cfg["max_reviews_per_day"]:
        warnings.append(
            f"有 {backlog} 道复习到期，今天最多安排 {cfg['max_reviews_per_day']} 道，其余顺延。"
        )
    window = at_time(day, cfg["session_end"]) - at_time(day, cfg["session_start"])
    planned_minutes = (
        target * cfg["new_slot_minutes"]
        + min(backlog, cfg["max_reviews_per_day"]) * cfg["review_slot_minutes"]
    )
    if planned_minutes > window.total_seconds() // 60:
        warnings.append(
            f"今日预计 {planned_minutes} 分钟，超过 {cfg['session_start']}–{cfg['session_end']} 的时段，"
            "请预留加时或调整配置。"
        )
    return {
        "day": day.isoformat(),
        "deadline": cfg["deadline"],
        "days_left": left,
        "target_new": target,
        "remaining": remaining,
        "review_backlog": backlog,
        "warnings": warnings,
        "items": rows,
        "progress": progress,
    }


def ensure_day(store: Store, problems: list[dict], cfg: dict, day_str: str | None = None) -> dict:
    day = parse_day(day_str)
    day_key = day.isoformat()
    store.expire_before(day_key)
    existing = store.plan(day_key)
    if existing:
        return plan_summary(store, problems, cfg, day_key)

    progress = store.progress()
    left = days_left(day, cfg)
    remaining = progress["remaining"]
    target = target_new(remaining, left, cfg["max_new_per_day"])

    state = store.problems()
    candidates = []
    for p in problems:
        status = state.get(p["id"])["status"] if p["id"] in state else "todo"
        if status in COMPLETE:
            continue
        row = state.get(p["id"])
        retry = row["retry"] if row else 0
        candidates.append((retry, p["order"], p))
    candidates.sort(key=lambda item: (-item[0], item[1]))

    chosen_new = [p for _, _, p in candidates[:target]]
    chosen_ids = {p["id"] for p in chosen_new}

    due = store.due_reviews(day_key)
    chosen_reviews = []
    for review in due:
        if review["problem_id"] in chosen_ids:
            continue
        if len(chosen_reviews) >= cfg["max_reviews_per_day"]:
            break
        chosen_reviews.append(review)

    items = []
    cursor = at_time(day, cfg["session_start"])
    slot = 0
    for p in chosen_new:
        end = cursor + timedelta(minutes=cfg["new_slot_minutes"])
        items.append({
            "problem_id": p["id"],
            "kind": NEW,
            "slot": slot,
            "planned_start": cursor.strftime("%H:%M"),
            "planned_end": end.strftime("%H:%M"),
        })
        cursor = end
        slot += 1
    for review in chosen_reviews:
        end = cursor + timedelta(minutes=cfg["review_slot_minutes"])
        items.append({
            "problem_id": review["problem_id"],
            "kind": REVIEW,
            "slot": slot,
            "planned_start": cursor.strftime("%H:%M"),
            "planned_end": end.strftime("%H:%M"),
            "review_id": review["id"],
        })
        cursor = end
        slot += 1

    store.insert_plan_items(day_key, items)
    summary = plan_summary(store, problems, cfg, day_key)
    store.set_meta(f"plan_created:{day_key}", summary["target_new"].__str__())
    return summary


def rebuild_day(store: Store, problems: list[dict], cfg: dict, day_str: str | None = None) -> dict:
    day = parse_day(day_str).isoformat()
    store.delete_day_plan(day)
    return ensure_day(store, problems, cfg, day)


def item_times(item, cfg: dict) -> tuple[datetime, datetime]:
    day = item["day"]
    start = datetime.fromisoformat(f"{day} {item['planned_start']}:00")
    end = datetime.fromisoformat(f"{day} {item['planned_end']}:00")
    return start, end


def add_extra_item(store: Store, problems: list[dict], cfg: dict, day_str: str | None, problem_id: int) -> dict:
    """专题加练：往今日计划追加一条 kind='extra'（DESIGN_v3 §5.5）。

    - 同题当天已有任意 kind 的计划行 → 拒绝重复添加。
    - 追加在最后一个槽位之后，25 分钟一档。
    """
    day = parse_day(day_str)
    day_key = day.isoformat()
    problem = next((p for p in problems if p["id"] == problem_id), None)
    if problem is None:
        raise ValueError(f"题目 {problem_id} 不在题库中")
    if store.has_plan_for(day_key, problem_id):
        raise ValueError("这题今天已经在计划里了")

    rows = store.plan(day_key)
    slot = store.next_slot_index(day_key) + 1
    if rows:
        last = rows[-1]
        start = datetime.fromisoformat(f"{day_key} {last['planned_end']}:00")
    else:
        start = at_time(day, cfg["session_start"])
    end = start + timedelta(minutes=cfg["new_slot_minutes"])
    item = {
        "problem_id": problem_id,
        "kind": "extra",
        "slot": slot,
        "planned_start": start.strftime("%H:%M"),
        "planned_end": end.strftime("%H:%M"),
    }
    store.insert_plan_items(day_key, [item])
    return plan_summary(store, problems, cfg, day_key)


def slot_limit_minutes(item, cfg: dict) -> int:
    # extra（专题加练）与 new 同档：25 分钟，不再被误当 review 的 15 分钟（DESIGN_v3 §5.5）。
    return cfg["new_slot_minutes"] if item["kind"] in (NEW, "extra") else cfg["review_slot_minutes"]
