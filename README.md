# 📡 5G 信号态势作战室

> Code with AI 海选赛 · 5G 信号可视化看板 · 进阶关卡作品
> 主仓库：https://github.com/jixuan-skylake/code-with-ai-5g-dashboard

把一份枯燥的 5G 路测样本（500 条 / 8 字段）转化为一个 **实时可交互、3D
可旋转、深色"作战室"风格** 的 Streamlit 看板。本作品同时覆盖比赛要求的
**基础关卡 + 进阶关卡** 全部硬性指标。

---

## ✨ 功能一览

### 基础关卡（`basic-done` / `base-done`）
- **pandas** 读取 `data/signal_samples.csv`（500 行 × 8 字段）
- **pydeck** 交互地图：每个采样点按 `RSRP_dBm` 信号强度变色
  - `> -90 dBm` → 绿色（优）
  - `-100 ~ -90 dBm` → 黄色（良）
  - `-110 ~ -100 dBm` → 橙色（中）
  - `< -110 dBm` → 红色（弱）
- 数据概览图：**各频段基站数量**，柱状图 / 饼图一键切换

### 进阶关卡（`advanced-done`）
- **左侧 Sidebar 联动筛选**（拖动过程中即时刷新地图 / KPI / 图表，**真正的实时**，不是 mouseup 才刷新 — 见 §「拖动实时更新修复」）
  - 频段 Band 多选
  - RSRP 范围 slider（dBm，自研 `live_range_slider` custom component）
  - 终端类型 TerminalType 多选（`Smartphone` / `CPE` / `IoT`）
  - 下载速率 `Download_Mbps` slider（自研 `live_range_slider`；也可智能识别
    `download` / `throughput` / `rate` / `速率` 关键词，找不到则回退至
    `SINR_dB` 或 `RSRP_dBm`）
- **3D 极客体验**：`pydeck.ColumnLayer` 让信号点站起来，柱高来自下载
  速率归一化（80–1500 m），颜色仍由 RSRP 决定。可旋转 / 缩放 / 悬停
  查看 tooltip。
- **作战室视觉**：暗色科技底 + 绿/红信号语义 + 渐变 KPI 卡 + 脉冲在线
  指示灯 + 标题 fade-in，全部纯 CSS（写在 `st.markdown` 里），无外部
  前端依赖。
- **多图联动**：频段柱状/饼图、终端类型环图、RSRP 直方图、RSRP×速率
  散点图，全部跟随筛选实时刷新。
- **工程化**
  - 核心逻辑拆到 `src/`（`data_loader / coloring / filters / heights`）
    四个纯函数模块，方便测试 & 复用。
  - 自研 Streamlit custom component `src/components/live_range.py` +
    `frontend/live_range_slider/index.html`（纯 vanilla JS / CSS，不依赖
    外部 CDN）解决 `st.slider` 不能拖动中实时回传的根因。
  - **47 条 pytest 单元测试** 100% 通过，覆盖：CSV 加载与列校验、RSRP
    分级与 NaN 兜底、Sidebar 多种筛选组合、3D 高度归一化的边界情况、
    `live_range_slider` 的值规整契约 + HTML 防回归。
  - 关键函数中文 + 英文注释齐全，遵循 `from __future__ import annotations`
    与类型提示。

---

## 🚀 运行方式（一键）

```bash
# 1. 安装依赖（兼容 requirements.txt 或赛题文案里写错的 requirement.txt）
pip install -r requirements.txt

# 2. 一键启动
streamlit run app.py --server.address 127.0.0.1
```

打开浏览器访问 `http://127.0.0.1:8501`（或 Streamlit 控制台输出的端口），
即可看到态势作战室主页。

如果 `http://localhost:8501` 显示「无法访问此网站」，请直接使用
`http://127.0.0.1:8501`。少数本机代理 / DNS 工具会改写 `localhost`，
而 `127.0.0.1` 会直连本机回环地址。

