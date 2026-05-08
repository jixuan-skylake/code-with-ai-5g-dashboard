# 🤖 AI Coding Agent 交互日志

> 比赛硬核交付物 · Code with AI 海选赛
>
> 主用 Agent：**Claude Code (Opus 4.7, 1M context)**
> 辅助：本机 macOS 终端、headless Chromium (Playwright Python) 自动截图。
>
> 本日志保留真实派工与执行轨迹，**未伪造任何外部对话**。

---

## 0. Codex 监督 / 调度日志（用户 ↔ Codex）

本节由 Codex 在 Claude Code 完成主体构建后追加，记录 Codex 作为总调度与验收者的真实交互过程。

### 0.1 用户原始目标

用户要求 Codex 按既有工作流推进「Code with AI 海选赛 · 5G 信号可视化看板挑战」：

- 使用可见的 Claude Code 终端执行主要工程实现，不使用后台 `claude -p`。
- 在 `/Users/skylake/Desktop/AI-Match` 中完成 Streamlit 看板、截图、测试、README、AI_PROMPTS 和 GitHub 公开仓库。
- 完成基础与进阶关卡，并按比赛要求推送 `basic-done` / `advanced-done` 标签。
- Codex 负责监督、审查、验收和最终交付；非紧急情况不中断 Claude。

### 0.2 Codex 定位并派工给可见 Claude Code

Codex 按用户的 Claude 调度规则执行了以下只读定位步骤：

```bash
ps -axo pid,ppid,stat,etime,command | rg 'claude --dangerously-skip-permissions|claude($| )'
ps -p 31401 -o pid,ppid,tty,stat,etime,command
lsof -a -p 31401 -d cwd
osascript -e 'tell application "Terminal" to get the tty of every tab of every window'
```

确认目标会话为：

- PID：`31401`
- TTY：`/dev/ttys004`
- 工作目录：`/Users/skylake/Desktop/AI-Match`
- Terminal：`window 1 / tab 1`
- 标题：Claude Code

随后 Codex 用 Terminal AppleScript 的 `do script ... in tab 1 of window 1` 把完整比赛任务书发送给该 Claude Code 会话，并在没有进入执行状态时补发一次 Return。成功信号是 Claude Code 进入 `Thinking / tool call` 状态。

### 0.3 过程中的用户补充要求

用户在 Claude 工作期间追加了三条要求，Codex 均记录并纳入最终验收：

1. 「不需要，你等待claude工作吧，不要过份干预」
   - Codex 改为低频观察，只在 Claude 完成关键阶段后读取状态，不再追加实现指令。

2. 「后面的验收也是需要你去打开浏览器查看的哈，不要忘记了」
   - Codex 将浏览器真实验收加入最终检查项：本地启动 Streamlit，打开浏览器观察页面，而不是只信任测试或截图。

3. 「AI_PROMPT.md文件在他写完以后你也要继续写入你的，把我们的对话记录加在上面」
   - Claude 写完本文件后，Codex 追加本节，记录 Codex 的派工、等待、监督、浏览器验收计划和最终启动说明。

4. 「你需要告诉我怎么启动这个项目，我也需要自己去浏览器打开运行查看效果」
   - Codex 将启动方式写入最终交付说明：`cd /Users/skylake/Desktop/AI-Match && streamlit run app.py`，浏览器访问 `http://localhost:8501`。

### 0.4 Codex 监督节点摘要

Codex 在不干扰 Claude 主流程的前提下观察到以下关键节点：

- Claude 成功拉取比赛数据，并识别 CSV 含 `Download_Mbps` 字段。
- Claude 先完成基础版提交；最初因用户任务文本误写同步创建了 `base-done` 与 `basic-done`，后续用户更正后正式口径只保留 `basic-done`。
- Claude 完成进阶版：sidebar 联动筛选、3D 柱状地图、KPI、图表切换、CSS 动效、测试模块。
- Claude 执行 `pytest`，结果为 `32 passed`。
- Claude 启动 Streamlit，`/_stcore/health` 返回 HTTP 200。
- Claude 生成 3 张运行截图到 `docs/screenshots/`。
- Claude 新建公开仓库 `jixuan-skylake/code-with-ai-5g-dashboard`，推送 `main` 和全部比赛标签。

### 0.5 Codex 后续验收计划

Claude 完成后，Codex 继续执行以下独立验收，不把 Claude 的完成报告直接当作最终结论：

- 复查 `git status`、remote、提交和 tag。
- 追加本 Codex 监督日志并单独提交到 `main`，不移动已经用于比赛计时的 `advanced-done` tag。
- 本地重新运行 `pytest`。
- 本地启动 `streamlit run app.py`。
- 通过浏览器打开本地页面，检查 sidebar、KPI、3D 地图、图表和交互筛选是否可见可用。
- 把启动命令和仓库地址在最终回复中明确给用户。

