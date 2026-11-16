# Hot100 训练器 v2 详细设计（待审核）

目标：解决「没有动力打开它」的问题。六条需求按编号分五个阶段交付（需求 1 的页面优化贯穿各阶段）：
P1 页面骨架 + 激励系统 → P2 专题练习 → P3 精选题库 + 模拟考试 → P4 手撕面试（严格） → P5 Agent 教练（DeepSeek，key 由用户在设置里手动输入）。

已确认的决策：
- 教练接入：OpenAI 兼容接口，默认 DeepSeek（`https://api.deepseek.com`，model `deepseek-chat`）。**API key 不经过对话、不入库明文展示**：设置页密码框手动输入，本地保存，接口只回掩码。
- 考试题源：精选池离线抽题 + 全题库在线兜底开关。
- 面试强度：严格（不可暂停、无提示/参考、一次提交）。
- 网络事实：leetcode.cn GraphQL 当前可直连（已实测）；DeepSeek 国内直连，不需要 Magpie。

不变约束：Python 标准库、单文件仪表盘、只监听 127.0.0.1、现有 88 题训练流程与数据不破坏。

---

## 0. 现状基线

表：`problems / plan_items / reviews / sessions / notifications / meta / code_runs / code_mode`。
判题：`hot100/judge.py` 双模式 + 隔离子进程；用例：`official.official_cases()`（88 题 223 例，期望优先题面原文、缺失用 BANK oracle）。
页面：单 PAGE，模态框 + 全屏写代码工作台（`#ws`）。

复用点：工作台 `openWorkspace(item, opts)` 增加 opts 支持锁定/隐藏按钮；`judge.run` 直接用于考试/面试判题；`md` 渲染器用于教练报告。

---

## 1. P1 页面骨架 + 激励系统

### 1.1 导航与布局

顶部品牌行下加主导航（五个 tab，客户端切换 section，不刷新页面）：

```
[练习计划] [专题练习] [模拟考试] [手撕面试] [复盘报告]
```

- 练习计划：现有 main 布局整体保留，上方插入 **hero 激励条**。
- hero 激励条（所有 tab 可见）：连续天数火焰、等级进度条（XP）、今日任务环（已完成/今日计划）、徽章数（点开徽章墙模态）。
- 徽章解锁：专用 toast（金色描边 + 徽章名），普通 toast 不变。
- 移动端：导航横向滚动；hero 折行两行。

### 1.2 新增表

```sql
CREATE TABLE IF NOT EXISTS xp_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  day TEXT NOT NULL,
  kind TEXT NOT NULL,          -- ac_new/ac_review/exam/interview/hard_ac/streak_bonus/topic_ac
  ref_id INTEGER,              -- session/exam/interview/run id
  xp INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS achievements (
  id TEXT PRIMARY KEY,         -- 徽章定义 key
  unlocked_at TEXT NOT NULL,
  day TEXT NOT NULL
);
```

 streak / best_streak / week 统计**不建表**，由 `sessions.day + exams.day + interviews.day` 现算（有完成记录的日子算活跃）。

### 1.3 XP 与等级规则（只奖不罚）

| 事件 | XP |
| --- | --- |
| 新题独立完成 | 30 |
| 新题借提示完成 | 20 |
| 新题看题解后复现 | 15 |
| 复习完成（任何结果非 unfinished） | 10 |
| 专题自由练习全过（pass_rate=100） | 10 |
| hard 题首次全过（额外） | +25 |
| 考试提交且 score≥60 | 40 |
| 面试提交（无论通过率） | 35 |
| 当日活跃 streak 奖励 | +5×min(streak,7)，每天首次事件时补发 |

等级：升到第 n 级需 `100 + (n-1)*60` XP（累计求和）；hero 显示当前级与本级进度。
XP 发放入口统一 `store.grant_xp(kind, ref_id, day)`，内部判重（同 ref 同 kind 只发一次）。

### 1.4 徽章定义（12 枚，代码内常量表）

first_ac 首杀 / streak7 七日连击 / streak30 月度坚持 / hard_first 硬骨头 /
exam_pass 考官认可（score≥80）/ exam_full 满分考官（score=100）/
interview_debut 面试首秀 / interview_full 面试通关（全过）/
topic_master 专题征服（任一专题全部完成）/ night_owl 夜猫（22:00 后完成）/
century 百炼（累计 100 次全过运行）/ conqueror 题库征服者（88 题全部 done）。

解锁检查 `store.check_achievements()` 在 finish/submit/run 后调用；新解锁写入表并随响应返回 `new_badges`，前端弹金色 toast。

