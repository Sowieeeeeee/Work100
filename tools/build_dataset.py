"""把力扣热题 100 的原始数据整理成本地训练器使用的 problems.json。

这个脚本可以重复运行；换题库时用 --plan-slug 指定其他学习计划。
"""
from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hot100 import acm_runtime  # noqa: E402

DIFF_CN = {"EASY": "简单", "MEDIUM": "中等", "HARD": "困难", "Easy": "简单", "Medium": "中等", "Hard": "困难"}

# 元数据里的类型不足以区分“矩阵/区间/网格/边”，这里按题目覆盖。
PARAM_KINDS = {
    "two-sum": [("nums", "int_array"), ("target", "int")],
    "group-anagrams": [("strs", "string_array")],
    "longest-consecutive-sequence": [("nums", "int_array")],
    "move-zeroes": [("nums", "int_array")],
    "container-with-most-water": [("height", "int_array")],
    "3sum": [("nums", "int_array")],
    "longest-substring-without-repeating-characters": [("s", "str")],
    "find-all-anagrams-in-a-string": [("s", "str"), ("p", "str")],
    "subarray-sum-equals-k": [("nums", "int_array"), ("k", "int")],
    "maximum-subarray": [("nums", "int_array")],
    "merge-intervals": [("intervals", "intervals")],
    "rotate-array": [("nums", "int_array"), ("k", "int")],
    "product-of-array-except-self": [("nums", "int_array")],
    "set-matrix-zeroes": [("matrix", "matrix")],
    "spiral-matrix": [("matrix", "matrix")],
    "rotate-image": [("matrix", "matrix")],
    "search-a-2d-matrix-ii": [("matrix", "matrix"), ("target", "int")],
    "intersection-of-two-linked-lists": [
        ("listA", "linked_list"), ("listB", "linked_list"), ("skipA", "int"), ("skipB", "int")
    ],
    "reverse-linked-list": [("head", "linked_list")],
    "palindrome-linked-list": [("head", "linked_list")],
    "linked-list-cycle": [("head", "linked_list"), ("pos", "int")],
    "linked-list-cycle-ii": [("head", "linked_list"), ("pos", "int")],
    "merge-two-sorted-lists": [("list1", "linked_list"), ("list2", "linked_list")],
    "add-two-numbers": [("l1", "linked_list"), ("l2", "linked_list")],
    "remove-nth-node-from-end-of-list": [("head", "linked_list"), ("n", "int")],
    "swap-nodes-in-pairs": [("head", "linked_list")],
    "copy-list-with-random-pointer": [("head", "random_list")],
    "sort-list": [("head", "linked_list")],
    "binary-tree-inorder-traversal": [("root", "tree")],
    "maximum-depth-of-binary-tree": [("root", "tree")],
    "invert-binary-tree": [("root", "tree")],
    "symmetric-tree": [("root", "tree")],
    "diameter-of-binary-tree": [("root", "tree")],
    "binary-tree-level-order-traversal": [("root", "tree")],
    "convert-sorted-array-to-binary-search-tree": [("nums", "int_array")],
    "validate-binary-search-tree": [("root", "tree")],
    "kth-smallest-element-in-a-bst": [("root", "tree"), ("k", "int")],
    "binary-tree-right-side-view": [("root", "tree")],
    "flatten-binary-tree-to-linked-list": [("root", "tree")],
    "construct-binary-tree-from-preorder-and-inorder-traversal": [
        ("preorder", "int_array"), ("inorder", "int_array")
    ],
    "path-sum-iii": [("root", "tree"), ("targetSum", "int")],
    "lowest-common-ancestor-of-a-binary-tree": [("root", "tree"), ("p", "int"), ("q", "int")],
    "number-of-islands": [("grid", "char_grid")],
    "rotting-oranges": [("grid", "grid_int")],
    "course-schedule": [("numCourses", "int"), ("prerequisites", "edges")],
    "permutations": [("nums", "int_array")],
    "subsets": [("nums", "int_array")],
    "letter-combinations-of-a-phone-number": [("digits", "str")],
    "combination-sum": [("candidates", "int_array"), ("target", "int")],
    "generate-parentheses": [("n", "int")],
    "word-search": [("board", "char_grid"), ("word", "str")],
    "palindrome-partitioning": [("s", "str")],
    "search-insert-position": [("nums", "int_array"), ("target", "int")],
    "search-a-2d-matrix": [("matrix", "matrix"), ("target", "int")],
    "find-first-and-last-position-of-element-in-sorted-array": [("nums", "int_array"), ("target", "int")],
    "search-in-rotated-sorted-array": [("nums", "int_array"), ("target", "int")],
    "find-minimum-in-rotated-sorted-array": [("nums", "int_array")],
    "valid-parentheses": [("s", "str")],
    "decode-string": [("s", "str")],
    "daily-temperatures": [("temperatures", "int_array")],
    "kth-largest-element-in-an-array": [("nums", "int_array"), ("k", "int")],
    "top-k-frequent-elements": [("nums", "int_array"), ("k", "int")],
    "best-time-to-buy-and-sell-stock": [("prices", "int_array")],
    "jump-game": [("nums", "int_array")],
    "jump-game-ii": [("nums", "int_array")],
    "partition-labels": [("s", "str")],
    "climbing-stairs": [("n", "int")],
    "pascals-triangle": [("numRows", "int")],
    "house-robber": [("nums", "int_array")],
    "perfect-squares": [("n", "int")],
    "coin-change": [("coins", "int_array"), ("amount", "int")],
    "word-break": [("s", "str"), ("wordDict", "string_array")],
    "longest-increasing-subsequence": [("nums", "int_array")],
    "maximum-product-subarray": [("nums", "int_array")],
    "partition-equal-subset-sum": [("nums", "int_array")],
    "unique-paths": [("m", "int"), ("n", "int")],
    "minimum-path-sum": [("grid", "grid_int")],
    "longest-palindromic-substring": [("s", "str")],
    "longest-common-subsequence": [("text1", "str"), ("text2", "str")],
    "edit-distance": [("word1", "str"), ("word2", "str")],
    "single-number": [("nums", "int_array")],
    "majority-element": [("nums", "int_array")],
    "sort-colors": [("nums", "int_array")],
    "next-permutation": [("nums", "int_array")],
    "find-the-duplicate-number": [("nums", "int_array")],
}

