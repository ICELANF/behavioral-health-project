"""
BehaviorOS V4.0 系统验证脚本
基于实际项目结构 (D:\\behavioral-health-project)
使用: python verify_behavioros.py
"""

import os, sys, json, time
from datetime import datetime
from pathlib import Path
from collections import defaultdict

BASE_URL = "http://localhost:8000"
AUTH_TOKEN = ""  # 填你的Bearer token
PROJECT_ROOT = Path(__file__).parent

# ============================================
# 第一层: 静态结构验证 (不需要启动服务)
# ============================================

EXPECTED_STRUCTURE = {
    "Sprint 0 - 基础层 (MEU-01~08)": {
        "api": [
            "api/main.py", "api/auth.py", "api/auth_api.py", "api/user_api.py",
            "api/config.py", "api/database.py", "api/dependencies.py",
            "api/schemas.py", "api/routes.py",
            "api/routers/health.py", "api/routers/auth.py",
        ],
        "core": [
            "core/auth.py", "core/database.py", "core/health.py",
            "core/logging_config.py", "core/middleware.py", "core/models.py",
        ],
        "migration": [
            "alembic/versions/001_initial_schema.py",
            "alembic/versions/002_full_schema.py",
        ],
    },
    "Sprint 1 - 治理层 (MEU-09~20)": {
        "api": [
            "api/agent_api.py", "api/agent_ecosystem_api.py",
            "api/agent_feedback_api.py", "api/agent_template_api.py",
            "api/baps_api.py", "api/chat_rest_api.py", "api/chat_history.py",
            "api/policy_api.py", "api/governance_api.py", "api/safety_api.py",
            "api/assessment_api.py", "api/assessment_assignment_api.py",
            "api/assessment_pipeline_api.py",
            "api/survey_api.py", "api/survey_response_api.py", "api/survey_stats_api.py",
            "api/device_rest_api.py", "api/device_data.py",
            "api/device_alert_api.py", "api/device_trigger.py",
            "api/knowledge.py", "api/knowledge_sharing_api.py",
            "api/learning_api.py", "api/batch_ingestion_api.py",
            "api/coach_api.py", "api/coach_message_api.py",
            "api/coach_push_queue_api.py", "api/tenant_api.py",
            "api/routers/chat.py", "api/routers/assessment.py",
            "api/routers/diagnostic.py", "api/routers/knowledge.py",
            "api/routers/tracking.py",
        ],
        "core": [
            "core/master_agent.py",
            "core/agents/master_agent.py", "core/agents/router.py",
            "core/agents/coordinator.py", "core/agents/policy_gate.py",
            "core/agents/specialist_agents.py", "core/agents/trust_guide_agent.py",
            "core/agents/generic_llm_agent.py", "core/agents/base.py",
            "core/policy_engine.py", "core/conflict_resolver.py",
            "core/decision_core.py", "core/decision_models.py",
            "core/decision_trace.py", "core/cost_controller.py",
            "core/cost_attribution.py",
            "core/brain/decision_engine.py", "core/brain/pattern_detector.py",
            "core/brain/policy_gate.py", "core/brain/stage_runtime.py",
            "core/baps/scoring_engine.py", "core/baps/questionnaires.py",
            "core/baps/report_generator.py",
            "core/behavioral_profile.py", "core/behavioral_profile_service.py",
            "core/behavior_facts_service.py",
            "core/safety/input_filter.py", "core/safety/output_filter.py",
            "core/safety/generation_guard.py", "core/safety/pipeline.py",
            "core/safety/rag_safety.py",
            "core/knowledge/retriever.py", "core/knowledge/chunker.py",
            "core/knowledge/embedding_service.py", "core/knowledge/document_service.py",
            "core/knowledge/sharing_service.py", "core/knowledge/batch_ingestion_service.py",
            "core/assessment_engine.py", "core/diagnostic_pipeline.py",
            "core/survey_service.py",
        ],
        "agents": [
            "agents/base.py", "agents/base_agent.py", "agents/collaboration.py",
            "agents/factory.py", "agents/octopus_engine.py", "agents/octopus_fsm.py",
            "agents/orchestrator.py", "agents/registry.py", "agents/router.py",
            "agents/snapshot_factory.py", "agents/workflow_engine.py",
        ],
        "baps": [
            "baps/cause_scoring.py", "baps/health_competency_assessment.py",
            "baps/obstacle_assessment.py", "baps/progressive_assessment.py",
            "baps/spi_calculator.py", "baps/urgency_assessment.py",
        ],
        "migration": [
            "alembic/versions/003_add_behavioral_profiles.py",
            "alembic/versions/004_add_micro_actions_and_messaging.py",
            "alembic/versions/005_add_assessment_assignments.py",
            "alembic/versions/006_add_device_alerts.py",
            "alembic/versions/007_add_challenge_tables.py",
            "alembic/versions/008_add_coach_push_queue.py",
            "alembic/versions/009_add_food_analyses.py",
            "alembic/versions/010_add_tenant_tables.py",
            "alembic/versions/011_add_knowledge_tables.py",
            "alembic/versions/012_add_raw_content_to_knowledge_doc.py",
            "alembic/versions/013_add_content_governance.py",
            "alembic/versions/014_add_content_interaction_models.py",
            "alembic/versions/015_add_learning_persistence_models.py",
            "alembic/versions/016_add_exam_activity_ingestion_models.py",
            "alembic/versions/017_add_knowledge_domains_and_file_columns.py",
            "alembic/versions/018_survey_engine.py",
            "alembic/versions/019_v3_diagnostic_pipeline.py",
            "alembic/versions/020_fix_orm_db_drift.py",
            "alembic/versions/021_safety_and_audio.py",
            "alembic/versions/022_agent_templates.py",
            "alembic/versions/023_routing_config.py",
            "alembic/versions/024_knowledge_sharing.py",
            "alembic/versions/025_feedback_learning.py",
            "alembic/versions/026_agent_ecosystem.py",
            "alembic/versions/027_v002_v003_catchup.py",
        ],
    },
    "Sprint 2 - 价值重塑 (MEU-21~26)": {
        "api": [
            "api/micro_action_api.py", "api/challenge_api.py",
            "api/companion_api.py", "api/journey_api.py",
            "api/reflection_api.py", "api/food_recognition_api.py",
            "api/content_api.py", "api/content_contribution_api.py",
            "api/content_manage_api.py", "api/program_api.py",
            "api/paths_api.py", "api/question_api.py",
            "api/high_freq_api.py", "api/exam_api.py",
            "api/exam_session_api.py", "api/routers/incentive.py",
        ],
        "core": [
            "core/stage_engine.py", "core/stage_mapping.py",
            "core/stage_aware_selector.py", "core/stage_personalization.py",
            "core/dual_track_engine.py",
            "core/intervention_matcher.py", "core/intervention_strategy_engine.py",
            "core/intervention_tracker.py", "core/intervention_combinations.py",
            "core/micro_action_service.py", "core/challenge_service.py",
            "core/companion_tracker.py", "core/reflection_service.py",
            "core/high_freq_question_service.py", "core/content_access_service.py",
            "core/program_service.py", "core/course_stage_mapping.py",
            "core/implicit_data.py", "core/trust_score_service.py",
        ],
        "migration": [
            "alembic/versions/028_policy_engine.py",
            "alembic/versions/029_skill_graph.py",
            "alembic/versions/030_behavior_rx_foundation.py",
            "alembic/versions/031_expert_self_registration.py",
        ],
    },
    "Sprint 3 - 体系完善 (MEU-27~32)": {
        "api": [
            "api/expert_agent_api.py", "api/expert_content_api.py",
            "api/expert_registration_api.py",
            "api/analytics_api.py", "api/admin_analytics_api.py",
            "api/user_stats_api.py", "api/credits_api.py",
            "api/script_library_api.py", "api/search_api.py",
            "api/segments_api.py", "api/reminder_api.py",
        ],
        "core": [
            "core/expert_analytics.py", "core/effectiveness_metrics.py",
            "core/feedback_service.py", "core/data_visibility_service.py",
            "core/data_extractor.py", "core/rule_registry.py",
            "core/scheduler.py", "core/user_segments.py",
            "core/script_library_service.py", "core/reminder_service.py",
            "core/milestone_service.py", "core/responsibility_tracker.py",
            "core/privacy_impact.py",
        ],
        "migration": [
            "alembic/versions/032_v4_foundation.py",
            "alembic/versions/033_stage_engine_and_governance.py",
        ],
    },
    "Sprint 4 - 生态激活 (MEU-33~37)": {
        "api": [
            "api/peer_matching_api.py", "api/peer_support_api.py",
            "api/ecosystem_v4_api.py", "api/incentive_phase_api.py",
            "api/promotion_api.py", "api/push_recommendation_api.py",
            "api/agency_api.py", "api/advanced_rights_api.py",
            "api/upload_api.py", "api/miniprogram.py",
            "api/xingjian_api.py", "api/websocket_api.py",
            "api/v14/routes.py", "api/v14/admin_routes.py",
            "api/v14/copilot_routes.py", "api/v14/disclosure_routes.py",
            "api/v14/quality_routes.py",
        ],
        "core": [
            "core/peer_matching_service.py", "core/peer_support_service.py",
            "core/ecosystem_service.py", "core/incentive_phase_engine.py",
            "core/incentive_integration.py", "core/promotion_service.py",
            "core/push_recommendation_service.py",
            "core/agency_engine.py", "core/agency_service.py",
            "core/referral_engine.py", "core/auto_exit_handler.py",
            "core/unified_narrative_service.py", "core/tcm_integration.py",
            "core/v14/rhythm_engine.py", "core/v14/trigger_router.py",
            "core/v14/agents.py", "core/agents/v4_agents.py",
        ],
        "behavior_rx": [
            "behavior_rx/behavior_rx_engine.py",
            "behavior_rx/agent_collaboration_orchestrator.py",
            "behavior_rx/agent_handoff_service.py",
            "behavior_rx/master_agent_integration.py",
            "behavior_rx/rx_models.py", "behavior_rx/rx_routes.py",
            "behavior_rx/rx_schemas.py",
            "behavior_rx/core/rx_conflict_resolver.py",
            "behavior_rx/core/behavior_rx_engine.py",
            "behavior_rx/agents/adherence_expert_agent.py",
            "behavior_rx/agents/behavior_coach_agent.py",
            "behavior_rx/agents/cardiac_expert_agent.py",
            "behavior_rx/agents/metabolic_expert_agent.py",
            "behavior_rx/agents/base_expert_agent.py",
        ],
        "migration": [
            "alembic/versions/034_v4_sprint2_sprint3.py",
        ],
    },
}


