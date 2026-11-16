# -*- coding: utf-8 -*-
r"""
199. 二叉树的右视图（中等）· 二叉树
https://leetcode.cn/problems/binary-tree-right-side-view/

【核心代码模式】
- 判题驱动会实例化 Solution 并调用 rightSideView(...)，参数已按力扣官方示例解析好。
- 直接 return 结果即可，不需要写输入输出，也不需要 main。
- 下面的节点类由平台预先提供，可以修改或删除后自己重写。
- 切换到 ACM 模式可编辑含 main 与输入输出的完整程序。
"""

class TreeNode:
    """二叉树节点。"""

    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


# Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right
class Solution:
    def rightSideView(self, root: Optional[TreeNode]) -> List[int]:
        pass
