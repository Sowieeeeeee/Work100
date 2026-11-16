"""统一题源（DESIGN_v3 §2.1）。

88 题（core）与精选题池（pool）在判题/材料生成/教练链路上必须长得一样，
差别只有三处：

- core 有 `bank.BANK` 参考解（可做 oracle、可生成 reference/）；
- core 的原始数据在 `data/raw_questions.json`，pool 的在 `data/pool_raw.json`；
- pool 题的材料按需生成，不写 reference/。

这个模块只负责「按 slug / id 找到题和它的原始数据」，不 import
official / materials / judge，避免循环依赖；需要它们时在方法内延迟 import。
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

from .config import DATA

POOL_FILE = DATA / "exam_pool.json"
POOL_RAW_FILE = DATA / "pool_raw.json"
CORE_FILE = DATA / "problems.json"
CORE_RAW_FILE = DATA / "raw_questions.json"

_lock = threading.RLock()


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except (OSError, ValueError):
        return default


class ProblemSource:
    """题源基类。"""

    kind = ""

    def all(self) -> list[dict]:
        raise NotImplementedError

    def get(self, pid: int) -> dict | None:
        raise NotImplementedError

    def raw_of(self, slug: str) -> dict | None:
        raise NotImplementedError

    def has_reference(self, pid: int) -> bool:
        return False

    def ensure_materials(self, problem: dict, create_solution: bool = True) -> dict:
        from . import materials

        return materials.ensure_problem(
            problem,
            create_solution=create_solution,
            with_reference=self.has_reference(problem["id"]),
        )


class CoreSource(ProblemSource):
    """88 题：problems.json + raw_questions.json + bank.BANK。"""

    kind = "core"

    def __init__(self) -> None:
        self._problems: list[dict] | None = None
        self._by_id: dict[int, dict] = {}
        self._raw: dict[str, dict] | None = None

    def _load(self) -> None:
        if self._problems is not None:
            return
        data = _read_json(CORE_FILE, {})
        self._problems = list(data.get("problems") or [])
        self._by_id = {p["id"]: p for p in self._problems}

    def _load_raw(self) -> dict[str, dict]:
        if self._raw is None:
            raw = _read_json(CORE_RAW_FILE, {})
            self._raw = raw if isinstance(raw, dict) else {}
        return self._raw

    def all(self) -> list[dict]:
        self._load()
        return list(self._problems or [])

    def get(self, pid: int) -> dict | None:
        self._load()
        return self._by_id.get(int(pid))

    def raw_of(self, slug: str) -> dict | None:
        return self._load_raw().get(slug)

    def has_reference(self, pid: int) -> bool:
        from .bank import BANK

        return int(pid) in BANK


class PoolSource(ProblemSource):
    """精选题池：exam_pool.json + pool_raw.json，按文件 mtime 失效重载。"""

    kind = "pool"

    def __init__(self) -> None:
        self._problems: list[dict] = []
        self._by_id: dict[int, dict] = {}
        self._raw: dict[str, dict] = {}
        self._stamp: tuple = ()

    def _stamp_of(self) -> tuple:
        out = []
        for path in (POOL_FILE, POOL_RAW_FILE):
            try:
                out.append(path.stat().st_mtime_ns)
            except OSError:
                out.append(0)
        return tuple(out)

    def _load(self) -> None:
        stamp = self._stamp_of()
        if stamp == self._stamp:
            return
        with _lock:
            if stamp == self._stamp_of():
                data = _read_json(POOL_FILE, {})
                problems = data.get("problems") if isinstance(data, dict) else data
                self._problems = list(problems or [])
                self._by_id = {p["id"]: p for p in self._problems if "id" in p}
                raw = _read_json(POOL_RAW_FILE, {})
                self._raw = raw if isinstance(raw, dict) else {}
                self._stamp = stamp

    def all(self) -> list[dict]:
        self._load()
        return list(self._problems)

    def get(self, pid: int) -> dict | None:
        self._load()
        return self._by_id.get(int(pid))

    def raw_of(self, slug: str) -> dict | None:
        self._load()
        return self._raw.get(slug)


_core = CoreSource()
_pool = PoolSource()


def core() -> CoreSource:
    return _core


def pool() -> PoolSource:
    return _pool


def sources() -> tuple[ProblemSource, ...]:
    return (_core, _pool)


def raw_lookup(slug: str) -> dict:
    """先 core 后 pool；都没有才抛 KeyError（与 official.raw_of 原语义一致）。"""
    for source in sources():
        raw = source.raw_of(slug)
        if raw:
            return raw
    raise KeyError(slug)


def find_problem(pid: int) -> dict | None:
    """全局按 id 找题：core 优先（同 id 时以 88 题条目为准，见 DESIGN_v3 §3.1）。"""
    for source in sources():
        problem = source.get(pid)
        if problem:
            return problem
    return None


def all_problems() -> list[dict]:
    """core + pool 去重合并，core 在前。"""
    seen: set[int] = set()
    out: list[dict] = []
    for source in sources():
        for problem in source.all():
            pid = problem.get("id")
            if pid is None or pid in seen:
                continue
            seen.add(pid)
            out.append(problem)
    return out


def reset() -> None:
    """测试用：清掉缓存，下次访问重新读盘。"""
    global _core, _pool
    with _lock:
        _core = CoreSource()
        _pool = PoolSource()