# 返回值类型；没有列出的题目按元数据自动推断。
RETURN_KINDS = {
    "move-zeroes": "int_array",
    "rotate-array": "int_array",
    "set-matrix-zeroes": "matrix",
    "rotate-image": "matrix",
    "flatten-binary-tree-to-linked-list": "tree",
    "sort-colors": "int_array",
    "next-permutation": "int_array",
    "intersection-of-two-linked-lists": "intersection_value",
    "linked-list-cycle-ii": "cycle_index",
    "lowest-common-ancestor-of-a-binary-tree": "node_value",
    "group-anagrams": "groups_str",
    "3sum": "groups_int",
    "permutations": "groups_int",
    "subsets": "groups_int",
    "combination-sum": "groups_int",
    "palindrome-partitioning": "groups_str",
    "letter-combinations-of-a-phone-number": "string_array",
    "generate-parentheses": "string_array",
    "top-k-frequent-elements": "int_array",
    "binary-tree-level-order-traversal": "groups_int",
    "pascals-triangle": "groups_int",
    "copy-list-with-random-pointer": "random_list",
    "construct-binary-tree-from-preorder-and-inorder-traversal": "tree",
    "convert-sorted-array-to-binary-search-tree": "tree",
    "invert-binary-tree": "tree",
    "binary-tree-inorder-traversal": "int_array",
    "binary-tree-right-side-view": "int_array",
    "kth-largest-element-in-an-array": "int",
}

COMPARE = {
    "group-anagrams": "unordered_nested",
    "3sum": "unordered_nested",
    "permutations": "unordered_outer",
    "subsets": "unordered_nested",
    "letter-combinations-of-a-phone-number": "unordered_flat",
    "combination-sum": "unordered_nested",
    "generate-parentheses": "unordered_flat",
    "palindrome-partitioning": "unordered_outer",
    "top-k-frequent-elements": "unordered_flat",
    "longest-palindromic-substring": "any_palindrome",
    "convert-sorted-array-to-binary-search-tree": "valid_bst",
}

DESIGN_SLUGS = {"lru-cache", "min-stack", "implement-trie-prefix-tree"}

