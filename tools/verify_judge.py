"""全量回归：88 题 × 官方全部用例，ACM 与核心代码两种模式都必须全过。

用法：python -m tools.verify_judge
ACM 用 reference/ 下的参考题解；核心代码模式由 BANK 算法现场包装成力扣签名。
"""
from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hot100 import judge, materials, official  # noqa: E402

IMPORTS = (
    "from collections import Counter, OrderedDict, defaultdict, deque\n"
    "import bisect\nimport heapq\nimport math\nimport sys\n\n\n"
)


def core_reference(problem: dict) -> str:
    """把 BANK 的 ACM 算法包装成核心代码模式的参考实现（仅测试用）。"""
    pid = problem["id"]
    io = problem["io"]
    meta = official.meta_of(problem)
    kinds = {k for _, k in io["params"]} | {io["ret"]}
    if pid in (141, 142, 160):
        kinds.add("linked_list")
    nodes = []
    if "linked_list" in kinds:
        nodes.append("ListNode")
    if "tree" in kinds:
        nodes.append("TreeNode")
    if "random_list" in kinds:
        nodes.append("RandomNode")
    node_src = materials._node_class_source(nodes) + "\n\n\n" if nodes else ""
    src = materials.solve_source(pid)
    if official.is_design(problem):
        lines = src.splitlines()
        start = next(i for i, l in enumerate(lines) if l.startswith("    class "))
        end = next(i for i, l in enumerate(lines) if l.startswith("    out = []"))
        cls = textwrap.dedent("\n".join(lines[start:end])).rstrip() + "\n"
        return IMPORTS + node_src + cls
    impl = re.sub(r"\bsolve\b", "_impl", src)
    # 方法签名以力扣官方 snippet 为准（metaData 里 141/142/160 还带 pos/skip 等构造参数）。
    snippet = official.snippet_of(problem)
    m = re.search(r"def\s+" + re.escape(meta["name"]) + r"\(\s*self\s*(?:,\s*([^)]*))?\)", snippet)
    params = [p.strip().split(":")[0].strip() for p in m.group(1).split(",")] if m and m.group(1) else []
    extra = {141: ", -1", 142: ", -1", 160: ", 0, 0"}.get(pid, "")
    call = ", ".join(params) + extra
    wrapper = (
        f"class Solution:\n"
        f"    def {meta['name']}(self, {', '.join(params)}):\n"
        f"        return _impl({call})\n"
    )
    return IMPORTS + node_src + impl + "\n\n" + wrapper


def main() -> int:
    data = materials.load_problems()
    problems = data["problems"]
    total_cases = 0
    failures: list[str] = []
    for problem in problems:
        cases = official.official_cases(problem)
        total_cases += len(cases)
        paths = materials.problem_paths(problem["id"], problem["slug"])
        acm_code = paths["reference"].read_text(encoding="utf-8")
        for mode, code in (("acm", acm_code), ("core", core_reference(problem))):
            result = judge.run(problem, mode, code, str(paths["reference"]))
            bad = [r for r in result["results"] if not r["ok"]]
            if bad or len(result["results"]) != len(cases):
                failures.append(
                    f"{problem['id']} {problem['slug']} [{mode}] "
                    f"{len(result['results']) - len(bad)}/{len(cases)}"
                )
                for r in bad[:2]:
                    failures.append(f"    case {r['index']}: {r['status']} {r['detail'][:160]}")
    print(f"problems: {len(problems)} cases: {total_cases} failures: {len(failures)}")
    for line in failures:
        print(line)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())