### 1.5 API 变更

- `GET /api/state` 增加 `motivation` 块：
  `{xp, level, level_xp, level_need, streak, best_streak, today:{done,planned}, badges:[{id,name,desc,unlocked,at}], week:[{day,minutes,done,xp,pass_rate}]}`（week 为最近 7 天）。
- `POST /api/finish`、`/api/run` 响应增加 `xp_gained, new_badges`。
- 徽章墙数据已在 state，无新端点。

### 1.6 验收

浏览器探针：完成一次 pid=1（脚本代答后清理）→ hero 数字变化、金色 toast、徽章墙首杀点亮；移动端导航不溢出；现有计时/复习流程回归不变。

---

## 2. P2 专题练习

### 2.1 数据

专题键 = 现有 `problem["group"]`（哈希、双指针、滑动窗口、链表、二叉树、回溯、动态规划、图、堆、栈、贪心、二分查找…以 problems.json 实际值为准）；精选题库入池后按其 `topicTags` 中文名归并到同一视图（多标签题在每个标签下都出现）。

### 2.2 页面

- 专题卡片网格：名称、题数、已完成、最佳通过率均值、进度条；难度过滤（全部/简单/中等/困难）。
- 点卡片 → 专题详情列表：每行 题号/标题/难度/状态/最佳通过率 + [写代码] [题面] [加入今日计划]。
- 「加入今日计划」→ `POST /api/plan/add {problem_id}`：planner 在今日末尾追加 `kind="extra"` 的 plan_item（不占用 new/review 名额， UNIQUE(day,problem_id,kind) 防重）；之后走正常计时流程。
- 直接 [写代码] = 自由练习：不计时，运行全过发 topic_ac XP。

### 2.3 API

- `GET /api/topics` → `[{key,name,total,done,avg_rate,problems:[{id,title,difficulty,status,best_rate,in_plan}]}]`（含池题；池题状态读 `pool_progress`，见 P3）。
- `POST /api/plan/add`。

### 2.4 验收

专题计数与 problems.json 分组一致；加入今日计划后仪表盘出现 extra 行且可计时；重复加入不产生重复行。

---

## 3. P3 精选题库 + 模拟考试

### 3.1 题库构建 `tools/build_exam_pool.py`

来源（leetcode.cn GraphQL，已实测直连）：studyplan `top-100-liked` + `top-interview-150` 并集去重，取 Medium/Hard，预计 250–350 题。
逐题 `questionData`：questionFrontendId、titleSlug、translatedTitle、translatedContent、difficulty、metaData、codeSnippets、exampleTestcases、topicTags(translatedName)。间隔 0.25s，失败重试 2 次。

I/O 适配：把 `tools/build_dataset.py` 里的 metaData→kind 映射抽成 `hot100/io_map.py: infer_io(raw)`；**验收要求 io_map 对现有 88 题的输出与 problems.json 的 io 完全一致**（build_dataset 本体不动，避免覆盖官方全量样例）。

用例：`official.official_cases(problem, allow_oracle=False)`（新增参数：池题无 BANK，期望只取题面原文）。**任何一例题面期望解析失败的题直接不入池**，构建日志打印入池/淘汰数与原因。入池前校验：core snippet 可 compile、ACM 模板可生成、全部用例双格式文本非空。

产物 `data/exam_pool.json`：与 problems.json 同构的 problem 列表 + `tags`。服务器启动加载；`pool_progress` 表记录池题状态：

```sql
CREATE TABLE IF NOT EXISTS pool_progress (
  problem_id INTEGER PRIMARY KEY,   -- 池题用负数 id 段？否：池题 id = 100000 + frontendId，避免与 88 题冲突
  status TEXT NOT NULL DEFAULT 'todo',
  best_rate REAL,
  attempts INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT
);
```

池题 id 规则：`100000 + questionFrontendId`（前端显示原题号）。88 题若也在池中，共享同一 id（Hot100 id 即原题号）→ 池题 id 直接用 frontendId，但 88 题已占用 1..3000 段？Hot100 的 id 就是力扣题号（1,49,128…）。**冲突处理**：池内与 88 题重合的题直接引用主题库条目（不重复存），pool_progress 只存非 88 题；id 空间天然不冲突（同题同号）。

### 3.2 在线兜底

`POST /api/exam/start {source:"online"}`：GraphQL `problemsetQuestionList`（filters.difficulty）随机 skip 抽 slug → questionData → io_map + official_cases(allow_oracle=False) → 成功缓存 `data/online_cache.json`；单题最多重试 6 次抽换；网络失败返回明确错误并建议切精选池。在线题同样写 pool_progress。