def verify_structure():
    """第一层: 文件结构验证"""
    print("=" * 70)
    print("  第一层: 项目文件结构验证")
    print(f"  路径: {PROJECT_ROOT}")
    print("=" * 70)

    all_results = {}
    grand_found = grand_missing = 0

    for sprint, categories in EXPECTED_STRUCTURE.items():
        print(f"\n── {sprint} ──")
        s_found = s_missing = 0
        missing_list = []

        for cat, files in categories.items():
            for f in files:
                fp = PROJECT_ROOT / f.replace("/", os.sep)
                if fp.exists():
                    s_found += 1
                else:
                    s_missing += 1
                    missing_list.append(f"[{cat}] {f}")

        total = s_found + s_missing
        pct = s_found / total * 100 if total else 0
        bar = "#" * int(pct / 5) + "." * (20 - int(pct / 5))
        print(f"  [{bar}] {s_found}/{total} ({pct:.0f}%)")

        if missing_list:
            for m in missing_list[:8]:
                print(f"    x {m}")
            if len(missing_list) > 8:
                print(f"    ... +{len(missing_list) - 8} more")

        grand_found += s_found
        grand_missing += s_missing
        all_results[sprint] = {"found": s_found, "missing": s_missing, "missing_files": missing_list}

    grand_total = grand_found + grand_missing
    print(f"\n  总计: {grand_found}/{grand_total} ({grand_found/grand_total*100:.0f}%)")
    if grand_missing == 0:
        print("  >>> 全部文件存在!")
    else:
        print(f"  >>> {grand_missing} 个文件缺失")
    return all_results


