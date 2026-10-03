---
doc_id: signalbox.human.start-here
language: zh-CN
status: foundation-explanatory
authority: ../specification.md
contract_revision: 6
---

[English](00-start-here.en.md) · **简体中文**

<a id="proxy-layer-model"></a>
# 从这里开始：一个家庭里的三次请求

手机和电脑连接到样例路由器 Mintie。Signalbox 帮你看清每次请求的策略，
以及判断它是否按预期工作需要什么证据。`SIG-01`

| 请求 | Mintie 需要知道什么 | 选择的路径 | 路径无法确认时 |
| --- | --- | --- | --- |
| DIRECT allowlist 以外的普通网站 | destination 与 policy match | 固定的 general primary：Alder | 保留 guard，不自动回落 DIRECT |
| 受保护应用中命中规则的依赖 | protected set 与 transport | residential role：Hearth | fail closed，不降级到普通出口或 DIRECT |
| canonical HTTPS origin 上的已批准私有服务 | origin、批准范围、dedicated gateway | Alder Private 到 exact private destination | 保留访问限制，不臆造 public fallback |

DIRECT allowlist 可以有意接住一条普通请求，但不会自动覆盖同一应用的所有连接。
缺少可用 domain match 的连接仍可能走默认代理出口。
[案例 1 和 2](50-worked-cases.zh-CN.md) 展示集合重叠与 IP-only 连接。

这里由路由器统一拥有透明策略。应用显式代理、OS proxy 与本机 TUN 也可以承担
策略；若它们与路由器争夺接管权，就需要明确的 compatibility design。

<a id="identity-namespaces"></a>
## 让名字有具体的工作

`IDENT-02`

| 故事中的名字 | Portable role | 工作 |
| --- | --- | --- |
| Mintie | `routing-control-plane` | 拥有 interception、DNS policy 与 enforcement |
| Alder | `general-primary` | 固定的普通 proxy-required 路径 |
| Rowan | `general-secondary` | 可独立观测的备用，不隐含自动 failover |
| Hearth | `claude-residential` | 受保护应用出口，不 fallback |
| Alder Private | `private-ingress-primary` | 独立 gateway identity，即使宿主是 Alder |

名字是 sample identity；role 承载策略和 capability 语义。endpoint、账号与 credential
属于 repo 外的 private deployment binding。同宿主不会给普通出口私有服务权限。

<a id="realization-and-acceptance"></a>
## Probe 绿了，手机却仍然打不开

路由器可以连到 Alder，手机却可能在抵达 interception 以前就失败。
这次 probe 绕过了手机路径中的一段。先看
[packet path 与观测位置](10-architecture.zh-CN.md#actual-packet-path)，再走
[案例 3](50-worked-cases.zh-CN.md#router-probe-versus-lan)。`CLAIM-01`

```text
SOURCE -> INSTALLED -> ACTIVATED -> PATH-EVIDENCE
                                      :
                                      +--> scoped ACCEPTANCE RECORD
```

source check 证明 source；安装 readback 证明文件存在；activation readback 证明
loaded process 与 kernel state；path probe 证明当时那条具名路径。
人或 client 可以接受某个 scoped result，但这个决定不能升级证据，也不能让它永久新鲜。

<a id="fail-closed"></a>
## 安全失败是什么体验

受保护请求可能停止工作，management access 仍然可用。要求的路径失败或 unknown 时，
这是预期的 guard 行为。DIRECT 只用于 allowlist，永远不是 proxy-failure fallback。
必须保留独立 management / break-glass 路径。`ROUTE-02`

<a id="health-model"></a>
## 选择下一条证据

health 分开观察 control plane、每条 egress/private lane 与家庭 underlay。
一个 subject 的 PASS 不会证明另一个 subject；aggregate 保留各自 outcome，
没有 top-level verdict。`HEALTH-01` `HEALTH-10`

- 常醒设备正常，休眠设备卡顿：同 radio、同时间对照；看
  [案例 4](50-worked-cases.zh-CN.md#awake-versus-sleeping)。
- report 刚发布，probe 却已经很旧：拒绝它作为当前恢复证据；看
  [案例 5](50-worked-cases.zh-CN.md#new-report-old-observations)。
- query 无法确认状态：保留 `unknown`，不能写成 OFF 或 absent。

profile cardinality、publication window、observation age 与 current-pointer identity
的精确规则在 [health and observability](../reference/health-and-observability.md)。
完整 agent 交接和恢复竞态入口在 [Agent Surface](../agent/README.md)。
