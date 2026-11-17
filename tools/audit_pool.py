"""P3 题库审计：抽 20 道池题做结构性 + 判题链路冒烟（不依赖 AI/oracle）。

用法：python -m tools.audit_pool [--n 20]

审计内容（能离线自证的部分，DESIGN_v3 §3.2 的「独立正确性」需要 AI/人工写参考实现，
在无 oracle 的离线环境无法全自动完成，这里只覆盖结构性正确性）：
- io_map 白名单命中、Python3 片段可编译、用例 ≥2 且无「期望解析不出被丢」的用例；
- 把官方空体片段（pass）喂给 judge.run，必须跑通「输入解析 → 判题 → 对比」全链路，
  且 0 通过（空体不可能答对），进程不崩；
- 输出写入 logs/pool_audit.log。
"""
from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hot100 import judge, official, problem_source  # noqa: E402
from hot100.config import LOGS  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    args = ap.parse_args()

    pool = problem_source.pool().all()
    if not pool:
        print("精选题库为空，请先运行 tools/build_exam_pool.py")
        return 1
    sample = random.sample(pool, min(args.n, len(pool)))
    LOGS.mkdir(parents=True, exist_ok=True)
    log_path = LOGS / "pool_audit.log"

    failures = 0
    lines = [f"== pool_audit {datetime.now().isoformat(sep=' ', timespec='seconds')} =="]
    for p in sample:
        pid, slug = p["id"], p["slug"]
        reasons = []
        io = p.get("io")
        if not io or not io.get("params"):
            reasons.append("io 缺失")
        snippet = official.snippet_of({"id": pid, "slug": slug})
        try:
            compile(snippet, f"<{slug}>", "exec")
        except Exception as exc:  # noqa: BLE001
            reasons.append(f"片段编译失败 {exc}")
        try:
            cases = official.official_cases(p, allow_oracle=False)
            if len(cases) < 2:
                reasons.append(f"用例不足 {len(cases)}")
        except Exception as exc:  # noqa: BLE001
            reasons.append(f"用例解析失败 {exc}")
        # 判题链路冒烟：空体片段必须 0 通过且不崩。
        if not reasons:
            try:
                res = judge.run(p, "core", snippet, f"<audit-{slug}>")
                if res["metrics"]["passed"] != 0:
                    reasons.append(f"空体片段竟通过 {res['metrics']['passed']} 例")
            except Exception as exc:  # noqa: BLE001
                reasons.append(f"判题链路崩溃 {exc}")
        status = "OK" if not reasons else "REJECT"
        if reasons:
            failures += 1
        msg = f"{status} #{pid:>4} {slug}: {'; '.join(reasons) if reasons else '结构性通过，判题链路 0 通过正常'}"
        print(msg)
        lines.append(msg)

    lines.append(f"结果：{len(sample) - failures}/{len(sample)} 通过结构审计")
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"\n审计 {len(sample)} 题，{failures} 题异常 → 见 {log_path}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
