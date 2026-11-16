"""判题子进程：隔离执行用户代码，逐用例向父进程回报 JSON 行。

以 `python -B -m hot100.judge_worker` 启动；stdin 收一份 JSON 任务，
stdout 每跑完一个用例输出一行结果，最后输出一行 done。
父进程超时杀进程时，已输出的用例结果仍然有效。
"""
from __future__ import annotations

import base64
import copy
import io
import json
import marshal
import sys
import time
import traceback
import types


def _emit(row: dict) -> None:
    sys.stdout.write(json.dumps(row, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _tail_error(exc: BaseException) -> str:
    lines = traceback.format_exception_only(type(exc), exc)
    text = "".join(lines).strip()
    tb = traceback.extract_tb(exc.__traceback__)
    where = ""
    for frame in reversed(tb):
        if frame.filename not in (__file__, "<string>"):
            where = f"（第 {frame.lineno} 行 {frame.name}）"
            break
    return text + where


def _run_acm(code_obj, path: str, case: dict) -> tuple[str, str]:
    stdin = io.StringIO(case["input_acm"] + "\n")
    stdout, stderr = io.StringIO(), io.StringIO()
    old = (sys.stdin, sys.stdout, sys.stderr)
    sys.stdin, sys.stdout, sys.stderr = stdin, stdout, stderr
    sys.setrecursionlimit(1000000)
    try:
        exec(code_obj, {"__name__": "__main__", "__file__": path})
    finally:
        sys.stdin, sys.stdout, sys.stderr = old
    return stdout.getvalue(), stderr.getvalue()


def _run_core(code_obj, path: str, case: dict, problem: dict, official):
    ns = {"__name__": "user_core", "__file__": path}
    sys.setrecursionlimit(100000)
    exec(code_obj, ns)
    meta = official.meta_of(problem)
    args = official.runtime_args(problem, copy.deepcopy(case["args"]), ns)
    pid = problem["id"]
    if official.is_design(problem):
        classname = meta["classname"]
        if classname not in ns:
            raise ValueError(f"核心代码模式需要定义 class {classname}")
        ops, argv = args
        obj, out = None, []
        for op, a in zip(ops, argv):
            if op == classname:
                obj = ns[classname](*a)
                out.append(None)
            else:
                if obj is None:
                    raise ValueError(f"操作 {op} 出现在构造之前")
                out.append(getattr(obj, op)(*a))
        return out
    if "Solution" not in ns:
        raise ValueError("核心代码模式需要定义 class Solution")
    method = getattr(ns["Solution"](), meta["name"], None)
    if method is None:
        raise ValueError(f"Solution 里缺少方法 {meta['name']}，请保留力扣签名")
    head = args[0] if pid in (141, 142) else None
    ret = method(*args)
    return official.canonical_return(problem, ret, head=head)


def main() -> int:
    payload = json.loads(sys.stdin.read())
    from hot100 import checker, official

    problem = payload["problem"]
    mode = payload["mode"]
    path = payload["path"]
    code_obj = None
    if payload.get("bc"):
        # 字节码只可能来自本机父进程 compile() 的结果（内部可信通道），
        # 这里仍校验类型与文件名，任何不符都回退到源码编译。
        try:
            candidate = marshal.loads(base64.b64decode(payload["bc"]))
            if isinstance(candidate, types.CodeType) and candidate.co_filename == path:
                code_obj = candidate
        except Exception:
            code_obj = None
    if code_obj is None:
        code_obj = compile(payload["code"], path, "exec")

    for case in payload["cases"]:
        t0 = time.perf_counter()
        row = {"type": "case", "index": case["index"], "actual": "", "detail": ""}
        try:
            if mode == "acm":
                out, err = _run_acm(code_obj, path, case)
                row["actual"] = out.strip()
                if out == "":
                    # 注意：空链表等合法答案会 print 出空行（"\n"），只有完全无输出才算错误。
                    row.update(
                        status="error",
                        ok=False,
                        detail="程序没有输出任何内容：检查 main / 入口是否被删除或改坏。"
                        + (f"\nstderr：{err.strip()[-400:]}" if err.strip() else ""),
                    )
                else:
                    actual = checker.parse_actual(problem["io"]["ret"], out)
                    expected = checker.parse_actual(problem["io"]["ret"], case["expected_acm"])
                    passed = checker.compare(problem, actual, expected, {"input": case["input_acm"]})
                    row.update(status="pass" if passed else "fail", ok=passed)
                    if not passed:
                        row["detail"] = "输出与官方期望不一致。" + (case.get("note") or "")
            else:
                actual = _run_core(code_obj, path, case, problem, official)
                row["actual"] = json.dumps(actual, ensure_ascii=False)
                passed = checker.compare(problem, actual, case["expected"], {"input": case["input_acm"]})
                row.update(status="pass" if passed else "fail", ok=passed)
                if not passed:
                    row["detail"] = "返回值与官方期望不一致。" + (case.get("note") or "")
        except SystemExit as exc:
            row.update(status="error", ok=False, detail=f"代码调用了 sys.exit({exc.code})，判题按运行错误处理。")
        except BaseException as exc:  # noqa: BLE001 - 用户代码的任何异常都要回报
            row.update(status="error", ok=False, detail=_tail_error(exc))
        row["ms"] = round((time.perf_counter() - t0) * 1000, 2)
        row["actual"] = row["actual"][:4000]
        row["detail"] = row["detail"][:2000]
        _emit(row)
    _emit({"type": "done"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())