def verify_migrations():
    """第二层: Alembic迁移链验证"""
    print("\n" + "=" * 70)
    print("  第二层: Alembic迁移链验证 (001-034)")
    print("=" * 70)

    mdir = PROJECT_ROOT / "alembic" / "versions"
    if not mdir.exists():
        print("  x 迁移目录不存在")
        return

    files = sorted([f.name for f in mdir.glob("[0-9]*.py")])
    nums = []
    for f in files:
        try:
            nums.append(int(f.split("_")[0]))
        except ValueError:
            pass

    print(f"  发现 {len(nums)} 个迁移文件")

    gaps = []
    for i in range(1, 35):
        if i not in nums:
            gaps.append(f"{i:03d}")

    if gaps:
        print(f"  x 缺失编号: {', '.join(gaps)}")
    else:
        print(f"  >>> 001-034 连续完整!")

    # 检查最新迁移
    if nums:
        print(f"  最新迁移: {max(nums):03d}")
    print(f"\n  手动确认: alembic current / alembic history")


def verify_main_routes():
    """第三层: 检查main.py路由注册"""
    print("\n" + "=" * 70)
    print("  第三层: main.py 路由注册检查")
    print("=" * 70)

    main_path = PROJECT_ROOT / "api" / "main.py"
    if not main_path.exists():
        print("  x api/main.py 不存在")
        return

    content = main_path.read_text(encoding="utf-8", errors="ignore")

    api_dir = PROJECT_ROOT / "api"
    api_modules = sorted([f.stem for f in api_dir.glob("*_api.py")])

    registered = []
    unregistered = []
    for mod in api_modules:
        if mod in content:
            registered.append(mod)
        else:
            unregistered.append(mod)

    print(f"  共 {len(api_modules)} 个 *_api.py 模块")
    print(f"  已注册: {len(registered)}")
    print(f"  未注册: {len(unregistered)}")

    if unregistered:
        print(f"\n  可能未注册的模块:")
        for u in unregistered:
            print(f"    ? {u}.py")
    else:
        print(f"  >>> 全部API模块已在main.py中引用!")

    # 同样检查 routers 和 v14
    for subdir in ["routers", "v14"]:
        rdir = api_dir / subdir
        if rdir.exists():
            router_files = [f.stem for f in rdir.glob("*.py")
                           if f.stem != "__init__"]
            found_in_main = [r for r in router_files if r in content or subdir in content]
            print(f"\n  api/{subdir}/: {len(router_files)} 个文件, "
                  f"{len(found_in_main)} 个在main.py中引用")