### 0.6 本地访问问题排查

用户反馈浏览器里 `localhost` 显示「无法访问此网站」。Codex 排查后确认：

- 当时没有任何 `streamlit run app.py` 进程在运行。
- `8501` 和 `8765` 端口都没有监听者。
- 日志中的 `Stopping...` 来自验收脚本结束时主动停止临时 Streamlit 服务。

Codex 随后在一个新的可见 Terminal 窗口中启动：

```bash
cd /Users/skylake/Desktop/AI-Match
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
streamlit run app.py --server.port 8501 --server.address 127.0.0.1 --browser.gatherUsageStats false
```

验证结果：

- `curl http://127.0.0.1:8501/_stcore/health` 返回 HTTP 200。
- `lsof` 显示 Python 正在监听 `127.0.0.1:8501`。
- 使用 `DASHBOARD_URL=http://127.0.0.1:8501/ python3 scripts/take_screenshots.py` 成功重新生成 3 张截图。

最终给用户的本机访问地址为：`http://127.0.0.1:8501`。

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

> 后续更正：用户说明 `base-done` 是误写，基础关卡正式 tag 应为
> `basic-done`。因此最终 README 和远端 tag 列表以 `basic-done` /
> `advanced-done` 为准；多余的 `base-done` 已移除。

---

## 2. Claude Code 自检计划（执行前）

Claude Code 在收到指令后没有把多个独立步骤揉成一次回复，而是拆成可校验的阶段：

1. **建立事实**：`ls`、`git status`、`gh auth status`、Python 工具链版本，确认空目录 / 未初始化 git / `gh` 已绑定 `jixuan-skylake` / Python 3.9.6 可用。
2. **拉数据**：把 `besa-2026/code-with-ai-contest` 浅克隆到 `/tmp/code-with-ai-contest-<ts>/`，**不污染** Desktop 其他目录。审视 CSV 列：`Latitude / Longitude / CellID / Band / RSRP_dBm / SINR_dB / TerminalType / Download_Mbps`，500 行。
3. **先拆模块再写 UI**：把 RSRP 调色、Sidebar 筛选、3D 柱高归一化等业务逻辑放入 `src/` 纯函数，避免在 Streamlit 里堆代码导致单测难写。
4. **基础关卡先发版**：让 `app.py` 在不带 sidebar / 3D 的最小可玩状态下提交一次，正式打 `basic-done`。
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
5. `git init -b main` → `git add` 白名单 → 第 1 次 commit，打 `basic-done`
   tag。早期因任务文本误写曾临时创建 `base-done`，后续按用户更正移除。
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

## 8. 后续修复：拖动筛选时未实时更新（用户后续追加要求）

### 8.1 用户的 bug 报告（原文）

> 用户刚刚发现一个交互缺陷：进阶关卡要求『拖动筛选器时，右侧地图和图表必须实时更新』，但当前 app.py 使用 Streamlit 原生 st.slider，实际行为是在松开拖动条以后才 rerun 更新地图/图表。

### 8.2 系统化根因分析

不直接猜，先把 Streamlit 的事件模型摸清：

- `st.slider` 在前端是 BaseWeb 的 `Slider` React 组件。
- 该组件只在 **change-end**（鼠标 mouseup / blur）时通过 WebSocket 发送
  `widgetStateRequest` —— 这条消息才是触发 Python 脚本 rerun 的信号。
- 拖动过程中虽然组件内部 state 在变，但是 **不会** 通过 WebSocket 通知
  Python 端，因此 map / KPI / charts 在松手前都看不到中间值。
- 这是 Streamlit 已知行为；社区里有大量 issue（仍未上游修复），通常推荐
  做法是写一个 custom component。

### 8.3 修复方案

写一个本地 Streamlit custom component，绕过 BaseWeb 的事件契约：

- `frontend/live_range_slider/index.html`：纯 vanilla JS / CSS。两个
  `<input type="range">` 叠在一条轨道上做双滑块；监听 `input` 事件
  （拖动过程中每帧都会触发，区别于 `change` 仅 mouseup 才触发）。
- 通过 `window.parent.postMessage({ type: 'streamlit:setComponentValue', ... })`
  把当前 `{low, high}` 直接推给 Streamlit 父窗口。Streamlit 收到后立刻
  重新执行 Python 脚本，下游的 `apply_filters / pydeck / KPI` 自然跟着刷新。
- `src/components/live_range.py`：用 `streamlit.components.v1.declare_component(path=...)`
  把上面的 HTML 注册为可重复调用的组件，并提供 `_normalize_range`
  容错函数（处理 dict / list / tuple 三种 payload，clamp 到合法范围，自动
  交换反向边界）。
