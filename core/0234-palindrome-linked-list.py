# -*- coding: utf-8 -*-
r"""
234. 回文链表（简单）· 链表
https://leetcode.cn/problems/palindrome-linked-list/

【核心代码模式】
- 判题驱动会实例化 Solution 并调用 isPalindrome(...)，参数已按力扣官方示例解析好。
- 直接 return 结果即可，不需要写输入输出，也不需要 main。
- 下面的节点类由平台预先提供，可以修改或删除后自己重写。
- 切换到 ACM 模式可编辑含 main 与输入输出的完整程序。
"""

class ListNode:
    """单链表节点。"""

    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def isPalindrome(self, head: Optional[ListNode]) -> bool:
        pass
