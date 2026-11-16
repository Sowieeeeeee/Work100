"""二叉树相关题解。"""
from __future__ import annotations

from collections import deque

from .base import register


@register(94, ["中序遍历：左子树 -> 根 -> 右子树。", "递归或显式栈都可以；显式栈可以避免递归深度限制。"], "O(n) 时间，O(h) 空间")
def solve_94(root):
    ans = []
    stack = []
    cur = root
    while cur or stack:
        while cur:
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()
        ans.append(cur.val)
        cur = cur.right
    return ans


@register(104, ["最大深度 = 1 + max(左子树深度, 右子树深度)。", "空结点深度为 0。"], "O(n) 时间，O(h) 空间")
def solve_104(root):
    if not root:
        return 0
    return 1 + max(solve_104(root.left), solve_104(root.right))


@register(226, ["递归翻转左右子树，再交换当前结点的左右孩子。", "空结点直接返回。"], "O(n) 时间，O(h) 空间")
def solve_226(root):
    if not root:
        return None
    root.left, root.right = solve_226(root.right), solve_226(root.left)
    return root


@register(101, ["对称要求左子树的左孩子与右子树的右孩子对称，左子树的右孩子与右子树的左孩子对称。", "写一个辅助函数同时比较两个结点。"], "O(n) 时间，O(h) 空间")
def solve_101(root):
    def mirror(a, b):
        if not a and not b:
            return True
        if not a or not b or a.val != b.val:
            return False
        return mirror(a.left, b.right) and mirror(a.right, b.left)

    return mirror(root, root) if root else True


@register(543, ["直径可能不经过根结点，要在每个结点处更新答案。", "后序遍历返回子树高度，同时用“左高 + 右高”更新最大直径。"], "O(n) 时间，O(h) 空间")
def solve_543(root):
    best = 0

    def height(node):
        nonlocal best
        if not node:
            return 0
        left = height(node.left)
        right = height(node.right)
        best = max(best, left + right)
        return 1 + max(left, right)

    height(root)
    return best


@register(102, ["用队列做 BFS，每次先记下当前层的结点数。", "处理完这一层后，把这一层的值加入结果。"], "O(n) 时间，O(n) 空间")
def solve_102(root):
    if not root:
        return []
    ans = []
    q = deque([root])
    while q:
        level = []
        for _ in range(len(q)):
            node = q.popleft()
            level.append(node.val)
            if node.left:
                q.append(node.left)
            if node.right:
                q.append(node.right)
        ans.append(level)
    return ans


@register(108, ["有序数组的中点作为根，左右两半递归建树。", "这样能保证高度平衡；答案不唯一，任选一个中点即可。"], "O(n) 时间，O(log n) 空间")
def solve_108(nums):
    class TreeNode:
        def __init__(self, val=0, left=None, right=None):
            self.val = val
            self.left = left
            self.right = right

    def build(lo, hi):
        if lo > hi:
            return None
        mid = (lo + hi) // 2
        node = TreeNode(nums[mid])
        node.left = build(lo, mid - 1)
        node.right = build(mid + 1, hi)
        return node

    return build(0, len(nums) - 1)


@register(98, ["不能只比较父子结点，要限制整棵子树的范围。", "递归时传入开区间 (low, high)；空区间用 None 表示。"], "O(n) 时间，O(h) 空间")
def solve_98(root):
    def valid(node, low, high):
        if not node:
            return True
        if low is not None and node.val <= low:
            return False
        if high is not None and node.val >= high:
            return False
        return valid(node.left, low, node.val) and valid(node.right, node.val, high)

    return valid(root, None, None)


@register(230, ["二叉搜索树的中序遍历是升序序列。", "中序遍历到第 k 个结点时直接返回。"], "O(h + k) 时间，O(h) 空间")
def solve_230(root, k):
    stack = []
    cur = root
    count = 0
    while cur or stack:
        while cur:
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()
        count += 1
        if count == k:
            return cur.val
        cur = cur.right
    return -1


@register(199, ["右视图就是每一层最右边的结点。", "BFS 时记录每层最后一个结点。"], "O(n) 时间，O(n) 空间")
def solve_199(root):
    if not root:
        return []
    ans = []
    q = deque([root])
    while q:
        size = len(q)
        for i in range(size):
            node = q.popleft()
            if i == size - 1:
                ans.append(node.val)
            if node.left:
                q.append(node.left)
            if node.right:
                q.append(node.right)
    return ans


@register(114, ["展开后的顺序是前序遍历：根 -> 左 -> 右。", "递归处理左右子树，把左子树接到右边，再接上原来的右子树。"], "O(n) 时间，O(h) 空间")
def solve_114(root):
    # 返回展开后的头结点和尾结点，保证每个结点只处理一次。
    def flatten(node):
        if not node:
            return None, None
        left_head, left_tail = flatten(node.left)
        right_head, right_tail = flatten(node.right)
        node.left = None
        if left_head:
            node.right = left_head
            left_tail.right = right_head
        else:
            node.right = right_head
        tail = right_tail or left_tail or node
        return node, tail

    head, _ = flatten(root)
    return head


@register(105, ["前序的第一个元素是根；在中序里找到根，左边是左子树，右边是右子树。", "用哈希表记录中序下标，避免每层重复扫描。"], "O(n) 时间，O(n) 空间")
def solve_105(preorder, inorder):
    index = {value: i for i, value in enumerate(inorder)}

    class TreeNode:
        def __init__(self, val=0, left=None, right=None):
            self.val = val
            self.left = left
            self.right = right

    def build(pre_lo, pre_hi, in_lo, in_hi):
        if pre_lo > pre_hi:
            return None
        root_val = preorder[pre_lo]
        root = TreeNode(root_val)
        mid = index[root_val]
        left_size = mid - in_lo
        root.left = build(pre_lo + 1, pre_lo + left_size, in_lo, mid - 1)
        root.right = build(pre_lo + left_size + 1, pre_hi, mid + 1, in_hi)
        return root

    return build(0, len(preorder) - 1, 0, len(inorder) - 1)


@register(437, ["路径不要求从根开始，但必须向下。", "用前缀和：到当前结点的路径和 - target 出现过的次数，就是以当前结点结尾的合法路径数。"], "O(n) 时间，O(n) 空间")
def solve_437(root, targetSum):
    count = {0: 1}

    def dfs(node, prefix):
        if not node:
            return 0
        prefix += node.val
        ans = count.get(prefix - targetSum, 0)
        count[prefix] = count.get(prefix, 0) + 1
        ans += dfs(node.left, prefix) + dfs(node.right, prefix)
        count[prefix] -= 1
        return ans

    return dfs(root, 0)


@register(236, ["最近公共祖先满足：p、q 分别在它的两侧，或者它本身就是 p/q。", "后序遍历，左右子树各返回是否找到目标；两边都找到时当前结点就是答案。"], "O(n) 时间，O(h) 空间")
def solve_236(root, p, q):
    def dfs(node):
        if not node or node.val == p or node.val == q:
            return node
        left = dfs(node.left)
        right = dfs(node.right)
        if left and right:
            return node
        return left or right

    return dfs(root)
