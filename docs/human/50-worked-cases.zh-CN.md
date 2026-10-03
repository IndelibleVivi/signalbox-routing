---
doc_id: signalbox.human.worked-cases
language: zh-CN
status: source-reference
authority: ../specification.md
contract_revision: 6
---

[English](50-worked-cases.en.md) · **简体中文**

# 五次可以重放的判断

这些案例教你判断何时证据足以支持结论。所有 input 都是
[synthetic](../../examples/scenarios/cases.json)。replay 复用 canonical route grammar
和 health evaluator；输入的 route match、observation label 是模型，不是 DNS query、
packet capture 或 radio diagnosis。

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
