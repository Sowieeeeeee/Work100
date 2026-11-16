# 155. 最小栈

中等 · 栈 · [力扣原题](https://leetcode.cn/problems/min-stack/)

## 题意

设计一个支持 `push` ，`pop` ，`top` 操作，并能在常数时间内检索到最小元素的栈。

实现 `MinStack` 类:

 - `MinStack()` 初始化堆栈对象。

 - `void push(int value)` 将元素 `value` 推入堆栈。

 - `void pop()` 删除堆栈顶部的元素。

 - `int top()` 获取堆栈顶部的元素。

 - `int getMin()` 获取堆栈中的最小元素。

## 约束

- `-2^31 <= val <= 2^31 - 1`
- `pop`、`top` 和 `getMin` 操作总是在 **非空栈** 上调用
- `push`, `pop`, `top`, and `getMin`最多被调用 `3 * 10^4` 次

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
8
MinStack
push -2
push 0
push -3
getMin
pop
top
getMin
```

输出：

```text
null
null
null
null
-3
null
0
-2
```

## 训练约定

- 先独立想 15 分钟，再看提示；25 分钟内完成，30 分钟是硬上限。
- 卡住时先看提示 1，再看提示 2；仍写不出再看参考题解。
- 看过参考题解后，标记为“看题解后复现”，并闭卷重写一遍。
- 参考题解：[打开](../reference/0155-min-stack.py)（完成或决定看答案后再打开）。
