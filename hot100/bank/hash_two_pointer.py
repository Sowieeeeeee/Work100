"""哈希、双指针、滑动窗口、普通数组与矩阵。"""
from __future__ import annotations

from collections import defaultdict

from .base import register


@register(1, ["用哈希表记住“已经见过的数”，避免两重循环。", "遍历到 x 时，先查 target - x 是否出现过。"], "O(n) 时间，O(n) 空间")
def solve_1(nums, target):
    # 哈希表：值 -> 下标
    seen = {}
    for i, x in enumerate(nums):
        need = target - x
        if need in seen:
            return [seen[need], i]
        seen[x] = i
    return []


@register(49, ["两个词是字母异位词，当且仅当排序后的字符串相同。", "把排序结果当作哈希表的键，原词放进同一个桶。"], "O(n·k log k) 时间，O(n·k) 空间")
def solve_49(strs):
    groups = defaultdict(list)
    for word in strs:
        key = "".join(sorted(word))
        groups[key].append(word)
    return list(groups.values())


@register(128, ["把数组放进集合，只从“序列起点”开始向后扩展。", "x 是起点当且仅当 x-1 不在集合里。"], "O(n) 时间，O(n) 空间")
def solve_128(nums):
    values = set(nums)
    best = 0
    for x in values:
        if x - 1 in values:
            continue
        cur = x
        length = 1
        while cur + 1 in values:
            cur += 1
            length += 1
        best = max(best, length)
    return best


@register(283, ["用一个指针记录下一个非零元素应该放的位置。", "扫描结束后，把剩余位置全部补 0；必须原地修改。"], "O(n) 时间，O(1) 额外空间")
def solve_283(nums):
    write = 0
    for x in nums:
        if x != 0:
            nums[write] = x
            write += 1
    while write < len(nums):
        nums[write] = 0
        write += 1
    return nums


@register(11, ["面积由 shorter * width 决定，左右指针从两端开始。", "每次移动较矮的一侧，因为移动高的一侧不可能让面积变大。"], "O(n) 时间，O(1) 空间")
def solve_11(height):
    left, right = 0, len(height) - 1
    best = 0
    while left < right:
        area = min(height[left], height[right]) * (right - left)
        best = max(best, area)
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1
    return best


@register(15, ["先排序，固定第一个数，再用左右指针找另外两个数。", "跳过重复元素，避免同一个三元组被重复加入。"], "O(n^2) 时间，O(1) 额外空间（不计结果）")
def solve_15(nums):
    nums.sort()
    n = len(nums)
    ans = []
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        left, right = i + 1, n - 1
        target = -nums[i]
        while left < right:
            total = nums[left] + nums[right]
            if total == target:
                ans.append([nums[i], nums[left], nums[right]])
                left += 1
                right -= 1
                while left < right and nums[left] == nums[left - 1]:
                    left += 1
                while left < right and nums[right] == nums[right + 1]:
                    right -= 1
            elif total < target:
                left += 1
            else:
                right -= 1
    return ans


@register(3, ["维护一个不含重复字符的窗口 [left, right]。", "用字典记录字符最近一次出现的下标，遇到重复就把 left 跳过去。"], "O(n) 时间，O(字符集) 空间")
def solve_3(s):
    last = {}
    left = 0
    best = 0
    for right, ch in enumerate(s):
        if ch in last and last[ch] >= left:
            left = last[ch] + 1
        last[ch] = right
        best = max(best, right - left + 1)
    return best


@register(438, ["窗口长度固定为 len(p)，比较窗口内的字符计数。", "滑动时只增减进出窗口的两个字符，不必重新统计整个窗口。"], "O(n + m) 时间，O(字符集) 空间")
def solve_438(s, p):
    n, m = len(s), len(p)
    if m > n:
        return []
    need = [0] * 26
    window = [0] * 26
    base = ord("a")
    for ch in p:
        need[ord(ch) - base] += 1
    for i in range(m):
        window[ord(s[i]) - base] += 1
    ans = []
    if window == need:
        ans.append(0)
    for i in range(m, n):
        window[ord(s[i]) - base] += 1
        window[ord(s[i - m]) - base] -= 1
        if window == need:
            ans.append(i - m + 1)
    return ans


@register(560, ["把“子数组和”转成“两个前缀和的差”。", "用哈希表记录每个前缀和出现的次数。"], "O(n) 时间，O(n) 空间")
def solve_560(nums, k):
    count = {0: 1}
    prefix = 0
    ans = 0
    for x in nums:
        prefix += x
        ans += count.get(prefix - k, 0)
        count[prefix] = count.get(prefix, 0) + 1
    return ans


