"""技巧类题解。"""
from __future__ import annotations

from .base import register


@register(136, ["异或满足 a ^ a = 0，a ^ 0 = a。", "把所有数异或起来，成对出现的数会抵消，剩下只出现一次的数。"], "O(n) 时间，O(1) 空间")
def solve_136(nums):
    ans = 0
    for x in nums:
        ans ^= x
    return ans


@register(169, ["多数元素出现次数超过一半，可以用摩尔投票。", "维护候选值和票数：相同则加一，不同则减一，票数为零时换候选。"], "O(n) 时间，O(1) 空间")
def solve_169(nums):
    candidate = None
    count = 0
    for x in nums:
        if count == 0:
            candidate = x
        count += 1 if x == candidate else -1
    return candidate


@register(75, ["原地排序 0/1/2，用三个指针划分三个区域。", "left 左边都是 0，right 右边都是 2；遇到 2 时交换后不能立刻前进。"], "O(n) 时间，O(1) 空间")
def solve_75(nums):
    left, i, right = 0, 0, len(nums) - 1
    while i <= right:
        if nums[i] == 0:
            nums[left], nums[i] = nums[i], nums[left]
            left += 1
            i += 1
        elif nums[i] == 2:
            nums[i], nums[right] = nums[right], nums[i]
            right -= 1
        else:
            i += 1
    return nums


@register(31, ["从右往左找第一个“左边比右边小”的位置 i。", "在 i 右边找比 nums[i] 大的最小元素交换，再把 i 右边反转成升序。"], "O(n) 时间，O(1) 空间")
def solve_31(nums):
    n = len(nums)
    i = n - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1
    if i >= 0:
        j = n - 1
        while nums[j] <= nums[i]:
            j -= 1
        nums[i], nums[j] = nums[j], nums[i]
    nums[i + 1:] = reversed(nums[i + 1:])
    return nums


@register(287, ["把下标 i 指向 nums[i]，问题变成找环的入口。", "先用快慢指针相遇，再让一个指针回到 0，同步前进找到入口。"], "O(n) 时间，O(1) 空间")
def solve_287(nums):
    slow = fast = 0
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    finder = 0
    while finder != slow:
        finder = nums[finder]
        slow = nums[slow]
    return slow