> 💡 主题已在 `.streamlit/config.toml` 内置为 dark；如果你的 Streamlit
> 版本默认浅色，请确保不要把它覆盖回 light。

---

## 🧪 测试

```bash
pip install -r requirements.txt   # 含 pytest
pytest                             # 期望输出：47 passed
```

测试文件位于 `tests/`：

| 文件 | 覆盖内容 |
|---|---|
| `tests/test_data_loader.py` | CSV 加载 / 列缺失 / NaN 行清洗 / 速率列自动识别（含中文关键词） |
| `tests/test_coloring.py`    | RSRP 四档分级，NaN 兜底，`attach_color_columns` 不修改原 df |
| `tests/test_filters.py`     | Band / RSRP / Terminal / Speed 单条与组合筛选，空多选语义 |
| `tests/test_heights.py`     | 端点映射、线性插值、常量退化、NaN 输入、非法 bound 报错 |
| `tests/test_live_range.py`  | 自研 `live_range_slider` 值规整契约 + HTML 防回归（`input` 事件、`setComponentValue`、不引外部 CDN） |

进阶端到端验证（需要先启动 Streamlit）：

```bash
streamlit run app.py --server.address 127.0.0.1 --server.port 8501 &
DASHBOARD_URL=http://127.0.0.1:8501/ python3 scripts/verify_live_drag.py
# 期望：6 条以上 setComponentValue 消息 + KPI 中段已变化 → [PASS]
```

---

## 📂 项目结构

```
AI-Match/
├── app.py                     # Streamlit 入口（进阶版）
├── requirements.txt           # 主依赖
├── requirement.txt            # 兼容赛题文案中的单数拼写
├── pytest.ini
├── .streamlit/config.toml     # 内置 dark 主题
├── src/
│   ├── __init__.py
│   ├── data_loader.py         # CSV 加载 + 列校验 + 速率列侦测
│   ├── coloring.py            # RSRP 四档调色（绿/黄/橙/红 + tier 标签）
│   ├── filters.py             # 联动筛选（band / rsrp / terminal / speed）
│   ├── heights.py             # 3D 柱高归一化（NaN 安全）
│   └── components/
│       ├── __init__.py
│       └── live_range.py      # 自研 Streamlit custom component（拖动实时回传）
├── frontend/
│   └── live_range_slider/
│       └── index.html         # 纯 vanilla JS/CSS 双滑块 + Streamlit bridge
├── tests/                     # 47 条 pytest 用例
├── data/signal_samples.csv    # 比赛数据（来源：besa-2026/code-with-ai-contest）
├── docs/screenshots/          # 验收截图（3 张 + 拖动实时刷新证据 1 张）
├── scripts/
│   ├── take_screenshots.py    # Playwright 截图脚本
│   └── verify_live_drag.py    # Playwright 端到端验证拖动实时更新
├── AI_PROMPTS.md              # AI Coding Agent 交互日志
└── README.md
```

---

## 🗃️ 数据来源

