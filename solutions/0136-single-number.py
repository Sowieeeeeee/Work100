# -*- coding: utf-8 -*-
r"""
136. 只出现一次的数字（简单）· 技巧
https://leetcode.cn/problems/single-number/

【ACM 模式】
- 本题按标准输入输出作答，不要写 class Solution，也不要使用力扣的函数签名。
- 输入输出格式见下；程序从 stdin 读入，向 stdout 输出。

【输入】
- `nums`：先读长度 n，再读 n 个整数。

【输出】
- 一个整数。

【样例 1】
输入:
3
2 2 1

输出:
1

【训练流程】
1. 先独立想 15 分钟，不看提示。
2. 卡住时在仪表盘点“提示 1/2”，不要直接看参考题解。
3. 25 分钟内完成；超时先在仪表盘标记“未完成”，下一轮优先重做。
4. 如果看了参考题解，完成后标记“看题解后复现”，并闭卷再写一遍。

参考题解（完成后看）：reference/0136-single-number.py
"""

from collections import deque
import sys


class ListNode:
    """单链表节点。"""

    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class TreeNode:
    """二叉树节点。"""

    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class RandomNode:
    """带随机指针的链表节点。"""

    def __init__(self, val=0, next=None, random=None):
        self.val = val
        self.next = next
        self.random = random


class Reader:
    """按空白或按行读取输入，两种方式可以混用。"""

    def __init__(self):
        import sys

        self.lines = sys.stdin.read().replace("\r\n", "\n").split("\n")
        self.line_no = 0
        self.parts = []

    def token(self):
        while not self.parts:
            if self.line_no >= len(self.lines):
                raise EOFError("输入数据不足")
            line = self.lines[self.line_no]
            self.line_no += 1
            self.parts = line.split()
        return self.parts.pop(0)

    def line(self):
        if self.parts:
            rest = " ".join(self.parts)
            self.parts = []
            return rest
        while self.line_no < len(self.lines) and not self.lines[self.line_no].strip():
            self.line_no += 1
        if self.line_no >= len(self.lines):
            return ""
        line = self.lines[self.line_no].strip()
        self.line_no += 1
        return line

    def int(self):
        return int(self.token())


def read_int(r):
    """读一个整数。"""
    return r.int()


def read_bool(r):
    """读 true / false。"""
    return r.token().lower() == "true"


def read_str(r):
    """读一行字符串（保留空格）。"""
    return r.line()


def read_int_array(r):
    """先读长度 n，再读 n 个整数。"""
    n = r.int()
    return [r.int() for _ in range(n)]


def read_string_array(r):
    """先读个数 n，再逐行读 n 个字符串。"""
    n = r.int()
    return [r.line() for _ in range(n)]


def read_matrix(r):
    """先读 rows cols，再逐行读 rows * cols 个整数。"""
    rows, cols = r.int(), r.int()
    return [[r.int() for _ in range(cols)] for _ in range(rows)]


def read_char_grid(r):
    """先读 rows cols，再逐行读 rows 个长度为 cols 的字符串。"""
    rows, cols = r.int(), r.int()
    grid = []
    for _ in range(rows):
        row = r.line().replace(" ", "")
        if len(row) < cols:
            row = row.ljust(cols)
        grid.append(list(row[:cols]))
    return grid


def read_intervals(r):
    """先读区间个数 n，再读 n 行，每行两个整数。"""
    n = r.int()
    return [[r.int(), r.int()] for _ in range(n)]


def read_edges(r):
    """先读边数 m，再读 m 行，每行一条有向边 u v。"""
    m = r.int()
    return [[r.int(), r.int()] for _ in range(m)]


def read_list(r):
    """先读结点数 n，再读 n 个整数，构造单链表。"""
    n = r.int()
    vals = [r.int() for _ in range(n)]
    dummy = ListNode()
    tail = dummy
    for v in vals:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def build_intersection(a_vals, b_vals, skip_a, skip_b):
    """构造两条相交链表；skip_a / skip_b 是相交前的结点数。"""
    nodes_a = [ListNode(v) for v in a_vals]
    for i in range(len(nodes_a) - 1):
        nodes_a[i].next = nodes_a[i + 1]
    if skip_a < 0 or skip_b < 0 or skip_a >= len(nodes_a) or skip_b >= len(b_vals):
        nodes_b = [ListNode(v) for v in b_vals]
        for i in range(len(nodes_b) - 1):
            nodes_b[i].next = nodes_b[i + 1]
        return None, (nodes_a[0] if nodes_a else None), (nodes_b[0] if nodes_b else None)
    nodes_b = [ListNode(v) for v in b_vals[:skip_b]]
    for i in range(len(nodes_b) - 1):
        nodes_b[i].next = nodes_b[i + 1]
    head_b = nodes_b[0] if nodes_b else nodes_a[skip_a]
    if nodes_b:
        nodes_b[-1].next = nodes_a[skip_a]
    return nodes_a[skip_a], (nodes_a[0] if nodes_a else None), head_b


def build_cycle(vals, pos):
    """构造带环链表，返回头结点。"""
    if not vals:
        return None
    nodes = [ListNode(v) for v in vals]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    if 0 <= pos < len(nodes):
        nodes[-1].next = nodes[pos]
    return nodes[0]


