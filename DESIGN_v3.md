# Hot100 训练器 v3 设计（执行版）

> 取代 `DESIGN_v2.md`。v3 = v2 的审核结论 + 硬伤修复 + dsh 教练 + 预构建 250–300 题池路线 + 前置重构 P0。
> v2 原文只保留在 git 历史里，不再作为实施依据。

---

## 0. 决策记录（v3 定稿）

| 议题 | 决定 | 依据 |
| --- | --- | --- |
| 教练运行时 | **使用 dsh（DeepSeek Harness）**，HTTP(OpenAI 兼容) 为降级后端，本地规则版为最终兜底 | 用户决策；见 §6 |
| 题库 | **原方案：预构建 250–300 题池**（top-100-liked ∪ top-interview-150，Medium/Hard）+ 在线兜底 | 用户决策；见 §3 |
| 前置重构 | **必须做 P0** | v2 审核 A1/A2/A6：不做则 P3/P4 反复返工 |
| 代码仓库 | `https://github.com/Sowieeeeeee/Work100`，`main` 为主干 | 用户决策；见 §8 |
| 提交纪律 | Conventional Commits + 每完成一个功能单元立即提交 | 用户决策；见 §8 |

不变约束（v2 沿用，全部仍然有效）：

- Python 3.10+ 标准库；不引入第三方依赖（dsh 以**外部子进程**方式接入，不进入依赖树）。
- 仪表盘单文件 `hot100/dashboard.py`，不引入前端框架/构建链。
- 只监听 `127.0.0.1`。
- 现有 88 题训练流程、`problems.json`、`solutions/`、`core/`、`reference/`、`state.db` 不破坏。

---

## 1. 现状基线（已实测，v2 的表述需按此处校正）

| 项 | 事实 | 证据 |
| --- | --- | --- |
| 题集 | 88 题 = 20 简单 + 68 中等，**0 道困难** | `data/problems.json`；grep `"difficulty": "(困难\|Hard)"` 零命中 |
| 用例 | 88 题 / 223 用例，双模式全过 | `python -m tools.verify_judge` |
| 表 | `problems / plan_items / reviews / sessions / notifications / meta / code_runs / code_mode` | `hot100/store.py:47` |
| 力扣原始数据 | 强依赖 `data/raw_questions.json`（654 KB，按 slug 索引） | `hot100/official.py:22 _raw()`、`:26 raw_of()` |
| 用例生成 | 题面示例 ∪ `exampleTestcases`，缺失期望由 `BANK` oracle 补 | `hot100/official.py:133`、`:156`、`:427` |
| 判题 | 双模式 + 隔离子进程 + 字节码注入 | `hot100/judge.py`、`hot100/judge_worker.py` |
| 工作台 | 与**文件**强耦合：run 先写盘再读盘 | `hot100/server.py:367-369` |
| 练习统计 | 每次 run 无条件写 `code_runs` + `last_mode` | `hot100/server.py:376-377` |
| 页面 | 单 `PAGE` 字符串 1131 行 / 58 KB，4s 轮询全量重绘 | `hot100/dashboard.py:4`、`:479`、`:1123` |
| 配置 | `CONFIG_FIELDS` 白名单 10 个字段，`data/config.json` 明文 | `hot100/server.py:24`、`data/config.json` |
| 专题 | `problem["group"]` 为力扣 studyplan 分组（哈希/双指针/滑动窗口/子串/普通数组/矩阵/链表/二叉树…），另有 `problem["topics"]` 官方标签 | `data/problems.json:13` 起 |

---

## 2. P0 前置重构（约 500–700 行，UI 零变化）

目标：让「池题」与「88 题」在同一条判题/材料链路上共存，且考试/面试不污染练习数据。**P0 不通过回归就不进 P1。**

### 2.1 统一题源 `hot100/problem_source.py`

```python
class ProblemSource:            # 抽象
    def all(self) -> list[dict]
    def get(self, pid: int) -> dict | None
    def raw_of(self, slug: str) -> dict          # metaData/codeSnippets/translatedContent/exampleTestcases
    def has_reference(self, pid: int) -> bool    # BANK 是否有参考解
    def kind(self) -> str                        # "core" | "pool"

class CoreSource(ProblemSource)  # data/problems.json + data/raw_questions.json + bank.BANK
class PoolSource(ProblemSource)  # data/exam_pool.json + data/pool_raw.json（无 BANK、无 reference）
```

