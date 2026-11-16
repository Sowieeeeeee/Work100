"""生成题面、ACM 模板和参考题解。"""
from __future__ import annotations

import inspect
import json
import re
import textwrap
from pathlib import Path

from . import acm_runtime, official
from .bank import BANK
from .config import CORE, DATA, REFERENCE, ROOT, SOLUTIONS

PROBLEMS_DIR = ROOT / "problems"


def load_problems() -> dict:
    return json.loads((DATA / "problems.json").read_text(encoding="utf-8"))


def runtime_source() -> str:
    source = Path(acm_runtime.__file__).read_text(encoding="utf-8")
    source = re.sub(r'^""".*?"""\s*', "", source, flags=re.S)
    return source.strip() + "\n"


def problem_paths(pid: int, slug: str) -> dict:
    name = f"{pid:04d}-{slug}"
    return {
        "statement": PROBLEMS_DIR / f"{name}.md",
        "solution": SOLUTIONS / f"{name}.py",
        "core": CORE / f"{name}.py",
        "reference": REFERENCE / f"{name}.py",
    }


def code_path(problem: dict, mode: str) -> Path:
    paths = problem_paths(problem["id"], problem["slug"])
    return paths["core"] if mode == "core" else paths["solution"]


def code_fence(text: str) -> str:
    return "```text\n" + text.rstrip() + "\n```"


def generate_statement(problem: dict, ref_name: str) -> str:
    io = problem["io"]
    lines = [
        f"# {problem['id']}. {problem['title']}",
        "",
        f"{problem['difficulty']} · {problem['group']} · [力扣原题]({problem['link']})",
        "",
        "## 题意",
        "",
        problem.get("description") or "题面见力扣原题链接。",
        "",
        "## 约束",
        "",
    ]
    constraints = problem.get("constraints") or []
    if constraints:
        lines.extend(f"- {item}" for item in constraints)
    else:
        lines.append("- 见力扣原题链接。")
    lines.extend(["", "## ACM 输入格式", "", "- 所有数字/字符串按空白或按行读入，具体如下："])
    lines.extend(f"- {item}" for item in io["input_doc"])
    lines.extend(["", "## ACM 输出格式", ""])
    lines.extend(f"- {item}" for item in io["output_doc"])
    for i, sample in enumerate(io.get("samples") or [], 1):
        lines.extend([
            "",
            f"## 样例 {i}",
            "",
            "输入：",
            "",
            code_fence(sample["input"]),
            "",
            "输出：",
            "",
            code_fence(sample["output"]),
        ])
    lines.extend([
        "",
        "## 训练约定",
        "",
        "- 先独立想 15 分钟，再看提示；25 分钟内完成，30 分钟是硬上限。",
        "- 卡住时先看提示 1，再看提示 2；仍写不出再看参考题解。",
        "- 看过参考题解后，标记为“看题解后复现”，并闭卷重写一遍。",
        "- 参考题解：[打开](../reference/" + ref_name + ")（完成或决定看答案后再打开）。",
        "",
    ])
    return "\n".join(lines)


def parse_bindings(problem: dict) -> tuple[list[str], list[str], list[str]]:
    """返回 (变量声明行, 参数名列表, 特殊处理标记)。"""
    io = problem["io"]
    pid = problem["id"]
    if io["mode"] == "design":
        return ["    ops, args = read_design(r)"], ["ops", "args"], ["design"]
    if pid == 160:
        return [
            "    na = read_int(r)",
            "    av = [read_int(r) for _ in range(na)]",
            "    nb = read_int(r)",
            "    bv = [read_int(r) for _ in range(nb)]",
            "    skip_a = read_int(r)",
            "    skip_b = read_int(r)",
            "    target, list_a, list_b = build_intersection(av, bv, skip_a, skip_b)",
        ], ["list_a", "list_b", "skip_a", "skip_b"], ["intersection"]
    if pid in (141, 142):
        return [
            "    n = read_int(r)",
            "    vals = [read_int(r) for _ in range(n)]",
            "    pos = read_int(r)",
            "    head = build_cycle(vals, pos)",
        ], ["head", "pos"], ["cycle"]
    readers = {
        "int": "read_int(r)",
        "bool": "read_bool(r)",
        "str": "read_str(r)",
        "int_array": "read_int_array(r)",
        "string_array": "read_string_array(r)",
        "matrix": "read_matrix(r)",
        "grid_int": "read_matrix(r)",
        "char_grid": "read_char_grid(r)",
        "intervals": "read_intervals(r)",
        "edges": "read_edges(r)",
        "linked_list": "read_list(r)",
        "tree": "read_tree(r)",
        "random_list": "read_random_list(r)",
    }
    lines, names = [], []
    for name, kind in io["params"]:
        lines.append(f"    {name} = {readers[kind]}")
        names.append(name)
    return lines, names, []


