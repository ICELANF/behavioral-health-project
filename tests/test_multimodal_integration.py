"""
测试多模态集成
Test Multimodal Integration

测试多模态客户端和Trigger引擎的集成
"""
import asyncio
import sys
from pathlib import Path
import pytest

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.multimodal_client import get_multimodal_client
from core.trigger_engine import get_trigger_engine


@pytest.mark.asyncio
async def test_multimodal_client():
    """测试多模态客户端"""
    print("\n" + "=" * 60)
    print("测试1: 多模态客户端")
    print("=" * 60)

    client = get_multimodal_client()

    # 健康检查
    print("\n[1] 健康检查")
    health = await client.health_check()
    print(f"状态: {health.get('status')}")

    # 文本处理
    print("\n[2] 文本情感分析")
    text_result = await client.process_text(
        "今天心情不太好，有点焦虑，血糖也高了"
    )
    print(f"情感: {text_result.get('sentiment')}")
    print(f"主要情绪: {text_result.get('primary_emotion')}")
    print(f"风险分数: {text_result.get('risk_score')}")

    # HRV处理
    print("\n[3] HRV数据处理")
    hrv_result = await client.process_heartrate([72, 75, 71, 68, 73, 76])
    print(f"平均心率: {hrv_result.get('heart_rate')} bpm")
    print(f"HRV-SDNN: {hrv_result.get('hrv_sdnn')} ms")

    # 血糖处理
    print("\n[4] 血糖数据处理")
    glucose_result = await client.process_glucose([95, 98, 125, 145, 138, 120, 105])
    print(f"信号类型: {glucose_result.get('signal_type')}")

    # 饮食融合
    print("\n[5] 饮食融合评估")
    meal_result = await client.fuse_meal_assessment(
        user_id=1,
        text_content="今天早餐吃了米饭和青菜",
        glucose_before=95,
        glucose_after=135,
        meal_type="breakfast"
    )
    print(f"总评分: {meal_result.get('overall_score')}/10")
    print(f"风险等级: {meal_result.get('risk_level')}")
    print(f"建议: {meal_result.get('recommendations', [])[:1]}")

    print("\n[OK] 多模态客户端测试通过!")


@pytest.mark.asyncio
async def test_trigger_engine():
    """测试Trigger引擎"""
    print("\n" + "=" * 60)
    print("测试2: Trigger 识别引擎")
    print("=" * 60)

    engine = get_trigger_engine()

    # 测试1: 纯文本Trigger
    print("\n[1] 文本Trigger识别")
    triggers = await engine.recognize_triggers(
        user_id=1,
        text_content="今天心情不太好，有点焦虑"
    )
    print(f"识别到 {len(triggers)} 个Triggers:")
    for trigger in triggers:
        print(f"  - {trigger.name} ({trigger.tag_id}) - 严重程度: {trigger.severity.value}")

    # 测试2: HRV Trigger
    print("\n[2] HRV Trigger识别")
    triggers = await engine.recognize_triggers(
        user_id=1,
        hrv_values=[72, 75, 71, 68, 73, 76]  # 低HRV
    )
    print(f"识别到 {len(triggers)} 个Triggers:")
    for trigger in triggers:
        print(f"  - {trigger.name} ({trigger.tag_id}) - 严重程度: {trigger.severity.value}")

    # 测试3: 血糖Trigger
    print("\n[3] 血糖Trigger识别")
    triggers = await engine.recognize_triggers(
        user_id=1,
        glucose_values=[95, 98, 125, 145, 138, 120, 105]  # 高血糖+波动
    )
    print(f"识别到 {len(triggers)} 个Triggers:")
    for trigger in triggers:
        print(f"  - {trigger.name} ({trigger.tag_id}) - 严重程度: {trigger.severity.value}")

    # 测试4: 综合识别
    print("\n[4] 综合Trigger识别")
    triggers = await engine.recognize_triggers(
        user_id=1,
        text_content="今天心情不太好，有点焦虑，血糖也高了",
        hrv_values=[65, 68, 62, 60, 66, 64],  # 低HRV
        glucose_values=[95, 120, 145, 138, 125, 110]  # 高血糖
    )
    print(f"识别到 {len(triggers)} 个Triggers:")
    for trigger in triggers:
        print(f"  - {trigger.name} ({trigger.tag_id})")
        print(f"    类别: {trigger.category.value}, 严重程度: {trigger.severity.value}")
        print(f"    置信度: {trigger.confidence:.2f}")

    # 显示Trigger字典
    print("\n[5] Trigger字典统计")
    all_triggers = engine.get_all_triggers()
    print(f"总计定义了 {len(all_triggers)} 个Trigger标签:")
    print(f"  - 生理类: {len([k for k, v in all_triggers.items() if 'glucose' in k or 'hrv' in k or 'heart' in k or 'sleep' in k])}")
    print(f"  - 心理类: {len([k for k, v in all_triggers.items() if 'anxiety' in k or 'depression' in k or 'stress' in k or 'sentiment' in k or 'motivation' in k or 'crisis' in k])}")
    print(f"  - 行为类: {len([k for k, v in all_triggers.items() if 'task' in k or 'checkin' in k or 'adherence' in k or 'meal' in k or 'sedentary' in k])}")

    print("\n[OK] Trigger引擎测试通过!")


