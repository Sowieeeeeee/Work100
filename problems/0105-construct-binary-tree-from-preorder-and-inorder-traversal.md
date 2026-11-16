# 105. 从前序与中序遍历序列构造二叉树

中等 · 二叉树 · [力扣原题](https://leetcode.cn/problems/construct-binary-tree-from-preorder-and-inorder-traversal/)

## 题意

给定两个整数数组 `preorder` 和 `inorder` ，其中 `preorder` 是二叉树的**先序遍历**， `inorder` 是同一棵树的**中序遍历**，请构造二叉树并返回其根节点。

## 约束

- `1 <= preorder.length <= 3000`
- `inorder.length == preorder.length`
- `-3000 <= preorder[i], inorder[i] <= 3000`
- `preorder` 和 `inorder` 均 **无重复** 元素
- `inorder` 均出现在 `preorder`
- `preorder` **保证** 为二叉树的前序遍历序列
- `inorder` **保证** 为二叉树的中序遍历序列

## ACM 输入格式

- 所有数字/字符串按空白或按行读入，具体如下：
- `preorder`：先读长度 n，再读 n 个整数。
- `inorder`：先读长度 n，再读 n 个整数。

## ACM 输出格式

- 先输出层序长度，再输出层序 token；null 表示空结点。

## 样例 1

输入：

```text
5
3 9 20 15 7
5
9 3 15 20 7
```

输出：

```text
7
3 9 20 null null 15 7
```

## 样例 2

输入：

```text
1
-1
1
-1
```

输出：

```text
1
-1
```

## 训练约定

- 先独立想 15 分钟，再看提示；25 分钟内完成，30 分钟是硬上限。
- 卡住时先看提示 1，再看提示 2；仍写不出再看参考题解。
- 看过参考题解后，标记为“看题解后复现”，并闭卷重写一遍。
- 参考题解：[打开](../reference/0105-construct-binary-tree-from-preorder-and-inorder-traversal.py)（完成或决定看答案后再打开）。
