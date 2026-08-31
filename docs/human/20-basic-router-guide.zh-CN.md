---
doc_id: signalbox.human.basic-router-guide
language: zh-CN
status: f1-reader-path
authority: ../specification.md
contract_revision: 3
---

[English](20-basic-router-guide.en.md) · **简体中文**

<a id="router-job"></a>
# 路由器基础使用说明

Signalbox 看起来比普通“路由器教程”大，是因为它把教程下面的安全 contract 也放了
进来。日常使用时，路由器的工作其实很简单：接管 approved client scope，只做一次
分类，把每类流量交给声明好的 role，并拒绝不安全 fallback。`SIG-01` `ROUTE-01`

把 policy 移到路由器以后，各个 app 不必再统一自己的 proxy setting；相应地，
路由器必须负责 DNS ownership、route order、failure behavior 与 inspectable state。
只有这四项仍然明确时，集中控制才是真的省心。

<a id="minimum-policy"></a>
## 最少要说明清楚的 policy

改 implementation 之前，先写下五个答案：

| 问题 | Signalbox 的安全答案 |
| --- | --- |
| 哪些 clients 属于接管 scope？ | 明确的 device、subnet 或 approved client set |
| 什么可以走 DIRECT？ | 具名 allowlist；不能是 default，也不能是 proxy failure fallback |
| 普通 proxy-required 流量去哪里？ | 一个 pinned `general-primary` role |
| 哪些流量要求受保护身份？ | high-recall match set，绑定独立的 no-fallback role |
| 是否需要 private ingress？ | 可选；需要时用 dedicated gateway identity 与 exact destination |

`ROUTE-02` 规定 DIRECT 只能来自 allowlist。secondary exit 的存在不自动产生
failover；protected lane 也不会因为普通出口“还能用”就继承它。

[Mintie sample](../../examples/mintie/README.md) 用友好 identity 展示了这些答案。
这些名字让 policy 好读，但不是 endpoint 或 provider 要求。

<a id="safe-failure"></a>
## 日常所说的 fail closed

如果 proxy-required route 无法被证明，相关流量就失败，而不是从 raw WAN 偷跑。
即使 routing process 启动失败或无法建立安全 state，independent guard 仍然保留。
`ENFORCE-01`

Fail closed 应当有清楚边界，不是表演式断网：

- approved local management 与 bootstrap path 仍然显式保留；
- break-glass path 不依赖正在维修的 lane；
- 查不到的 rule 或 table 是 `unknown`，不是“已关闭”；
- diagnostics 先观察，不会顺手改变 route selection。

用户看见的现象可能只是“这个网页打不开”；policy 含义则是“受保护流量没有被
允许降级到更不可信的路径”。

<a id="what-proof-means"></a>
## 每一盏绿灯只证明自己的层

`CLAIM-01`

| 证据 | 能证明什么 | 不能证明什么 |
| --- | --- | --- |
| `make verify` | tracked source 与 contracts 一致 | 路由器上已经安装任何东西 |
| file readback | payload 存在于观察到的位置 | 已经 loaded 或 active |
| process、config、route、guard readback | 观察到的 runtime shape | app path 一定成功 |
| exact lane probe | 那条 path 在那次 observation 下成立 | 其他 lane 或未来时间 |
| browser / device acceptance | 某个人对 named scope 的决定 | 永久 technical health |

所以 health 是一组按 subject 分开的 receipts，不是一个万能绿色路由器图标。已经
保存的 deployment aggregate 只记录 assembly 当时求得的 outcomes；要知道现在，
必须读取 current reports 并重新 assemble。

<a id="next-path"></a>
## 只在任务需要时继续下钻

- 要实现 interception、DNS、precedence 或 guard：看[分流、DNS 与
  fail-closed](30-routing-dns-and-fail-closed.zh-CN.md)。
- 要让同一个 app origin 同时支持 public / private access：看[Tailnet 与 VPS
  private ingress](40-tailnet-vps-private-ingress.zh-CN.md)。
- 要 review exact machine semantics：看 [Agent Surface](../agent/README.md)。

基础说明故意保持短。更深的 contracts 是为了让人或 agent 真正实现这句短 promise
时，不必在危险部分靠猜。
