"""图论与回溯题解。"""
from __future__ import annotations

from collections import deque

from .base import register


@register(200, ["遍历每个格子，遇到 '1' 就用 DFS/BFS 把整座岛淹掉。", "每启动一次搜索，岛屿数量加一。"], "O(mn) 时间，O(mn) 空间")
def solve_200(grid):
    rows, cols = len(grid), len(grid[0]) if grid else 0
    count = 0

    def sink(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != "1":
            return
        grid[r][c] = "0"
        sink(r + 1, c)
        sink(r - 1, c)
        sink(r, c + 1)
        sink(r, c - 1)

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1":
                count += 1
                sink(r, c)
    return count


@register(994, ["多个腐烂橘子同时向外扩散，适合多源 BFS。", "先统计新鲜橘子数；BFS 每层代表一分钟，最后若还有新鲜橘子返回 -1。"], "O(mn) 时间，O(mn) 空间")
def solve_994(grid):
    rows, cols = len(grid), len(grid[0])
    q = deque()
    fresh = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2:
                q.append((r, c))
            elif grid[r][c] == 1:
                fresh += 1
    minutes = 0
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    while q and fresh:
        for _ in range(len(q)):
            r, c = q.popleft()
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                    grid[nr][nc] = 2
                    fresh -= 1
                    q.append((nr, nc))
        minutes += 1
    return minutes if fresh == 0 else -1


@register(207, ["课程依赖构成有向图，问题等价于判断是否有环。", "用入度 + 队列做拓扑排序；能处理完所有课程就返回 true。"], "O(V + E) 时间，O(V + E) 空间")
def solve_207(numCourses, prerequisites):
    graph = [[] for _ in range(numCourses)]
    indegree = [0] * numCourses
    for course, need in prerequisites:
        graph[need].append(course)
        indegree[course] += 1
    q = deque(i for i in range(numCourses) if indegree[i] == 0)
    seen = 0
    while q:
        node = q.popleft()
        seen += 1
        for nxt in graph[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                q.append(nxt)
    return seen == numCourses


@register(46, ["回溯：每一层选择一个还没用过的数字。", "用 used 数组标记选择，撤销选择后继续尝试下一个。"], "O(n·n!) 时间，O(n) 空间")
def solve_46(nums):
    ans = []
    path = []
    used = [False] * len(nums)

    def dfs():
        if len(path) == len(nums):
            ans.append(path.copy())
            return
        for i, x in enumerate(nums):
            if used[i]:
                continue
            used[i] = True
            path.append(x)
            dfs()
            path.pop()
            used[i] = False

    dfs()
    return ans


@register(78, ["每个元素只有“选”和“不选”两种状态。", "递归到数组末尾时把当前子集加入答案；空集也会被加入。"], "O(n·2^n) 时间，O(n) 空间")
def solve_78(nums):
    ans = []
    path = []

    def dfs(i):
        if i == len(nums):
            ans.append(path.copy())
            return
        dfs(i + 1)  # 不选 nums[i]
        path.append(nums[i])  # 选 nums[i]
        dfs(i + 1)
        path.pop()

    dfs(0)
    return ans


@register(17, ["建立数字到字母的映射，逐位做笛卡尔积。", "回溯到 digits 末尾时收集当前字符串。"], "O(4^n) 时间，O(n) 空间")
def solve_17(digits):
    if not digits:
        return []
    mapping = {
        "2": "abc", "3": "def", "4": "ghi", "5": "jkl",
        "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz",
    }
    ans = []
    path = []

    def dfs(i):
        if i == len(digits):
            ans.append("".join(path))
            return
        for ch in mapping[digits[i]]:
            path.append(ch)
            dfs(i + 1)
            path.pop()

    dfs(0)
    return ans


@register(39, ["同一个数字可以重复使用，所以递归时下标不 +1。", "先排序；当前和超过 target 就剪枝，等于 target 就收集。"], "O(n^(target/min)) 时间，O(target/min) 空间")
def solve_39(candidates, target):
    candidates.sort()
    ans = []
    path = []

    def dfs(start, remain):
        if remain == 0:
            ans.append(path.copy())
            return
        for i in range(start, len(candidates)):
            x = candidates[i]
            if x > remain:
                break
            path.append(x)
            dfs(i, remain - x)
            path.pop()

    dfs(0, target)
    return ans


@register(22, ["从左到右构造括号串，记录已用的左括号和右括号数量。", "左括号最多 n 个；右括号数量不能超过左括号数量。"], "O(4^n / sqrt(n)) 时间，O(n) 空间")
def solve_22(n):
    ans = []
    path = []

    def dfs(left, right):
        if len(path) == 2 * n:
            ans.append("".join(path))
            return
        if left < n:
            path.append("(")
            dfs(left + 1, right)
            path.pop()
        if right < left:
            path.append(")")
            dfs(left, right + 1)
            path.pop()

    dfs(0, 0)
    return ans


@register(79, ["从每个格子出发尝试匹配 word 的第一个字符。", "DFS 向四个方向扩展；访问过的格子临时改成特殊字符，回溯时恢复。"], "O(mn·4^L) 时间，O(L) 空间")
def solve_79(board, word):
    rows, cols = len(board), len(board[0])
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    def dfs(r, c, i):
        if i == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols or board[r][c] != word[i]:
            return False
        saved = board[r][c]
        board[r][c] = "#"
        for dr, dc in directions:
            if dfs(r + dr, c + dc, i + 1):
                board[r][c] = saved
                return True
        board[r][c] = saved
        return False

    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False


@register(131, ["先预处理每个子串是否回文，减少重复判断。", "回溯：从当前位置尝试所有回文前缀，递归处理剩余后缀。"], "O(n·2^n) 时间，O(n^2) 空间")
def solve_131(s):
    n = len(s)
    is_pal = [[False] * n for _ in range(n)]
    for right in range(n):
        for left in range(right + 1):
            if s[left] == s[right] and (right - left <= 2 or is_pal[left + 1][right - 1]):
                is_pal[left][right] = True

    ans = []
    path = []

    def dfs(start):
        if start == n:
            ans.append(path.copy())
            return
        for end in range(start, n):
            if is_pal[start][end]:
                path.append(s[start:end + 1])
                dfs(end + 1)
                path.pop()

    dfs(0)
    return ans
