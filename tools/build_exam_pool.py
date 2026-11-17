"""构建精选题库（P3）：top-100-liked ∪ top-interview-150 的 Medium/Hard 题。

用法：python -m tools.build_exam_pool（或 python tools/build_exam_pool.py）
产物：
- data/exam_pool.json   {built_at, source, total, problems:[...]}（problem 结构与 problems.json 同构）
- data/pool_raw.json    {slug: {metaData, codeSnippets, translatedContent, exampleTestcases, ...}}

入池闸门（缺一即淘汰，日志记原因与计数，见 DESIGN_v3 §3.1）：
1. io_map.infer_io 返回非 None（白名单内、非 design）；
2. Python3 核心代码片段可 compile；
3. official.official_cases(allow_oracle=False) ≥ 2 例，且无「期望解析不出来被丢」的用例；
4. to_acm_input / lc_display 双格式可解析（第 3 步内部已覆盖，出错即淘汰）；
5. compare == "exact"（infer_io 恒 exact）。

id 规则：池题 id 直接用力扣 questionFrontendId；与 88 题重合时跳过（复用主题库）。
"""
from __future__ import annotations

import argparse
import copy
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hot100 import io_map, official  # noqa: E402
from hot100.config import DATA  # noqa: E402
from hot100.materials import load_problems  # noqa: E402

GRAPHQL = "https://leetcode.cn/graphql/"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://leetcode.cn/problemset/",
    "Accept": "application/json",
}
DIFF_CN = {"Easy": "简单", "Medium": "中等", "Hard": "困难", "EASY": "简单", "MEDIUM": "中等", "HARD": "困难"}

STUDYPLAN_QUERY = """
query studyPlanV2Detail($planSlug:String!){studyPlanV2Detail(planSlug:$planSlug){
  name planSubGroups{name questions{titleSlug difficulty}}
}}
"""

QUESTION_QUERY = """
query questionData($titleSlug:String!){question(titleSlug:$titleSlug){
  questionFrontendId titleSlug translatedTitle difficulty metaData
  codeSnippets{lang langSlug code} exampleTestcases
  topicTags{name translatedName slug} translatedContent
}}
"""

PROBLEMSET_QUERY = """
query problemsetQuestionList($categorySlug:String,$limit:Int,$skip:Int,$filters:QuestionListFilterInput){
  problemsetQuestionList(categorySlug:$categorySlug limit:$limit skip:$skip filters:$filters){
    total questions{frontendQuestionId titleSlug difficulty paidOnly}
  }
}
"""


def _gql(query: str, variables: dict, opname: str) -> dict:
    body = json.dumps({"query": query, "variables": variables, "operationName": opname}).encode()
    req = urllib.request.Request(GRAPHQL, data=body, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GraphQL HTTP {exc.code}: {exc.read()[:200]!r}") from exc


def fetch_slugs(plan_slug: str) -> list[tuple[str, str]]:
    data = _gql(STUDYPLAN_QUERY, {"planSlug": plan_slug}, "studyPlanV2Detail")
    detail = data["data"]["studyPlanV2Detail"]
    out = []
    for group in detail["planSubGroups"]:
        for q in group["questions"]:
            out.append((q["titleSlug"], q["difficulty"]))
    return out


def fetch_problemset(difficulty: str, skip: int = 0, limit: int = 100) -> list[dict]:
    data = _gql(PROBLEMSET_QUERY, {
        "categorySlug": "", "skip": skip, "limit": limit,
        "filters": {"difficulty": difficulty, "orderBy": "FREQUENCY", "sortOrder": "DESCENDING"},
    }, "problemsetQuestionList")
    node = data["data"]["problemsetQuestionList"]
    return node["questions"] if node else []


def fetch_question(slug: str, retries: int = 2) -> dict:
    last = None
    for attempt in range(retries + 1):
        try:
            data = _gql(QUESTION_QUERY, {"titleSlug": slug}, "questionData")
            q = data["data"]["question"]
            if not q:
                raise RuntimeError(f"questionData 为空 {slug}")
            return q
        except Exception as exc:  # noqa: BLE001 - 网络重试
            last = exc
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"拉取 {slug} 失败：{last}")