def read_tree(r):
    """先读层序序列长度 n，再读 n 个 token（null 表示空结点）。"""
    n = r.int()
    tokens = [r.token() for _ in range(n)]
    if not tokens or tokens[0] == "null":
        return None
    root = TreeNode(int(tokens[0]))
    q = deque([root])
    i = 1
    while q and i < n:
        node = q.popleft()
        if i < n:
            t = tokens[i]
            i += 1
            if t != "null":
                node.left = TreeNode(int(t))
                q.append(node.left)
        if i < n:
            t = tokens[i]
            i += 1
            if t != "null":
                node.right = TreeNode(int(t))
                q.append(node.right)
    return root


def read_random_list(r):
    """先读结点数 n，再读 n 行：val random_index（-1 表示空）。"""
    n = r.int()
    if n == 0:
        return None
    pairs = []
    for _ in range(n):
        val = r.int()
        idx = r.token()
        pairs.append((val, None if idx == "null" or idx == "-1" else int(idx)))
    nodes = [RandomNode(v) for v, _ in pairs]
    for i, node in enumerate(nodes):
        if i + 1 < n:
            node.next = nodes[i + 1]
        idx = pairs[i][1]
        node.random = nodes[idx] if idx is not None else None
    return nodes[0]


def fmt_bool(value):
    return "true" if value else "false"


def fmt_int_array(arr):
    """一行输出，空格分隔。"""
    return " ".join(str(x) for x in arr)


def fmt_matrix(matrix):
    """先输出行数，再每行输出一行整数。"""
    lines = [str(len(matrix))]
    lines.extend(" ".join(str(x) for x in row) for row in matrix)
    return "\n".join(lines)


def fmt_groups(groups):
    """先输出组数，再每组输出“元素个数 + 元素”。"""
    lines = [str(len(groups))]
    for group in groups:
        row = " ".join(str(x) for x in group)
        lines.append(f"{len(group)} {row}".rstrip())
    return "\n".join(lines)


def fmt_string_array(arr):
    """先输出个数，再逐行输出字符串。"""
    return "\n".join([str(len(arr))] + list(arr))


def fmt_list(head):
    """输出链表的所有值，空格分隔；空链表输出空行。"""
    vals = []
    while head:
        vals.append(str(head.val))
        head = head.next
    return " ".join(vals)


def index_of_node(head, target):
    """返回 target 结点在链表中的下标；找不到返回 -1。"""
    i = 0
    while head:
        if head is target:
            return i
        head = head.next
        i += 1
    return -1


def fmt_tree(root):
    """按层序输出，null 表示空结点，末尾的 null 省略。"""
    if root is None:
        return "0"
    out = []
    q = deque([root])
    while q:
        node = q.popleft()
        if node is None:
            out.append("null")
            continue
        out.append(str(node.val))
        q.append(node.left)
        q.append(node.right)
    while out and out[-1] == "null":
        out.pop()
    return str(len(out)) + "\n" + " ".join(out)


def fmt_random_list(head):
    """输出结点数，再逐行输出 val random_index（null 表示空）。"""
    nodes = []
    while head:
        nodes.append(head)
        head = head.next
    index = {id(node): i for i, node in enumerate(nodes)}
    lines = [str(len(nodes))]
    for node in nodes:
        lines.append(f"{node.val} {'null' if node.random is None else index[id(node.random)]}")
    return "\n".join(lines)


def parse_int(text):
    return int(text.strip().split()[0])


def parse_bool(text):
    return text.strip().lower().startswith("true")


def parse_string(text):
    return text.strip()


def parse_int_array(text):
    return [int(x) for x in text.split()]


def parse_string_array(text):
    lines = [line.strip() for line in text.strip().split("\n") if line.strip() != ""]
    if not lines:
        return []
    n = int(lines[0])
    return lines[1 : 1 + n]


def parse_matrix(text):
    lines = [line for line in text.strip().split("\n") if line.strip() != ""]
    if not lines:
        return []
    rows = int(lines[0].split()[0])
    return [[int(x) for x in lines[i + 1].split()] for i in range(rows)]


def parse_groups(text):
    lines = [line for line in text.strip().split("\n") if line.strip() != ""]
    if not lines:
        return []
    count = int(lines[0].split()[0])
    groups = []
    for i in range(count):
        parts = lines[i + 1].split()
        if not parts:
            groups.append([])
            continue
        k = int(parts[0])
        groups.append(parts[1 : 1 + k])
    return groups


def parse_tree_tokens(text):
    parts = text.split()
    if not parts:
        return []
    n = int(parts[0])
    return parts[1 : 1 + n]


def parse_design_lines(text):
    return [line.strip() if line.strip() else "null" for line in text.strip().split("\n") if line.strip()]


def read_design(r):
    """读入操作序列：第一行 m，随后 m 行“操作名 [参数...]”。"""
    m = r.int()
    ops, args = [], []
    for _ in range(m):
        parts = r.line().split()
        if not parts:
            continue
        ops.append(parts[0])
        args.append([parse_scalar(x) for x in parts[1:]])
    return ops, args


def parse_scalar(text):
    """把设计题参数解析成 int / float / 字符串。"""
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def fmt_design(values):
    """每个操作输出一行；没有返回值输出 null。"""
    lines = []
    for value in values:
        if value is None:
            lines.append("null")
        elif isinstance(value, bool):
            lines.append("true" if value else "false")
        else:
            lines.append(str(value))
    return "\n".join(lines)


def solve(nums):
    # TODO: 在这里实现算法。
    # 输入已经由上方的 main() 解析好，直接使用参数即可。
    # 返回值类型见文件开头的【输出】说明。
    raise NotImplementedError("删掉这一行，写下你的解法")

def main():
    sys.setrecursionlimit(1000000)
    r = Reader()
    nums = read_int_array(r)
    ans = solve(nums)
    print(ans)


if __name__ == "__main__":
    main()