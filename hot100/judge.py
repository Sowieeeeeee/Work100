"""双模式判题与无感知预编译。

- ACM 模式：整份程序（含 main 与全部辅助函数）在隔离子进程里按标准输入输出运行；
- 核心代码模式：只执行力扣签名的 class Solution / 设计类，由判题驱动喂官方示例；
- 预编译：编辑时后台 compile() 并缓存字节码，运行时直接把 marshal 字节码交给
  判题子进程 exec，用户不需要点任何“编译”按钮。
"""
from __future__ import annotations

import base64
import hashlib
import json
import marshal
import subprocess
import sys
import threading
import time
from collections import OrderedDict

from . import official
from .config import ROOT

MODES = ("acm", "core")
RUN_TIMEOUT = 30

_cache: "OrderedDict[str, object]" = OrderedDict()
_lock = threading.Lock()
_CACHE_MAX = 96


def code_hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _store(h: str, obj) -> None:
    with _lock:
        _cache[h] = obj
        _cache.move_to_end(h)
        while len(_cache) > _CACHE_MAX:
            _cache.popitem(last=False)


def compiled(code: str, filename: str):
    """取缓存的编译结果；没有就编译并入缓存。SyntaxError 向上抛。"""
    h = code_hash(code)
    with _lock:
        obj = _cache.get(h)
        if obj is not None:
            _cache.move_to_end(h)
            return obj
    obj = compile(code, filename, "exec")
    _store(h, obj)
    return obj


def precompile(code: str, filename: str = "<editor>") -> dict:
    """后台预编译：只回报语法诊断与耗时，供编辑器静默展示。"""
    t0 = time.perf_counter()
    try:
        compiled(code, filename)
    except SyntaxError as exc:
        return {
            "ok": False,
            "ms": round((time.perf_counter() - t0) * 1000, 1),
            "error": {
                "line": exc.lineno or 0,
                "offset": exc.offset or 0,
                "msg": exc.msg or "语法错误",
            },
        }
    except ValueError as exc:
        return {"ok": False, "ms": 0, "error": {"line": 0, "offset": 0, "msg": str(exc)}}
    return {"ok": True, "ms": round((time.perf_counter() - t0) * 1000, 1), "error": None}


def _payload(problem: dict, mode: str, code: str, path: str, cases: list[dict]) -> bytes:
    body = {
        "mode": mode,
        "path": path,
        "problem": {"id": problem["id"], "slug": problem["slug"], "io": problem["io"]},
        "cases": cases,
        "code": code,
    }
    try:
        obj = compiled(code, path)
        body["bc"] = base64.b64encode(marshal.dumps(obj)).decode("ascii")
    except SyntaxError:
        raise
    except Exception:
        body["bc"] = None
    return json.dumps(body, ensure_ascii=False).encode("utf-8")


def run(problem: dict, mode: str, code: str, path: str) -> dict:
    """跑全部官方用例，返回逐用例结果与通过率指标。"""
    return run_cases(problem, mode, code, path, official.official_cases(problem))


def run_cases(problem: dict, mode: str, code: str, path: str, cases: list[dict]) -> dict:
    """跑一组给定用例（考试/面试复用，不依赖 BANK，不落盘）。"""
    if mode not in MODES:
        raise ValueError(f"未知模式 {mode}")
    slim = [
        {
            "index": c["index"],
            "args": c["args"],
            "expected": c["expected"],
            "input_acm": c["input_acm"],
            "input_lc": c["input_lc"],
            "expected_acm": c["expected_acm"],
            "expected_lc": c["expected_lc"],
            "note": c.get("note", ""),
        }
        for c in cases
    ]
    payload = _payload(problem, mode, code, path, slim)
    t0 = time.perf_counter()
    interrupted = False
    try:
        proc = subprocess.run(
            [sys.executable, "-B", "-m", "hot100.judge_worker"],
            input=payload,
            capture_output=True,
            timeout=RUN_TIMEOUT,
            cwd=str(ROOT),
            env=_env(),
        )
        out = proc.stdout
    except subprocess.TimeoutExpired as exc:
        interrupted = True
        out = exc.stdout or b""
    wall_ms = round((time.perf_counter() - t0) * 1000, 1)

    results = []
    for line in out.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("type") == "case":
            results.append(row)
    by_index = {r["index"]: r for r in results}
    final = []
    for c in slim:
        row = by_index.get(c["index"])
        if row is None:
            row = {
                "index": c["index"],
                "status": "timeout" if interrupted else "error",
                "ok": False,
                "ms": 0,
                "detail": "判题进程超时被终止，该用例未跑完。" if interrupted else "判题进程中断，该用例没有结果。",
                "actual": "",
            }
        row.setdefault("input", c["input_acm"] if mode == "acm" else c["input_lc"])
        row.setdefault("expected", c["expected_acm"] if mode == "acm" else c["expected_lc"])
        row.setdefault("note", c.get("note", ""))
        final.append(row)

    passed = sum(1 for r in final if r["status"] == "pass")
    failed = sum(1 for r in final if r["status"] == "fail")
    errors = sum(1 for r in final if r["status"] in ("error", "timeout"))
    times = [r["ms"] for r in final if r["status"] in ("pass", "fail")]
    metrics = {
        "total": len(final),
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "pass_rate": round(passed * 100 / len(final), 1) if final else 0,
        "total_ms": round(sum(r["ms"] for r in final), 1),
        "avg_ms": round(sum(times) / len(times), 1) if times else 0,
        "max_ms": round(max(times), 1) if times else 0,
        "wall_ms": wall_ms,
        "interrupted": interrupted,
    }
    return {"mode": mode, "results": final, "metrics": metrics}


def _env() -> dict:
    import os

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(ROOT)
    return env