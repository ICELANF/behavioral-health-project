"""
BehaviorOS Agent检索路由器
=============================
基于 agent_retrieval_map/*.yaml 配置，将 Agent上下文 → 结构化检索计划

用法:
    router = AgentRetrievalRouter()
    plan = router.get_retrieval_plan("CoachAgent", context)

context字典结构:
    {
        "ttm_stage": "S1",               # TTM阶段 S0-S6
        "user_message": "怎么开始?",      # 用户原文
        "signals": ["user_asks_how_to_start"],  # signal_detector输出
        "rx_domain": None,               # 处方域（nutrition/exercise等）
        "data_source": None,             # 数据来源（cgm_device等）
        "user_profile": {}               # 用户档案
    }
"""

import yaml
from pathlib import Path
from typing import Optional


class AgentRetrievalRouter:

    def __init__(self, rules_dir: str = "agent_retrieval_map"):
        self.rules: dict = {}
        self.ki_registry: dict = {}
        self._load_all_rules(Path(rules_dir))

    def _load_all_rules(self, rule_dir: Path):
        # 加载KI注册表
        master_file = rule_dir / "_MASTER_INDEX.yaml"
        if master_file.exists():
            with open(master_file) as f:
                master = yaml.safe_load(f)
                self.ki_registry = master.get("ki_registry", {})

        # 加载各Agent规则
        for f in rule_dir.glob("*.yaml"):
            if f.name.startswith("_"):
                continue
            with open(f) as fp:
                data = yaml.safe_load(fp)
                # 支持单文件多Agent（用 --- 分隔或列表）
                if isinstance(data, list):
                    for agent_data in data:
                        self.rules[agent_data["agent_id"]] = agent_data
                else:
                    self.rules[data["agent_id"]] = data

    def get_retrieval_plan(
        self,
        agent_id: str,
        context: dict,
        max_rules: int = 3
    ) -> list[dict]:
        """
        返回排好优先级的检索计划列表
        每个元素包含: rule_id, query, target_ki, fallback_ki, filter, priority
        """
        agent_data = self.rules.get(agent_id)
        if not agent_data:
            return []

        agent_rules = agent_data.get("retrieval_rules", [])
        matched = []

        for rule in agent_rules:
            if self._matches(rule["trigger_condition"], context):
                # 过滤掉pending状态的KI，自动降级到fallback
                target_ki = self._resolve_ki(rule.get("target_ki", []))
                fallback_ki = self._resolve_ki(rule.get("fallback_ki", []))

                matched.append({
                    "rule_id": rule["rule_id"],
                    "name": rule.get("name", ""),
                    "query": rule["retrieval_query"],
                    "target_ki": target_ki,
                    "fallback_ki": fallback_ki,
                    "pending_ki": rule.get("pending_ki", []),
                    "filter": rule.get("retrieval_filter", {}),
                    "expected_output": rule.get("expected_output", ""),
                    "priority": rule["priority"],
                    "notes": rule.get("notes", "")
                })

        # P0优先，P1其次，P2最后，同级保持原顺序
        priority_order = {"P0": 0, "P1": 1, "P2": 2}
        sorted_rules = sorted(
            matched,
            key=lambda x: priority_order.get(x["priority"], 99)
        )
        return sorted_rules[:max_rules]

    def _resolve_ki(self, ki_list: list[str]) -> list[str]:
        """过滤掉pending状态的KI，仅返回active的"""
        return [
            ki for ki in ki_list
            if self.ki_registry.get(ki, {}).get("status") == "active"
        ]

    def _matches(self, condition: dict, context: dict) -> bool:
        """
        检查规则触发条件是否匹配当前上下文
        支持: ttm_stage, signal, keywords_any, data_source, assessment_type
        """
        # TTM阶段检查
        if "ttm_stage" in condition:
            if context.get("ttm_stage") not in condition["ttm_stage"]:
                return False

        # 信号检查
        if "signal" in condition:
            signals = context.get("signals", [])
            signal_val = condition["signal"]
            # 支持 "signal_a OR signal_b" 语法
            if " OR " in str(signal_val):
                any_signal = [s.strip() for s in str(signal_val).split(" OR ")]
                if not any(s in signals for s in any_signal):
                    # 如果没有信号匹配，再检查keywords_any作为降级
                    pass
            elif signal_val not in signals:
                # 没有信号时，如果有 OR 分支（keywords_any），不直接失败
                if "keywords_any" not in condition:
                    return False

        # 关键词检查
        if "keywords_any" in condition:
            msg = context.get("user_message", "")
            if not any(kw in msg for kw in condition["keywords_any"]):
                return False

        # 数据源检查
        if "data_source" in condition:
            if context.get("data_source") != condition["data_source"]:
                return False

        # 处方域检查
        if "rx_domain" in condition:
            if context.get("rx_domain") != condition["rx_domain"]:
                return False

        # 评估类型检查
        if "assessment_type" in condition:
            if context.get("assessment_type") not in condition["assessment_type"]:
                return False

        return True

    def get_ki_info(self, ki_id: str) -> dict:
        """查询KI的基本信息"""
        return self.ki_registry.get(ki_id, {})

    def list_pending_ki(self) -> list[dict]:
        """列出所有pending状态的KI（需要生成的）"""
        return [
            {"ki_id": ki_id, **info}
            for ki_id, info in self.ki_registry.items()
            if info.get("status") == "pending"
        ]

    def coverage_report(self) -> dict:
        """生成KI覆盖率报告"""
        report = {}
        for agent_id, agent_data in self.rules.items():
            referenced_ki = set()
            for rule in agent_data.get("retrieval_rules", []):
                referenced_ki.update(rule.get("target_ki", []))
                referenced_ki.update(rule.get("fallback_ki", []))
                referenced_ki.update(rule.get("pending_ki", []))
            report[agent_id] = {
                "rule_count": len(agent_data.get("retrieval_rules", [])),
                "ki_referenced": list(referenced_ki),
                "ki_count": len(referenced_ki)
            }

        # 找出没有被任何Agent引用的KI
        all_referenced = set()
        for v in report.values():
            all_referenced.update(v["ki_referenced"])
        unreferenced = [
            ki_id for ki_id in self.ki_registry
            if ki_id not in all_referenced
        ]
        report["_unreferenced_ki"] = unreferenced
        return report