# ---------------- 题面文案（复用 build_dataset 的语义，自包含） ----------------
def strip_tags(text: str) -> str:
    text = re.sub(r"<sup[^>]*>(.*?)</sup>", r"^\1", text, flags=re.S)
    text = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", text, flags=re.S)
    text = re.sub(r"<em[^>]*>(.*?)</em>", r"*\1*", text, flags=re.S)
    text = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", text, flags=re.S)
    text = re.sub(r"<li[^>]*>", "- ", text)
    text = re.sub(r"</li>", "\n", text)
    text = re.sub(r"</p>", "\n\n", text)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def description_of(content: str) -> str:
    text = content or ""
    cut = re.split(r"(?:<strong[^>]*class=\"example\"[^>]*>|<p>\s*<strong[^>]*>)\s*示例", text, maxsplit=1)[0]
    if cut == text:
        cut = re.split(r"示例\s*1", text, maxsplit=1)[0]
    return re.sub(r"\n+", "\n\n", strip_tags(cut)).strip()


def constraints_of(content: str) -> list[str]:
    uls = re.findall(r"<ul[^>]*>(.*?)</ul>", content or "", flags=re.S)
    if not uls:
        return []
    items = re.findall(r"<li[^>]*>(.*?)</li>", uls[-1], flags=re.S)
    return [strip_tags(item) for item in items if strip_tags(item)]


# ---------------- 闸门 ----------------
def _no_dropped_cases(problem: dict) -> bool:
    """每个 exampleTestcases 输入都必须能在题面示例里找到期望输出（否则 allow_oracle=False 会丢）。"""
    page_keys: set[str] = set()
    for ex in official.html_examples(problem):
        try:
            args = official.assignment_values(ex["input"])
            page_keys.add(official._norm_args(args))
        except Exception:  # noqa: BLE001
            continue
    for lines in official.judge_inputs(problem):
        try:
            args = [official.lc_parse(line) for line in lines]
        except Exception:  # noqa: BLE001
            return False
        if official._norm_args(args) not in page_keys:
            return False
    return True


