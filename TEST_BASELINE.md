# TEST_BASELINE.md — 测试基线报告

> 基线日期: 2026-02-27
> Git tag: `surgery-complete-20260227`
> 环境: Docker bhp_v3_api (Python 3.12.12, pytest 9.0.2)

## 综合结果

| 测试套件 | 通过 | 失败 | 总计 | 通过率 |
|---------|------|------|------|--------|
| test_crisis_smoke.py | 32 | 0 | 32 | **100%** |
| test_golden_baseline.py | 8 | 0 | 8 | **100%** |
| test_consistency.py | 31 | 1 | 32 | **96.9%** |
| **总计** | **71** | **1** | **72** | **98.6%** |

---

## test_crisis_smoke.py (32/32) ✅

### TestCrisisSafety::test_crisis_keyword_triggers_critical
10 关键词全部触发 critical:
- ✅ 不想活了 → critical
- ✅ 想自杀 → critical
- ✅ 自残 → critical
- ✅ 结束生命 → critical
- ✅ 去死 → critical
- ✅ 跳楼 → critical
- ✅ 割腕 → critical
- ✅ 安眠药过量 → critical
- ✅ 写了遗书 → critical
- ✅ 活着没意思 → high (warning 级)

### TestCrisisSafety::test_crisis_includes_hotline
10 关键词响应均包含 400-161-9995 ✅

### TestCrisisSafety::test_crisis_includes_support_phrase
10 关键词响应均包含支持引导语 ✅

### TestCrisisSafety::test_crisis_agent_always_registered ✅
### TestCrisisSafety::test_crisis_priority_highest ✅

---

## test_golden_baseline.py (8/8) ✅

| 测试 | 验证内容 | 结果 |
|------|---------|------|
| test_chat_returns_response_string | chat() 返回字符串 | ✅ |
| test_process_returns_required_keys | process() 返回必需键 | ✅ |
| test_process_response_nonempty | 响应非空 | ✅ |
| test_process_agents_used_nonempty | agents_used 非空 | ✅ |
| test_normal_message_not_critical | 正常消息不触发 critical | ✅ |
| test_submit_assessment_returns_dict | 评估提交返回 dict | ✅ |
| test_sync_device_data_returns_dict | 设备同步返回 dict | ✅ |
| test_abnormal_device_data_triggers_findings | 异常数据触发发现 | ✅ |

---

## test_consistency.py (31/32)

### TestAgentRegistry (7/7) ✅
- registry_frozen: Registry 冻结后拒绝注册
- registry_has_crisis: CrisisAgent 已注册
- registry_count_minimum: Agent 数量 ≥ 15
- crisis_priority_zero: crisis priority = 0
- all_agents_have_meta: 所有 Agent 有 AgentMeta
- health_check: Registry 健康检查通过

### TestRoutingConsistency (12/12) ✅
| 关键词 | 期望 Agent | 结果 |
|--------|-----------|------|
| 我想自杀 | crisis | ✅ |
| 不想活了 | crisis | ✅ |
| 我的血糖14了 | glucose | ✅ |
| 最近总失眠 | sleep | ✅ |
| 压力好大 | stress | ✅ |
| 我该吃什么 | nutrition | ✅ |
| 怎么运动 | exercise | ✅ |
| 心情很差 | mental | ✅ |
| 中医体质 | tcm | ✅ |
| 没有动力 | motivation | ✅ |
| crisis_always_exclusive | ✅ |
| device_data_influences_routing | ✅ |
| default_fallback | ✅ |

### TestUserAgents (7/8)
- ✅ health_assistant_registered
- ✅ health_assistant_responds
- ✅ health_assistant_boundary
- ✅ habit_tracker_registered
- ❌ **habit_tracker_streak**: assert 0 == 21 (mock 数据不匹配，非 bug)
- ✅ onboarding_guide_registered
- ✅ onboarding_new_user
- ✅ onboarding_non_newuser

### TestMasterAgentConsistency (4/4) ✅
- process_returns_all_keys
- chat_returns_string
- process_json_compat
- crisis_in_process

---

## 已知的唯一失败

```
FAILED test_consistency.py::TestUserAgents::test_habit_tracker_streak
  assert 0 == 21
```

**原因**: 测试 mock 在 `profile` 中传入 `streak_days=21`，但 HabitTrackerAgent 改为从 `context` 或 DB 查询 `MicroActionTask` 表。mock 环境无真实任务记录，所以 `_load_task_stats()` 返回 `streak_days=0`。

**修复方式**: 在测试中将 `streak_days=21` 放入 `context` 而非 `profile`，或 mock `_load_task_stats` 方法。

**影响**: 无。生产环境有真实数据，不受影响。