MANUAL_SAMPLES = {
    "group-anagrams": [
        {
            "args": [["eat", "tea", "tan", "ate", "nat", "bat"]],
            "output": [["bat"], ["nat", "tan"], ["ate", "eat", "tea"]],
        }
    ],
    "binary-tree-right-side-view": [
        {"args": [[1, 2, 3, None, 5, None, 4]], "output": [1, 3, 4]},
    ],
    "valid-parentheses": [
        {"args": ["()"], "output": True},
        {"args": ["()[]{}"], "output": True},
        {"args": ["(]"], "output": False},
    ],
    "top-k-frequent-elements": [
        {"args": [[1, 1, 1, 2, 2, 3], 2], "output": [1, 2]},
        {"args": [[1], 1], "output": [1]},
    ],
    "single-number": [
        {"args": [[2, 2, 1]], "output": 1},
        {"args": [[4, 1, 2, 1, 2]], "output": 4},
    ],
    "sort-colors": [
        {"args": [[2, 0, 2, 1, 1, 0]], "output": [0, 0, 1, 1, 2, 2]},
        {"args": [[2, 0, 1]], "output": [0, 1, 2]},
    ],
}

KIND_DOC = {
    "int": "一个整数",
    "bool": "true / false",
    "str": "一行字符串",
    "int_array": "先读长度 n，再读 n 个整数",
    "string_array": "先读个数 n，再逐行读 n 个字符串",
    "matrix": "先读 rows cols，再读 rows 行、每行 cols 个整数",
    "grid_int": "先读 rows cols，再读 rows 行、每行 cols 个整数",
    "char_grid": "先读 rows cols，再读 rows 行字符串（每行长 cols）",
    "intervals": "先读区间数 n，再读 n 行，每行 l r",
    "edges": "先读边数 m，再读 m 行，每行 u v",
    "linked_list": "先读结点数 n，再读 n 个整数",
    "tree": "先读层序长度 n，再读 n 个 token；null 表示空结点",
    "random_list": "先读结点数 n，再读 n 行：val random_index（null 表示空）",
}

RETURN_DOC = {
    "int": "一个整数",
    "bool": "true 或 false",
    "str": "一行字符串",
    "int_array": "一行，空格分隔的整数；空数组输出空行",
    "string_array": "第一行个数，随后每行一个字符串",
    "matrix": "第一行行数 r，随后 r 行整数",
    "groups_int": "第一行组数，随后每组“元素个数 + 元素”",
    "groups_str": "第一行组数，随后每组“字符串个数 + 字符串”",
    "tree": "第一行层序长度，第二行层序 token（null 为空）",
    "linked_list": "一行，空格分隔的链表值；空链表输出空行",
    "random_list": "第一行结点数，随后每行 val random_index",
    "intersection_value": "相交节点的值；不相交输出 -1",
    "cycle_index": "环入口的下标；无环输出 -1",
    "node_value": "目标节点的值",
    "design": "每个操作一行；无返回值输出 null",
}


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
    desc = strip_tags(cut)
    desc = re.sub(r"\n+", "\n\n", desc).strip()
    return desc


def constraints_of(content: str) -> list[str]:
    text = content or ""
    uls = re.findall(r"<ul[^>]*>(.*?)</ul>", text, flags=re.S)
    if not uls:
        return []
    items = re.findall(r"<li[^>]*>(.*?)</li>", uls[-1], flags=re.S)
    out = []
    for item in items:
        cleaned = strip_tags(item).strip()
        if cleaned:
            out.append(cleaned)
    return out


def parse_output_value(text: str, ret_kind: str):
    text = text.strip()
    if ret_kind == "intersection_value":
        m = re.search(r"'(-?\d+)'", text)
        if m:
            return int(m.group(1))
        if "No intersection" in text or "不相交" in text:
            return -1
        return None
    if ret_kind == "cycle_index":
        m = re.search(r"索引为\s*(-?\d+)", text)
        if m:
            return int(m.group(1))
        if "null" in text or "无环" in text:
            return -1
        return None
    if ret_kind in {"int", "node_value"}:
        m = re.search(r"-?\d+", text)
        return int(m.group()) if m else None
    if ret_kind == "bool":
        if text.startswith("true") or text.startswith("True"):
            return True
        if text.startswith("false") or text.startswith("False"):
            return False
        return None
    try:
        decoder = json.JSONDecoder()
        value, _ = decoder.raw_decode(text)
        return value
    except (json.JSONDecodeError, ValueError):
        if ret_kind == "str":
            return text.strip('"').strip("“”")
        return None


