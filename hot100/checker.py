"""样例校验：运行题解文件并比较输出。"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from . import acm_runtime


def parse_actual(ret: str, text: str):
    text = text.strip()
    if ret in {"int", "intersection_value", "cycle_index", "node_value"}:
        return int(text.split()[0])
    if ret == "bool":
        return text.lower().startswith("true")
    if ret == "str":
        return text
    if ret == "int_array":
        return [int(x) for x in text.split()]
    if ret == "string_array":
        return acm_runtime.parse_string_array(text)
    if ret == "matrix":
        return acm_runtime.parse_matrix(text)
    if ret == "groups_int":
        return [[int(x) for x in group] for group in acm_runtime.parse_groups(text)]
    if ret == "groups_str":
        return acm_runtime.parse_groups(text)
    if ret == "tree":
        return acm_runtime.parse_tree_tokens(text)
    if ret == "linked_list":
        return [int(x) for x in text.split()]
    if ret == "random_list":
        lines = [line for line in text.split("\n") if line.strip()]
        if not lines:
            return []
        result = []
        for line in lines[1:]:
            parts = line.split()
            result.append((int(parts[0]), None if parts[1] == "null" else int(parts[1])))
        return result
    if ret == "design":
        return [line.strip() for line in text.split("\n") if line.strip()]
    raise ValueError(f"unsupported ret kind {ret}")


def normalize_nested(value):
    return sorted(tuple(sorted(item)) if isinstance(item, list) else item for item in value)


def normalize_outer(value):
    return sorted(tuple(item) for item in value)


def tree_from_tokens(tokens: list[str]):
    from collections import deque

    class Node:
        def __init__(self, val):
            self.val = val
            self.left = None
            self.right = None

    if not tokens or tokens[0] == "null" or tokens[0] is None:
        return None
    root = Node(int(tokens[0]))
    q = deque([root])
    i = 1
    while q and i < len(tokens):
        node = q.popleft()
        if i < len(tokens):
            t = tokens[i]
            i += 1
            if t is not None and t != "null":
                node.left = Node(int(t))
                q.append(node.left)
        if i < len(tokens):
            t = tokens[i]
            i += 1
            if t is not None and t != "null":
                node.right = Node(int(t))
                q.append(node.right)
    return root


def inorder(root):
    return inorder(root.left) + [root.val] + inorder(root.right) if root else []


def height(root):
    return 0 if not root else 1 + max(height(root.left), height(root.right))


def is_valid_bst(values: list[str], expected_n: int) -> bool:
    root = tree_from_tokens(values)
    order = inorder(root)
    if len(order) != expected_n or order != sorted(order):
        return False

    def balanced(node):
        if not node:
            return 0, True
        left_h, left_ok = balanced(node.left)
        right_h, right_ok = balanced(node.right)
        ok = left_ok and right_ok and abs(left_h - right_h) <= 1
        return 1 + max(left_h, right_h), ok

    return balanced(root)[1]


def compare(problem: dict, actual, expected, sample: dict) -> bool:
    mode = problem["io"].get("compare", "exact")
    if mode == "exact":
        return actual == expected
    if mode == "unordered_nested":
        return normalize_nested(actual) == normalize_nested(expected)
    if mode == "unordered_outer":
        return normalize_outer(actual) == normalize_outer(expected)
    if mode == "unordered_flat":
        return sorted(map(str, actual)) == sorted(map(str, expected))
    if mode == "any_palindrome":
        s = sample["input"].splitlines()[0].strip() if sample["input"] else ""
        return (
            isinstance(actual, str)
            and len(actual) == len(expected)
            and actual == actual[::-1]
            and actual in s
        )
    if mode == "valid_bst":
        lines = sample["input"].splitlines()
        n = int(lines[0].strip())
        if not is_valid_bst(actual, n):
            return False
        # 108 这类题还要求树里恰好是输入的全部值（形状不唯一）
        if len(lines) > 1 and lines[1].strip():
            nums = sorted(int(x) for x in lines[1].split())
            return inorder(tree_from_tokens(actual)) == nums
        return True
    return actual == expected


def _decode(data: bytes | None) -> str:
    if not data:
        return ""
    for encoding in ("utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "replace")


def run_file(path: Path, stdin: str, timeout: int = 15) -> tuple[bool, str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        proc = subprocess.run(
            [sys.executable, str(path)],
            input=stdin.encode("utf-8"),
            capture_output=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return False, "超时（>15 秒）"
    if proc.returncode != 0:
        error = _decode(proc.stderr).strip().splitlines()
        return False, "运行出错：" + (error[-1] if error else f"退出码 {proc.returncode}")
    return True, _decode(proc.stdout)


def check_file(problem: dict, path: Path) -> list[dict]:
    results = []
    for i, sample in enumerate(problem["io"].get("samples") or [], 1):
        ok, output = run_file(path, sample["input"])
        if not ok:
            results.append({"sample": i, "ok": False, "detail": output})
            continue
        try:
            actual = parse_actual(problem["io"]["ret"], output)
            expected = parse_actual(problem["io"]["ret"], sample["output"])
            passed = compare(problem, actual, expected, sample)
        except Exception as exc:
            results.append({"sample": i, "ok": False, "detail": f"输出解析失败：{exc}\n实际输出：{output!r}"})
            continue
        detail = "" if passed else f"期望：{sample['output']!r}\n实际：{output!r}"
        results.append({"sample": i, "ok": passed, "detail": detail})
    return results
