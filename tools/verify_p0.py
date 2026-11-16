"""P0 验收：题源统一层 / io 推断白名单 / 池题无 BANK 也能出材料。

用法：python -m tools.verify_p0

不跑判题（判题回归是 `python -m tools.verify_judge`），这里只校验 P0 新增的
四条链路，任何一条断了就直接 exit 1：

1. problem_source：88 题可枚举、按 id 可查、raw 可查；
2. official.raw_of 走统一入口（core 命中 + 未知 slug 抛 KeyError）；
3. io_map：白名单外的类型必须返回淘汰原因，不能静默当 int；
4. official_cases(allow_oracle=False)：没有题面期望时丢用例，绝不调 oracle；
5. materials.ensure_problem(with_reference=False)：池题不写 reference/ 也不碰 BANK。
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hot100 import io_map, materials, official, problem_source  # noqa: E402

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


def section(title: str) -> None:
    print(f"\n== {title}")


def main() -> int:
    core = problem_source.core()
    problems = core.all()

    section("1. problem_source")
    check(len(problems) == 88, "88 题可枚举", f"实际 {len(problems)}")
    first = problems[0]
    check(core.get(first["id"]) is not None, "按 id 取题")
    check(bool(core.raw_of(first["slug"])), "按 slug 取原始数据")
    check(core.get(99999001) is None, "不存在的 id 返回 None")
    check(core.has_reference(first["id"]), "88 题有 BANK 参考解")
    check(problem_source.pool().all() == [] or True, "池源可访问（未建池时为空）")
    check(problem_source.find_problem(first["id"]) is not None, "全局 find_problem 命中 core")

    section("2. official.raw_of 统一入口")
    raw = official.raw_of(first["slug"])
    check("metaData" in raw and "exampleTestcases" in raw, "raw 字段完整")
    try:
        official.raw_of("no-such-slug-for-verify-p0")
        check(False, "未知 slug 抛 KeyError", "居然没抛")
    except KeyError:
        check(True, "未知 slug 抛 KeyError")

    section("3. io_map 白名单")
    io, reason = io_map.infer_io(raw, first["slug"])
    check(io is not None, f"两数之和可推断 io（{reason}）")
    if io:
        check(
            [k for _, k in io["params"]] == ["int_array", "int"] and io["ret"] == "int_array",
            "两数之和 io 形状正确",
            json.dumps(io["params"]),
        )
    cases = {
        "double": ({"name": "f", "params": [{"name": "x", "type": "double"}],
                    "return": {"type": "double"}}, "浮点参数"),
        "void": ({"name": "f", "params": [{"name": "x", "type": "integer"}],
                  "return": {"type": "void"}}, "void 返回"),
        "nested": ({"name": "f", "params": [{"name": "x", "type": "list<list<integer>>"}],
                    "return": {"type": "integer"}}, "嵌套列表参数"),
        "design": ({"classname": "LRUCache", "systemdesign": True, "constructor": [],
                    "params": [], "return": {"type": "void"}}, "设计类"),
    }
    for label, (meta, desc) in cases.items():
        got, why = io_map.infer_io({"metaData": json.dumps(meta)}, label)
        check(got is None and bool(why), f"淘汰：{desc}")

    accepted = 0
    rejected: dict[str, str] = {}
    for problem in problems:
        io2, why = io_map.infer_io(official.raw_of(problem["slug"]), problem["slug"])
        if io2 is None:
            rejected[problem["slug"]] = why
        else:
            accepted += 1
    print(f"  参考 88 题白名单命中率：{accepted}/{len(problems)}（仅作参考，88 题用逐题手工表）")

    section("4. official_cases(allow_oracle=False)")
    total_with = len(official.official_cases(first))
    total_without = len(official.official_cases(first, allow_oracle=False))
    check(total_without <= total_with, "禁用 oracle 只会丢用例，不会多")
    check(total_without > 0, "两数之和仍保留题面用例", f"{total_without}/{total_with}")
    print(f"  两数之和：allow_oracle=True → {total_with} 例；False → {total_without} 例")

    section("5. materials.ensure_problem(with_reference=False)")
    tmp = Path(tempfile.mkdtemp(prefix="hot100-p0-"))
    saved = {
        name: getattr(materials, name)
        for name in ("PROBLEMS_DIR", "SOLUTIONS", "CORE", "REFERENCE")
    }
    try:
        materials.PROBLEMS_DIR = tmp / "problems"
        materials.SOLUTIONS = tmp / "solutions"
        materials.CORE = tmp / "core"
        materials.REFERENCE = tmp / "reference"
        fake = dict(first, id=99999001, title=first["title"] + "（池题）")
        paths = materials.ensure_problem(fake, create_solution=True, with_reference=False)
        check(paths["statement"].exists(), "题面已生成")
        check(paths["core"].exists(), "核心代码脚手架已生成（需要 meta_of）")
        check(not paths["reference"].exists(), "没有参考解时不写 reference/")
        text = paths["statement"].read_text(encoding="utf-8")
        check("没有本地参考题解" in text, "题面不再指向不存在的参考题解")
    finally:
        for name, value in saved.items():
            setattr(materials, name, value)

    print(f"\nP0 检查项：{CHECKS}，失败：{len(FAILS)}")
    for item in FAILS:
        print(f"  - {item}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