def official_examples(raw: dict, spec: dict) -> list[dict]:
    """从 exampleTestcases 和题面输出中还原官方样例。"""
    lines = [ln.strip() for ln in (raw.get("exampleTestcases") or "").split("\n") if ln.strip()]
    params = spec["params"]
    grouped = []
    if spec["mode"] == "design":
        for i in range(0, len(lines) - 1, 2):
            try:
                ops = json.loads(lines[i])
                args = json.loads(lines[i + 1])
            except json.JSONDecodeError:
                continue
            grouped.append(([ops, args], None))
    elif raw["titleSlug"] == "intersection-of-two-linked-lists":
        for i in range(0, len(lines) - 4, 5):
            try:
                vals = [json.loads(lines[i + j]) for j in range(5)]
            except json.JSONDecodeError:
                continue
            grouped.append(([vals[1], vals[2], vals[3], vals[4]], None))
    else:
        width = len(params)
        for i in range(0, len(lines) - width + 1, width):
            try:
                args = [json.loads(lines[i + j]) for j in range(width)]
            except json.JSONDecodeError:
                continue
            grouped.append((args, None))

    # 抽取题面中的输出行。
    content = raw.get("translatedContent") or ""
    outputs = []
    for block in re.findall(r"<pre[^>]*>(.*?)</pre>", content, flags=re.S):
        plain = strip_tags(block)
        plain_lines = [ln.strip() for ln in plain.split("\n")]
        for idx, line in enumerate(plain_lines):
            normalized = line.strip().strip("*").strip()
            match = re.search(r"输出\s*[：:]\s*(.*)", line)
            if match:
                value = match.group(1).strip().strip("*").strip()
                value = value.strip("`").strip()
                if not value and idx + 1 < len(plain_lines):
                    value = plain_lines[idx + 1].strip().strip("*").strip("`").strip()
                outputs.append(value)
                break
            if normalized == "输出":
                value = ""
                if idx + 1 < len(plain_lines):
                    value = plain_lines[idx + 1].strip().strip("*").strip("`").strip()
                outputs.append(value)
                break

    result = []
    # 个别题目的示例数量与输出块数量不一致（例如缺少某个示例的输出），
    # 这时只保留第一个示例，避免把输出错配到别的输入上。
    if len(outputs) != len(grouped):
        grouped = grouped[:1]
        outputs = outputs[:1]
    for i, (args, _) in enumerate(grouped):
        if i >= len(outputs):
            break
        value = parse_output_value(outputs[i], spec["ret"])
        if value is None:
            continue
        result.append({"args": args, "output": value})
    return result


def fmt_input_value(kind: str, value) -> str:
    if kind == "int":
        return str(value)
    if kind == "bool":
        return "true" if value else "false"
    if kind == "str":
        return str(value)
    if kind == "int_array":
        return f"{len(value)}\n" + " ".join(str(x) for x in value)
    if kind == "string_array":
        return "\n".join([str(len(value))] + [str(x) for x in value])
    if kind in {"matrix", "grid_int"}:
        rows = len(value)
        cols = len(value[0]) if rows else 0
        body = "\n".join(" ".join(str(x) for x in row) for row in value)
        return f"{rows} {cols}\n{body}" if body else f"{rows} {cols}"
    if kind == "char_grid":
        rows = len(value)
        cols = len(value[0]) if rows else 0
        body = "\n".join("".join(str(x) for x in row) for row in value)
        return f"{rows} {cols}\n{body}" if body else f"{rows} {cols}"
    if kind in {"intervals", "edges"}:
        body = "\n".join(f"{a} {b}" for a, b in value)
        return f"{len(value)}\n{body}" if body else "0"
    if kind == "linked_list":
        return f"{len(value)}\n" + " ".join(str(x) for x in value)
    if kind == "tree":
        tokens = ["null" if x is None else str(x) for x in value]
        return f"{len(tokens)}\n" + " ".join(tokens)
    if kind == "random_list":
        rows = []
        for pair in value:
            val, idx = pair
            rows.append(f"{val} {'null' if idx is None else idx}")
        return "\n".join([str(len(value))] + rows)
    raise ValueError(f"unsupported input kind: {kind}")


def fmt_input(spec: dict, args: list) -> str:
    if spec["mode"] == "design":
        ops, op_args = args
        lines = [str(len(ops))]
        for op, argv in zip(ops, op_args):
            parts = [op] + [str(x) for x in argv]
            lines.append(" ".join(parts))
        return "\n".join(lines)
    parts = []
    for (name, kind), value in zip(spec["params"], args):
        parts.append(fmt_input_value(kind, value))
    return "\n".join(parts)