def output_lines(problem: dict, flags: list[str]) -> list[str]:
    io = problem["io"]
    ret = io["ret"]
    if "design" in flags:
        return ["    print(fmt_design(ans))"]
    if "intersection" in flags:
        return ["    print(-1 if ans is None else ans.val)"]
    if "cycle" in flags and problem["id"] == 142:
        return ["    print(-1 if ans is None else index_of_node(head, ans))"]
    formatters = {
        "int": "print(ans)",
        "bool": "print(fmt_bool(ans))",
        "str": "print(ans)",
        "node_value": "print(ans.val)",
        "int_array": "print(fmt_int_array(ans))",
        "string_array": "print(fmt_string_array(ans))",
        "matrix": "print(fmt_matrix(ans))",
        "groups_int": "print(fmt_groups(ans))",
        "groups_str": "print(fmt_groups(ans))",
        "tree": "print(fmt_tree(ans))",
        "linked_list": "print(fmt_list(ans))",
        "random_list": "print(fmt_random_list(ans))",
    }
    if ret not in formatters:
        raise ValueError(f"unsupported return kind {ret}")
    return ["    " + formatters[ret]]


def generate_main(problem: dict) -> str:
    declarations, names, flags = parse_bindings(problem)
    call = ", ".join(names)
    lines = [
        "",
        "def main():",
        "    sys.setrecursionlimit(1000000)",
        "    r = Reader()",
        *declarations,
        f"    ans = solve({call})",
        *output_lines(problem, flags),
        "",
        "",
        'if __name__ == "__main__":',
        "    main()",
    ]
    return "\n".join(lines)


def solve_source(pid: int) -> str:
    entry = BANK[pid]
    source = inspect.getsource(entry["fn"])
    lines = source.splitlines()
    while lines and not lines[0].lstrip().startswith("def "):
        lines.pop(0)
    source = textwrap.dedent("\n".join(lines)).strip() + "\n"
    source = re.sub(rf"\bsolve_{pid}\b", "solve", source)
    return source


def design_template(problem: dict) -> str:
    design = problem["io"].get("design") or {}
    classname = design.get("classname") or "Solution"
    ctor_params = [p["name"] for p in design.get("constructor", [])]
    methods = design.get("methods", [])
    lines = ["def solve(ops, args):", f"    class {classname}:"]
    lines.append(f"        def __init__(self{', ' + ', '.join(ctor_params) if ctor_params else ''}):")
    lines.append("            # TODO: 初始化数据结构")
    lines.append("            pass")
    lines.append("")
    for method in methods:
        params = [p["name"] for p in method.get("params", [])]
        signature = f"        def {method['name']}(self{', ' + ', '.join(params) if params else ''}):"
        lines.append(signature)
        ret = method.get("return", {}).get("type", "void")
        if ret == "void":
            lines.append("            # TODO: 实现该方法（无返回值）")
            lines.append("            pass")
        else:
            lines.append("            # TODO: 实现该方法并返回结果")
            lines.append("            return None")
        lines.append("")
    lines.extend([
        "    out = []",
        "    obj = None",
        "    for op, argv in zip(ops, args):",
        f'        if op == "{classname}":',
        f"            obj = {classname}(*argv)",
        "            out.append(None)",
        "        else:",
        "            out.append(getattr(obj, op)(*argv))",
        "    return out",
    ])
    return "\n".join(lines) + "\n"


def generate_practice(problem: dict) -> str:
    io = problem["io"]
    ref_name = f"{problem['id']:04d}-{problem['slug']}.py"
    samples = io.get("samples") or []
    sample_text = ""
    if samples:
        sample = samples[0]
        sample_text = (
            "\n【样例 1】\n输入:\n" + sample["input"] + "\n\n输出:\n" + sample["output"] + "\n"
        )
    header = (
        f'# -*- coding: utf-8 -*-\n'
        f'r"""\n'
        f'{problem["id"]}. {problem["title"]}（{problem["difficulty"]}）· {problem["group"]}\n'
        f'{problem["link"]}\n\n'
        "【ACM 模式】\n"
        "- 本题按标准输入输出作答，不要写 class Solution，也不要使用力扣的函数签名。\n"
        "- 输入输出格式见下；程序从 stdin 读入，向 stdout 输出。\n\n"
        "【输入】\n"
        + "\n".join(f"- {item}" for item in io["input_doc"])
        + "\n\n【输出】\n"
        + "\n".join(f"- {item}" for item in io["output_doc"])
        + "\n"
        + sample_text
        + "\n【训练流程】\n"
        "1. 先独立想 15 分钟，不看提示。\n"
        "2. 卡住时在仪表盘点“提示 1/2”，不要直接看参考题解。\n"
        "3. 25 分钟内完成；超时先在仪表盘标记“未完成”，下一轮优先重做。\n"
        "4. 如果看了参考题解，完成后标记“看题解后复现”，并闭卷再写一遍。\n"
        f"\n参考题解（完成后看）：reference/{ref_name}\n"
        '"""\n'
        "\n"
    )
    if io["mode"] == "design":
        stub = design_template(problem)
    else:
        params = ", ".join(name for name, _ in io["params"])
        stub = (
            f"def solve({params}):\n"
            "    # TODO: 在这里实现算法。\n"
            "    # 输入已经由上方的 main() 解析好，直接使用参数即可。\n"
            "    # 返回值类型见文件开头的【输出】说明。\n"
            '    raise NotImplementedError("删掉这一行，写下你的解法")\n'
        )
    return header + runtime_source() + "\n\n" + stub + generate_main(problem)


