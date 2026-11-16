# 207. 课程表

中等 · 图论 · [力扣原题](https://leetcode.cn/problems/course-schedule/)

## 题意

你这个学期必须选修 `numCourses` 门课程，记为 `0` 到 `numCourses - 1` 。

在选修某些课程之前需要一些先修课程。 先修课程按数组 `prerequisites` 给出，其中 `prerequisites[i] = [ai, bi]` ，表示如果要学习课程 `ai` 则 **必须** 先学习课程 `bi` 。

 - 例如，先修课程对 `[0, 1]` 表示：想要学习课程 `0` ，你需要先完成课程 `1` 。

请你判断是否可能完成所有课程的学习？如果可以，返回 `true` ；否则，返回 `false` 。

## 约束

- `1 <= numCourses <= 2000`
- `0 <= prerequisites.length <= 5000`
- `prerequisites[i].length == 2`
- `0 <= ai, bi < numCourses`
- `prerequisites[i]` 中的所有课程对 **互不相同**

## ACM 输入格式

- 所有数字/字符串按空白或按行读入，具体如下：
- `numCourses`：一个整数。
- `prerequisites`：先读边数 m，再读 m 行，每行 u v。

## ACM 输出格式

- true 或 false。

## 样例 1

输入：

```text
2
1
1 0
```

输出：

```text
true
```

## 样例 2

输入：

```text
2
2
1 0
0 1
```

输出：

```text
false
```

## 训练约定

- 先独立想 15 分钟，再看提示；25 分钟内完成，30 分钟是硬上限。
- 卡住时先看提示 1，再看提示 2；仍写不出再看参考题解。
- 看过参考题解后，标记为“看题解后复现”，并闭卷重写一遍。
- 参考题解：[打开](../reference/0207-course-schedule.py)（完成或决定看答案后再打开）。
