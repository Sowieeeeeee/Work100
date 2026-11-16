"""参考题解注册表。"""
from __future__ import annotations

BANK = {}


def register(pid: int, hints: list[str], complexity: str):
    """登记一道题的参考实现。

    hints 是两级中文提示，只在用户主动点击时展示。
    """

    def deco(fn):
        BANK[int(pid)] = {
            "fn": fn,
            "hints": list(hints),
            "complexity": complexity,
        }
        return fn

    return deco
