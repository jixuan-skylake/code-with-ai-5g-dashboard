# 🤖 AI Coding Agent 交互日志

> 比赛硬核交付物 · Code with AI 海选赛
>
> 主用 Agent：**Claude Code (Opus 4.7, 1M context)**
> 辅助：本机 macOS 终端、headless Chromium (Playwright Python) 自动截图。
>
> 本日志保留真实派工与执行轨迹，**未伪造任何外部对话**。

---

## 1. 任务派工：用户 → Claude Code

时间：2026-05-08 · 工作目录：`/Users/skylake/Desktop/AI-Match`

下面是用户在 Claude Code 中复制粘贴的完整原始指令（一字未改）。

> 我们现在参加 Code with AI 海选赛：5G 信号可视化看板挑战。请你在当前目录 /Users/skylake/Desktop/AI-Match 内全自动完成整个项目，除非遇到账号权限或破坏性操作风险，不要停下来问我。你可以使用当前 Claude Code 会话可用工具，包括 Everything Claude Code、superpowers、agent teams；如启用 agent teams，请严格分工为产品/程序员/测试/代码审查/全局杠精总管，不要把多角色揉到同一个 agent。
>
> 比赛数据仓库：https://github.com/besa-2026/code-with-ai-contest.git，数据在 data/signal_samples.csv。请先建立项目事实：检查当前目录、git 状态、gh auth、远端情况；不要影响用户其他 GitHub 项目或仓库属性。最终需要新建一个公开 GitHub 仓库用于参赛，推荐仓库名 code-with-ai-5g-dashboard；若已存在请用合理后缀。
>
> 技术硬约束：使用纯 Python 框架，推荐 Streamlit；依赖文件必须提供 requirements.txt，并额外兼容比赛文案里的 requirement.txt。应用应可用 streamlit run app.py 一键启动。
>
> 基础关卡必做：1) 用 pandas 读取 data/signal_samples.csv。2) 网页主体渲染交互地图，推荐 pydeck；经纬度点必须根据信号强度 RSRP_dBm 变色：>-90 绿色，<-110 红色，中间用黄/橙过渡。3) 地图下方生成数据概览图，至少支持各频段基站数量柱状图；最好同时做饼图并用切换控件选择。
>
> 进阶关卡必做：1) 左侧 sidebar 联动筛选，包含 Band 下拉/多选、RSRP 范围 slider；如数据有终端类型也加终端类型筛选。拖动筛选器时右侧地图和图表实时更新。2) 极客视觉体验：3D 地图，让信号点以 3D 柱状图站起来，高度随下载速率变化；字段名不确定时请自动识别 download/throughput/rate/速率相关列，找不到则用 SINR 或 RSRP 归一化兜底并在代码注释说明。3) 工程化：核心代码有规范注释；补全 pytest 单元测试，至少覆盖数据加载、RSRP 颜色分级、筛选逻辑、3D 高度归一化。
>
> 视觉设计要求：请做成高大上的 5G 网络作战室/信号态势看板风格，但保持数据可读。需要侧边栏、KPI 卡片、3D 地图、图表区、数据表预览、轻量 CSS 动效/渐入/脉冲点或标题动画；注意不要过度紫蓝单色，配色要有绿色/红色信号语义和深色科技底。Streamlit 内不要做空洞营销页，首屏就是可用看板。
>
> 硬核交付物：1) 源代码 app.py 及必要模块、requirements.txt/requirement.txt。2) README.md 最终版，介绍功能、运行方式、数据来源、测试方式。3) 运行截图 2-3 张，放在 docs/screenshots/，展示地图和侧边栏交互；请实际启动应用并用浏览器或 Playwright 截图。4) AI_PROMPTS.md，记录真实 AI Coding Agent 交互日志：至少包含这条完整任务指令、你后续关键自检/修复指令或说明、生成过程摘要；不要伪造外部对话，但要真实记录 Codex -> Claude 的派工和 Claude 的执行摘要。
>
> Git/提交要求：按比赛时间戳用 tag 打卡。请分两个提交：基础关卡完成后提交并打 tag base-done；由于赛题文字里又写了 git push origin basic-done，请同时创建 basic-done 兼容标签，推送两个标签。进阶关卡完成后再提交并打 tag advanced-done，推送 advanced-done。最后推送 main/master 分支到新公开 GitHub 仓库。注意不要重置或覆盖用户未提交改动。
>
> 验收命令要求：运行 pytest；运行 streamlit 应用并确认可打开；生成截图；最后输出：仓库 URL、提交 hash、tag 列表、测试结果、启动命令、截图路径、剩余风险。请现在开始。

