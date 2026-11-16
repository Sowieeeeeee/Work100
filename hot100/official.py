"""力扣官方数据：函数签名、完整官方用例，以及 LC / ACM / 运行时三种格式互转。

用例来源有两处，取并集，保证不少于力扣任何一处展示：
1. `exampleTestcases`：力扣判题器实际使用的示例输入；
2. 题面 HTML 里的“示例 N”：含官方期望输出。
输入对不上的用例，期望输出由参考解（BANK）计算补齐。
"""
from __future__ import annotations

import copy
import html as html_mod
import json
import re
from collections import deque
from functools import lru_cache

from . import acm_runtime, problem_source


def raw_of(slug: str) -> dict:
    """题源统一入口（P0）：先查 88 题原始数据，再查精选题池原始数据。"""
    return problem_source.raw_lookup(slug)


def meta_of(problem: dict) -> dict:
    return json.loads(raw_of(problem["slug"])["metaData"])


def is_design(problem: dict) -> bool:
    return problem["io"]["mode"] == "design" or bool(meta_of(problem).get("systemdesign"))


def lc_param_count(problem: dict) -> int:
    meta = meta_of(problem)
    if is_design(problem):
        return 2
    return len(meta["params"])


# ---------------------------------------------------------------- 签名
def snippet_of(problem: dict) -> str:
    """力扣官方 Python3 代码片段，空函数体补 pass，保证可直接编译。"""
    for item in raw_of(problem["slug"])["codeSnippets"]:
        if item.get("lang") == "Python3":
            code = item["code"].rstrip() + "\n"
            break
    else:  # pragma: no cover - 数据缺失兜底
        meta = meta_of(problem)
        params = ", ".join(p["name"] for p in meta["params"])
        code = f"class Solution:\n    def {meta['name']}(self, {params}):\n        pass\n"
    lines = code.split("\n")
    out: list[str] = []
    for i, line in enumerate(lines):
        out.append(line)
        stripped = line.rstrip()
        if not re.match(r"^\s*(def |class )", stripped) or not stripped.endswith(":"):
            continue
        indent = len(line) - len(line.lstrip())
        nxt = next((l for l in lines[i + 1:] if l.strip()), "")
        nindent = len(nxt) - len(nxt.lstrip()) if nxt else -1
        if nindent <= indent:
            out.append(" " * (indent + 4) + "pass")
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------- LC 文本解析
def lc_parse(text: str):
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fixed = re.sub(r"\bnull\b", "None", text)
        fixed = re.sub(r"\btrue\b", "True", fixed)
        fixed = re.sub(r"\bfalse\b", "False", fixed)
        import ast

        return ast.literal_eval(fixed)


def split_top(text: str) -> list[str]:
    """按顶层逗号切分，忽略括号与引号内部的逗号。"""
    parts, buf, depth, quote = [], [], 0, None
    for ch in text:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch in "[{(":
            depth += 1
            buf.append(ch)
        elif ch in "]})":
            depth -= 1
            buf.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def assignment_values(text: str) -> list:
    values = []
    for part in split_top(text):
        m = re.match(r"^[A-Za-z_]\w*\s*=\s*(.*)$", part, re.S)
        values.append(lc_parse(m.group(1) if m else part))
    return values


def _clean(seg: str) -> str:
    seg = re.sub(r"<br\s*/?>", "\n", seg)
    seg = re.sub(r"</p>|</div>|</pre>", "\n", seg)
    seg = re.sub(r"<[^>]+>", "", seg)
    return html_mod.unescape(seg).replace("\xa0", " ")


def _segment(text: str, label: str) -> str | None:
    m = re.search(label + r"\s*[：:]\s*(.*?)(?=\n\s*(?:输入|输出|解释|说明|注意|提示)\s*[：:]|$)", text, re.S)
    return m.group(1).strip() if m else None


def html_examples(problem: dict) -> list[dict]:
    """题面里的示例：输入文本 + 输出文本，按示例编号顺序。"""
    content = raw_of(problem["slug"])["translatedContent"]
    markers = list(re.finditer(r"(?:示例|Example)\s*\d+\s*[：:]", content))
    out = []
    for i, mk in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(content)
        region = content[mk.end():end]
        pre = re.search(r"<pre>(.*?)</pre>", region, re.S)
        div = re.search(r'<div class="example-block">(.*?)</div>', region, re.S)
        cand = [m for m in (pre, div) if m]
        if not cand:
            continue
        block = min(cand, key=lambda m: m.start())
        text = _clean(block.group(1))
        inp = _segment(text, "输入")
        outp = _segment(text, "输出")
        if inp is None or outp is None:
            continue
        out.append({"input": inp, "output": outp})
    return out


