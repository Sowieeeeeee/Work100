"""贪心与动态规划题解。"""
from __future__ import annotations

import bisect
import math

from .base import register


@register(121, ["只允许先买后卖，遍历时维护历史最低价。", "当前价格减最低价就是以今天卖出的最大利润。"], "O(n) 时间，O(1) 空间")
def solve_121(prices):
    min_price = float("inf")
    best = 0
    for price in prices:
        min_price = min(min_price, price)
        best = max(best, price - min_price)
    return best


@register(55, ["维护当前能到达的最远下标。", "如果最远下标已经覆盖当前位置，就继续扩展；否则说明卡住了。"], "O(n) 时间，O(1) 空间")
def solve_55(nums):
    farthest = 0
    for i, step in enumerate(nums):
        if i > farthest:
            return False
        farthest = max(farthest, i + step)
    return True


@register(45, ["把跳跃看成 BFS：每一跳覆盖一个区间。", "在上一跳能到达的范围内，找出下一跳能到达的最远位置。"], "O(n) 时间，O(1) 空间")
def solve_45(nums):
    jumps = 0
    current_end = 0
    farthest = 0
    for i in range(len(nums) - 1):
        farthest = max(farthest, i + nums[i])
        if i == current_end:
            jumps += 1
            current_end = farthest
    return jumps


@register(763, ["先记录每个字符最后出现的位置。", "遍历时不断扩展当前片段的右边界；走到右边界就切分。"], "O(n) 时间，O(1) 空间")
def solve_763(s):
    last = {ch: i for i, ch in enumerate(s)}
    ans = []
    start = end = 0
    for i, ch in enumerate(s):
        end = max(end, last[ch])
        if i == end:
            ans.append(end - start + 1)
            start = end + 1
    return ans


@register(70, ["到第 n 阶的方法数等于前两阶之和。", "只保留最近两个状态，空间可以降到 O(1)。"], "O(n) 时间，O(1) 空间")
def solve_70(n):
    if n <= 2:
        return n
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b


@register(118, ["每一行的首尾都是 1。", "中间元素等于上一行相邻两个元素之和。"], "O(n^2) 时间，O(n^2) 空间")
def solve_118(numRows):
    ans = []
    for r in range(numRows):
        row = [1] * (r + 1)
        for c in range(1, r):
            row[c] = ans[r - 1][c - 1] + ans[r - 1][c]
        ans.append(row)
    return ans


@register(198, ["相邻房屋不能同时偷。", "dp[i] = max(dp[i-1], dp[i-2] + nums[i])，只保留前两个状态。"], "O(n) 时间，O(1) 空间")
def solve_198(nums):
    prev2 = prev1 = 0
    for x in nums:
        prev2, prev1 = prev1, max(prev1, prev2 + x)
    return prev1


@register(279, ["定义 dp[x] 为凑出 x 的最少完全平方数个数。", "枚举平方数 j*j，dp[x] = min(dp[x], dp[x-j*j] + 1)。"], "O(n√n) 时间，O(n) 空间")
def solve_279(n):
    dp = [0] + [float("inf")] * n
    for x in range(1, n + 1):
        j = 1
        while j * j <= x:
            dp[x] = min(dp[x], dp[x - j * j] + 1)
            j += 1
    return dp[n]


@register(322, ["完全背包：dp[amount] 表示凑出该金额的最少硬币数。", "对每个金额枚举硬币，取最小值；凑不出时保持无穷大。"], "O(amount·n) 时间，O(amount) 空间")
def solve_322(coins, amount):
    dp = [0] + [float("inf")] * amount
    for x in range(1, amount + 1):
        for coin in coins:
            if coin <= x:
                dp[x] = min(dp[x], dp[x - coin] + 1)
    return -1 if dp[amount] == float("inf") else dp[amount]


@register(139, ["dp[i] 表示前 i 个字符能否拆分。", "枚举最后一个单词的起点 j，若 dp[j] 为真且 s[j:i] 在字典中，则 dp[i] 为真。"], "O(n^2·L) 时间，O(n) 空间")
def solve_139(s, wordDict):
    words = set(wordDict)
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True
    max_len = max((len(w) for w in words), default=0)
    for i in range(1, n + 1):
        for j in range(max(0, i - max_len), i):
            if dp[j] and s[j:i] in words:
                dp[i] = True
                break
    return dp[n]


