# Signalbox 阅读站（reading station）

这是一个把仓库里 canonical Markdown 投影成静态页面的阅读站。它沿用已选定的
telegraph-station 设计：深绿外框、暖色封面、接近白色的阅读纸、黄铜与穿孔纸带细节。
它是 source 展示，不是 proxy client、不是 installer，也不是任何 live 网络的健康证明。

## 安装与构建

需要 Git checkout、一个隔离的 Python 环境与仓库的开发依赖。`markdown-it-py` 只在 build 时使用，
不进入运行时；浏览器端只有 plain HTML/CSS/JS。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --requirement requirements-dev.txt
make site PYTHON=.venv/bin/python
```

输出写在被 `.gitignore` 忽略的 `build/site/`。不要编辑构建产物：那只是生成结果，
不是 source，也不是部署证据。构建脚本是 `scripts/build_site.py`。

## 本地预览

只在 loopback 上服务，默认端口 `8765`。如果该端口已被占用，用 `SITE_PORT` 覆盖，
例如改用 `8766` 时：

```bash
make site-serve PYTHON=.venv/bin/python
# 浏览器打开 http://localhost:8765/

# 端口被占用时：
make site-serve PYTHON=.venv/bin/python SITE_PORT=8766
# 浏览器打开 http://localhost:8766/
```

首页是 `index.html`。阅读页是仓库路径加 `.html`，例如
`docs/human/40-tailnet-vps-private-ingress.zh-CN.html`。刷新、deep link、浏览器返回与
中英对照链接都基于普通文件路径，在 project subpath 下也能工作，不需要 SPA fallback。

## GitHub Pages 发布与恢复

公开地址是 [Signalbox — 通信札记](https://indeliblevivi.github.io/signalbox-routing/)。
[Pages workflow](../.github/workflows/pages.yml) 在 `main` push 或手动 dispatch 时工作；
feature branch 的 PR 只运行 source gate，不发布。合入 `main` 会触发公开发布，
因此 merge 或手动重发都必须在相应的部署授权内进行。

仓库 Pages publishing source 使用 **GitHub Actions**，`github-pages` environment
只允许 `main` 部署；`main` 保留 repository branch protection。workflow 用 Python 3.13
安装 development requirements，
运行 `make verify`（包含 deterministic site build），确认 source worktree 未改变，
再上传唯一的 `build/site/` artifact。deploy job 依赖 build 成功，用 GitHub OIDC
与 Pages permission 发布；没有长期部署 secret，也不上传整个 checkout。

在已有授权内重新发布当前 `main`：

```bash
gh workflow run pages.yml --ref main
gh run list --workflow pages.yml --limit 5
gh run watch <run-id> --exit-status
```

失败时先查看该 run 的完整日志。build/verification 失败不会进入 deploy；修复 source
并经 PR 合入后重试。若需要恢复先前内容，以 revert PR 恢复已知良好的 source，
走相同 gate 和发布流程，不 force-push，也不手改 generated HTML。首次部署前没有旧站
可回退；部署失败本身不证明公开站点当前是哪一版。

成功 run 与 `github-pages` environment 记录 deployment；它们不替代线上读回。
发布后检查 HTTPS 首页、直接打开并刷新阅读页、中英与 anchor 链接、三张图和 CSS/JS、
工作台与收信匣。公开 `build-manifest.json` 的 `source_identity.commit` 应与该 deployment
的 source SHA 一致，`state` 应为 `exact-head`。current deployment 状态见
[current state](../docs/current-state.md) 与
[Pages runs](https://github.com/IndelibleVivi/signalbox-routing/actions/workflows/pages.yml)。

## 内容与 source 归属

- Article 内容全部来自 canonical Markdown，在 build 时读取。双语 pair 的注册表是
  `contracts/docs-pairs.json`：六组 `docs/human/` 章节 pair，加上根 `README.md`
  与 `README.zh-CN.md` 作为第七组。另有必要的 `docs/agent/`、`docs/reference/`、
  `docs/specification.md`、`examples/`、`schemas/README.md`，以及阅读站自己的
  `site/README.md`。
- 文章权威仍是它的 Markdown source，不是生成的 HTML。要改正文，改 source，
  然后重新构建。
- 仓库内相对链接要么解析到生成的 reading page（含稳定 `#anchor`），要么解析为
  精确的 public GitHub source link（contracts、schemas、scripts、tests、无法成页的
  目标）。输出里不出现本地绝对路径。