def fmt_output_value(kind: str, value) -> str:
    if kind == "int":
        return str(value)
    if kind == "bool":
        return "true" if value else "false"
    if kind == "str":
        return str(value)
    if kind == "node_value":
        return str(value)
    if kind == "int_array":
        return acm_runtime.fmt_int_array(value)
    if kind == "string_array":
        return acm_runtime.fmt_string_array(value)
    if kind == "matrix":
        return acm_runtime.fmt_matrix(value)
    if kind == "groups_int" or kind == "groups_str":
        return acm_runtime.fmt_groups(value)
    if kind == "tree":
        tokens = ["null" if x is None else str(x) for x in value]
        while tokens and tokens[-1] == "null":
            tokens.pop()
        return f"{len(tokens)}\n" + " ".join(tokens) if tokens else "0"
    if kind == "linked_list":
        return " ".join(str(x) for x in value)
    if kind == "random_list":
        rows = [str(len(value))]
        for val, idx in value:
            rows.append(f"{val} {'null' if idx is None else idx}")
        return "\n".join(rows)
    if kind == "intersection_value" or kind == "cycle_index":
        return str(value)
    if kind == "design":
        return acm_runtime.fmt_design(value)
    raise ValueError(f"unsupported return kind: {kind}")


def infer_kind(type_name: str) -> str:
    mapping = {
        "integer": "int",
        "string": "str",
        "boolean": "bool",
        "character": "str",
        "double": "float",
        "integer[]": "int_array",
        "string[]": "string_array",
        "character[][]": "char_grid",
        "integer[][]": "matrix",
        "ListNode": "linked_list",
        "TreeNode": "tree",
        "list<integer>": "int_array",
        "list<string>": "string_array",
        "list<list<integer>>": "groups_int",
        "list<list<string>>": "groups_str",
        "void": "void",
    }
    return mapping.get(type_name, "int")


