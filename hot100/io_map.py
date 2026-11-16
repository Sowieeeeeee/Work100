"""从力扣 `metaData` 推断题目需要的 io 描述（P0 题源统一层的一部分）。

设计原则（见 DESIGN_v3 §2.2）：**只做通用推断，猜不出来就淘汰**。
`tools/build_dataset.py` 里那套逐 slug 的手工表（PARAM_KINDS / RETURN_KINDS /
COMPARE / DESIGN_SLUGS / MANUAL_SAMPLES）是给 88 题定制的，无法外推到几百道新题；
其通用分支 `infer_kind` 对未识别类型会静默返回 "int"（build_dataset.py:477），
对池题是灾难。这里改成显式白名单：不在白名单 = 返回淘汰原因。

调用方（tools/build_exam_pool.py）拿到 `None` 就该把这道题丢弃并记录原因。
"""
from __future__ import annotations

import json

# ---------------------------------------------------------------- 白名单
# 只保留能保证「LC 文本 -> 运行时对象 -> ACM 文本 -> 输出比对」全链路一致的种类。
PARAM_TYPE_KINDS = {
    "integer": "int",
    "long": "int",            # Python int 无界，long 只影响题面文档
    "boolean": "bool",
    "string": "str",
    "integer[]": "int_array",
    "string[]": "string_array",
    "integer[][]": "matrix",  # 与 read_matrix/fmt_matrix 自洽；区间类题按 exact 比对
    "ListNode": "linked_list",
    "TreeNode": "tree",
}

RETURN_TYPE_KINDS = dict(PARAM_TYPE_KINDS)

SUPPORTED_PARAM_KINDS = frozenset(PARAM_TYPE_KINDS.values())
SUPPORTED_RET_KINDS = frozenset(RETURN_TYPE_KINDS.values())

PARAM_DOC = {
    "int": "一个整数",
    "bool": "true / false",
    "str": "一行字符串",
    "int_array": "先读长度 n，再读 n 个整数",
    "string_array": "先读个数 n，再逐行读 n 个字符串",
    "matrix": "先读 rows cols，再读 rows 行、每行 cols 个整数",
    "linked_list": "先读结点数 n，再读 n 个整数",
    "tree": "先读层序长度 n，再读 n 个 token；null 表示空结点",
}

RETURN_DOC = {
    "int": "一个整数",
    "bool": "true 或 false",
    "str": "一行字符串",
    "int_array": "一行，空格分隔的整数；空数组输出空行",
    "string_array": "第一行个数，随后每行一个字符串",
    "matrix": "第一行行数 r，随后 r 行整数",
    "linked_list": "一行，空格分隔的链表值；空链表输出空行",
    "tree": "第一行层序长度，第二行层序 token（null 为空）",
}


def _meta_of(raw: dict) -> dict:
    """metaData 可能是 str（GraphQL 原样）也可能是 dict（已解析）。"""
    meta = raw.get("metaData")
    if isinstance(meta, dict):
        return meta
    if not meta:
        return {}
    try:
        return json.loads(meta)
    except (TypeError, ValueError):
        return {}


def _kind_of(type_name: str, table: dict[str, str]) -> str | None:
    return table.get((type_name or "").strip())


def infer_io(raw: dict, slug: str = "", pid: int = 0) -> tuple[dict | None, str]:
    """返回 (io, "") 或 (None, 淘汰原因)。

    io 结构与 `data/problems.json` 里的 `problem["io"]` 同构，可直接喂给
    judge / materials / official，无需池题特判。
    """
    meta = _meta_of(raw)
    if not meta:
        return None, "metaData 缺失或无法解析"
    if meta.get("systemdesign"):
        return None, "设计类题目（systemdesign）不通用推断"
    if meta.get("constructor"):
        return None, "交互式题目（有 constructor）不通用推断"

    name = meta.get("name")
    params = meta.get("params") or []
    if not isinstance(params, list) or not params:
        return None, "metaData.params 为空"
    if not name and not params:
        return None, "metaData.name 缺失"

    out_params: list[list[str]] = []
    for item in params:
        pname = (item or {}).get("name") or ""
        ptype = (item or {}).get("type") or ""
        kind = _kind_of(ptype, PARAM_TYPE_KINDS)
        if kind is None:
            return None, f"参数 {pname or '?'} 的类型 {ptype!r} 不在白名单"
        if not pname:
            return None, f"参数类型 {ptype!r} 缺少参数名"
        out_params.append([pname, kind])

    ret_type = (meta.get("return") or {}).get("type") or ""
    ret = _kind_of(ret_type, RETURN_TYPE_KINDS)
    if ret is None:
        return None, f"返回类型 {ret_type!r} 不在白名单（void/嵌套/浮点一律不支持）"

    io = {
        "mode": "standard",
        "classname": "",
        "params": out_params,
        "ret": ret,
        "compare": "exact",
        "input_doc": [
            f"`{pname}`：{PARAM_DOC[kind]}" for pname, kind in out_params
        ],
        "output_doc": [RETURN_DOC[ret]],
        "samples": [],
    }
    return io, ""


def describe_rejections(raws: dict[str, dict]) -> dict[str, str]:
    """批量推断，返回 {slug: 淘汰原因}；能推出来的不出现。"""
    rejected: dict[str, str] = {}
    for slug, raw in raws.items():
        io, reason = infer_io(raw, slug)
        if io is None:
            rejected[slug] = reason
    return rejected
