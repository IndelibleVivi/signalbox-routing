---
doc_id: signalbox.human.worked-cases
language: zh-CN
status: source-reference
authority: ../specification.md
contract_revision: 6
---

[English](50-worked-cases.en.md) · **简体中文**

# 七个可以细读的判断

synthetic replay 最初提供五个可以重放的判断，下面又补了两篇只用于解释外部
机制的案例。replay 的 input 都是
[synthetic](../../examples/scenarios/cases.json)。replay 复用 canonical route grammar
和 health evaluator；输入的 route match、observation label 是模型，不是 DNS query、
packet capture 或 radio diagnosis。

案例 6 与 7 处理 Tailscale 的 4via6 与 prefix failover。它们没有进入
`examples/scenarios/cases.json`，也不调用 replay evaluator：两篇只用公开文档解释
路由机制，不产生 live 或 synthetic 的 PASS/FAIL 结论。

```bash
.venv/bin/python -m scripts.replay
.venv/bin/python -m scripts.replay --case canonical-direct-overlap
```

每个 JSON result 都有 `expected`、`actual` 和 `passed`。
同一批场景进入 [agent surface tests](../../tests/test_agent_surface.py)。

<a id="canonical-direct-overlap"></a>
## 1. Canonical hostname 同时命中 DIRECT

**症状：** 已批准的私有服务 hostname 同时在 private origin set 和宽泛 DIRECT
allowlist 中。`ROUTE-06` `PRIVATE-01` `PRIVATE-02`

**已知 / 未知：** synthetic match 命中 canonical private ingress 与两个 DIRECT rule。
source 提供 Alder Private、宿主 Alder、private-ingress role 和 lane profile。
实际 private binding 与 reachability 仍未知。

**路径与观测：** client → origin policy → Alder Private → exact private destination。
先检查 selected route，再用 `.venv/bin/python -m scripts.policy` 跟完整 gateway chain。

**输入 / 结果：** `canonical-direct-overlap` 选择 `canonical-private-ingress`，action
`private-ingress`，binding `alder-private`。host、role、capability、HTTPS origin 或
health coverage 被改坏时，policy diagnostic 指出断裂的具体引用。

**错误推断 / 反证：** “在 DIRECT set 中，所以直接访问等价。”更早的 canonical match
选择 dedicated identity。把 DIRECT 提前或替换 action，source validation 会拒绝。

**允许的结论：** source precedence 保护了 dedicated path；它不证明私有连通性、
server authorization 或 browser acceptance。

<a id="domain-versus-ip-only"></a>
## 2. 域名 DIRECT，同一应用的 IP-only 请求走代理

**症状：** 一个应用看起来用了两条路径。`ROUTE-02` `ROUTE-07`

**已知 / 未知：** domain request 命中 `approved-direct`；另一连接没有可用 domain
match，只命中 default。真实 deployment 是否通过 DNS ownership 或 sniffing 恢复
hostname，仍未知。

**路径与观测：** domain evidence → allowlist → DIRECT；IP-only destination → default
→ Alder。观察每条 connection 拥有的 match information，不能只看应用名。

**输入 / 结果：** `domain-versus-ip-only` 得到 domain route `approved-direct`，IP route
`default-proxy-required`，`same_application_implies_same_route: false`。

**错误推断 / 反证：** “domain rule 覆盖整个应用。”IP-only 连接缺少这个 match。
connection-level selection evidence 可以推翻应用级的笼统判断。

**允许的结论：** 两种选择都符合 reference；protected traffic 仍需要 high-recall set，
这个案例不授予 protected bypass。

<a id="router-probe-versus-lan"></a>
## 3. Router-local probe 全绿，LAN client 仍失败

**症状：** lane probe 绿了，手机却无法连接。`CLAIM-02` `HEALTH-10` `ENFORCE-01`

**已知 / 未知：** egress transport PASS；LAN admission、interception、mark/policy
routing 与 local delivery 没有被观察。