@register(300, ["维护一个“长度为 i 的递增子序列的最小结尾值”数组。", "用二分找到当前值应该替换的位置；数组长度就是 LIS 长度。"], "O(n log n) 时间，O(n) 空间")
def solve_300(nums):
    tails = []
    for x in nums:
        pos = bisect.bisect_left(tails, x)
        if pos == len(tails):
            tails.append(x)
        else:
            tails[pos] = x
    return len(tails)


@register(152, ["负负得正，所以同时维护以当前元素结尾的最大乘积和最小乘积。", "遇到负数时，最大值和最小值会互换角色。"], "O(n) 时间，O(1) 空间")
def solve_152(nums):
    best = cur_max = cur_min = nums[0]
    for x in nums[1:]:
        if x < 0:
            cur_max, cur_min = cur_min, cur_max
        cur_max = max(x, cur_max * x)
        cur_min = min(x, cur_min * x)
        best = max(best, cur_max)
    return best


@register(416, ["问题等价于能否选出若干数，使和为总和的一半。", "0/1 背包：dp[s] 表示能否凑出和 s；每个数只能使用一次，容量要倒序。"], "O(n·sum) 时间，O(sum) 空间")
def solve_416(nums):
    total = sum(nums)
    if total % 2:
        return False
    target = total // 2
    dp = [False] * (target + 1)
    dp[0] = True
    for x in nums:
        for s in range(target, x - 1, -1):
            dp[s] = dp[s] or dp[s - x]
    return dp[target]


@register(62, ["从左上到右下，一共要走 m-1 步向下、n-1 步向右。", "答案是组合数 C(m+n-2, m-1)。"], "O(min(m,n)) 时间，O(1) 空间")
def solve_62(m, n):
    return math.comb(m + n - 2, min(m, n) - 1)


@register(64, ["dp[r][c] 表示走到该格子的最小路径和。", "只能从上方或左方过来，取较小值加上当前格子。"], "O(mn) 时间，O(n) 空间")
def solve_64(grid):
    rows, cols = len(grid), len(grid[0])
    dp = [0] * cols
    for r in range(rows):
        for c in range(cols):
            if r == 0 and c == 0:
                dp[c] = grid[r][c]
            elif r == 0:
                dp[c] = dp[c - 1] + grid[r][c]
            elif c == 0:
                dp[c] = dp[c] + grid[r][c]
            else:
                dp[c] = min(dp[c], dp[c - 1]) + grid[r][c]
    return dp[-1]


@register(5, ["回文串可以从中心向两边扩展。", "中心可能是一个字符，也可能是两个字符之间；分别枚举并取最长。"], "O(n^2) 时间，O(1) 空间")
def solve_5(s):
    if not s:
        return ""
    start, end = 0, 0

    def expand(left, right):
        while left >= 0 and right < len(s) and s[left] == s[right]:
            left -= 1
            right += 1
        return left + 1, right - 1

    for i in range(len(s)):
        for left, right in (expand(i, i), expand(i, i + 1)):
            if right - left > end - start:
                start, end = left, right
    return s[start:end + 1]


@register(1143, ["dp[i][j] 表示 text1 前 i 个字符与 text2 前 j 个字符的 LCS 长度。", "字符相同则 dp[i-1][j-1] + 1；否则取上方和左方的较大值。"], "O(mn) 时间，O(n) 空间")
def solve_1143(text1, text2):
    n = len(text2)
    dp = [0] * (n + 1)
    for ch in text1:
        prev = 0
        for j in range(1, n + 1):
            saved = dp[j]
            if ch == text2[j - 1]:
                dp[j] = prev + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev = saved
    return dp[n]


@register(72, ["dp[i][j] 表示 word1 前 i 个字符变成 word2 前 j 个字符的最少操作数。", "三种操作取最小：删除、插入、替换；字符相同时直接继承左上角。"], "O(mn) 时间，O(n) 空间")
def solve_72(word1, word2):
    n = len(word2)
    dp = list(range(n + 1))
    for i, ch1 in enumerate(word1, 1):
        prev = dp[0]
        dp[0] = i
        for j, ch2 in enumerate(word2, 1):
            saved = dp[j]
            if ch1 == ch2:
                dp[j] = prev
            else:
                dp[j] = min(dp[j], dp[j - 1], prev) + 1
            prev = saved
    return dp[n]
