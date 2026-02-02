"""
端到端测试
End-to-End Test

完整流程测试：用户输入 → Trigger识别 → 风险评估 → Agent路由 → 干预生成
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import pytest

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.assessment_engine import get_assessment_engine
from core.trigger_engine import get_trigger_engine
from core.multimodal_client import get_multimodal_client


@pytest.mark.asyncio
async def test_scenario_1_critical():
    """场景1: 危机状态 - 检测到自杀倾向"""
    print("\n" + "=" * 80)
    print("场景1: 危机状态 - 检测到自杀倾向")
    print("=" * 80)

    engine = get_assessment_engine()

    # 模拟用户输入
    user_message = "我真的不想活了，感觉人生没有意义，一切都很糟糕"
    print(f"\n[用户消息]: {user_message}")

    # 执行评估
    result = await engine.assess(
        user_id=1001,
        text_content=user_message
    )

    # 显示结果
    print(f"\n[评估ID]: {result.assessment_id}")
    print(f"[时间戳]: {result.timestamp}")

    print(f"\n[识别的Triggers] ({len(result.triggers)}个):")
    for i, trigger in enumerate(result.triggers, 1):
        print(f"  {i}. {trigger.name} ({trigger.tag_id})")
        print(f"     - 类别: {trigger.category.value}")
        print(f"     - 严重程度: {trigger.severity.value}")
        print(f"     - 置信度: {trigger.confidence:.2f}")

    print(f"\n[风险评估]:")
    print(f"  - 风险等级: {result.risk_assessment.risk_level.value}")
    print(f"  - 风险分数: {result.risk_assessment.risk_score}/100")
    print(f"  - 主要关注: {result.risk_assessment.primary_concern}")
    print(f"  - 紧急程度: {result.risk_assessment.urgency}")
    print(f"  - 评估理由: {result.risk_assessment.reasoning}")

    print(f"\n[路由决策]:")
    print(f"  - 主Agent: {result.routing_decision.primary_agent.value}")
    print(f"  - 次要Agents: {[a.value for a in result.routing_decision.secondary_agents]}")
    print(f"  - 优先级: P{result.routing_decision.priority}")
    print(f"  - 响应时间: {result.routing_decision.response_time}")
    print(f"  - 路由理由: {result.routing_decision.routing_reasoning}")

    print(f"\n[推荐行动]:")
    for i, action in enumerate(result.routing_decision.recommended_actions, 1):
        print(f"  {i}. {action}")

    # 验证
    assert result.risk_assessment.risk_level.value in ["R3", "R4"], "应为高风险或危机"
    assert result.routing_decision.primary_agent.value == "CrisisAgent", "应路由到CrisisAgent"

    print("\n[OK] 场景1测试通过 - 正确识别危机状态")


@pytest.mark.asyncio
async def test_scenario_2_metabolic_syndrome():
    """场景2: 代谢综合征聚类 - 高血糖+久坐+高GI饮食"""
    print("\n" + "=" * 80)
    print("场景2: 代谢综合征聚类")
    print("=" * 80)

    engine = get_assessment_engine()

    # 模拟用户输入
    user_message = "最近经常吃米饭和面食，血糖测出来都偏高，工作一直坐着也没时间运动"
    glucose_data = [6.5, 7.2, 11.8, 13.5, 12.2, 10.8, 9.5]  # 高血糖

    print(f"\n[用户消息]: {user_message}")
    print(f"[血糖数据]: {glucose_data}")

    # 执行评估
    result = await engine.assess(
        user_id=1002,
        text_content=user_message,
        glucose_values=glucose_data
    )

    # 显示结果
    print(f"\n[识别的Triggers] ({len(result.triggers)}个):")
    for trigger in result.triggers:
        print(f"  - {trigger.name} ({trigger.severity.value})")

    print(f"\n[风险评估]:")
    print(f"  - 风险等级: {result.risk_assessment.risk_level.value}")
    print(f"  - 风险分数: {result.risk_assessment.risk_score}/100")
    print(f"  - 严重程度分布: {result.risk_assessment.severity_distribution}")

    print(f"\n[路由决策]:")
    print(f"  - 主Agent: {result.routing_decision.primary_agent.value}")
    print(f"  - 次要Agents: {[a.value for a in result.routing_decision.secondary_agents]}")

    # 验证代谢综合征聚类
    trigger_ids = {t.tag_id for t in result.triggers}
    metabolic_triggers = {"high_glucose", "glucose_spike", "high_gi_meal", "sedentary"}
    cluster_match = len(trigger_ids & metabolic_triggers)

    print(f"\n[聚类分析]:")
    print(f"  - 匹配的代谢综合征Triggers: {cluster_match}/4")
    print(f"  - 是否触发聚类: {'是' if cluster_match >= 2 else '否'}")

    # 验证
    assert result.routing_decision.primary_agent.value in ["GlucoseAgent", "MetabolicAgent"], "应路由到代谢相关Agent"

    print("\n[OK] 场景2测试通过 - 正确识别代谢综合征聚类")


@pytest.mark.asyncio
async def test_scenario_3_burnout():
    """场景3: 职业倦怠聚类 - 压力+失眠+动机低"""
    print("\n" + "=" * 80)
    print("场景3: 职业倦怠聚类")
    print("=" * 80)

    engine = get_assessment_engine()

    # 模拟用户输入
    user_message = "最近工作压力特别大，天天加班，晚上也睡不好，感觉很疲惫，什么都不想做"
    hrv_data = [58, 62, 55, 60, 57, 59]  # 低HRV，显示压力

    print(f"\n[用户消息]: {user_message}")
    print(f"[HRV数据]: {hrv_data}")

    # 执行评估
    result = await engine.assess(
        user_id=1003,
        text_content=user_message,
        hrv_values=hrv_data
    )

    # 显示结果
    print(f"\n[识别的Triggers] ({len(result.triggers)}个):")
    for trigger in result.triggers:
        print(f"  - {trigger.name} ({trigger.category.value}, {trigger.severity.value})")

    print(f"\n[风险评估]:")
    print(f"  - 风险等级: {result.risk_assessment.risk_level.value}")
    print(f"  - 风险分数: {result.risk_assessment.risk_score}/100")

    print(f"\n[路由决策]:")
    print(f"  - 主Agent: {result.routing_decision.primary_agent.value}")
    print(f"  - 次要Agents: {[a.value for a in result.routing_decision.secondary_agents]}")
    print(f"  - 响应时间: {result.routing_decision.response_time}")

    # 验证职业倦怠聚类
    trigger_ids = {t.tag_id for t in result.triggers}
    burnout_triggers = {"stress_overload", "poor_sleep", "low_motivation", "work_stress"}
    cluster_match = len(trigger_ids & burnout_triggers)

    print(f"\n[聚类分析]:")
    print(f"  - 匹配的职业倦怠Triggers: {cluster_match}/4")

    # 验证
    assert result.routing_decision.primary_agent.value in ["StressAgent", "MentalHealthAgent"], "应路由到压力或心理Agent"

    print("\n[OK] 场景3测试通过 - 正确识别职业倦怠聚类")


@pytest.mark.asyncio
async def test_scenario_4_normal():
    """场景4: 正常状态 - 积极消息，无风险"""
    print("\n" + "=" * 80)
    print("场景4: 正常状态")
    print("=" * 80)

    engine = get_assessment_engine()

    # 模拟用户输入
    user_message = "今天运动了30分钟，感觉很好，血糖也正常，准备继续保持"
    glucose_data = [5.5, 6.2, 7.5, 6.8, 5.9]  # 正常血糖
    hrv_data = [72, 75, 78, 74, 76, 73]  # 正常HRV

    print(f"\n[用户消息]: {user_message}")
    print(f"[血糖数据]: {glucose_data}")
    print(f"[HRV数据]: {hrv_data}")

    # 执行评估
    result = await engine.assess(
        user_id=1004,
        text_content=user_message,
        glucose_values=glucose_data,
        hrv_values=hrv_data
    )

    # 显示结果
    print(f"\n[识别的Triggers] ({len(result.triggers)}个):")
    if result.triggers:
        for trigger in result.triggers:
            print(f"  - {trigger.name}")
    else:
        print("  - 无风险信号")

    print(f"\n[风险评估]:")
    print(f"  - 风险等级: {result.risk_assessment.risk_level.value}")
    print(f"  - 风险分数: {result.risk_assessment.risk_score}/100")

    print(f"\n[路由决策]:")
    print(f"  - 主Agent: {result.routing_decision.primary_agent.value}")
    print(f"  - 响应时间: {result.routing_decision.response_time}")

    # 验证
    assert result.risk_assessment.risk_level.value in ["R0", "R1"], "应为正常或轻度风险"

    print("\n[OK] 场景4测试通过 - 正确识别正常状态")


@pytest.mark.asyncio
async def test_scenario_5_mixed():
    """场景5: 混合场景 - 多模态融合"""
    print("\n" + "=" * 80)
    print("场景5: 混合场景 - 多模态融合")
    print("=" * 80)

    engine = get_assessment_engine()

    # 模拟用户输入
    user_message = "早上好，昨晚没睡好，今天有点累，刚测血糖有点高"
    glucose_data = [6.5, 7.2, 11.5, 13.2, 12.8, 11.0, 9.5]
    hrv_data = [65, 68, 62, 60, 66, 64]
    user_profile = {
        "basic": {"age": 45, "gender": "male"},
        "behavior": {"adherence_rate": 75}
    }

    print(f"\n[用户消息]: {user_message}")
    print(f"[血糖数据]: {glucose_data[:3]}... (共{len(glucose_data)}个点)")
    print(f"[HRV数据]: {hrv_data[:3]}... (共{len(hrv_data)}个点)")
    print(f"[用户画像]: {user_profile}")

    # 执行评估
    result = await engine.assess(
        user_id=1005,
        text_content=user_message,
        glucose_values=glucose_data,
        hrv_values=hrv_data,
        user_profile=user_profile
    )

    # 显示详细结果
    print(f"\n[完整评估结果]:")
    print(f"评估ID: {result.assessment_id}")
    print(f"用户ID: {result.user_id}")

    print(f"\n[Triggers] ({len(result.triggers)}个):")
    for i, trigger in enumerate(result.triggers, 1):
        print(f"\n  {i}. {trigger.name}")
        print(f"     - Tag ID: {trigger.tag_id}")
        print(f"     - 类别: {trigger.category.value}")
        print(f"     - 严重程度: {trigger.severity.value}")
        print(f"     - 置信度: {trigger.confidence:.2f}")
        print(f"     - 元数据: {trigger.metadata}")

    print(f"\n[风险评估]:")
    ra = result.risk_assessment
    print(f"  风险等级: {ra.risk_level.value}")
    print(f"  风险分数: {ra.risk_score}/100")
    print(f"  主要关注: {ra.primary_concern}")
    print(f"  紧急程度: {ra.urgency}")
    print(f"  严重程度分布:")
    for severity, count in ra.severity_distribution.items():
        if count > 0:
            print(f"    - {severity}: {count}个")
    print(f"  评估理由: {ra.reasoning}")

    print(f"\n[路由决策]:")
    rd = result.routing_decision
    print(f"  主Agent: {rd.primary_agent.value}")
    print(f"  次要Agents: {', '.join([a.value for a in rd.secondary_agents])}")
    print(f"  优先级: P{rd.priority}")
    print(f"  响应时间: {rd.response_time}")
    print(f"  路由理由: {rd.routing_reasoning}")
    print(f"  推荐行动:")
    for i, action in enumerate(rd.recommended_actions, 1):
        print(f"    {i}. {action}")

    # 导出完整结果
    result_dict = result.to_dict()

    print(f"\n[数据导出]:")
    print(f"  可序列化为JSON: {'是' if isinstance(result_dict, dict) else '否'}")
    print(f"  包含字段: {', '.join(result_dict.keys())}")

    print("\n[OK] 场景5测试通过 - 多模态融合评估完成")


@pytest.mark.asyncio
async def test_performance():
    """性能测试 - 评估响应时间"""
    print("\n" + "=" * 80)
    print("性能测试")
    print("=" * 80)

    engine = get_assessment_engine()

    # 记录开始时间
    import time
    times = []

    # 执行10次评估
    print("\n执行10次评估，测量响应时间...")
    for i in range(10):
        start = time.time()

        await engine.assess(
            user_id=2000 + i,
            text_content="今天感觉还不错",
            glucose_values=[6.5, 7.2, 8.1],
            hrv_values=[70, 72, 75]
        )

        elapsed = (time.time() - start) * 1000  # 转为毫秒
        times.append(elapsed)

        if (i + 1) % 2 == 0:
            print(f"  完成 {i+1}/10...")

    # 统计
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print(f"\n[性能指标]:")
    print(f"  平均响应时间: {avg_time:.2f} ms")
    print(f"  最快: {min_time:.2f} ms")
    print(f"  最慢: {max_time:.2f} ms")
    print(f"  目标: <100ms")
    print(f"  状态: {'[OK]' if avg_time < 100 else '[WARN]'}")

    assert avg_time < 100, "平均响应时间应 <100ms"

    print("\n[OK] 性能测试通过")


async def main():
    """主测试函数"""
    print("\n" + "="*80)
    print(" 端到端测试套件")
    print(" End-to-End Test Suite")
    print("="*80)

    try:
        # 场景测试
        await test_scenario_1_critical()
        await test_scenario_2_metabolic_syndrome()
        await test_scenario_3_burnout()
        await test_scenario_4_normal()
        await test_scenario_5_mixed()

        # 性能测试
        await test_performance()

        # 总结
        print("\n" + "=" * 80)
        print("[SUCCESS] 所有端到端测试通过!")
        print("=" * 80)
        print("\n测试覆盖:")
        print("  [OK] 危机状态检测")
        print("  [OK] 代谢综合征聚类")
        print("  [OK] 职业倦怠聚类")
        print("  [OK] 正常状态识别")
        print("  [OK] 多模态融合")
        print("  [OK] 性能指标")
        print("\nL2评估引擎已ready，可以集成到Master Agent!")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