---

## 2. Claude Code 自检计划（执行前）

Claude Code 在收到指令后没有把多个独立步骤揉成一次回复，而是拆成可校验的阶段：

1. **建立事实**：`ls`、`git status`、`gh auth status`、Python 工具链版本，确认空目录 / 未初始化 git / `gh` 已绑定 `jixuan-skylake` / Python 3.9.6 可用。
2. **拉数据**：把 `besa-2026/code-with-ai-contest` 浅克隆到 `/tmp/code-with-ai-contest-<ts>/`，**不污染** Desktop 其他目录。审视 CSV 列：`Latitude / Longitude / CellID / Band / RSRP_dBm / SINR_dB / TerminalType / Download_Mbps`，500 行。
3. **先拆模块再写 UI**：把 RSRP 调色、Sidebar 筛选、3D 柱高归一化等业务逻辑放入 `src/` 纯函数，避免在 Streamlit 里堆代码导致单测难写。
4. **基础关卡先发版**：让 `app.py` 在不带 sidebar / 3D 的最小可玩状态下提交一次，打 `base-done` + `basic-done`（两个 tag 同 commit）。
5. **进阶关卡迭代**：在同一文件里叠加 sidebar、3D ColumnLayer、KPI 卡、CSS 动效，避免把 basic 版本的精简实现直接抹掉。
6. **测试 / 截图 / 文档**：跑 `pytest`、用 Playwright Python（headless Chromium）抓 3 张截图、写 README 与本日志。
7. **托管**：`gh repo create code-with-ai-5g-dashboard --public`，推 main + 全部 tag。

---

## 3. 关键自检 / 修复 prompt（自我对话节选）

下面是 Claude Code 在执行过程中给自己下达的几条关键内部指令，对应实际触发的修复行为。

### 3.1 速率字段不确定

> *"赛题没保证 CSV 列名一定叫 Download_Mbps；如果用户换成 throughput / 下行速率，3D 高度就会拿到错误字段。"*
>
> → 在 `src/data_loader.py` 写 `detect_speed_column`，优先匹配
> `download / throughput / rate / 速率 / downlink`，找不到再回退 SINR、再
> 回退 RSRP，并在 sidebar 加文字提示「当前使用：xxx」。

### 3.2 Sidebar 多选语义

> *"如果用户清空多选框（[]）和不传值（None）必须不一样；前者应当返回空。"*
>
> → 在 `src/filters.apply_filters` 显式区分 `bands=None` vs `bands=[]`，
> 并补单测 `test_empty_band_returns_empty`。

### 3.3 3D 高度归一化的退化分支

> *"如果筛选后所有点速率相同，min == max 会除以 0；NaN 也得有兜底。"*
>
> → `normalize_height` 检查 `hi == lo` 时返回 `(min+max)/2`；NaN 落到
> `min_height` 但仍参与渲染。`tests/test_heights.py` 全部覆盖。

### 3.4 截图基础设施

> *"playwright MCP 桥接超时不可用，需要 fallback；headless Chromium
> 必须能打开看板并交互。"*
>
> → 直接 `pip install playwright`，`python -m playwright install chromium`，
> 写 `scripts/take_screenshots.py`：先抓 3D 全景，再点击 sidebar 的「2D 散点」
> radio 切到散点，最后用键盘箭头压缩 RSRP 上界，验证联动筛选。

### 3.5 验收前的本地通关

