import asyncio
from datetime import datetime
from core.decision_models import DecisionContext, BloodGlucoseData
from core.decision_core import DecisionCore

async def dry_run_test():
    print("🚀 正在启动老张的健康干预决策模拟...")
    
    # 1. 模拟老张的当前状态
    glucose = BloodGlucoseData(
        value=12.5,  # 模拟高血糖
        meal_relation="after_meal",
        timestamp=datetime.now()
    )
    
    context = DecisionContext(
        user_id=1001,
        user_name="老张",
        current_glucose=glucose,
        recent_triggers=["glucose_spike", "sedentary"],
        behavioral_tags=["compliance_low"]
    )
    
    # 2. 初始化决策大脑
    # 注意：这里会尝试加载 DecisionCore，它会引用你刚写的轻量化 trigger_engine
    engine = DecisionCore()
    
    print(f"📊 当前状态：用户={context.user_name}, 血糖={glucose.value} {glucose.unit}")
    print("🧠 正在生成干预建议...\n")
    
    # 3. 第一次调用（走 Dify）
    import time
    t1 = time.time()
    result = await engine.decide_intervention(context)
    elapsed1 = time.time() - t1

    print("-" * 30)
    print(f"✅ 第一次调用（Dify）  耗时: {elapsed1:.2f}s")
    print(f"策略名称: {result['strategy_name']}")
    print(f"建议内容: {result['content']}")
    print(f"优先级: {result['priority']}")
    print("-" * 30)

    # 4. 第二次调用（应命中缓存）
    t2 = time.time()
    result2 = await engine.decide_intervention(context)
    elapsed2 = time.time() - t2

    print(f"\n✅ 第二次调用（缓存）  耗时: {elapsed2:.4f}s")
    print(f"建议内容: {result2['content'][:60]}...")
    print("-" * 30)

if __name__ == "__main__":
    asyncio.run(dry_run_test())