- `official.raw_of(slug)` 改为委托 `problem_source.raw_of`，**先查 core 再查 pool**；`_raw()` 的 `@lru_cache(maxsize=1)`（`official.py:22`）改为两级缓存（core 一次、pool 按 mtime 失效）。
- `materials.ensure_problem(problem, create_solution=True, with_reference=True)`：池题 `with_reference=False`，跳过 `generate_reference`（它需要 `BANK[pid]`，`materials.py:282`）。
- `materials.ensure_all()` 行为不变（只处理 88 题），因此 `App.__init__`（`server.py:115`）无需改动语义。
- 兼容性硬要求：`problems.json`、`solutions/`、`core/`、`reference/` 在 P0 前后**字节不变**。

### 2.2 io 推断 `hot100/io_map.py`

```python
SUPPORTED_PARAM_KINDS = {"int","bool","str","int_array","string_array","matrix","linked_list","tree"}
SUPPORTED_RET_KINDS   = {"int","bool","str","int_array","string_array","matrix","linked_list","tree",
                         "node_value","cycle_index","intersection_value","void"}
def infer_io(raw: dict, slug: str) -> tuple[dict | None, str]   # (io, 淘汰原因)
```

- 只移植 `tools/build_dataset.py` 的**通用** `infer_kind`（`:458`），**不复制**逐 slug 的 `PARAM_KINDS`/`RETURN_KINDS`/`COMPARE`/`DESIGN_SLUGS`（`:23`/`:116`/`:145`/`:157`）。
- 通用 `infer_kind` 未命中会默认返回 `int`（`build_dataset.py:477`）——**这是 v2 的隐性炸弹**：v3 改为「未命中 = 淘汰」，返回原因。
- `compare` 只允许 `exact`；`is_design`（`official.py:34`）为真的题一律淘汰（设计类需要 `io["design"]` 的构造/方法表，通用推断不可靠）。
- 88 题一致性断言只用于证明「没有回归」，不作为池题正确性证明。

### 2.3 判题入口拆分 `hot100/server.py`

| 入口 | 语义 | 落盘 | 写 `code_runs` | 用途 |
| --- | --- | --- | --- | --- |
| `App.run(payload)` | 练习（现状） | ✅ | ✅ | P1/P2 练习工作台 |
| `App.run_detached(problem, mode, code, cases)` | 一次性判题 | ❌ | ❌ | 考试、面试、教练自检 |
| `App.compile_check(code)` | 后台预编译 | ❌ | ❌ | 编辑器状态灯 |

- `run_detached` 复用 `judge.run` 的核心逻辑，抽出 `judge.run_cases(problem, mode, code, path, cases)`；`judge.run` 变成 `run_cases` + `official_cases` 的薄包装。**`verify_judge` 的输出必须保持 0 失败。**

### 2.4 前端工作台存储后端 `hot100/dashboard.py`

```js
ws.storage = {kind:"file"}            // 默认；kind ∈ file|exam|interview
ws.storage = {kind:"exam", examId, problemId}
```

- `flushSave()`（`dashboard.py:836`）/`loadCode()`（`:859`）按 `ws.storage.kind` 分派到 `/api/code` 或 `/api/exam/save` / `/api/interview/save`。
- `render()`（`:479`）改为 `renderActiveTab()`：只重绘当前 section；轮询（`:1123`）只更新 hero 数字与计时条，**绝不重绘考试/面试壳**。
- 关键图标/按钮在 `ws.storage.kind !== "file"` 时隐藏：`#wsReset`、`#wsStatement`（考试中题面在考试壳内）、模式切换 `#wsModes`。

### 2.5 P0 验收

```bash
python -m tools.verify_judge        # 必须 "problems: 88 cases: 223 failures: 0"
git status --short                  # solutions/ core/ reference/ problems/*.md data/problems.json 无改动
```

外加：`/api/state` 单次响应 < 40 KB；`data/state.db` 表结构仅新增、不修改既有列。

---

## 3. P3 精选题库 + 模拟考试（原方案路线，补齐闸门）

### 3.1 构建 `tools/build_exam_pool.py`

来源：leetcode.cn GraphQL（已实测直连）studyplan `top-100-liked` ∪ `top-interview-150`，取 Medium/Hard，**目标 250–300 题**（去重后落在区间内；不足 250 时日志告警并可加 `top-interview-100`）。

逐题 `questionData` 拉取：`questionFrontendId / titleSlug / translatedTitle / translatedContent / difficulty / metaData / codeSnippets / exampleTestcases / topicTags(translatedName)`，间隔 0.25s，失败重试 2 次。

