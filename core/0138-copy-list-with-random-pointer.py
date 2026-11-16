# -*- coding: utf-8 -*-
r"""
138. 随机链表的复制（中等）· 链表
https://leetcode.cn/problems/copy-list-with-random-pointer/

【核心代码模式】
- 判题驱动会实例化 Solution 并调用 copyRandomList(...)，参数已按力扣官方示例解析好。
- 直接 return 结果即可，不需要写输入输出，也不需要 main。
- 下面的节点类由平台预先提供，可以修改或删除后自己重写。
- 切换到 ACM 模式可编辑含 main 与输入输出的完整程序。
"""

class RandomNode:
    """带随机指针的链表节点。"""

    def __init__(self, val=0, next=None, random=None):
        self.val = val
        self.next = next
        self.random = random


"""
# Definition for a Node.
class Node:
    def __init__(self, x: int, next: 'Node' = None, random: 'Node' = None):
        self.val = int(x)
        self.next = next
        self.random = random
"""

class Solution:
    def copyRandomList(self, head: 'Optional[Node]') -> 'Optional[Node]':
        pass