def build_spec(slug: str, raw: dict) -> dict:
    if slug in DESIGN_SLUGS:
        meta = json.loads(raw["metaData"])
        return {
            "mode": "design",
            "classname": meta.get("classname", ""),
            "design": {
                "classname": meta.get("classname", ""),
                "constructor": meta.get("constructor", {}).get("params", []),
                "methods": meta.get("methods", []),
            },
            "params": [],
            "ret": "design",
            "compare": "exact",
            "input_doc": [
                "第一行：操作数 m。",
                "随后 m 行：每行一个操作名和参数（空格分隔）。",
                "第一行通常是构造函数，例如 `LRUCache 2`；void 操作没有返回值。",
            ],
            "output_doc": ["每个操作输出一行；构造函数和 void 操作输出 `null`。"],
            "samples": MANUAL_SAMPLES.get(slug, []),
        }
    meta = json.loads(raw["metaData"])
    slug_params = PARAM_KINDS.get(slug)
    if slug_params:
        params = list(slug_params)
    else:
        params = [(p["name"], infer_kind(p["type"])) for p in meta.get("params", [])]
    ret = RETURN_KINDS.get(slug)
    if not ret:
        ret = infer_kind(meta.get("return", {}).get("type", "integer"))
    compare = COMPARE.get(slug, "exact")
    input_doc = [f"`{name}`：{KIND_DOC.get(kind, kind)}。" for name, kind in params]
    if slug == "intersection-of-two-linked-lists":
        input_doc = [
            "`listA`：先读结点数 n，再读 n 个整数。",
            "`listB`：先读结点数 n，再读 n 个整数。",
            "`skipA`、`skipB`：两个整数，表示相交起点在各自链表中的下标。",
            "注意：力扣原始输入里的 intersectVal 不参与输入，程序自行判断是否相交。",
        ]
    if slug in {"linked-list-cycle", "linked-list-cycle-ii"}:
        input_doc = [
            "`head`：先读结点数 n，再读 n 个整数。",
            "`pos`：尾结点连接到的下标；-1 表示无环。",
        ]
    if slug == "copy-list-with-random-pointer":
        input_doc = ["`head`：先读结点数 n，再读 n 行，每行 `val random_index`；null 表示随机指针为空。"]
    if slug == "lowest-common-ancestor-of-a-binary-tree":
        input_doc = [
            "`root`：先读层序长度 n，再读 n 个 token；null 表示空结点。",
            "`p`、`q`：两个整数，表示目标结点的值。",
        ]
    if ret == "tree" and slug == "flatten-binary-tree-to-linked-list":
        output_doc = ["按层序输出展开后的链表（只使用右指针），null 表示空位。"]
    elif ret == "tree":
        output_doc = ["先输出层序长度，再输出层序 token；null 表示空结点。"]
    elif ret == "random_list":
        output_doc = ["先输出结点数 n，再输出 n 行 `val random_index`。"]
    elif ret == "groups_int":
        output_doc = ["第一行输出组数；随后每组输出“元素个数 + 元素”，空格分隔。"]
    elif ret == "groups_str":
        output_doc = ["第一行输出组数；随后每组输出“字符串个数 + 字符串”，空格分隔。"]
    elif ret == "string_array":
        output_doc = ["第一行输出个数，随后每行一个字符串。"]
    elif ret == "intersection_value":
        output_doc = ["相交节点的值；不相交输出 -1。"]
    elif ret == "cycle_index":
        output_doc = ["环入口的下标；无环输出 -1。"]
    else:
        output_doc = [RETURN_DOC.get(ret, ret) + "。"]
    return {
        "mode": "standard",
        "classname": "",
        "params": params,
        "ret": ret,
        "compare": compare,
        "input_doc": input_doc,
        "output_doc": output_doc,
        "samples": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default=str(ROOT / "data" / "raw_questions.json"))
    parser.add_argument("--plan", default=str(ROOT / "data" / "plan_raw.json"))
    parser.add_argument("--out", default=str(ROOT / "data" / "problems.json"))
    parser.add_argument("--difficulties", default="EASY,MEDIUM")
    args = parser.parse_args()

    raw_all = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    if "data" in plan:
        plan = plan["data"].get("studyPlanV2Detail") or plan["data"]
    allowed = {x.strip().upper() for x in args.difficulties.split(",") if x.strip()}
    group_map = {}
    for gi, group in enumerate(plan["planSubGroups"]):
        for q in group["questions"]:
            group_map[q["titleSlug"]] = (gi, group["name"])

    problems = []
    order = 0
    for slug, raw in raw_all.items():
        diff = raw["difficulty"].upper()
        if diff not in allowed:
            continue
        spec = build_spec(slug, raw)
        if not spec.get("samples"):
            samples = official_examples(raw, spec)
            if samples:
                spec["samples"] = samples
        if not spec["samples"] and slug in MANUAL_SAMPLES:
            spec["samples"] = MANUAL_SAMPLES[slug]
        # 统一转换成 ACM 文本。
        acm_samples = []
        for sample in spec["samples"][:3]:
            try:
                text_in = fmt_input(spec, sample["args"])
                text_out = fmt_output_value(spec["ret"], sample["output"])
            except Exception as exc:  # 数据有问题时保留题面，不让构建中断
                print(f"[warn] {slug} sample skipped: {exc}")
                continue
            acm_samples.append({"input": text_in, "output": text_out})
        spec["samples"] = acm_samples
        gi, gname = group_map.get(slug, (99, "其他"))
        problems.append({
            "id": int(raw["questionFrontendId"]),
            "slug": slug,
            "title": raw["translatedTitle"],
            "title_en": raw["title"],
            "difficulty": DIFF_CN.get(raw["difficulty"], raw["difficulty"]),
            "group": gname,
            "group_order": gi,
            "order": order,
            "link": f"https://leetcode.cn/problems/{slug}/",
            "description": description_of(raw.get("translatedContent") or ""),
            "constraints": constraints_of(raw.get("translatedContent") or ""),
            "topics": [t.get("translatedName") or t.get("name") for t in raw.get("topicTags", [])],
            "io": spec,
        })
        order += 1

    problems.sort(key=lambda p: (p["group_order"], p["order"]))
    for i, p in enumerate(problems):
        p["order"] = i
    out = {
        "name": "LeetCode 热题 100（简单 + 中等）",
        "source": "https://leetcode.cn/studyplan/top-100-liked/",
        "deadline": "2026-11-10",
        "total": len(problems),
        "problems": problems,
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {len(problems)} problems -> {args.out}")
    for p in problems:
        print(f"{p['id']:>4} {p['difficulty']} {p['title']}  samples={len(p['io']['samples'])}")


if __name__ == "__main__":
    main()