**入池闸门（缺一即淘汰，日志记原因与计数）：**

1. `io_map.infer_io()` 返回非 None（kind 在白名单内，非 design）；
2. 核心代码片段（Python3 `codeSnippets`）可 `compile()`；
3. `official.official_cases(problem, allow_oracle=False)` 至少返回 2 个用例，且**没有被丢弃的用例**（v2 计划里 `allow_oracle` 参数根本不存在，`official.py:427` 会直接 `KeyError` → 由 P0 新增该参数）；
4. `to_acm_input`/`lc_display` 双格式文本非空且可解析；
5. `compare == "exact"`。

产物（两个文件，缺一不可）：

- `data/exam_pool.json`：`{built_at, source, total, problems:[...]}`，problem 结构与 `problems.json` 同构；
- `data/pool_raw.json`：`{slug: {metaData, codeSnippets, translatedContent, exampleTestcases}}` —— 供 P0 的 `PoolSource.raw_of` 使用。

**id 规则（v2 此处自相矛盾，v3 定稿）**：池题 id **直接用力扣 `questionFrontendId`**；与 88 题重合（同 id）时**复用主题库条目**，`pool_progress` 只为非 88 题写行。id 空间因此天然唯一。

```sql
CREATE TABLE IF NOT EXISTS pool_progress (
  problem_id INTEGER PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'todo',
  best_rate REAL,
  attempts INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT
);
```

### 3.2 独立正确性审计（v2 的「自证」不成立，`verify_judge` 依赖 `BANK`：`tools/verify_judge.py:26`）

`tools/audit_pool.py`：随机抽 `N=20` 池题，每题用 AI/人工写一份与题面示例无关的实现，跑 `judge.run` 必须 100%。失败 → 该题下线并记入 `logs/pool_audit.log`。UI 上池题标注「用例来自官方题面示例」。

### 3.3 在线兜底

`POST /api/exam/start {source:"online"}`：`problemsetQuestionList` 按难度随机 skip 抽 slug（排除最近 10 场）→ `questionData` → 同一套入池闸门 → 成功写 `data/online_cache.json` 并落 `pool_progress`。单题最多重抽 8 次；失败返回明确错误 + 一键切精选池。

### 3.4 考试流程与表

```sql
CREATE TABLE IF NOT EXISTS exams (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL, source TEXT NOT NULL,
  minutes INTEGER NOT NULL, deadline TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'running',        -- running/finished/abandoned
  problem_ids TEXT NOT NULL, score REAL,
  passed INTEGER, total INTEGER, elapsed_sec INTEGER,
  late INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS exam_answers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exam_id INTEGER NOT NULL, problem_id INTEGER NOT NULL,
  mode TEXT NOT NULL, code TEXT NOT NULL DEFAULT '',
  passed INTEGER, total INTEGER, pass_rate REAL, updated_at TEXT NOT NULL,
  UNIQUE(exam_id, problem_id)
);
```

- `POST /api/exam/start {medium:2, hard:1, minutes:60, source:"pool"}`：默认 2 mid + 1 hard，可调 1–3 mid / 0–2 hard / 30–120 分钟。返回 `{exam_id, deadline, problems:[{id,title,difficulty,statement_html,input_preview}]}`。
  - **不下发期望输出**（v2 §3.3 的 `cases_preview` 会泄题，已删）：`input_preview` 只含输入文本与前 2 个用例的输入。
- `POST /api/exam/run {exam_id, problem_id, code}`：走 `run_detached`，只返回 `{passed,total,pass_rate,failed_indexes[]}`；**不落盘、不写 `code_runs`**。
- `POST /api/exam/save`：900ms debounce 草稿；`POST /api/exam/submit {exam_id, answers[]}`：逐题判题，`score = 三题 pass_rate 均值`，`> deadline+30s` 记 `late=1` 仍判分；客户端归零自动提交。
- `GET /api/exam/history`、`GET /api/exam?id=`（报告：逐题通过率/耗时/代码/用例明细，**提交后才给**）、`POST /api/exam/abandon`。
- XP：`score≥60 → 40`；`exam_full`（score=100）徽章。

### 3.5 验收

`tools/verify_exam.py`：抽 5 场 → 空代码提交得 0 → 灌入审计通过的参考实现得 100 → 断网场景明确报错或命中缓存 → `code_runs` 行数不变 → `solutions/` 字节不变。

---

## 4. P4 手撕面试（严格）