- 不依赖任何外部 CDN，所需 JS / CSS 全部入仓库。

### 8.4 TDD：先红后绿

新增 `tests/test_live_range.py`（15 条测试），分两段：

- **Python 契约**：`_normalize_range` 处理 None / dict / list / tuple /
  字符串数字 / 反向边界 / clamp 越界 / 非法类型。
- **HTML 契约**（防回归）：直接对 `frontend/live_range_slider/index.html`
  的文本做正则检查，断言它仍然 `addEventListener('input', ...)`、仍然
  `streamlit:setComponentValue` / `streamlit:componentReady`、且不引入任何
  外部 `https://` / `http://` URL。

第一次 `pytest tests/test_live_range.py` 因为 `src.components` 不存在直接红
（`ModuleNotFoundError`），随后 implement → 15 全绿。

### 8.5 端到端验证（Playwright）

写 `scripts/verify_live_drag.py`：

1. 在浏览器全局注入一个 `setComponentValue` 计数器。
2. 通过 Playwright 找到 `live_range_slider` 的 iframe。
3. **不**用真实鼠标拖拽，而是脚本式连续 `dispatchEvent('input')` 8 次，
   覆盖 RSRP 滑块下界从 -130 到 -95；之间从不 `change`。
4. 检查 `setComponentValue` 消息计数 ≥ 5（通过去重后实际 ≥ 5 即可），
   并对比 KPI「采样点」从 baseline 到 drag 结束的差异是否 > 0。
5. 落一张 `docs/screenshots/04_live_drag_proof.png`。

实测结果：

```
baseline messages=0 KPI(采样点)=500
setComponentValue messages during drag: 6
KPI(采样点) after drag: 269 (was 500)
[PASS] live drag updates confirmed end-to-end
```

→ 6 条中段 setComponentValue 消息送达 + KPI 从 500 跌到 269（其它 KPI 也
随之变化），证明 mouseup **之前** 就完成了多次 Python rerun，bug 修复成立。

### 8.6 涉及改动

| 类型 | 路径 |
|---|---|
| 新增 | `frontend/live_range_slider/index.html` |
| 新增 | `src/components/__init__.py` |
| 新增 | `src/components/live_range.py` |
| 新增 | `tests/test_live_range.py` |
| 新增 | `scripts/verify_live_drag.py` |
| 新增 | `docs/screenshots/04_live_drag_proof.png` |
| 改动 | `app.py`（导入 `live_range_slider`，替换 RSRP / Download 两处 `st.slider`，sidebar caption 增加说明）|
| 改动 | `docs/screenshots/01_overview_3d.png` / `02_2d_scatter.png` / `03_filter_narrowed.png`（重新截图，沿用新滑块视觉）|
| 改动 | `README.md` / `AI_PROMPTS.md`（本节）|

### 8.7 Tag 策略

按用户更正，基础关卡正式 tag 是 `basic-done`，不是 `base-done`。因此最终
远端只保留两个比赛计时 tag，并且不移动它们：

```
basic-done      → 675b099  （未变）
advanced-done   → e170d58  （未变）
```

只在 `main` 分支上加新提交并推送，让评委如果想看「比赛计时点的代码」
和「修复后的代码」分别对应哪个 commit 都很清楚。

后续 Codex 复核时删除了本地与远端多余的 `base-done`，避免 GitHub tag
页面和 README 里出现错误打卡口径。

### 8.8 验收命令（在已克隆仓库根目录下）

```bash
pytest                                  # 47 passed
streamlit run app.py --server.address 127.0.0.1 --server.port 8501 &
DASHBOARD_URL=http://127.0.0.1:8501/ python3 scripts/verify_live_drag.py
# 期望输出：[PASS] live drag updates confirmed end-to-end
```

---

## 9. 后续修复 #2：拖动结束后 slider 手柄弹回初始值

### 9.1 用户的 bug 报告（原文）

> 用户发现实时 slider 的第二个 bug：拖动 RSRP 或下载速率双滑条时，数据
> 确实按中间值更新，但滑块手柄会在 rerun 后弹回初始最大值/初始位置。
> 例如把下载速率最大值拖到 700 多，地图/柱状图按 700 多过滤了，但
> slider 文案/手柄又显示 998 最大值。

### 9.2 系统化根因分析

把 §8 修好的链路再过一遍，找出弹回点：

1. 用户拖动 → iframe `onInput` → `setComponentValue({low:0, high:700})`。
2. Streamlit 触发 rerun，Python 脚本从头执行。
3. `app.py` 调 `live_range_slider("速率", value=(speed_min, speed_max), key="speed_live")`
   ——`value` 永远是固定的 `(0, 998)`！