- 每个 reading page 都会显示它由哪个 Markdown 生成，并提供对应 source link。

## 资产来源（provenance）

`site/assets/` 下三张图来自选定并提供的 design kit，按字节原样放入，保留原始 alpha
与构图：

| 文件 | 内容 | sha256（内容标识） |
| --- | --- | --- |
| `receiving-room.webp` | 通信室主插画（猫、电报机、黄铜台灯、纸带） | `ce34c1ac…ad47745` |
| `tape-s-mark.webp` | 穿孔纸带 S 标记 | `e040ec46…a77dd06e` |
| `courier-note.webp` | 猫与信封的页边插画 | `728f68b9…9ecead0c` |

这三张图是用户提供的生成式视觉资产。`receiving-room.webp`、`tape-s-mark.webp`、
`courier-note.webp` 只是格式与体积上的网页优化，原始 PNG master 不进入 Git。
这些是 factual attribution，不附带任何项目 license 授权；仓库整体也没有选择 license。
构建产物中的 `build-manifest.json` 记录同样的内容 hash，用来确认资产没有被替换；
它同时记录构建时的 Git HEAD 与 working-tree 状态（`exact-head` 或
`dirty-worktree`），不会用 commit hash 冒充已修改文件的内容。

`site/assets/site.css` 与 `site/assets/site.js` 是仓库内作者手写的样式与交互，
不是 kit 原样拷贝；kit 的 HTML 没有作为第二份实现保留。

## 字体与 diagram 的网络边界

- 字体：`site.css` 顶部 `@import` 一个 Google Fonts stylesheet，请求 `Special Elite`
  与 `IBM Plex Mono`。加载失败时回退到系统 monospace / 中文系统字体，正文始终可读。
  这是唯一的第三方字体请求。
- Diagram：canonical Mermaid source 原样保留在 Markdown（因此也保留在代码块里）。
  页面从 pinned public CDN（`cdn.jsdelivr.net/npm/mermaid@11.4.1`）按需 import 一个
  browser renderer 渐进增强。渲染成功时先显示 graph，原始 source 收进一个可展开的
  `<details>`；CDN 或渲染失败时，可读的 Mermaid source 保持可见。没有手抄第二份
  graph，也没有安装 Mermaid 构建插件。宽图在阅读列内横向滚动，保留可读字号；
  图解区域可用键盘聚焦与滚动。
- 除此之外没有 analytics、没有账户、没有 backend、没有自动 probe。

## 工作台（workbench）

首页的 workbench 把 `examples/scenarios/cases.json` 的八个 synthetic scenario 做成
可选择的重放回执。数值由 build 时调用 canonical 的 `scripts.replay.replay_case`
算出，再与 expected 逐字段比较。它明确区分 “expected judgment matched” 与实际
pass/fail/unknown：一次 match 可能正是预期中的 fail 或 unknown，不代表 live health。
它不是新的 evaluator，也不改变 `scripts/replay.py`。

## 交互

- 收信匣 dialog：26 档字母位移、key wrap、解出后显示 hidden note；原生 `<dialog>`，
  键盘可用，Escape 关闭并把焦点还给触发按钮，打开时焦点落在位移旋钮。
- 值班猫：点击主插画轮换句子，第三次显示 Maxwell 电报情诗一行，紧邻作者与
  source link（引文只出现一次）。
- 纸带呼号：在 `SIGNALBOX` 与国际摩尔斯电码之间切换。

没有 autoplay，没有持续动画；focus 保持可见，用集成填充/下划线或克制的黄铜强调，
不使用沉重的深色/红色 focus ring。`prefers-reduced-motion` 会关闭动画与平滑滚动。

## 已知限制

- 这是 source 内容的静态投影。站点上线、构建与 source test 不证明任何 installed、activated、
  live path、恢复或 owner/client acceptance。
- 生成的 Mermaid 依赖外部 CDN；离线时只显示 code fallback。
- 仓库仍没有选择 license；本站内容跟随其 source 的授权状态。