```sql
CREATE TABLE IF NOT EXISTS interviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL, problem_id INTEGER NOT NULL,
  mode TEXT NOT NULL, minutes INTEGER NOT NULL, deadline TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'running',        -- running/finished/abandoned
  first_run_sec INTEGER, runs INTEGER NOT NULL DEFAULT 0,
  passed INTEGER, total INTEGER, pass_rate REAL, elapsed_sec INTEGER,
  code TEXT NOT NULL DEFAULT '',
  outline_text TEXT, outline_sec INTEGER,        -- 创新点 2
  impression REAL                                 -- 面试印象分 0-100
);
CREATE TABLE IF NOT EXISTS interview_qa (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  interview_id INTEGER NOT NULL, q TEXT NOT NULL, a TEXT,
  score REAL, created_at TEXT NOT NULL
);
```

流程（三段式，见 §7 创新点 2）：

1. `POST /api/interview/start {minutes:35, difficulty:"mixed"}` → 抽 1 题（排除最近 10 场）；先模式选择（锁定），再**口述阶段**：限时 3 分钟写「思路/数据结构/复杂度/边界」，`POST /api/interview/outline` 提交后锁定。
2. 进入锁定工作台：隐藏模式切换/提示/参考/重置；倒计时不可暂停；保留后台预编译状态灯（语法检查算合理帮助，不算泄题）。
3. `[运行]` 允许，只回 `{passed,total,failed_indexes[]}`，计 `runs`、记 `first_run_sec`；`[提交并结束]` 仅一次。
4. 结束页：通过率 / 用时 / 首跑时间 / 运行次数 + 教练追问区（dsh）→ 作答 → `impression`。

验收：`tools/verify_interview.py`（脚本化 start→outline→run→submit）；锁定项在 DOM 中不存在（断言 DOM 无 `#wsReset`/`#wsStatement`/`#wsModes`）；超时自动提交；abandon 不发 XP。

---

## 5. P1 激励 + P2 专题（沿用 v2，含 6 处修订）

### 5.1 导航与布局（P1）

顶部品牌行下五个 tab：`[练习计划] [专题练习] [模拟考试] [手撕面试] [复盘报告]`，客户端切换 section、不刷新页面。`renderActiveTab()` 分派（P0 §2.4）。hero 激励条：连续天数火焰 / 等级进度 / 今日任务环 / 徽章数。

### 5.2 表与 XP

```sql
CREATE TABLE IF NOT EXISTS xp_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  day TEXT NOT NULL, kind TEXT NOT NULL, ref_id INTEGER,
  xp INTEGER NOT NULL, created_at TEXT NOT NULL,
  UNIQUE(kind, ref_id)                    -- v3 新增：设计依赖「同 ref 同 kind 只发一次」
);
CREATE TABLE IF NOT EXISTS achievements (
  id TEXT PRIMARY KEY, unlocked_at TEXT NOT NULL, day TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS failure_fingerprints (   -- 创新点 1
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  problem_id INTEGER NOT NULL, tag TEXT NOT NULL,
  evidence TEXT, source TEXT NOT NULL,               -- rule|coach
  day TEXT NOT NULL, created_at TEXT NOT NULL
);
```

XP 规则（只奖不罚）沿用 v2 表，**新增长期源**（v2 的曲线做完题库就饱和：满 88 题 ≈ 2.6k XP，而 10 级累计需 3060 XP）：

| 事件 | XP |
| --- | --- |
| 每日任务环全清 | +30 |
| 同 tag 连续 2 次通过（失败指纹降权） | +15 |
| 10 级后每级所需 XP 递增 +120（prestige 循环） | — |

`store.grant_xp(kind, ref_id, day)`：`INSERT OR IGNORE`，返回是否新发。

### 5.3 徽章（12 枚）

沿用 v2 定义与解锁检查点（finish/submit/run 后调用 `store.check_achievements()`），新增返回 `new_badges` → 金色 toast。`century`（100 次全过）统计 `code_runs`，P0 已保证考试/面试不写该表。

### 5.4 API

- `GET /api/state` 的 `motivation` **只放 6 个数字**：`{xp, level, level_xp, level_need, streak, badge_count}` + `today:{done,planned}`。
- 新端点：`GET /api/badges`、`GET /api/week`（口径 = `sessions ∪ exams ∪ interviews`，统一在 `store.activity_by_day()`）、`GET /api/topics`、`GET /api/reports`。
- `POST /api/finish`、`/api/run` 响应加 `xp_gained, new_badges, fingers[]`。

### 5.5 专题（P2）

