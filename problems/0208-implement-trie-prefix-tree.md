# 208. 实现 Trie (前缀树)

中等 · 图论 · [力扣原题](https://leetcode.cn/problems/implement-trie-prefix-tree/)

## 题意

**Trie**（发音类似 "try"）或者说 **前缀树** 是一种树形数据结构，用于高效地存储和检索字符串数据集中的键。这一数据结构有相当多的应用情景，例如自动补全和拼写检查。

请你实现 Trie 类：

 - `Trie()` 初始化前缀树对象。

 - `void insert(String word)` 向前缀树中插入字符串 `word` 。

 - `boolean search(String word)` 如果字符串 `word` 在前缀树中，返回 `true`（即，在检索之前已经插入）；否则，返回 `false` 。

 - `boolean startsWith(String prefix)` 如果之前已经插入的字符串 `word` 的前缀之一为 `prefix` ，返回 `true` ；否则，返回 `false` 。

## 约束

- `1 <= word.length, prefix.length <= 2000`
- `word` 和 `prefix` 仅由小写英文字母组成
- `insert`、`search` 和 `startsWith` 调用次数 **总计** 不超过 `3 * 10^4` 次

## ACM 输入格式

- 所有数字/字符串按空白或按行读入，具体如下：
- 第一行：操作数 m。
- 随后 m 行：每行一个操作名和参数（空格分隔）。
- 第一行通常是构造函数，例如 `LRUCache 2`；void 操作没有返回值。

## ACM 输出格式

- 每个操作输出一行；构造函数和 void 操作输出 `null`。

## 样例 1

输入：

```text
7
Trie
insert apple
search apple
search app
startsWith app
insert app
search app
```

输出：

```text
null
null
true
false
true
null
true
```

## 训练约定

- 先独立想 15 分钟，再看提示；25 分钟内完成，30 分钟是硬上限。
- 卡住时先看提示 1，再看提示 2；仍写不出再看参考题解。
- 看过参考题解后，标记为“看题解后复现”，并闭卷重写一遍。
- 参考题解：[打开](../reference/0208-implement-trie-prefix-tree.py)（完成或决定看答案后再打开）。