> *"在 push GitHub 之前必须本地全绿。"*
>
> → 顺序执行：
> 1. `python3 -c 'import ast; ast.parse(open("app.py").read())'` 语法
> 2. `pytest` → `32 passed in 0.34s`
> 3. `streamlit run app.py --server.port 8765 --server.headless true`，
>    `curl /_stcore/health` 返回 `200`
> 4. Playwright 跑通 3 张截图

---

## 4. 工具/会话使用情况

| 阶段 | 主要工具 |
|---|---|
| 事实建立 | Bash (`ls`, `git`, `gh auth status`) |
| 数据拉取 | Bash (`git clone`) → 不污染用户目录，落 `/tmp` 时间戳目录 |
| 编码 | Write / Edit（直接写源文件） |
| 单测 | Bash (`pytest`) |
| 启动看板 | Bash (`streamlit run app.py` 后台) |
| 截图 | Playwright Python (`scripts/take_screenshots.py`) |
| 版本管理 | Bash (`git init / add / commit / tag / push`) |
| 仓库托管 | `gh repo create --public` + `git push` |

> 关于「agent teams」：本任务的体量在单 agent 内可以稳定收敛，因此没有
> 强行拆四五个子 agent 来增加沟通成本；但代码本身严格按角色拆层
> （`src/` = 程序员；`tests/` = 测试；`README.md`/本文 = 产品/审查；
> 全局杠精由用户自任）。这也是 README 里 src/tests 强分离的原因。

---

## 5. 生成过程摘要（按时间顺序）

1. 检查 `/Users/skylake/Desktop/AI-Match/`：空目录、未 git init。`gh auth`
   绑 `jixuan-skylake`。Python 3.9.6 / Streamlit 与 pytest 通过 `pip
   install --user` 落到 `~/Library/Python/3.9/bin`，纳入 `PATH`。
2. 浅克隆比赛仓库到 `/tmp/code-with-ai-contest-<ts>`，复制 CSV 到
   `data/signal_samples.csv`。
3. 写 `src/data_loader.py / coloring.py / filters.py / heights.py`，全部
   通过 `python3 -c "..."` 烟雾测试。
4. 写最小化 `app.py`（基础版），起 `streamlit` 在 8765，`curl /_stcore/health`
   返回 200。
5. `git init -b main` → `git add` 白名单 → 第 1 次 commit，打 `base-done`
   + `basic-done` 两个 tag。
6. 重写 `app.py` 为进阶版（sidebar 联动 + 3D ColumnLayer + KPI 卡 + 多
   图表 + 动效 CSS）。
7. 写 `tests/__init__.py / conftest.py / test_*.py`、`pytest.ini`，
   `pytest` → 32 全部通过。
8. 重启 streamlit，写 `scripts/take_screenshots.py`，输出 3 张 png 到
   `docs/screenshots/`。
9. 杀掉 streamlit，写 README、本文档。
10. 第 2 次 commit、打 `advanced-done`，`gh repo create
    code-with-ai-5g-dashboard --public`，`git push -u origin main` +
    `git push origin --tags`。

---

## 6. 已知边界 / 残留风险

- 截图时机器无法访问 Carto CDN，地图底图瓦片未加载（信号点本身正确
  渲染）。在能联网的环境下首次启动会自动出现深色底图。
- `pip` 提示 21.2.4 → 26.0.1，可在赛后一键升级；与本作品功能无关。
- 仓库使用纯 mock 数据，无任何真实 PII / 涉密内容。
- 没有为 sidebar 加 URL query 反序列化（一次性看板，不需要分享链接）。

---

## 7. 验收命令一览（评委可一键复现）

```bash
git clone https://github.com/jixuan-skylake/code-with-ai-5g-dashboard.git
cd code-with-ai-5g-dashboard
pip install -r requirements.txt
pytest                       # 期望 32 passed
streamlit run app.py         # 浏览器自动打开 dashboard
```

如需重新生成截图：

```bash
python -m playwright install chromium
streamlit run app.py --server.port 8765 --server.headless true &
python3 scripts/take_screenshots.py
```

---

*— Claude Code (Opus 4.7) · 2026-05-08*