- 两种视图共用渲染：`?tag=group`（studyplan 分组）与 `?tag=official`（`problem["topics"]` 官方标签）。多标签题在每个标签下出现。
- `POST /api/plan/add {problem_id}`：先 `ensure_day()`（今日无计划先生成），再 `planner.add_extra_item()`。
- **v2 未覆盖的三个坑（v3 修）**：
  1. `rebuild_day` 会删整日计划（`planner.py:148`），且设置保存后前端自动 `/api/replan`（`dashboard.py:1102`）→ `delete_day_plan` 必须保留 `kind='extra'` 与非 `pending` 行；
  2. `slot_limit_minutes` 把非 `new` 一律当 review（`planner.py:161`）、`App.state` 的 limit 同理（`server.py:151` 一带）→ 显式 `extra` 分支（25 分钟）；
  3. 同题当天已有任何 kind 的计划行时拒绝重复添加。
- 自由练习（不经计划直接写代码）全过发 `topic_ac` XP。

---

## 6. P5 教练（dsh 优先）

### 6.1 后端三层

```
CoachProvider (hot100/coach/provider.py)
 ├─ DshCoach      : 子进程调 dsh（DeepSeek Harness），key 由 dsh 自己管
 ├─ HttpCoach     : stdlib urllib → OpenAI 兼容 /chat/completions（DeepSeek）
 └─ LocalCoach    : 规则版（ast 统计 + 用例归因），永远可用、零成本
```

配置：`coach_provider("auto")`、`coach_base_url`、`coach_model("deepseek-chat")`、`coach_timeout(60)`、`coach_dsh_cmd("dsh")`、`coach_dsh_args`、`coach_max_per_day(10)`。

- `auto` 解析顺序：检测到 `dsh` 可执行 → `DshCoach`；否则有 key → `HttpCoach`；否则 `LocalCoach`。UI 明确显示当前后端。
- **dsh 接入按「命令模板 + JSON 契约」设计，不硬编码 CLI**：`coach_dsh_cmd` + `coach_dsh_args` 可配，默认尝试非交互模式（`dsh` 的 preview 期 CLI 参数未定，见 §9 待办 spike）。prompt 通过临时文件传入，避免命令行长度与转义问题。
- 统一契约：后端返回 `{content: markdown, adjustments: {...}|None, fingers: [tag,...]}`；解析失败则 `content` 退化为原始文本、`adjustments=None`。单飞锁（同一时刻只跑一个请求）+ 60s 超时。
- key 安全（v2 的 A9 硬伤）：**key 不进 `data/config.json`**，写 `data/secrets.json`（0600），并从 git 排除；`GET` 只回 `coach_key_mask`/`coach_key_set`。dsh 后端下我方不存 key。

### 6.2 缓存与端点

```sql
CREATE TABLE IF NOT EXISTS coach_reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL, ref_key TEXT NOT NULL,
  model TEXT NOT NULL, provider TEXT NOT NULL,
  content TEXT NOT NULL, adjustments TEXT, fingers TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(kind, ref_key)
);
```