def judge_inputs(problem: dict) -> list[list[str]]:
    lines = [l for l in raw_of(problem["slug"])["exampleTestcases"].split("\n") if l.strip()]
    n = lc_param_count(problem)
    return [lines[i:i + n] for i in range(0, len(lines) - n + 1, n)]


# ---------------------------------------------------------------- 期望输出
def expected_from_text(problem: dict, text: str):
    ret = problem["io"]["ret"]
    pid = problem["id"]
    if pid == 142:
        m = re.search(r"(?:index|索引)\s*(?:为)?\s*(-?\d+)", text)
        return int(m.group(1)) if m else -1
    if pid == 160:
        m = re.search(r"['\"](-?\d+)['\"]", text)
        return int(m.group(1)) if m else -1
    # 输出可能跨行（矩阵等），逐行累积直到能解析
    lines = [l for l in text.split("\n") if l.strip()]
    for i in range(len(lines), 0, -1):
        chunk = "\n".join(lines[:i]).strip()
        chunk = re.split(r"\n\s*(?:解释|说明|注意)", chunk)[0].strip()
        try:
            value = lc_parse(chunk)
        except Exception:
            continue
        return canonical_from_lc(ret, value)
    raise ValueError(f"无法解析官方输出：{text!r}")


def canonical_from_lc(ret: str, value):
    if ret == "tree":
        out = list(value)
        while out and out[-1] is None:
            out.pop()
        return out
    if ret == "random_list":
        return [[v, idx] for v, idx in value]
    if ret == "linked_list":
        return list(value)
    return value


def canonical_to_acm(ret: str, value) -> str:
    if ret in {"int", "node_value", "cycle_index", "intersection_value"}:
        return str(value)
    if ret == "bool":
        return "true" if value else "false"
    if ret == "str":
        return str(value)
    if ret == "int_array":
        return " ".join(str(x) for x in value)
    if ret == "linked_list":
        return " ".join(str(x) for x in value)
    if ret == "string_array":
        return "\n".join([str(len(value))] + [str(x) for x in value])
    if ret == "matrix":
        return "\n".join([str(len(value))] + [" ".join(str(x) for x in row) for row in value])
    if ret in {"groups_int", "groups_str"}:
        lines = [str(len(value))]
        for group in value:
            lines.append((str(len(group)) + " " + " ".join(str(x) for x in group)).rstrip())
        return "\n".join(lines)
    if ret == "tree":
        if not value:
            return "0"
        return str(len(value)) + "\n" + " ".join("null" if x is None else str(x) for x in value)
    if ret == "random_list":
        lines = [str(len(value))]
        for v, idx in value:
            lines.append(f"{v} {'null' if idx is None else idx}")
        return "\n".join(lines)
    if ret == "design":
        lines = []
        for v in value:
            if v is None:
                lines.append("null")
            elif isinstance(v, bool):
                lines.append("true" if v else "false")
            else:
                lines.append(str(v))
        return "\n".join(lines)
    raise ValueError(f"unsupported ret {ret}")


def lc_display(problem: dict, lc_args: list) -> str:
    meta = meta_of(problem)
    if is_design(problem):
        return "\n".join(json.dumps(v, ensure_ascii=False) for v in lc_args)
    names = [p["name"] for p in meta["params"]]
    return ", ".join(
        f"{n} = {json.dumps(v, ensure_ascii=False)}" for n, v in zip(names, lc_args)
    )


