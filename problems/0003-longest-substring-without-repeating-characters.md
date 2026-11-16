# 3. 无重复字符的最长子串

中等 · 滑动窗口 · [力扣原题](https://leetcode.cn/problems/longest-substring-without-repeating-characters/)

## 题意

给定一个字符串 `s` ，请你找出其中不含有重复字符的 **最长 子串**** **的长度。

## 约束

- `0 <= s.length <= 10^5`
- `s` 由英文字母、数字、符号和空格组成

## ACM 输入格式

- 所有数字/字符串按空白或按行读入，具体如下：
- `s`：一行字符串。

## ACM 输出格式

- 一个整数。

## 样例 1

输入：

```text
abcabcbb
```

输出：

```text
3
```

## 样例 2

输入：

```text
bbbbb
```

输出：

```text
1
```

## 样例 3

输入：

```text
pwwkew
```

输出：

```text
3
```

## 训练约定

- 先独立想 15 分钟，再看提示；25 分钟内完成，30 分钟是硬上限。
- 卡住时先看提示 1，再看提示 2；仍写不出再看参考题解。
- 看过参考题解后，标记为“看题解后复现”，并闭卷重写一遍。
- 参考题解：[打开](../reference/0003-longest-substring-without-repeating-characters.py)（完成或决定看答案后再打开）。