4. wrapper 把 `low=0, high=998` 当 args 传给 `_component_func`。
5. `_component_func` 把 `streamlit:render(args.low=0, args.high=998)` 投递给 iframe。
6. iframe `applyArgs` 不带条件地执行 `loEl.value = args.low; hiEl.value = args.high`，
   把刚被用户拖到 700 的输入框写回 998 → **手柄弹回**。
7. 与此同时 `_component_func` 返回 `{low:0, high:700}`（用户最新值）；
   `_normalize_range` 给 Python 端的 `(0, 700)`，下游 `apply_filters` 用 700 过滤。
   这就是「数据按 700，滑块显示 998」的两层不同步。

关键之处：步骤 4 拿到 `args.low/high` 时，wrapper **还没**「读到」用户的
最新值——`_component_func` 必须先调用才能拿到返回值。看似无解。

突破口：Streamlit 的 widget 协议会**在 rerun 启动前**就把 keyed 组件的
最新 commit 值塞进 `st.session_state[key]`（custom component 走的也是
`register_widget` 这条公共路径）。所以在调 `_component_func` 之**前**就
能从 `st.session_state["speed_live"]` 里拿到 `{low:0, high:700}`，把它当
`low/high` 传出去就行。

第二层加固：即便 Python 把正确的 args 送回去，万一 rerun 落在用户**正
在拖**的中间帧（mousemove 速率 ≥ 60Hz，rerun 也很快），iframe 仍会用
args 写回 input.value，造成 thumb 抖动。所以 JS 侧再加一道防御：当
`dragging=true` 时跳过 `applyArgs` 的 input.value 写入。

### 9.3 修复

| 文件 | 改动 |
|---|---|
| `src/components/live_range.py` | 新增纯函数 `_resolve_initial_value(prior, default_value, min, max)`：prior 优先、bounds 自动 clamp、不修改原值。`live_range_slider` 在调 `_component_func` 之前先 `st.session_state.get(key)` 拿 prior，传给 `_resolve_initial_value` 决定要送 iframe 的 `low/high` |
| `frontend/live_range_slider/index.html` | 加 `dragging` 状态变量，监听 `pointerdown / mousedown / touchstart / pointerup / mouseup / touchend / blur`（含 window 级，处理「鼠标拖出 iframe 后释放」），`applyArgs` 中包一层 `if (!dragging) { loEl.value = args.low; hiEl.value = args.high; }` |
| `tests/test_live_range.py` | 新增 6 条断言：`_resolve_initial_value` 的 prior-wins、no-prior-uses-default、no-prior-no-default-uses-full-range、prior-clamped-when-bounds-shrink、prior-accepts-tuple-shape；HTML 文本里必须出现 `dragging` + `pointerdown\|mousedown` |
| `scripts/verify_live_drag.py` | 第 3 项断言：drag 完成后重新定位 iframe，读 `loEl.value / hiEl.value`，对比 `window.__sliderMessages` 里最后一条 payload，差值 ≤ 1.5（slider step 容差）才算通过 |

### 9.4 TDD 红→绿

```
$ pytest tests/test_live_range.py
ImportError: cannot import name '_resolve_initial_value' from 'src.components.live_range'

# 实现 _resolve_initial_value + dragging 防御后再跑：
$ pytest tests/test_live_range.py
21 passed in 0.20s

$ pytest
53 passed in 0.41s   # 原 47 + sticky 6 条
```

### 9.5 端到端 Playwright 验证

```
$ DASHBOARD_URL=http://127.0.0.1:8501/ python3 scripts/verify_live_drag.py
baseline messages=0 KPI(采样点)=500
setComponentValue messages during drag: 6
KPI(采样点) after drag: 269 (was 500)
final iframe handles: lo=-95 hi=-70
last setComponentValue payload: {'low': -95, 'high': -70}
proof screenshot -> /Users/skylake/Desktop/AI-Match/docs/screenshots/04_live_drag_proof.png
[PASS] live drag updates confirmed end-to-end (input events + KPI rerun + iframe handle stays synced)
```

三项契约同时通过：① ≥ 5 条 `setComponentValue`；② KPI 500 → 269；
③ iframe 手柄值 `(-95, -70)` 与最后一次推送 `{low: -95, high: -70}`
**完全一致**。手柄不再弹回。

### 9.6 Tag 策略（同 §8）

`basic-done` / `advanced-done` 计时 tag 仍指向比赛原始 commit，未移动；
本次只在 `main` 上加一条新提交。

```
basic-done    -> 675b099  （未变）
advanced-done -> e170d58  （未变）
HEAD          -> <new>    （sticky-state 修复）
```

---

*— Claude Code (Opus 4.7) · 2026-05-08*