# ---------------------------------------------------------------- LC -> ACM 输入
def to_acm_input(problem: dict, lc_args: list) -> str:
    io = problem["io"]
    pid = problem["id"]
    if is_design(problem):
        ops, args = lc_args
        lines = [str(len(ops))]
        for op, argv in zip(ops, args):
            lines.append(" ".join([op] + [str(x) for x in argv]))
        return "\n".join(lines)
    if pid == 160:
        _, list_a, list_b, skip_a, skip_b = lc_args
        return "\n".join([
            str(len(list_a)), " ".join(map(str, list_a)),
            str(len(list_b)), " ".join(map(str, list_b)),
            str(skip_a), str(skip_b),
        ])
    if pid in (141, 142):
        vals, pos = lc_args
        return "\n".join([str(len(vals)), " ".join(map(str, vals)), str(pos)])
    lines = []
    for (name, kind), value in zip(io["params"], lc_args):
        if kind == "int":
            lines.append(str(value))
        elif kind == "bool":
            lines.append("true" if value else "false")
        elif kind == "str":
            lines.append(str(value))
        elif kind == "int_array":
            lines.append(str(len(value)))
            lines.append(" ".join(map(str, value)))
        elif kind == "string_array":
            lines.append(str(len(value)))
            lines.extend(str(x) for x in value)
        elif kind in {"matrix", "grid_int"}:
            lines.append(f"{len(value)} {len(value[0]) if value else 0}")
            lines.extend(" ".join(map(str, row)) for row in value)
        elif kind == "char_grid":
            lines.append(f"{len(value)} {len(value[0]) if value else 0}")
            lines.extend("".join(row) for row in value)
        elif kind in {"intervals", "edges"}:
            lines.append(str(len(value)))
            lines.extend(" ".join(map(str, row)) for row in value)
        elif kind == "linked_list":
            lines.append(str(len(value)))
            lines.append(" ".join(map(str, value)))
        elif kind == "tree":
            tokens = ["null" if x is None else str(x) for x in value]
            lines.append(str(len(tokens)))
            lines.append(" ".join(tokens))
        elif kind == "random_list":
            lines.append(str(len(value)))
            lines.extend(f"{v} {'null' if idx is None else idx}" for v, idx in value)
        else:
            raise ValueError(f"unsupported param kind {kind}")
    return "\n".join(lines)


# ---------------------------------------------------------------- LC -> 运行时对象
def _list_node(ns, vals):
    cls = ns["ListNode"]
    dummy = cls()
    tail = dummy
    for v in vals:
        tail.next = cls(v)
        tail = tail.next
    return dummy.next


def _tree_node(ns, tokens):
    cls = ns["TreeNode"]
    if not tokens or tokens[0] is None:
        return None
    root = cls(tokens[0])
    q = deque([root])
    i = 1
    while q and i < len(tokens):
        node = q.popleft()
        if i < len(tokens):
            t = tokens[i]
            i += 1
            if t is not None:
                node.left = cls(t)
                q.append(node.left)
        if i < len(tokens):
            t = tokens[i]
            i += 1
            if t is not None:
                node.right = cls(t)
                q.append(node.right)
    return root


def _random_node(ns, pairs):
    cls = ns["RandomNode"]
    nodes = [cls(v) for v, _ in pairs]
    for i, node in enumerate(nodes):
        if i + 1 < len(nodes):
            node.next = nodes[i + 1]
        idx = pairs[i][1]
        node.random = nodes[idx] if idx is not None else None
    return nodes[0] if nodes else None


def runtime_args(problem: dict, lc_args: list, ns: dict | None = None) -> list:
    """把 LC 示例值转成解题函数真正接收的对象（链表/树用 ns 里的类构造）。"""
    ns = ns or acm_runtime.__dict__
    pid = problem["id"]
    if pid == 160:
        _, list_a, list_b, skip_a, skip_b = lc_args
        _, head_a, head_b = acm_runtime.build_intersection(list_a, list_b, skip_a, skip_b)
        return [head_a, head_b]
    if pid in (141, 142):
        vals, pos = lc_args
        return [acm_runtime.build_cycle(vals, pos)]
    if is_design(problem):
        return list(lc_args)
    out = []
    for (name, kind), value in zip(problem["io"]["params"], lc_args):
        if kind == "linked_list":
            out.append(_list_node(ns, value))
        elif kind == "tree":
            out.append(_tree_node(ns, value))
        elif kind == "random_list":
            out.append(_random_node(ns, value))
        elif kind == "char_grid":
            out.append([list(row) for row in value])
        else:
            out.append(value)
    return out


def canonical_return(problem: dict, obj, head=None):
    """把解题函数返回值规范化成可与官方期望比较的 Python 值。"""
    ret = problem["io"]["ret"]
    pid = problem["id"]
    if pid == 142:
        return -1 if obj is None else acm_runtime.index_of_node(head, obj)
    if ret in {"node_value", "intersection_value"}:
        return -1 if obj is None else obj.val
    if ret == "linked_list":
        vals = []
        while obj:
            vals.append(obj.val)
            obj = obj.next
        return vals
    if ret == "tree":
        if obj is None:
            return []
        out = []
        q = deque([obj])
        while q:
            node = q.popleft()
            if node is None:
                out.append(None)
                continue
            out.append(node.val)
            q.append(node.left)
            q.append(node.right)
        while out and out[-1] is None:
            out.pop()
        return out
    if ret == "random_list":
        nodes = []
        cur = obj
        while cur:
            nodes.append(cur)
            cur = cur.next
        index = {id(n): i for i, n in enumerate(nodes)}
        return [[n.val, None if n.random is None else index[id(n.random)]] for n in nodes]
    return obj