def verify_endpoints():
    """第四层: HTTP端点存活检查"""
    print("\n" + "=" * 70)
    print("  第四层: HTTP端点存活验证")
    print(f"  目标: {BASE_URL}")
    print("=" * 70)

    try:
        import requests
    except ImportError:
        print("  需要: pip install requests")
        return

    # 检查服务
    try:
        r = requests.get(f"{BASE_URL}/docs", timeout=5)
        print(f"  服务在线 (status={r.status_code})")
    except requests.ConnectionError:
        print(f"  x 无法连接 {BASE_URL}")
        print(f"  请先启动服务，然后重新运行此脚本")
        return

    # 从OpenAPI自动发现
    print("\n  从 /openapi.json 自动发现路由...")
    try:
        r = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
        if r.status_code != 200:
            print(f"  x OpenAPI不可用 (status={r.status_code})")
            return

        schema = r.json()
        paths = schema.get("paths", {})
        print(f"  发现 {len(paths)} 个路由路径")

        session = requests.Session()
        session.headers["Content-Type"] = "application/json"
        if AUTH_TOKEN:
            session.headers["Authorization"] = AUTH_TOKEN

        stats = {"pass": 0, "fail": 0, "warn": 0}

        print(f"\n  {'方法':>7s} {'路径':45s} {'状态':>5s} {'耗时':>8s}")
        print(f"  {'─' * 70}")

        for path, methods_info in sorted(paths.items()):
            for method in methods_info:
                method = method.upper()
                if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    continue

                url = f"{BASE_URL}{path}"
                try:
                    start = time.time()
                    if method == "GET":
                        resp = session.get(url, timeout=10)
                    else:
                        resp = session.request(method, url, json={}, timeout=10)
                    ms = round((time.time() - start) * 1000, 1)

                    if resp.status_code in (200, 201, 204, 422):
                        icon = "v"
                        stats["pass"] += 1
                    elif resp.status_code in (401, 403):
                        icon = "~"
                        stats["warn"] += 1
                    else:
                        icon = "x"
                        stats["fail"] += 1

                    print(f"  {icon} {method:>6s} {path:45s} {resp.status_code:>5d} {ms:>6.0f}ms")

                except Exception as e:
                    print(f"  x {method:>6s} {path:45s} ERROR {str(e)[:20]}")
                    stats["fail"] += 1

        total = sum(stats.values())
        print(f"\n  端点汇总: {total}个")
        print(f"    v PASS: {stats['pass']}  (200/201/422)")
        print(f"    ~ WARN: {stats['warn']}  (401/403 认证)")
        print(f"    x FAIL: {stats['fail']}  (404/500+)")

        if stats["fail"] == 0:
            print(f"  >>> 全部端点存活!")

    except Exception as e:
        print(f"  x OpenAPI解析失败: {e}")