def generate_reference(problem: dict) -> str:
    entry = BANK[problem["id"]]
    hints = "\n".join(f"- 提示 {i}: {h}" for i, h in enumerate(entry["hints"], 1))
    header = (
        f'# -*- coding: utf-8 -*-\n'
        f'r"""\n'
        f'{problem["id"]}. {problem["title"]} · 参考题解\n'
        f'{problem["link"]}\n\n'
        f'复杂度：{entry["complexity"]}\n\n'
        f'{hints}\n\n'
        "说明：代码按 ACM 模式编写，包含完整输入解析、算法和输出。\n"
        '"""\n'
        "\n"
    )
    return header + runtime_source() + "\n\n" + solve_source(problem["id"]) + generate_main(problem)


def _node_class_source(names: list[str]) -> str:
    import inspect

    chunks = []
    for name in names:
        cls = getattr(acm_runtime, name)
        chunks.append(inspect.getsource(cls).rstrip())
    return "\n\n\n".join(chunks)


def generate_core(problem: dict) -> str:
    """核心代码模式脚手架：力扣官方签名 + 平台提供的节点类，全部可删改。"""
    io = problem["io"]
    meta = official.meta_of(problem)
    kinds = {k for _, k in io["params"]} | {io["ret"]}
    if problem["id"] in (141, 142, 160):
        kinds.add("linked_list")
    nodes = []
    if "linked_list" in kinds:
        nodes.append("ListNode")
    if "tree" in kinds:
        nodes.append("TreeNode")
    if "random_list" in kinds:
        nodes.append("RandomNode")
    if official.is_design(problem):
        call_doc = (
            f"- 判题驱动会先调用 {meta['classname']}(...) 构造对象，再按官方示例依次调用各方法。\n"
            "- 无返回值的方法返回 None 即可，驱动会输出 null。"
        )
    else:
        call_doc = (
            f"- 判题驱动会实例化 Solution 并调用 {meta['name']}(...)，参数已按力扣官方示例解析好。\n"
            "- 直接 return 结果即可，不需要写输入输出，也不需要 main。"
        )
    header = (
        f'# -*- coding: utf-8 -*-\n'
        f'r"""\n'
        f'{problem["id"]}. {problem["title"]}（{problem["difficulty"]}）· {problem["group"]}\n'
        f'{problem["link"]}\n\n'
        "【核心代码模式】\n"
        + call_doc
        + "\n- 下面的节点类由平台预先提供，可以修改或删除后自己重写。\n"
        "- 切换到 ACM 模式可编辑含 main 与输入输出的完整程序。\n"
        '"""\n\n'
    )
    body = _node_class_source(nodes) + "\n\n\n" if nodes else ""
    return header + body + official.snippet_of(problem)


def ensure_problem(problem: dict, create_solution: bool = True) -> dict:
    paths = problem_paths(problem["id"], problem["slug"])
    paths["statement"].parent.mkdir(parents=True, exist_ok=True)
    paths["solution"].parent.mkdir(parents=True, exist_ok=True)
    paths["core"].parent.mkdir(parents=True, exist_ok=True)
    paths["reference"].parent.mkdir(parents=True, exist_ok=True)
    ref_name = paths["reference"].name
    paths["statement"].write_text(generate_statement(problem, ref_name), encoding="utf-8")
    paths["reference"].write_text(generate_reference(problem), encoding="utf-8")
    if create_solution:
        if not paths["solution"].exists():
            paths["solution"].write_text(generate_practice(problem), encoding="utf-8")
        if not paths["core"].exists():
            paths["core"].write_text(generate_core(problem), encoding="utf-8")
    return paths


def ensure_all(create_solutions: bool = True) -> None:
    data = load_problems()
    for problem in data["problems"]:
        ensure_problem(problem, create_solution=create_solutions)