# ---------------------------------------------------------------- 参考解兜底期望
def oracle_expected(problem: dict, lc_args: list):
    from .bank import BANK

    if problem["id"] not in BANK:
        raise LookupError(f"题目 {problem['id']} 没有参考解，不能用 oracle 补期望输出")
    fn = BANK[problem["id"]]["fn"]
    # 原地修改类题目（旋转数组等）会改写入参，必须先 deepcopy，避免污染用例数据
    lc_args = copy.deepcopy(lc_args)
    args = runtime_args(problem, lc_args)
    head = args[0] if problem["id"] in (141, 142) else None
    if problem["id"] == 160:
        _, list_a, list_b, skip_a, skip_b = lc_args
        _, head_a, head_b = acm_runtime.build_intersection(list_a, list_b, skip_a, skip_b)
        ans = fn(head_a, head_b, skip_a, skip_b)
    elif problem["id"] in (141, 142):
        ans = fn(args[0], lc_args[1])
    elif is_design(problem):
        ans = fn(*args)
    else:
        ans = fn(*args)
    return canonical_return(problem, ans, head=head)


# ---------------------------------------------------------------- 合并用例
def _norm_args(values: list) -> str:
    return json.dumps(values, ensure_ascii=False, sort_keys=True)


@lru_cache(maxsize=256)
def _cases_cached(pid: int, slug: str, io_key: str, allow_oracle: bool = True) -> tuple:
    problem = {"id": pid, "slug": slug, "io": json.loads(io_key)}
    pages = html_examples(problem)
    page_parsed = []
    for ex in pages:
        try:
            if is_design(problem):
                lines = [l for l in ex["input"].split("\n") if l.strip()]
                args = [lc_parse(l) for l in lines[:2]]
            else:
                args = assignment_values(ex["input"])
            expected = expected_from_text(problem, ex["output"])
        except Exception:
            continue
        page_parsed.append({"args": args, "expected": expected, "output_text": ex["output"]})

    cases, seen = [], set()
    for lines in judge_inputs(problem):
        args = copy.deepcopy([lc_parse(l) for l in lines])
        key = _norm_args(args)
        match = next((p for p in page_parsed if _norm_args(p["args"]) == key), None)
        if match:
            expected, source = match["expected"], "page"
        elif not allow_oracle:
            # 没有题面期望、又不允许用参考解补：宁可丢用例，也不造期望（DESIGN_v3 §3.1）。
            continue
        else:
            expected, source = oracle_expected(problem, args), "judge"
        seen.add(key)
        cases.append(_make_case(problem, len(cases) + 1, args, expected, source))
    for p in page_parsed:
        key = _norm_args(p["args"])
        if key in seen:
            continue
        seen.add(key)
        cases.append(_make_case(problem, len(cases) + 1, p["args"], p["expected"], "page"))
    return tuple(cases)


def _make_case(problem: dict, index: int, args: list, expected, source: str) -> dict:
    compare = problem["io"].get("compare", "exact")
    note = ""
    if compare == "valid_bst":
        note = "本题按结构判定：只要是包含全部输入值的高度平衡二叉搜索树即可，形状不唯一。"
    elif compare == "any_palindrome":
        note = "本题任意一个最长回文子串都算通过。"
    elif compare in {"unordered_nested", "unordered_outer", "unordered_flat"}:
        note = "本题不要求分组/元素顺序，顺序不同也算通过。"
    return {
        "index": index,
        "args": copy.deepcopy(args),
        "expected": copy.deepcopy(expected),
        "source": source,
        "note": note,
        "input_acm": to_acm_input(problem, args),
        "input_lc": lc_display(problem, args),
        "expected_acm": canonical_to_acm(problem["io"]["ret"], expected),
        "expected_lc": json.dumps(expected, ensure_ascii=False),
    }


def official_cases(problem: dict, allow_oracle: bool = True) -> list[dict]:
    """题目全部官方用例。

    allow_oracle=False 用于精选题池：池题没有参考解，任何「题面解析不出期望」的
    用例都会被丢弃（调用方须据此把整题淘汰，见 tools/build_exam_pool.py）。
    """
    io = problem["io"]
    io_key = json.dumps({"params": io["params"], "ret": io["ret"], "mode": io["mode"]}, sort_keys=True)
    return [dict(c) for c in _cases_cached(problem["id"], problem["slug"], io_key, allow_oracle)]