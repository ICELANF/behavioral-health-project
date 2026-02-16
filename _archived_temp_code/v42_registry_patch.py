"""
V4.2 Agent注册表更新 — 28个Agent全部实现

执行: python v42_registry_patch.py patch /path/to/project [--dry-run|--apply]

做的事:
  1. 更新 assistant_agents/registry.py 的 AGENT_CLASSES 映射
  2. 更新 professional_agents/registry.py 的 AGENT_CLASSES 映射
  3. 确保新文件的 import 正确
"""
import sys
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# 用户层 12 Agent → 类映射
# ═══════════════════════════════════════════════════════════

ASSISTANT_REGISTRY = """
# V4.2 — 全部12个Agent已实现

AGENT_CLASSES = {
    # V4.1 已实现
    "health_assistant":    "assistant_agents.agents.health_assistant.Agent",

    # V4.2 P0 — 安全+引导
    "crisis_responder":    "assistant_agents.agents.crisis_responder.Agent",
    "onboarding_guide":    "assistant_agents.agents.onboarding_guide.Agent",

    # V4.2 — 四大领域
    "nutrition_guide":     "assistant_agents.agents.domain_agents.NutritionGuideAgent",
    "exercise_guide":      "assistant_agents.agents.domain_agents.ExerciseGuideAgent",
    "sleep_guide":         "assistant_agents.agents.domain_agents.SleepGuideAgent",
    "emotion_support":     "assistant_agents.agents.domain_agents.EmotionSupportAgent",

    # V4.2 — 辅助Agent
    "tcm_wellness":        "assistant_agents.agents.remaining_agents.TcmWellnessAgent",
    "motivation_support":  "assistant_agents.agents.remaining_agents.MotivationSupportAgent",
    "habit_tracker":       "assistant_agents.agents.remaining_agents.HabitTrackerAgent",
    "community_guide":     "assistant_agents.agents.remaining_agents.CommunityGuideAgent",
    "content_recommender": "assistant_agents.agents.remaining_agents.ContentRecommenderAgent",
}
"""

# ═══════════════════════════════════════════════════════════
# 教练层 16 Agent → 类映射
# ═══════════════════════════════════════════════════════════

PROFESSIONAL_REGISTRY = """
# V4.2 — 全部16个Agent已实现

AGENT_CLASSES = {
    # V4.1 已实现
    "behavior_coach":      "professional_agents.agents.behavior_coach.Agent",

    # V4.2 P0 — 双引擎
    "assessment_engine":   "professional_agents.agents.core_engines.AssessmentEngineAgent",
    "rx_composer":         "professional_agents.agents.core_engines.RxComposerAgent",

    # V4.2 — 9个领域专家
    "metabolic_expert":    "professional_agents.agents.remaining_agents.MetabolicExpertAgent",
    "cardiac_rehab":       "professional_agents.agents.remaining_agents.CardiacRehabAgent",
    "adherence_monitor":   "professional_agents.agents.remaining_agents.AdherenceMonitorAgent",
    "nutrition_expert":    "professional_agents.agents.remaining_agents.NutritionExpertAgent",
    "exercise_expert":     "professional_agents.agents.remaining_agents.ExerciseExpertAgent",
    "sleep_expert":        "professional_agents.agents.remaining_agents.SleepExpertAgent",
    "tcm_expert":          "professional_agents.agents.remaining_agents.TcmExpertAgent",
    "mental_expert":       "professional_agents.agents.remaining_agents.MentalExpertAgent",
    "chronic_manager":     "professional_agents.agents.remaining_agents.ChronicManagerAgent",

    # V4.2 — 康复+教育
    "rehab_expert":        "professional_agents.agents.remaining_agents.RehabExpertAgent",
    "health_educator":     "professional_agents.agents.remaining_agents.HealthEducatorAgent",

    # V4.2 — 督导+质控
    "supervisor_reviewer": "professional_agents.agents.remaining_agents.SupervisorReviewerAgent",
    "quality_auditor":     "professional_agents.agents.remaining_agents.QualityAuditorAgent",
}
"""