# ── 使用示例 ─────────────────────────────────────────────────

if __name__ == "__main__":
    router = AgentRetrievalRouter()

    # 示例1: S1阶段用户表达阻力
    context_resistance = {
        "ttm_stage": "S1",
        "user_message": "我试过了，没用的，太难了根本做不到",
        "signals": ["user_expresses_resistance"],
        "rx_domain": None
    }
    plan = router.get_retrieval_plan("CoachAgent", context_resistance)
    print("=== 示例1: S1阻力期 ===")
    for p in plan:
        print(f"  [{p['priority']}] {p['rule_id']} | 检索词: {p['query'][:40]}...")
        print(f"       目标KI: {p['target_ki']}")

    # 示例2: CGM数据触发
    context_cgm = {
        "ttm_stage": "S3",
        "user_message": "",
        "signals": ["cgm_data_received"],
        "data_source": "cgm_device"
    }
    plan2 = router.get_retrieval_plan("MetabolicAgent", context_cgm)
    print("\n=== 示例2: CGM数据触发 ===")
    for p in plan2:
        print(f"  [{p['priority']}] {p['rule_id']} | 目标KI: {p['target_ki']}")

    # 示例3: 覆盖率报告
    report = router.coverage_report()
    print("\n=== 覆盖率报告 ===")
    for agent_id, info in report.items():
        if not agent_id.startswith("_"):
            print(f"  {agent_id}: {info['rule_count']}条规则, {info['ki_count']}个KI")
    print(f"  未被引用的KI: {report.get('_unreferenced_ki', [])}")

    # 示例4: 待生成KI列表
    pending = router.list_pending_ki()
    print(f"\n=== 待生成KI ({len(pending)}个) ===")
    for ki in pending:
        print(f"  {ki['ki_id']}: {ki.get('title', 'TBD')}")