- `POST /api/coach/review {problem_id, mode, code}`：`ref_key = problem:mode:sha256(code)[:16]`，命中缓存直接返回（不重复花钱）。prompt 含：题面/IO/约束 + 用户代码 + 本次运行指标 + **失败用例编号与输入规模**（v2 缺，导致点评泛泛）。输出四节：代码质量 / 思路点评 / 3 条训练建议 / ```` ```json {"adjustments":{...},"fingers":[...]} ````。
- `POST /api/coach/report {kind:"exam"|"interview", id}`、`POST /api/coach/followups {interview_id}`。
- `POST /api/coach/apply {fields}`：白名单 `{focus_tags, daily_target, deadline, exam_cadence, max_new_per_day}`，前端逐字段确认后调用，写 `meta` 并 replan。
- 每日上限 `coach_max_per_day`，超出走 `LocalCoach` 并在 UI 标注。

### 6.3 页面

工作台右栏 tab `[用例结果] [教练点评]`；考试/面试结束页「生成复盘报告」；复盘报告 tab：周曲线（内联 SVG）+ 报告列表 + 徽章墙 + 失败指纹分布。

---

## 7. 创新点（v3 落地定义）

### 7.1 失败指纹驱动的复习（Failure-Fingerprint SRS）

- 规则路（离线）：失败用例集中在空/单元素/极值 → `boundary`；`timeout` 或 `max_ms > 5×avg` → `complexity`；AST 循环嵌套 ≥3 且用了 `sorted` → `complexity`；节点类报错 → `api_misuse`；输出解析失败 → `format`；错在题面语义（教练路）→ `pattern_miss`。
- 模型路：dsh 教练在 JSON 片段里回 `fingers`。
- 调度升级：复习不仅按题，还按 tag —— `due_tag(tag)` 生成同类迁移题插今日 extra 位；同 tag 连续 2 次通过 → 降权 +15 XP。
- 教练的调整建议直接读 `SELECT tag, COUNT(*) FROM failure_fingerprints GROUP BY tag`，把「训练进度和目标」建立在数据上（v2 只做泛化建议）。
- 成本：`hot100/fingerprint.py` ≈ 250–300 行 + 1 张表。

### 7.2 三段式面试评分（口述 → 手撕 → 追问）

- 口述 60–180s（逻辑锁在 `interviews.outline_text`）→ 手撕（`first_run_sec`/`runs`/一次通过率）→ 追问（`interview_qa`）。
- `impression = 0.3*口述完整度 + 0.4*一次成型 + 0.3*追问应答`；无 key 时用关键词+时间规则打分。
- 差异化：**别的平台测「题做出来了吗」，这里测「面试官会不会给你过」**，且完全离线可用。

---

## 8. 仓库与提交规范（Work100）

- 远端：`https://github.com/Sowieeeeeee/Work100`，主干 `main`。
- 本目录 `leetcode-hot100-trainer/` 独立成一个 git 仓库（工作区根 `C:/Workspace` 属于另一个 Bitbucket 仓库，且该目录当前未被其跟踪，避免交叉污染）。
- 分支：`main`（可发布）+ `feat/p1-motivation`、`feat/p3-exam` 等功能分支；功能完成 → 合回 `main`。
- 阶段标签：`v0.1.0-p0`、`v0.2.0-p1`…`v0.6.0-p5`；`CHANGELOG.md` 每阶段一条。
- **Conventional Commits**：`<type>(<scope>): <subject>`（subject ≤ 50 字符，中文正文允许）
  - type：`feat fix refactor test docs chore perf`
  - scope：`p0 judge exam interview coach ui store planner materials tools dataset repo`
  - 示例：`refactor(p0): 抽出 problem_source 统一题源`
- 每个提交前必须：涉及判题/材料 → `python -m tools.verify_judge` 0 失败；涉及前端 → headless 探针零报错。
- 禁止提交：`data/state.db`、`data/config.json`、`data/secrets.json`、`data/online_cache.json`、`logs/`、`__pycache__/`、`sessions/`。
- **自动提交**：每完成一个功能单元（一个 P 阶段的一个可验收子项）立即提交，不堆积。

---

## 9. 风险与待办

| 风险 | 缓解 |
| --- | --- |
| 池题用例期望错（无独立 oracle） | §3.2 抽样审计 20 题 + UI 标注用例来源 + 闸门淘汰 |
| io 推断静默错判（`build_dataset.py:477` 默认 `int`） | 白名单 + 未命中即淘汰 + `to_acm_input` 生成期断言 |
| 考试泄题 | 不下发 expected；`/run` 只回计数与失败编号 |
| 考试污染练习数据 | `run_detached` 不落盘、不写 `code_runs` |
| `extra` 计划项被 replan 删 | `delete_day_plan` 保留 extra/非 pending |
| dsh preview CLI 未定 | §6.1 命令模板可配 + `tools/coach_selftest.py` + 缺 dsh 自动降级 |
| key 泄漏 | `data/secrets.json` + gitignore + 掩码回显 + 日志脱敏 |
| 单文件仪表盘膨胀（58 KB → 预计 120 KB+） | P0 的 `renderActiveTab` 分派 + 每 tab 独立 section 块，禁止跨 tab 引用 |

待办 spike（P5 开工前 1 天）：确认 dsh 非交互调用方式与输出格式；确认 `deepseek-chat` vs V4.1 系列 model id。

---

## 10. 阶段顺序与总验收

```
P0（必须）→ P1 → P2 → P3 → P4 → P5
```

每阶段结束：

```bash
python -m tools.verify_judge     # 88/223/0
python -m tools.verify_p0        # 新增：题源注册表 + 池题最小建池 → 判题 → 材料生成
python -m tools.verify_exam      # P3 起
python -m tools.verify_interview # P4 起
```

外加：桌面 1440 / 移动 390 截图、控制台零报错、`/api/state` < 40 KB、考试期间轮询不重绘考试壳、`git status` 干净（无 secrets/无 db）。