**路径与观测：** 对照 [TProxy packet path](10-architecture.zh-CN.md#actual-packet-path)。
显式 router-local probe 从 egress 开始；手机要经过 admission、PREROUTING interception、
mark-to-table routing 和 transparent socket。forwarding guard 与 local-delivery admission
必须在真实 deployment hook 上分别确认。

**输入 / 结果：** `router-probe-versus-lan` 只给 egress PASS，client-path coverage 得到
`unknown`，列出四个被跳过的边界。补齐四条 PASS 才允许 coverage PASS；观察到失败则
是 FAIL。这些是 evidence coverage outcome，不是 health report。

**错误推断 / 反证：** “lane 通了，所以手机已经抵达 lane。”同步的 client attempt 与
admission/interception/local-delivery readback 可以找到它未跨过的第一个边界。

**允许的结论：** upstream reachability 只对这次 probe 成立。下一条证据应区分 admission、
interception、local delivery 与 dial-out；单纯重启 service 不提供这种区分。

<a id="awake-versus-sleeping"></a>
## 4. 常醒设备正常，省电设备卡顿

**症状：** sleeping client 延迟，连接同一 AP 的 awake client 仍正常。`CLAIM-03` `HEALTH-06`

**已知 / 未知：** 同步的 synthetic AP-to-client observation 对 awake PASS、sleeping FAIL；
两组 AP-to-upstream control 都 PASS。client class 和 sleep behavior 是观测变量；具体
driver、buffering、wake timing 或 interference 原因仍 unknown。

**路径与观测：** 同 radio、同时间比较 AP-to-client delivery，加入 AP-to-upstream control。
证据和 acceptance 都要覆盖受影响的 client class。

**输入 / 结果：** `awake-versus-sleeping` 返回 awake PASS、sleeping FAIL，fault boundary
`client-radio-interaction`，root cause `unknown`。upstream control 也失败时，撤回这种定位。

**错误推断 / 反证：** “awake client 证明 radio 健康”，或“client 变了，所以 defect 必在
client”。sleep-path observation 推翻前者。client change 可以触发潜在 AP defect；
变化的触发位置、故障机制与最佳修复位置可能不同。

**允许的结论：** 优先做有区分力的 sleep/delivery 对照。firmware/config history 调整实验
优先级，不能排除潜在 infrastructure defect。参考
[failure catalog](../reference/failure-catalog.md) 的 `FAIL-011`、`FAIL-012`。
测试不授权 radio、firmware 或 client config 变更。

<a id="new-report-old-observations"></a>
## 5. Report 刚发布，内部 evidence 已过龄

**症状：** 新 completion timestamp 看起来允许 restore，实际检查却很旧。
`HEALTH-12` `HEALTH-16` `HEALTH-20`

**已知 / 未知：** identity、gate context 不变；completion/publication 保留样例时间。
start 与所有 observation 向前移 61 天；没有重新观察当前 kernel state。

**路径与观测：** observer → timed observations → immutable report → canonical evaluator
→ exact restore decision。

```text
旧 probe ---- observation expiry ........ 新 completion / publication
                     authority 已结束               不能续期
```

**输入 / 结果：** `new-report-old-observations` 返回 effective `unknown`、
`restore_allowed: false`。profile 同时约束 attempt duration、每条 required observation
和 report age；最早的 required evidence expiry 限制 `valid_until`。

**错误推断 / 反证：** “report 刚完成，所以检查全新鲜。”对照实际 observation time 与
profile limit，canonical evaluator 会拒绝这种包装旧证据的 report。

**允许的结论：** 保留 guard，执行新的、已授权 preflight。publication 不能续期 evidence
或 restore authority。

generation 42→43、旧 attempt 晚完成、restart uncertainty 的重放入口在
[agent recovery races](../agent/workflow.md#recovery-sequencing)。

<a id="4via6-site-identity"></a>
## 6. 相同的 IPv4 range，不同的 site identity

**症状：** 家里与办公室都使用同一个私有 IPv4 范围。只看
`site A LAN ↔ site B LAN`，两台 router 似乎都“属于同一个网络”；但它们是两个
不同 site，里面的旧设备也可能有相同的 IPv4 地址。

**这不是 executable replay。** 本篇是外部机制的解释性案例，不进入
`examples/scenarios/cases.json`。它不计算 subnet route、不探测任何节点，也不
发出 live 或 synthetic 的 PASS/FAIL。

**机制：** 裸 IPv4 subnet route 无法仅凭一个相同 prefix 区分两个 site。
Tailscale 的 [4via6 subnet
文档](https://tailscale.com/docs/features/subnet-routers/4via6-subnets)把
每个 site 的身份编入唯一的 IPv6 mapping，因此保留原来的 IPv4 地址也能分辨
“site A 的 LAN”与“site B 的 LAN”。

```text
IPv4 prefix P at site A --site A mapping--> Tailnet reachability
IPv4 prefix P at site B --site B mapping--> different Tailnet reachability
                 same P                              distinct identity
```

**同一 site 的 redundancy：** 若两台 router 使用同一个 site ID 与 mapping，
它们可以宣告同一 site 的同一 prefix，为该 site 提供冗余。相同的 site ID 不能
拿来表示新的 site：那会把本来不同的目的地压成同一个身份。

**部署前的版本核对：** 查阅于 2026-10-22 的官方 4via6 文档要求为安全升级至
Tailscale 1.102.3 或更高，并链接相关 advisory。这里的 site mapping 不应被当作
旧版本仍可安全部署的依据。普通 IPv4 subnet router 的 SNAT 与回程问题，另见
[旅行路由器一篇](60-travel-router.zh-CN.md#subnet-path)。

**允许的结论：** 4via6 解决的是重叠 IPv4 site 的身份表达，不重编号设备，也不
证明 policy、DNS、firewall 或 path 已正确。部署后仍须取得具名 path evidence。

<a id="prefix-failure-vs-redundancy"></a>
## 7. 更具体 prefix 失败，不会自动落到较宽的 route

**症状：** 配置同时包含一个较宽的 route 与一个更具体的 prefix，具体 route
背后的 router 离线。页面失败后，读者容易推断较宽 route 会接手。

**这不是 executable replay。** 本篇同样只解释外部产品机制，不加入八个 canonical
scenario。下面的文本路径不是 route-table readback，也不是任何节点当前状态的
证据。

```text
specific prefix ---- offline router ---- X
                    no automatic fallthrough
broader prefix  ---- other router ----> separate candidate only
```

**机制：** Tailscale 的
[overlapping subnet route failover
文档](https://tailscale.com/docs/reference/troubleshooting/network-configuration/overlapping-subnet-route-failover)
说明 exact-prefix failover 与 less-specific fallback 不是一回事：更具体的
route 即使失效，也不会因为旁边存在较宽 route 而自动改用它。`via` 过滤的是哪些
router 有资格参与，不是给 router 排一个自动回退顺序。

**同一 prefix 的 redundancy：** 对同一个 exact prefix 配置多个合格 router，
才有重复候选可讨论。哪一台可用、它们是否真正宣告同一规则、policy 如何选择，
仍要看实际 readback。

**错误推断 / 反证：** “prefix 越宽越兜底。”观察 selected route 与 exact prefix
的候选状态，可以发现它并未自动改用较宽路径。网络层 route 也不能替应用层
authorization 作决定。

**允许的结论：** 具体 route 失败时，把结果保留为 fail 或 `UNKNOWN`，并检查
同一 exact prefix 是否真有冗余；不要宣称它会落到较宽路由。参见
[peer relay 与 transport](70-peer-relay.zh-CN.md#blocked-direct)以及
[旅行路由器与 client-free 设备](60-travel-router.zh-CN.md#subnet-path)。
