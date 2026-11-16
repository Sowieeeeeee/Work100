"""二分查找、栈与堆题解。"""
from __future__ import annotations

import heapq
from collections import Counter

from .base import register


@register(35, ["在有序数组中找第一个大于等于 target 的位置。", "循环不变量用左闭右开区间 [lo, hi)，最后 lo 就是答案。"], "O(log n) 时间，O(1) 空间")
def solve_35(nums, target):
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


@register(74, ["把 m×n 矩阵看成一个长度为 m*n 的有序数组。", "用下标 mid 同时算出所在行和列，再套普通二分。"], "O(log(mn)) 时间，O(1) 空间")
def solve_74(matrix, target):
    rows, cols = len(matrix), len(matrix[0])
    lo, hi = 0, rows * cols - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        value = matrix[mid // cols][mid % cols]
        if value == target:
            return True
        if value < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return False


@register(34, ["分别二分查找 target 的左边界和右边界。", "找左边界时，相等也继续向左收缩；找右边界时，相等也继续向右收缩。"], "O(log n) 时间，O(1) 空间")
def solve_34(nums, target):
    def lower_bound(x):
        lo, hi = 0, len(nums)
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] < x:
                lo = mid + 1
            else:
                hi = mid
        return lo

    left = lower_bound(target)
    if left == len(nums) or nums[left] != target:
        return [-1, -1]
    right = lower_bound(target + 1) - 1
    return [left, right]


@register(33, ["旋转数组一定有一半是有序的。", "判断 target 是否落在有序的那一半，再决定收缩哪一侧。"], "O(log n) 时间，O(1) 空间")
def solve_33(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:  # 左半段有序
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:  # 右半段有序
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1


@register(153, ["旋转后最小元素在“下降点”右侧。", "比较 nums[mid] 与 nums[hi]：mid 更大时，最小值在右侧；否则在左侧。"], "O(log n) 时间，O(1) 空间")
def solve_153(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1
        else:
            hi = mid
    return nums[lo]


@register(20, ["用栈保存尚未匹配的左括号。", "遇到右括号时，栈顶必须是同类型的左括号；最后栈必须为空。"], "O(n) 时间，O(n) 空间")
def solve_20(s):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif not stack or stack.pop() != pairs[ch]:
            return False
    return not stack


@register(394, ["遇到数字和 '[' 时，把之前的字符串和重复次数压栈。", "遇到 ']' 时弹出，按次数拼接后再接上当前字符串。"], "O(n) 时间，O(n) 空间")
def solve_394(s):
    stack = []
    num = 0
    current = ""
    for ch in s:
        if ch.isdigit():
            num = num * 10 + int(ch)
        elif ch == "[":
            stack.append((current, num))
            current = ""
            num = 0
        elif ch == "]":
            prev, repeat = stack.pop()
            current = prev + current * repeat
        else:
            current += ch
    return current


@register(739, ["要找右边第一个更高温度，适合单调递减栈。", "栈里存下标；新温度更高时不断弹出并结算天数。"], "O(n) 时间，O(n) 空间")
def solve_739(temperatures):
    ans = [0] * len(temperatures)
    stack = []
    for i, t in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < t:
            j = stack.pop()
            ans[j] = i - j
        stack.append(i)
    return ans


@register(215, ["维护一个大小为 k 的小顶堆，堆顶就是第 k 大的元素。", "遍历数组，堆不足 k 个就入堆；超过 k 个时，若当前值更大就替换堆顶。"], "O(n log k) 时间，O(k) 空间")
def solve_215(nums, k):
    heap = []
    for x in nums:
        if len(heap) < k:
            heapq.heappush(heap, x)
        elif x > heap[0]:
            heapq.heapreplace(heap, x)
    return heap[0]


@register(347, ["先统计每个元素的频率。", "用小顶堆维护频率最高的 k 个；输出顺序不重要。"], "O(n log k) 时间，O(n) 空间")
def solve_347(nums, k):
    freq = Counter(nums)
    return [x for x, _ in heapq.nlargest(k, freq.items(), key=lambda item: item[1])]