def verify_agents():
    """第五层: Agent注册一致性"""
    print("\n" + "=" * 70)
    print("  第五层: Agent体系一致性")
    print("=" * 70)

    locations = {
        "agents/":           PROJECT_ROOT / "agents",
        "core/agents/":      PROJECT_ROOT / "core" / "agents",
        "behavior_rx/agents/": PROJECT_ROOT / "behavior_rx" / "agents",
    }

    for label, path in locations.items():
        if path.exists():
            files = [f.stem for f in path.glob("*.py")
                    if f.stem not in ("__init__", "base", "base_agent", "base_expert_agent", "prompts")]
            print(f"\n  {label} ({len(files)} modules)")
            for f in sorted(files):
                print(f"    - {f}")
        else:
            print(f"\n  {label} (不存在)")

    # 检查 octopus_engine 和 master_agent 的关联
    print(f"\n  关键调度链:")
    chain_files = [
        "agents/octopus_engine.py",
        "agents/router.py",
        "core/agents/master_agent.py",
        "core/agents/coordinator.py",
        "core/agents/policy_gate.py",
        "core/policy_engine.py",
        "core/conflict_resolver.py",
        "core/decision_trace.py",
    ]
    for f in chain_files:
        fp = PROJECT_ROOT / f.replace("/", os.sep)
        exists = "v" if fp.exists() else "x"
        print(f"    {exists} {f}")


# ============================================
# 主入口
# ============================================

if __name__ == "__main__":
    print()
    print("  +=============================================+")
    print("  |  BehaviorOS V4.0 系统验证 (完整版)          |")
    print("  |  37 MEU / 80+ 端点 / 34 迁移 / 5 Sprint    |")
    print("  +=============================================+")
    print()

    verify_structure()
    verify_migrations()
    verify_main_routes()
    verify_endpoints()
    verify_agents()

    # 保存报告
    print("\n" + "=" * 70)
    print("  验证完成")
    print("=" * 70)
    print("""
  使用方式:
    python verify_behavioros.py             完整验证(建议先启动服务)
    python verify_behavioros.py > report.txt  保存输出到文件

  后续动作:
    1. 缺失文件 -> 检查是否改名或路径变更
    2. 迁移断号 -> alembic current / alembic upgrade head
    3. 端点FAIL -> 检查main.py路由注册
    4. Agent链断 -> 检查import依赖
""")
