---
doc_id: signalbox.human.start-here
language: zh-CN
status: foundation-explanatory
authority: ../specification.md
contract_revision: 3
---

[English](00-start-here.en.md) · **简体中文**

<a id="proxy-layer-model"></a>
# 从这里开始：把代理选择上移到路由器

Signalbox 想解决的不是“某个软件应该填哪个代理端口”，而是代理责任
应该由哪一层承担。`SIG-01`

```text
应用显式代理
  -> 操作系统代理 / PAC
  -> 本机 TUN
  -> 路由器透明接管
  -> 上游出口角色
```

越靠近网络入口，应用越不需要知道代理存在；但控制面需要承担更多
DNS、分流、失败语义、观察与恢复责任。路由器透明接管不是“自动更好”，
而是把原本分散在每台设备上的策略集中到一个可解释、可验证的位置。

<a id="identity-namespaces"></a>
## 三种名字不要混在一起

`IDENT-02`

| 类型 | Signalbox 里的例子 | 会不会随部署变化 |
| --- | --- | --- |
| Portable role | `general-primary` | 语义稳定 |
| Sample identity | `Alder` | 可替换，用于参考部署 |
| Private live binding | repo 外部的 endpoint / credential / provider | 经常变化，必须 fresh readback |

Mintie 是 reference deployment，不是 Signalbox 的另一个名字。她让教程有一套
完整、可跟随的拓扑，同时避免把猫自己的 live network 变成通用常数。

<a id="realization-and-acceptance"></a>
## 一个绿色灯只证明一层，acceptance 另算

`CLAIM-01`

```text
SOURCE -> INSTALLED -> ACTIVATED -> PATH-EVIDENCE
                                      :
                                      +--> ACCEPTANCE RECORD
```

- source test 通过，只证明 repo 表达了预期；
- 文件存在，只证明 payload 已安装；
- 进程、loaded config、route table 和 guard 正确，只证明 activated shape；
- lane probe 通过，只证明那次 path evidence；
- 真正的浏览器、PWA 或设备操作可以产生 named acceptance record，但它是
  对某个 scope 的决定，不会把技术证据升级，也不会永久证明 path 仍然健康。

任何一层查不到都应写 `unknown`，不能把 query failure 当成“没有规则”或
“已经关闭”。

<a id="fail-closed"></a>
## Fail closed 不是自动断网癖

`ROUTE-02`

DIRECT 只服务明确批准的 LAN、bootstrap 或直连 allowlist。受保护流量需要
代理时，如果出口、DNS、routing process 或 kernel state 无法确认，默认结果
是失败并保留保护，不是偷偷回落到裸 WAN。

这个安全语义也意味着必须保留独立 management / break-glass path；诊断者不应
只依赖自己正在修的那条代理链。

<a id="health-model"></a>
## Health 不只是“网页能打开”

`HEALTH-01` `HEALTH-10` `HEALTH-14` `HEALTH-15`

Signalbox 把 health 分为 transport、exit identity、DNS、control plane、
enforcement、resources、persistence 和 recovery readiness。`HealthProfile`
规定要测什么；每次 attempt 都发布 immutable `HealthReport`。旧成功超过
`valid_until`、generation 在 producer / subject / profile / epoch scope 内倒退、
epoch 意外变化，或 profile revision 不匹配以后，有效状态都是 `unknown`。

恢复前的 `recovery-preflight` 只为一个 exact operation 与 desired-state digest
检查能否安全 query、reconcile 和 restore。日常 health 则拆成一份 control-plane
report，以及每条 egress / private-ingress lane 各自的一份 report；aggregate 必须
保留所有 member outcome，不能把它们压成一个模糊的“全网绿色”。

每个 dimension 都由 explicit observations roll up。lane transport 要判 `pass`，
至少要同时有 transport-neutral 与 role-specific probe，而且来自独立 dependency
groups。profile、report 与 aggregate 都不会自己切 route。

Aggregate 是 historical assembly receipt，不会随着 wall clock 静默改变。member
outcome 只在 `assembled_at` 求值一次；要得到 current view，必须读取 fresh reports
并生成新的 aggregate。

今天的 cold-boot 事故提供了一个很好的例子：route table 逻辑上可能为空，
但如果平台无法可靠查询它，恢复就没有证据声称 runtime 已经 `OFF`。因此
queryability 本身也是 health。

下一步阅读：[Signalbox 架构与 packet path](10-architecture.zh-CN.md)。