### 3.3 考试流程与表

```sql
CREATE TABLE IF NOT EXISTS exams (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  source TEXT NOT NULL,             -- pool/online
  minutes INTEGER NOT NULL,
  deadline TEXT NOT NULL,           -- 服务器权威截止
  status TEXT NOT NULL DEFAULT 'running',  -- running/finished/abandoned
  problem_ids TEXT NOT NULL,        -- JSON [id,id,id]
  score REAL,                       -- 三题通过率均值 0-100
  passed INTEGER, total INTEGER,    -- 用例合计
  elapsed_sec INTEGER,
  late INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS exam_answers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exam_id INTEGER NOT NULL,
  problem_id INTEGER NOT NULL,
  mode TEXT NOT NULL,
  code TEXT NOT NULL DEFAULT '',
  passed INTEGER, total INTEGER, pass_rate REAL,
  updated_at TEXT NOT NULL,
  UNIQUE(exam_id, problem_id)
);
```

- `POST /api/exam/start {medium:2, hard:1, minutes:60, source:"pool"}`：默认 2 mid + 1 hard，数量/时长可调（1–3 mid、0–2 hard、30–120 分钟）。抽题排除最近 10 场考过的题；池不足时放宽排除并在响应 `notice` 说明。返回 `{exam_id, deadline, problems:[{id,title,difficulty,statement_html,cases_preview,io_doc}]}`。
- 考试壳（全屏，复用工作台编辑器）：顶部倒计时（以服务器 deadline 为准，本地时钟偏移用 start 响应校准）、题目标签页 ×3、每题独立模式选择（首次运行后锁定该题模式）、**无提示/参考/重置按钮**；草稿自动保存 `POST /api/exam/save`（900ms  debounce，刷新页面不丢代码）。
- `POST /api/exam/submit {exam_id, answers:[{problem_id,mode,code}]}`：逐题 `judge.run`；score=三题 pass_rate 均值；超过 deadline+30s 提交记 late=1（仍判分）；客户端倒计时归零自动提交。写 exam_answers 成绩、exams 汇总、pool_progress、XP/徽章。
- `GET /api/exam/history`、`GET /api/exam?id=`（报告：逐题通过率/耗时/代码/用例明细）。
- 放弃：`POST /api/exam/abandon`。

### 3.4 验收

构建日志：入池≥250、淘汰原因可查；io_map 与 88 题 io 一致性断言通过；脚本化考试（三题灌参考解/池题用在线期望自洽解？池题无参考解 → 用「core 模式 + 题面期望」自证：脚本提交空代码得 0 分、提交正确解需人工？改为：考试判题链路用 88 题中的 2 mid + 1 hard？88 题无 hard → 在线/池 hard 判题正确性由 P3 构建期「期望自洽校验」保证：对池题用 io_map+official 生成 ACM 输入，期望文本双模式解析一致即通过）。端到端：start→save→submit→history 全链路 + 倒计时自动提交 + late 标记。

---

## 4. P4 手撕面试（严格）

```sql
CREATE TABLE IF NOT EXISTS interviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  problem_id INTEGER NOT NULL,
  mode TEXT NOT NULL,               -- 开始时选定，之后锁定
  minutes INTEGER NOT NULL,
  deadline TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'running',  -- running/finished/abandoned
  first_run_sec INTEGER,            -- 开始到第一次运行
  runs INTEGER NOT NULL DEFAULT 0,
  passed INTEGER, total INTEGER, pass_rate REAL,
  elapsed_sec INTEGER,
  code TEXT NOT NULL DEFAULT ''
);
```

- `POST /api/interview/start {minutes:35, difficulty:"mixed"}`：抽 1 题（mixed=medium/hard 随机），返回题目 + 模式选择界面；选定模式后进入锁定工作台：隐藏模式切换/提示/参考/重置；倒计时不可暂停；[运行用例] 允许（计 runs、记 first_run_sec），[提交并结束] 仅一次。
- `POST /api/interview/save`（草稿）、`/submit`（判题+结束+XP+徽章）、`/abandon`。
- 结束页：通过率、用时、首跑时间、运行次数 + 教练追问区（P5；无 key 时本地规则追问：复杂度/边界/变式三问模板）。
- `GET /api/interview/history`。
- 验收：脚本化 start→run→submit；锁定项在 DOM 中不存在；超时自动提交；abandon 不发 XP。

---

