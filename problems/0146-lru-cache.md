# 146. LRU 缓存

中等 · 链表 · [力扣原题](https://leetcode.cn/problems/lru-cache/)

## 题意

请你设计并实现一个满足 LRU (最近最少使用) 缓存 约束的数据结构。

实现 `LRUCache` 类：

 - `LRUCache(int capacity)` 以 **正整数** 作为容量 `capacity` 初始化 LRU 缓存

 - `int get(int key)` 如果关键字 `key` 存在于缓存中，则返回关键字的值，否则返回 `-1` 。

 - `void put(int key, int value)` 如果关键字 `key` 已经存在，则变更其数据值 `value` ；如果不存在，则向缓存中插入该组 `key-value` 。如果插入操作导致关键字数量超过 `capacity` ，则应该 **逐出** 最久未使用的关键字。

函数 `get` 和 `put` 必须以 `O(1)` 的平均时间复杂度运行。

## 约束

- `1 <= capacity <= 3000`
- `0 <= key <= 10000`
- `0 <= value <= 10^5`
- 最多调用 `2 * 10^5` 次 `get` 和 `put`

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
10
LRUCache 2
put 1 1
put 2 2
get 1
put 3 3
get 2
put 4 4
get 1
get 3
get 4
```

输出：

```text
null
null
null
1
null
-1
null
-1
3
4
```

## 训练约定

- 先独立想 15 分钟，再看提示；25 分钟内完成，30 分钟是硬上限。
- 卡住时先看提示 1，再看提示 2；仍写不出再看参考题解。
- 看过参考题解后，标记为“看题解后复现”，并闭卷重写一遍。
- 参考题解：[打开](../reference/0146-lru-cache.py)（完成或决定看答案后再打开）。
