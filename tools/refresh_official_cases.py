"""把 data/problems.json 的样例刷新为力扣官方全量用例，并同步题面/参考题解。

用法：python -m tools.refresh_official_cases
- 用例 = 判题接口 exampleTestcases 与题面示例的并集，一个不删。
- 只重写 problems.json 的 io.samples；不会覆盖 solutions/ 与 core/ 里已有的用户代码。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hot100 import materials, official  # noqa: E402
from hot100.config import DATA  # noqa: E402


def main() -> None:
    path = DATA / "problems.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    total = 0
    for problem in data["problems"]:
        cases = official.official_cases(problem)
        problem["io"]["samples"] = [
            {"input": c["input_acm"], "output": c["expected_acm"]} for c in cases
        ]
        total += len(cases)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    materials.ensure_all(create_solutions=True)
    print(f"problems: {len(data['problems'])} official cases: {total}")


if __name__ == "__main__":
    main()