`data/signal_samples.csv` 来自比赛官方仓库
[besa-2026/code-with-ai-contest](https://github.com/besa-2026/code-with-ai-contest)
（`data/signal_samples.csv`），共 500 条模拟 5G 路测数据：

| 字段 | 类型 | 说明 |
|---|---|---|
| `Latitude` / `Longitude` | float | WGS-84 坐标（上海市区附近） |
| `CellID`        | int    | 5G 小区 ID |
| `Band`          | str    | 频段（n28 / n41 / n78 等）|
| `RSRP_dBm`      | float  | 参考信号接收功率（dBm） |
| `SINR_dB`       | float  | 信号干扰比（dB） |
| `TerminalType`  | str    | 终端类型 `Smartphone` / `CPE` / `IoT` |
| `Download_Mbps` | float  | 下载速率（Mbps），驱动 3D 柱高 |

---

## 📸 截图

放在 `docs/screenshots/`，对应 README 中的功能：

1. `01_overview_3d.png` — 默认 3D 柱状图全景，KPI + 多色信号柱站起来
2. `02_2d_scatter.png`  — 切换至 2D 散点模式
3. `03_filter_narrowed.png` — 拖动 RSRP 范围 slider 后，KPI / 地图 / 图表实时刷新
4. `04_live_drag_proof.png` — `scripts/verify_live_drag.py` 抓到的拖动「中段」状态：
   仅触发 `input` 事件、未触发 `change`，KPI 已从 500 → 269，证明 mouseup 之前
   已经完成多次 Python rerun（解决了原生 `st.slider` 的拖动延迟问题）。

> 已知运行时小提示：截图时机器无外网访问 Carto CDN，因此底图瓦片未加载；
> 信号点颜色与柱高均按代码逻辑正确渲染。在能访问外网的环境运行时，会
> 自动出现深色街道底图。

如需按默认 8501 端口重新生成截图：

```bash
DASHBOARD_URL=http://127.0.0.1:8501/ python3 scripts/take_screenshots.py
```

---

## 🤖 AI 交互日志

完整的 AI Coding Agent 交互记录见 [AI_PROMPTS.md](./AI_PROMPTS.md)，
包含原始任务指令、过程中的自检与修复、关键决策摘要。

---

## 🏷️ Git Tag 进度

| Tag | 含义 | Commit |
|---|---|---|
| `base-done` | 基础关卡完成（用户偏好用此名） | 见 `git log` |
| `basic-done` | 与 `base-done` 等价的兼容标签（赛题文案写法） | 同上 |
| `advanced-done` | 进阶关卡完成（含 sidebar / 3D / 测试 / 截图） | 见 `git log` |

```bash
git tag --list
# base-done
# basic-done
# advanced-done
```

---

## 🛠 拖动实时更新修复

进阶关卡硬性要求「拖动筛选器时右侧地图和图表必须实时更新」，但 Streamlit
原生 `st.slider` 只在 mouse-up 才会触发 Python rerun。本项目通过自研
custom component 解决：

| 问题 | 根因 | 修复 |
|---|---|---|
| RSRP / Download slider 拖动时 map / KPI / 图表不刷新 | `st.slider` 是 BaseWeb 组件，只在 change-end 发 `widgetStateRequest` | `frontend/live_range_slider/index.html` 用 `<input type="range">` + `'input'` 事件 + `streamlit:setComponentValue` postMessage 协议，每帧把当前值送回 Python |

可执行验证：

```bash
streamlit run app.py --server.address 127.0.0.1 --server.port 8501 &
DASHBOARD_URL=http://127.0.0.1:8501/ python3 scripts/verify_live_drag.py
# 期望：≥ 5 条 setComponentValue 消息 + KPI 中段变化 → [PASS]
```

完整设计与 TDD 过程参见 `AI_PROMPTS.md` §8。

---

## 🔧 常见问题

- **Q: `streamlit` 命令找不到？** 多数情况下 `pip install --user` 安装的脚本
  会落到 `~/Library/Python/3.x/bin`（macOS）或 `~/.local/bin`（Linux）。
  把它加入 `$PATH` 即可。
- **Q: 地图上没有底图？** 见上文「截图」章节，属于网络无法访问 Carto
  CDN 的环境表现。可以替换 `map_style` 为 Mapbox 自定义底图（需 token）。
- **Q: 数据被全部筛掉？** 看到「当前筛选条件下没有匹配的采样点」是
  `app.py` 的兜底空态——任何 sidebar 筛选都返回空时给出明确提示。
- **Q: 拖动还是只在松手才刷新？** 确认浏览器没有禁用 iframe / postMessage；
  也可以跑 `python3 scripts/verify_live_drag.py` 看是否输出 `[PASS]`。

---

License: 仅用于 Code with AI 海选赛参赛，数据归官方仓库所有。
