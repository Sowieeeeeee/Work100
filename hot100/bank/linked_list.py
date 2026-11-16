"""链表相关题解。"""
from __future__ import annotations

from collections import OrderedDict

from .base import register


@register(160, ["先分别求两条链表的长度，让长的先走长度差。", "之后同步前进，第一次遇到同一个结点就是交点（比较对象身份，不是值）。"], "O(m + n) 时间，O(1) 空间")
def solve_160(listA, listB, skipA, skipB):
    def length(head):
        n = 0
        while head:
            n += 1
            head = head.next
        return n

    len_a, len_b = length(listA), length(listB)
    a, b = listA, listB
    while len_a > len_b:
        a = a.next
        len_a -= 1
    while len_b > len_a:
        b = b.next
        len_b -= 1
    while a is not b:
        a = a.next
        b = b.next
    return a


@register(206, ["维护前驱 prev 和当前 cur。", "每次先把 cur.next 存下来，再让 cur.next 指向 prev。"], "O(n) 时间，O(1) 空间")
def solve_206(head):
    prev = None
    cur = head
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    return prev


@register(234, ["快慢指针找到中点，反转后半段。", "从两端向中间比较；比较完可以把后半段恢复，保持链表结构。"], "O(n) 时间，O(1) 空间")
def solve_234(head):
    if not head or not head.next:
        return True
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    # 反转以 slow 为起点的后半段
    prev = None
    cur = slow
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    left, right = head, prev
    ok = True
    while right:
        if left.val != right.val:
            ok = False
            break
        left = left.next
        right = right.next
    # 恢复后半段，避免修改输入结构
    tail = None
    cur = prev
    while cur:
        nxt = cur.next
        cur.next = tail
        tail = cur
        cur = nxt
    return ok


@register(141, ["用快慢指针，慢指针走一步，快指针走两步。", "如果有环，两者一定会在环内相遇。"], "O(n) 时间，O(1) 空间")
def solve_141(head, pos):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False


@register(142, ["先用快慢指针判断是否有环，并记录相遇点。", "相遇后，一个指针回到 head，两个指针都每次走一步，再次相遇处就是环入口。"], "O(n) 时间，O(1) 空间")
def solve_142(head, pos):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            p = head
            while p is not slow:
                p = p.next
                slow = slow.next
            return p
    return None


@register(21, ["用哨兵结点简化头结点处理。", "每次接上较小的结点，一条链表走完后直接接上另一条。"], "O(m + n) 时间，O(1) 空间")
def solve_21(list1, list2):
    dummy = type(list1)(0) if list1 else (type(list2)(0) if list2 else None)
    # 上面的写法在两条链表都为空时拿不到类型，改为直接构造
    class ListNode:
        def __init__(self, val=0, next=None):
            self.val = val
            self.next = next

    dummy = ListNode()
    tail = dummy
    a, b = list1, list2
    while a and b:
        if a.val <= b.val:
            tail.next = a
            a = a.next
        else:
            tail.next = b
            b = b.next
        tail = tail.next
    tail.next = a or b
    return dummy.next


@register(2, ["链表是逆序存储的，正好可以从低位开始相加。", "维护进位 carry；两条链表都走完后，如果 carry 还是 1，要再补一个结点。"], "O(max(m, n)) 时间，O(max(m, n)) 空间")
def solve_2(l1, l2):
    dummy = type(l1)(0) if l1 else (type(l2)(0) if l2 else None)
    if dummy is None:
        class ListNode:
            def __init__(self, val=0, next=None):
                self.val = val
                self.next = next
        dummy = ListNode()
    tail = dummy
    carry = 0
    a, b = l1, l2
    while a or b or carry:
        x = a.val if a else 0
        y = b.val if b else 0
        total = x + y + carry
        carry = total // 10
        tail.next = type(dummy)(total % 10)
        tail = tail.next
        a = a.next if a else None
        b = b.next if b else None
    return dummy.next


@register(19, ["用哨兵结点，避免删除头结点时特判。", "快指针先走 n+1 步，然后快慢一起走，慢指针停在被删结点的前一个。"], "O(n) 时间，O(1) 空间")
def solve_19(head, n):
    dummy = type(head)(0) if head else None
    if dummy is None:
        class ListNode:
            def __init__(self, val=0, next=None):
                self.val = val
                self.next = next
        dummy = ListNode()
    dummy.next = head
    fast = slow = dummy
    for _ in range(n + 1):
        fast = fast.next
    while fast:
        fast = fast.next
        slow = slow.next
    slow.next = slow.next.next
    return dummy.next


@register(24, ["用哨兵结点和三个指针 prev、a、b。", "每次交换 a、b，并把 prev 接到新的头，然后整体后移两位。"], "O(n) 时间，O(1) 空间")
def solve_24(head):
    class ListNode:
        def __init__(self, val=0, next=None):
            self.val = val
            self.next = next

    dummy = ListNode()
    dummy.next = head
    prev = dummy
    while prev.next and prev.next.next:
        a = prev.next
        b = a.next
        a.next = b.next
        b.next = a
        prev.next = b
        prev = a
    return dummy.next