@pytest.mark.asyncio
async def test_integration_scenario():
    """测试集成场景"""
    print("\n" + "=" * 60)
    print("测试3: 端到端集成场景")
    print("=" * 60)

    engine = get_trigger_engine()

    # 场景：用户早晨消息 + 设备数据
    print("\n[场景] 用户早晨报告 + 设备数据同步")
    print("-" * 60)

    user_message = "早上好，今天感觉有点累，昨晚没睡好，刚测了血糖有点高"
    hrv_data = [65, 68, 62, 60, 66, 64]  # 低HRV，表示压力/疲劳
    glucose_data = [6.5, 7.2, 11.5, 13.2, 12.8, 11.0, 9.5]  # 高血糖+波动

    print(f"用户消息: {user_message}")
    print(f"HRV数据: {hrv_data[:3]}... (共{len(hrv_data)}个点)")
    print(f"血糖数据: {glucose_data[:3]}... (共{len(glucose_data)}个点)")

    # 识别Triggers
    print("\n[*] Trigger识别中...")
    triggers = await engine.recognize_triggers(
        user_id=1,
        text_content=user_message,
        hrv_values=hrv_data,
        glucose_values=glucose_data
    )

    print(f"\n[OK] 识别到 {len(triggers)} 个Triggers:")
    for i, trigger in enumerate(triggers, 1):
        print(f"\n{i}. {trigger.name} ({trigger.tag_id})")
        print(f"   - 类别: {trigger.category.value}")
        print(f"   - 严重程度: {trigger.severity.value}")
        print(f"   - 置信度: {trigger.confidence:.2f}")
        print(f"   - 元数据: {trigger.metadata}")

    # 模拟路由决策
    print("\n" + "-" * 60)
    print("[ROUTING] 路由决策建议:")

    # 按严重程度分组
    critical = [t for t in triggers if t.severity.value == "critical"]
    high = [t for t in triggers if t.severity.value == "high"]
    moderate = [t for t in triggers if t.severity.value == "moderate"]

    if critical:
        print(f"\n[!] CRITICAL级别 ({len(critical)}个):")
        for t in critical:
            print(f"   - {t.name}")
        print("   建议: 立即启动 CrisisAgent")

    if high:
        print(f"\n[!] HIGH级别 ({len(high)}个):")
        for t in high:
            print(f"   - {t.name}")
        print("   建议: 启动 GlucoseAgent + MentalHealthAgent")

    if moderate:
        print(f"\n[!] MODERATE级别 ({len(moderate)}个):")
        for t in moderate:
            print(f"   - {t.name}")
        print("   建议: 启动 SleepAgent + StressAgent")

    print("\n[OK] 端到端场景测试完成!")


async def main():
    """主测试函数"""
    try:
        # 测试1: 多模态客户端
        await test_multimodal_client()

        # 测试2: Trigger引擎
        await test_trigger_engine()

        # 测试3: 集成场景
        await test_integration_scenario()

        print("\n" + "=" * 60)
        print("[SUCCESS] 所有测试通过!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
