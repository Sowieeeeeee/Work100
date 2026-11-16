# 79. 单词搜索

中等 · 回溯 · [力扣原题](https://leetcode.cn/problems/word-search/)

## 题意

给定一个 `m x n` 二维字符网格 `board` 和一个字符串单词 `word` 。如果 `word` 存在于网格中，返回 `true` ；否则，返回 `false` 。

单词必须按照字母顺序，通过相邻的单元格内的字母构成，其中“相邻”单元格是那些水平相邻或垂直相邻的单元格。同一个单元格内的字母不允许被重复使用。

## 约束

- `m == board.length`
- `n = board[i].length`
- `1 <= m, n <= 6`
- `1 <= word.length <= 15`
- `board` 和 `word` 仅由大小写英文字母组成

## ACM 输入格式

- 所有数字/字符串按空白或按行读入，具体如下：
- `board`：先读 rows cols，再读 rows 行字符串（每行长 cols）。
- `word`：一行字符串。

## ACM 输出格式

- true 或 false。

## 样例 1

输入：

```text
3 4
ABCE
SFCS
ADEE
ABCCED
```

输出：

```text
true
```

## 样例 2

输入：

```text
3 4
ABCE
SFCS
ADEE
SEE
```

输出：

```text
true
```

## 样例 3

输入：

```text
3 4
ABCE
SFCS
ADEE
ABCB
```

输出：

```text
false
```

## 训练约定

- 先独立想 15 分钟，再看提示；25 分钟内完成，30 分钟是硬上限。
- 卡住时先看提示 1，再看提示 2；仍写不出再看参考题解。
- 看过参考题解后，标记为“看题解后复现”，并闭卷重写一遍。
- 参考题解：[打开](../reference/0079-word-search.py)（完成或决定看答案后再打开）。