def gate(pid: int, slug: str, raw: dict) -> tuple[dict | None, str]:
    """返回 (problem, "") 或 (None, 淘汰原因)。problem 的 io.samples 已填好。"""
    io, reason = io_map.infer_io(raw, slug, pid)
    if io is None:
        return None, f"io 白名单外：{reason}"

    snippets = raw.get("codeSnippets") or []
    if not any(s.get("lang") == "Python3" for s in snippets):
        return None, "无 Python3 核心代码片段（premium/企业题）"
    try:
        snippet = official.snippet_of({"id": pid, "slug": slug})
        compile(snippet, f"<{slug}>", "exec")
    except Exception as exc:  # noqa: BLE001
        return None, f"核心代码片段编译失败：{exc}"

    problem = {"id": pid, "slug": slug, "io": io}
    try:
        cases = official.official_cases(problem, allow_oracle=False)
    except Exception as exc:  # noqa: BLE001
        return None, f"用例/IO 解析失败：{exc}"
    if len(cases) < 2:
        return None, f"用例不足（{len(cases)} < 2）"
    if not _no_dropped_cases(problem):
        return None, "存在期望解析不出的用例（会被 allow_oracle=False 丢弃）"

    io["samples"] = [{"input": c["input_acm"], "output": c["expected_acm"]} for c in cases[:3]]
    return problem, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plans", default="top-100-liked,top-interview-150")
    ap.add_argument("--min-pool", type=int, default=250)
    ap.add_argument("--target-candidates", type=int, default=420,
                    help="候选 Medium/Hard 题数上限（补齐来源：problemset 热度降序）")
    ap.add_argument("--force", action="store_true", help="忽略本地缓存，重新拉取全部题面")
    ap.add_argument("--interval", type=float, default=0.25)
    args = ap.parse_args()

    # 现有 88 题（复用主题库，池里不再重复）
    core_ids = {p["id"] for p in load_problems()["problems"]}

    # 1) 收集候选 slug：先学习计划（top-100-liked ∪ top-interview-150），
    #    不足 target_candidates 时用 problemset（Medium/Hard，按热度降序）补齐。
    seen_slugs: set[str] = set()
    candidates: dict[str, str] = {}
    for plan in [p.strip() for p in args.plans.split(",") if p.strip()]:
        for slug, diff in fetch_slugs(plan):
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)
            if diff.upper() in ("MEDIUM", "HARD"):
                candidates[slug] = diff.upper()
    if len(candidates) < args.target_candidates:
        for difficulty in ("MEDIUM", "HARD"):
            skip = 0
            while len(candidates) < args.target_candidates:
                page = fetch_problemset(difficulty, skip=skip, limit=100)
                if not page:
                    break
                for q in page:
                    slug = q["titleSlug"]
                    if slug in seen_slugs or q.get("paidOnly"):
                        continue
                    seen_slugs.add(slug)
                    candidates[slug] = q["difficulty"]
                skip += 100
    print(f"候选 Medium/Hard：{len(candidates)} 题（计划 {args.plans} + 热度补齐）")

    # 2) 逐题拉取（带本地缓存）
    pool_raw_path = DATA / "pool_raw.json"
    pool_raw: dict[str, dict] = {}
    if pool_raw_path.exists() and not args.force:
        try:
            pool_raw = json.loads(pool_raw_path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pool_raw = {}

    rejections: dict[str, int] = {}
    problems: list[dict] = []
    fetched = 0
    for idx, (slug, diff) in enumerate(candidates.items()):
        if slug in pool_raw:
            raw = pool_raw[slug]
        else:
            try:
                q = fetch_question(slug)
            except RuntimeError as exc:
                rejections["拉取失败"] = rejections.get("拉取失败", 0) + 1
                print(f"[skip] {slug}: {exc}")
                time.sleep(args.interval)
                continue
            raw = {
                "metaData": q["metaData"],
                "codeSnippets": q["codeSnippets"],
                "translatedContent": q.get("translatedContent") or "",
                "translatedTitle": q.get("translatedTitle") or "",
                "exampleTestcases": q.get("exampleTestcases") or "",
                "topicTags": q.get("topicTags") or [],
                "difficulty": q["difficulty"],
                "questionFrontendId": q["questionFrontendId"],
            }
            pool_raw[slug] = raw
            fetched += 1
            # 每拉一题就落盘，中断可续跑
            tmp = pool_raw_path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(pool_raw, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
            tmp.replace(pool_raw_path)

        pid = int(raw.get("questionFrontendId") or 0)
        if pid in core_ids:
            continue  # 复用主题库条目（DESIGN_v3 §3.1 id 规则）

        problem, reason = gate(pid, slug, raw)
        if problem is None:
            rejections[reason] = rejections.get(reason, 0) + 1
            time.sleep(args.interval)
            continue

        title = (raw.get("translatedTitle") or "").strip() or slug
        topics = [t.get("translatedName") or t.get("name") for t in raw.get("topicTags", []) if t]
        content = raw.get("translatedContent") or ""
        problems.append({
            "id": pid,
            "slug": slug,
            "title": title,
            "title_en": "",
            "difficulty": DIFF_CN.get(raw.get("difficulty", diff), "中等"),
            "group": topics[0] if topics else "精选题库",
            "group_order": 0,
            "order": idx,
            "link": f"https://leetcode.cn/problems/{slug}/",
            "description": description_of(content),
            "constraints": constraints_of(content),
            "topics": topics,
            "io": problem["io"],
        })
        time.sleep(args.interval)

    problems.sort(key=lambda p: p["id"])
    for i, p in enumerate(problems):
        p["order"] = i

    # 3) 写产物
    out = {
        "built_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
        "source": ",".join(args.plans.split(",")),
        "total": len(problems),
        "problems": problems,
    }
    (DATA / "exam_pool.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    pool_raw_path.write_text(
        json.dumps(pool_raw, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )

    print(f"\n入池：{len(problems)} 题（新拉取 {fetched} 题，缓存 {len(candidates) - fetched} 题）")
    print("淘汰原因分布：")
    for reason, n in sorted(rejections.items(), key=lambda kv: -kv[1]):
        print(f"  {n:>4}  {reason}")
    if len(problems) < args.min_pool:
        print(f"!! 警告：入池 {len(problems)} < 目标 {args.min_pool}，请检查网络或追加 --extra-plan")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