@register(53, ["定义以当前元素结尾的最大子数组和。", "要么接在前一段后面，要么从当前元素重新开始。"], "O(n) 时间，O(1) 空间")
def solve_53(nums):
    best = cur = nums[0]
    for x in nums[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best


@register(56, ["按左端点排序，重叠区间一定相邻。", "维护当前区间，能合并就更新右端点，不能合并就收尾。"], "O(n log n) 时间，O(n) 空间")
def solve_56(intervals):
    intervals.sort(key=lambda x: x[0])
    merged = []
    for left, right in intervals:
        if not merged or left > merged[-1][1]:
            merged.append([left, right])
        else:
            merged[-1][1] = max(merged[-1][1], right)
    return merged


@register(189, ["先对 k 取模，避免无意义的整圈旋转。", "整体反转、前 k 个反转、后 n-k 个反转，三次反转即可。"], "O(n) 时间，O(1) 空间")
def solve_189(nums, k):
    n = len(nums)
    k %= n
    if k == 0:
        return nums

    def reverse(lo, hi):
        while lo < hi:
            nums[lo], nums[hi] = nums[hi], nums[lo]
            lo += 1
            hi -= 1

    reverse(0, n - 1)
    reverse(0, k - 1)
    reverse(k, n - 1)
    return nums


@register(238, ["先从左到右算每个位置左侧的乘积。", "再从右到左乘上右侧乘积；不能使用除法。"], "O(n) 时间，O(1) 额外空间（不计输出）")
def solve_238(nums):
    n = len(nums)
    ans = [1] * n
    left = 1
    for i in range(n):
        ans[i] = left
        left *= nums[i]
    right = 1
    for i in range(n - 1, -1, -1):
        ans[i] *= right
        right *= nums[i]
    return ans


@register(73, ["不要立刻置零，否则会污染后面的判断。", "用第一行和第一列记录哪些行、列需要置零，并单独记录第一行/列是否含 0。"], "O(mn) 时间，O(1) 额外空间")
def solve_73(matrix):
    rows, cols = len(matrix), len(matrix[0])
    first_row_zero = any(matrix[0][c] == 0 for c in range(cols))
    first_col_zero = any(matrix[r][0] == 0 for r in range(rows))
    for r in range(1, rows):
        for c in range(1, cols):
            if matrix[r][c] == 0:
                matrix[r][0] = 0
                matrix[0][c] = 0
    for r in range(1, rows):
        if matrix[r][0] == 0:
            for c in range(1, cols):
                matrix[r][c] = 0
    for c in range(1, cols):
        if matrix[0][c] == 0:
            for r in range(1, rows):
                matrix[r][c] = 0
    if first_row_zero:
        for c in range(cols):
            matrix[0][c] = 0
    if first_col_zero:
        for r in range(rows):
            matrix[r][0] = 0
    return matrix


@register(54, ["用上下左右四个边界描述尚未访问的区域。", "每走完一条边就收缩对应边界，直到边界交叉。"], "O(mn) 时间，O(1) 额外空间（不计结果）")
def solve_54(matrix):
    if not matrix:
        return []
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1
    ans = []
    while top <= bottom and left <= right:
        for c in range(left, right + 1):
            ans.append(matrix[top][c])
        top += 1
        for r in range(top, bottom + 1):
            ans.append(matrix[r][right])
        right -= 1
        if top <= bottom:
            for c in range(right, left - 1, -1):
                ans.append(matrix[bottom][c])
            bottom -= 1
        if left <= right:
            for r in range(bottom, top - 1, -1):
                ans.append(matrix[r][left])
            left += 1
    return ans


@register(48, ["顺时针旋转 90 度等于先转置，再左右翻转。", "必须原地修改，转置时只遍历上三角。"], "O(n^2) 时间，O(1) 空间")
def solve_48(matrix):
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    for row in matrix:
        row.reverse()
    return matrix


@register(240, ["从右上角开始搜索：该位置是当前行的最大值、当前列的最小值。", "比 target 大就往左，比 target 小就往下。"], "O(m + n) 时间，O(1) 空间")
def solve_240(matrix, target):
    if not matrix or not matrix[0]:
        return False
    r, c = 0, len(matrix[0]) - 1
    while r < len(matrix) and c >= 0:
        value = matrix[r][c]
        if value == target:
            return True
        if value > target:
            c -= 1
        else:
            r += 1
    return False