def patch(app_dir: str, dry_run: bool = True):
    app = Path(app_dir)
    mode = "DRY RUN" if dry_run else "APPLY"
    print(f"\nV4.2 注册表更新 [{mode}]\n")

    # 用户层
    assistant_reg = app / "assistant_agents" / "registry.py"
    if assistant_reg.exists():
        content = assistant_reg.read_text(errors="ignore")
        if "crisis_responder" not in content:
            print(f"  {'[DRY]' if dry_run else '[FIX]'} {assistant_reg}: 更新AGENT_CLASSES")
            if not dry_run:
                # 替换AGENT_CLASSES块
                import re
                new_content = re.sub(
                    r'AGENT_CLASSES\s*=\s*\{[^}]*\}',
                    ASSISTANT_REGISTRY.strip().split('\n\n')[-1],
                    content, flags=re.DOTALL
                )
                if new_content == content:
                    # 没匹配到，追加
                    new_content = content + "\n\n" + ASSISTANT_REGISTRY
                assistant_reg.write_text(new_content)
        else:
            print(f"  ⏭  {assistant_reg}: 已包含V4.2 Agent")
    else:
        print(f"  ⚠️  {assistant_reg}: 不存在")

    # 教练层
    professional_reg = app / "professional_agents" / "registry.py"
    if professional_reg.exists():
        content = professional_reg.read_text(errors="ignore")
        if "assessment_engine" not in content:
            print(f"  {'[DRY]' if dry_run else '[FIX]'} {professional_reg}: 更新AGENT_CLASSES")
            if not dry_run:
                import re
                new_content = re.sub(
                    r'AGENT_CLASSES\s*=\s*\{[^}]*\}',
                    PROFESSIONAL_REGISTRY.strip().split('\n\n')[-1],
                    content, flags=re.DOTALL
                )
                if new_content == content:
                    new_content = content + "\n\n" + PROFESSIONAL_REGISTRY
                professional_reg.write_text(new_content)
        else:
            print(f"  ⏭  {professional_reg}: 已包含V4.2 Agent")
    else:
        print(f"  ⚠️  {professional_reg}: 不存在")

    # 新增文件清单
    new_files = [
        "assistant_agents/agents/crisis_responder.py",
        "assistant_agents/agents/onboarding_guide.py",
        "assistant_agents/agents/domain_agents.py",
        "assistant_agents/agents/remaining_agents.py",
        "professional_agents/agents/core_engines.py",
        "professional_agents/agents/remaining_agents.py",
    ]
    print(f"\n  新增文件:")
    for f in new_files:
        fpath = app / f
        exists = "✅" if fpath.exists() else "❌ 需复制"
        print(f"    {exists} {f}")

    print(f"""
{'═'*60}
  V4.2 执行步骤
{'═'*60}

  1. 复制6个新Agent文件到项目:
     cp assistant_agents/agents/crisis_responder.py   项目/assistant_agents/agents/
     cp assistant_agents/agents/onboarding_guide.py   项目/assistant_agents/agents/
     cp assistant_agents/agents/domain_agents.py      项目/assistant_agents/agents/
     cp assistant_agents/agents/remaining_agents.py   项目/assistant_agents/agents/
     cp professional_agents/agents/core_engines.py    项目/professional_agents/agents/
     cp professional_agents/agents/remaining_agents.py 项目/professional_agents/agents/

  2. 更新注册表:
     python v42_registry_patch.py patch . --apply

  3. 修改import路径（..base → 实际路径）

  4. 验证:
     curl http://localhost:8000/v1/assistant/agents   # 应返回12个
     curl http://localhost:8000/v1/agent/agents        # 应返回16个

  5. 冒烟回归:
     python -m pytest smoke_tests/ -v --tb=short
     python -m pytest test_integration.py -v --tb=short

  6. 提交:
     git add assistant_agents/ professional_agents/
     git commit -m "V4.2: 26个stub Agent全部实现 (12用户+16教练)"
     git push
""")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "patch":
        target = sys.argv[2] if len(sys.argv) > 2 else "."
        dry = "--apply" not in sys.argv
        patch(target, dry_run=dry)
    elif cmd == "show":
        print("=== 用户层 ===")
        print(ASSISTANT_REGISTRY)
        print("=== 教练层 ===")
        print(PROFESSIONAL_REGISTRY)
    else:
        print(__doc__)
