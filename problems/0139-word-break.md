# 139. 单词拆分

中等 · 动态规划 · [力扣原题](https://leetcode.cn/problems/word-break/)

## 题意

给你一个字符串 `s` 和一个字符串列表 `wordDict` 作为字典。如果可以利用字典中出现的一个或多个单词拼接出 `s` 则返回 `true`。

**注意：**不要求字典中出现的单词全部都使用，并且字典中的单词可以重复使用。

## 约束

- `1 <= s.length <= 300`
- `1 <= wordDict.length <= 1000`
- `1 <= wordDict[i].length <= 20`
- `s` 和 `wordDict[i]` 仅由小写英文字母组成
- `wordDict` 中的所有字符串 **互不相同**

## ACM 输入格式

- 所有数字/字符串按空白或按行读入，具体如下：
- `s`：一行字符串。
- `wordDict`：先读个数 n，再逐行读 n 个字符串。

## ACM 输出格式

- true 或 false。

## 样例 1

输入：

```text
leetcode
2
leet
code
```

输出：

```text
true
```

## 样例 2

输入：

```text
applepenapple
2
apple
pen
```

输出：

```text
true
```

## 样例 3

输入：

```text
catsandog
5
cats
dog
sand
and
cat
```

输出：

```text
false
```

## 训练约定

- 先独立想 15 分钟，再看提示；25 分钟内完成，30 分钟是硬上限。
- 卡住时先看提示 1，再看提示 2；仍写不出再看参考题解。
- 看过参考题解后，标记为“看题解后复现”，并闭卷重写一遍。
- 参考题解：[打开](../reference/0139-word-break.py)（完成或决定看答案后再打开）。