@register(138, ["第一遍复制结点，用哈希表建立“原结点 -> 新结点”。", "第二遍设置 next 和 random；也可以把新结点穿插在原链表中做到 O(1) 空间。"], "O(n) 时间，O(n) 空间")
def solve_138(head):
    if not head:
        return None
    mapping = {}
    cur = head
    while cur:
        mapping[cur] = type(cur)(cur.val)
        cur = cur.next
    cur = head
    while cur:
        mapping[cur].next = mapping.get(cur.next)
        mapping[cur].random = mapping.get(cur.random)
        cur = cur.next
    return mapping[head]


@register(148, ["链表排序适合归并排序：快慢指针找中点，递归排序两半。", "合并两个有序链表即可；递归深度 O(log n)。"], "O(n log n) 时间，O(log n) 空间")
def solve_148(head):
    if not head or not head.next:
        return head
    slow, fast = head, head.next
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    mid = slow.next
    slow.next = None
    left = solve_148(head)
    right = solve_148(mid)

    class ListNode:
        def __init__(self, val=0, next=None):
            self.val = val
            self.next = next

    dummy = ListNode()
    tail = dummy
    while left and right:
        if left.val <= right.val:
            tail.next = left
            left = left.next
        else:
            tail.next = right
            right = right.next
        tail = tail.next
    tail.next = left or right
    return dummy.next


@register(146, ["哈希表负责 O(1) 定位结点，双向链表负责 O(1) 调整最近使用顺序。", "get 命中后把结点移到链表头；put 超容量时删除链表尾。"], "get/put 均 O(1)，O(capacity) 空间")
def solve_146(ops, args):
    class Node:
        def __init__(self, key=0, value=0):
            self.key = key
            self.value = value
            self.prev = None
            self.next = None

    class LRUCache:
        def __init__(self, capacity):
            self.capacity = capacity
            self.cache = {}
            self.head = Node()
            self.tail = Node()
            self.head.next = self.tail
            self.tail.prev = self.head

        def _remove(self, node):
            node.prev.next = node.next
            node.next.prev = node.prev

        def _add_front(self, node):
            node.next = self.head.next
            node.prev = self.head
            self.head.next.prev = node
            self.head.next = node

        def get(self, key):
            if key not in self.cache:
                return -1
            node = self.cache[key]
            self._remove(node)
            self._add_front(node)
            return node.value

        def put(self, key, value):
            if key in self.cache:
                node = self.cache[key]
                node.value = value
                self._remove(node)
                self._add_front(node)
                return
            if len(self.cache) == self.capacity:
                last = self.tail.prev
                self._remove(last)
                del self.cache[last.key]
            node = Node(key, value)
            self.cache[key] = node
            self._add_front(node)

    out = []
    obj = None
    for op, argv in zip(ops, args):
        if op == "LRUCache":
            obj = LRUCache(*argv)
            out.append(None)
        elif op == "put":
            obj.put(*argv)
            out.append(None)
        elif op == "get":
            out.append(obj.get(*argv))
    return out


@register(155, ["需要一个辅助栈同步记录“当前最小值”。", "push 时辅助栈压入 min(新值, 当前最小值)；pop 时两个栈一起弹出。"], "所有操作 O(1)，O(n) 空间")
def solve_155(ops, args):
    class MinStack:
        def __init__(self):
            self.data = []
            self.mins = []

        def push(self, value):
            self.data.append(value)
            self.mins.append(value if not self.mins else min(value, self.mins[-1]))

        def pop(self):
            self.data.pop()
            self.mins.pop()

        def top(self):
            return self.data[-1]

        def getMin(self):
            return self.mins[-1]

    out = []
    obj = None
    for op, argv in zip(ops, args):
        if op == "MinStack":
            obj = MinStack()
            out.append(None)
        elif op == "push":
            obj.push(*argv)
            out.append(None)
        elif op == "pop":
            obj.pop()
            out.append(None)
        elif op == "top":
            out.append(obj.top())
        elif op == "getMin":
            out.append(obj.getMin())
    return out


@register(208, ["每个结点保存一个“字符 -> 子结点”的字典，并标记是否为单词结尾。", "insert 逐字符建路径；search 要求结尾标记为真；startsWith 只要求路径存在。"], "O(L) 每次操作，O(总字符数) 空间")
def solve_208(ops, args):
    class Trie:
        def __init__(self):
            self.root = {}

        def insert(self, word):
            node = self.root
            for ch in word:
                node = node.setdefault(ch, {})
            node["#"] = True

        def search(self, word):
            node = self.root
            for ch in word:
                if ch not in node:
                    return False
                node = node[ch]
            return node.get("#", False)

        def startsWith(self, prefix):
            node = self.root
            for ch in prefix:
                if ch not in node:
                    return False
                node = node[ch]
            return True

    out = []
    obj = None
    for op, argv in zip(ops, args):
        if op == "Trie":
            obj = Trie()
            out.append(None)
        elif op == "insert":
            obj.insert(*argv)
            out.append(None)
        elif op == "search":
            out.append(obj.search(*argv))
        elif op == "startsWith":
            out.append(obj.startsWith(*argv))
    return out