## 5. P5 Agent 教练（DeepSeek）

### 5.1 配置与 key 安全

config 新增：`coach_enabled(false)`、`coach_base_url("https://api.deepseek.com")`、`coach_model("deepseek-chat")`、`coach_api_key("")`、`coach_proxy("")`、`coach_timeout(60)`。
- 设置页密码框输入 key；`POST /api/config` 中 `coach_api_key` 为**只写字段**：空串=保持原值，`"__clear__"`=清除。
- 任何 GET 响应只给 `coach_key_mask`（`sk-****` + 末 4 位）与 `coach_key_set`；日志只记 model/耗时/状态码，不记 key 与代码全文。
- 首次点击教练功能弹确认模态：说明代码与题面将发送到所填 endpoint；同意后 `coach_enabled=true`。

### 5.2 客户端 `hot100/coach.py`

stdlib urllib 调 OpenAI 兼容 `/chat/completions`（非流式），支持 coach_proxy；超时/401/429 返回友好错误（401 提示检查 key，429 提示稍后）。温度 0.3。

### 5.3 端点与缓存

```sql
CREATE TABLE IF NOT EXISTS coach_reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,          -- review/exam/interview/followups
  ref_key TEXT NOT NULL,       -- problem:mode:codehash / exam:id / interview:id
  model TEXT NOT NULL,
  content TEXT NOT NULL,       -- markdown
  adjustments TEXT,            -- JSON 或 NULL
  created_at TEXT NOT NULL,
  UNIQUE(kind, ref_key)
);
```

- `POST /api/coach/review {problem_id, mode, code}`：同 code hash 命中缓存直接返回（不重复花钱）。prompt = 系统教练人设 + 题面/IO/约束 + 用户代码 + 本次运行指标 + 失败用例摘要；要求输出四节：代码质量（正确性/复杂度/风格/边界）、思路点评、训练建议（3 条可执行）、可选 ```json 调整建议 {max_new_per_day?, deadline?, focus_tags?, max_reviews_per_day?}```。
- `POST /api/coach/report {kind:"exam"|"interview", id}`：整场代码+指标+追问（面试）→ 复盘报告 markdown + 调整建议。
- `POST /api/coach/followups {interview_id}`：3 个追问（复杂度优化/边界/变式）。
- `POST /api/coach/apply {fields}`：把 adjustments 白名单字段写入 config 并 replan（等价用户手动改设置，前端逐字段展示确认后才调用）。
- `GET /api/reports`：复盘报告 tab 列表（coach_reviews + exams + interviews + 周统计）。
- 无 key / coach_enabled=false：`review` 走**本地规则版**（ast 统计循环嵌套/递归/排序/哈希使用、函数长度、失败用例归类），content 头部明确标注「本地规则版 · 未配置模型」；report/followups 用模板版。配置 key 后无缝切换。

### 5.4 页面

- 工作台右栏加 tab：[用例结果] [教练点评]；点评 tab 按钮「让教练看看这份代码」→ loading → markdown 渲染 + 「应用训练调整」按钮（有 adjustments 时）。
- 考试/面试结束页：「生成复盘报告」按钮 + 报告模态。
- 复盘报告 tab：周曲线（SVG：分钟柱 + 通过率线）、报告列表、徽章墙入口。

### 5.5 验收

无 key：规则版点评可用且标注清楚；key 掩码不回显、清空生效；`tools/coach_selftest.py`（用户填 key 后运行）发一条最小 prompt 验证连通；缓存命中不重复请求（日志计数）；apply 只改白名单字段且需前端确认。

---

## 6. 阶段计划与回归

每阶段结束跑：`python -m tools.verify_judge`（88×223×双模式 0 失败）+ API 冒烟 + headless Chrome 探针（桌面/移动截图、控制台零报错）。
P3 额外：io_map 一致性断言、池构建统计、考试全链路脚本。
交付顺序 P1→P5；每阶段独立可用，中断不留下半残功能（新 tab 未实现前不显示）。

## 7. 风险与兜底

- 题面期望解析失败的池题：淘汰不入池，日志可查（宁缺勿造）。
- 在线抽题网络中断：明确报错 + 一键切精选池。
- DeepSeek 欠费/限流：友好错误 + 本地规则版兜底，不阻塞练习。
- 考试/面试刷新页面：草稿服务端保存 + deadline 服务器权威，恢复后继续倒计时。
- key 泄露面：仅本地 config 文件；接口掩码；日志脱敏；不进入 git（config.json 已在 data/，提交范围只含代码/测试/文档）。