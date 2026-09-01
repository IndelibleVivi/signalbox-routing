---
doc_id: signalbox.human.routing-dns-fail-closed
language: zh-CN
status: f1-reader-path
authority: ../specification.md
contract_revision: 4
---

[English](30-routing-dns-and-fail-closed.en.md) · **简体中文**

<a id="routing-owner"></a>
# 分流、DNS 与 fail-closed policy

这一条路径写给正在设计 router control plane 的人。最关键的规则是：每个 protected
deployment scope 只有一个 transparent routing owner。`ROUTE-01`

“一个 owner”不等于“一个 process”。resolver、firewall、proxy engine 与 health
observer 可以协作；但它们的职责必须明确：由一个 policy 决定 classification 与
route action，不能让第二个 engine 悄悄争夺 interception、packet mark、default route
或 DNS answer。

实现之前先记录：

- captured client scope 与 exclusions；
- TCP、UDP、DNS 各自的 interception point；
- portable roles 与它们的 private bindings；
- route precedence 与 failure action；
- enforcement owner 与 management exception；
- observation owner、report location 与 freshness policy。

<a id="dns-ownership"></a>
## DNS 也是 routing ownership 的一部分

Transparent policy 不能假设每个 client 都乖乖使用路由器的普通 resolver。client
可能缓存 answer、使用 encrypted DNS、复用连接，或保留 Service Worker state。
因此要分别决定下面的问题由谁回答：

| 问题 | 必须声明的决定 |
| --- | --- |
| 请求的是哪个 hostname？ | DNS capture、protocol sniffing 或显式 application signal |
| 最终 dial 哪个 address？ | resolver result 或 bounded destination override |
| query 经过哪个 resolver？ | 每个 policy scope 只有一条 declared resolver path |
| 未证明的 QUIC 怎么办？ | 走已证明的 protected transport，或 reject |

Hostname match 与 destination override 是两件事。canonical private path 可以用
split DNS、SNI sniffing 与类似 `override_address` 的 dial target；但 browser 仍然
展示 canonical hostname，并验证 canonical certificate。private address 是 deployment
binding，不是 user-facing origin。

`ROUTE-05` 要求 protected UDP/443 在独立证明前被拒绝。明确 reject 比安静地从
DIRECT 漏出去安全。

<a id="route-precedence"></a>
## Specific route 必须先于 general route

`ROUTE-04` `ROUTE-06` `ROUTE-07`

Mintie reference order 表达的是下面这套 portable intent：

1. observe protocol，并 capture client DNS；
2. match approved canonical private ingress；
3. enforce protected UDP policy；
4. match high-recall protected application set；
5. evaluate explicit private / ordinary DIRECT allowlists；
6. 其余 proxy-required 流量交给 pinned `general-primary`。

在 Mintie reference projection 里，这些 settled route IDs 还绑定 exact action、match
form 与 allowed fields。只有顺序正确仍然不够：替换 action 或添加未声明 route field
都会被当作 grammar drift 拒绝。

最重要的 overlap 是 private ingress 与 DIRECT。宽泛 private-address allowlist 不能先
吃掉 canonical hostname，否则 packet 会绕过 dedicated gateway identity。即使
general egress 与 private gateway co-locate，二者 capability 仍然分开。

Protected application matching 为 recall 优化；first-party、auth、storage、telemetry、
risk 与 observed compatibility dependencies 可以共用其 egress。该 role 不可用时，
matched traffic 失败，不移动到 general primary、general secondary 或 DIRECT。

<a id="fail-closed-enforcement"></a>
## Enforcement 必须独立

`ROUTE-02` `ENFORCE-01`

Routing process 决定 intended path；guard 在 process 或 kernel state 不可信时阻止
forbidden public DIRECT。二者都要分别验证：

- process / config evidence 不能证明 guard 存在；
- guard 存在也不能证明 upstream route 成功；
- safe-state setup 失败时仍保留 guard；
- management 与 break-glass access 有清楚边界；
- recovery 不把“release direct”当作普通诊断捷径。

某个 implementation-specific firewall、policy table 或 mark 可以满足 contract，
但这些 identifier 不因此成为 Signalbox 的通用常数。

<a id="health-and-recovery"></a>
## 先 observe；mutation 由另一份 contract 管

`HEALTH-07` `HEALTH-15` `HEALTH-16`

Health reports 分别观察 control plane 与每条 lane；query failure 保持 `unknown`。
任何 recorded pass 在打开 restore gate 前，都必须经过 canonical evaluator：先验证
structure 与 semantics，要求 `published_at <= evaluated_at <= valid_until`，再
exact-match producer、subject、profile 与 revision、epoch、generation、report ID、
attempt ID 和 operation context。更高 generation 也不是“足够新”；它会中止这次
decision，让 consumer 重新读取 current pointer。ordinary operational health 不授权
route mutation。

Deployment aggregate 是 historical receipt。它的 `evaluated_at` 等于
`assembled_at`，member field 叫 `effective_outcome_at_assembly`；每个 member 都经过
同一个 canonical evaluator。不能把旧 aggregate 当成 current health；需要现在的
视图时，要从 fresh member reports 重新 assemble。

如果 deployment 以后选择 automatic failover，也要另设带 hysteresis、operation
identity、rollback 与 receipt 的 state machine。latency selector 不是 strict
primary/secondary policy。

只有确实需要 canonical private access 时，才继续读 [Tailnet 与 VPS private
ingress](40-tailnet-vps-private-ingress.zh-CN.md)。
