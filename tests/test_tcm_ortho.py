"""
中医骨科康复 — 测试套件

测试范围:
  1. 安全门规则 (50+ 边界用例)
  2. 评估引擎 (PainScale/PainAssess/TCMSyndrome/RehabStage)
  3. Agent基础流程 (意图识别/功法匹配/分期逻辑)
  4. 路由注册完整性

运行: pytest test_tcm_ortho.py -v
"""
import sys
import os
import pytest

# 添加项目根路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.safety.safety_rules_ortho import (
    OrthoSafetyGate, SafetyLevel, SafetyCheckResult,
    RED_FLAG_PATTERNS, HIGH_RISK_PATTERNS, BOUNDARY_PATTERNS,
    SPECIAL_POPULATION_TAGS,
)
from core.engines.pain_engines import (
    PainScaleEngine, PainAssessEngine, TCMSyndromeEngine, RehabStageEngine,
    PainIntensity, PainType, PainCatastrophizingScore, PainSelfEfficacyScore,
    RehabStage,
)
from api.routes_tcm_ortho import (
    TCM_ORTHO_AGENT_REGISTRY, GATEWAY_EXTENSIONS,
    get_user_layer_agents, get_coach_layer_agents,
)


# ================================================================
# 1. 安全门测试
# ================================================================

class TestOrthoSafetyGate:
    """骨科安全门规则测试"""

    def setup_method(self):
        self.gate = OrthoSafetyGate()

    # ── L1 红旗症状 ──

    def test_l1_severe_headache_with_consciousness(self):
        result = self.gate.check("剧烈头痛伴意识模糊")
        assert result.level == SafetyLevel.L1_EMERGENCY
        assert result.should_halt is True
        assert result.notify_coach is True

    def test_l1_chest_pain_breathing(self):
        result = self.gate.check("胸痛而且呼吸困难很严重")
        assert result.level == SafetyLevel.L1_EMERGENCY

    def test_l1_sudden_limb_weakness(self):
        result = self.gate.check("左腿突发无力站不起来")
        assert result.level == SafetyLevel.L1_EMERGENCY

    def test_l1_fracture_suspicion(self):
        result = self.gate.check("摔倒后手臂畸形变形疑似骨折")
        assert result.level == SafetyLevel.L1_EMERGENCY

    def test_l1_cauda_equina(self):
        result = self.gate.check("腰痛伴鞍区麻木和大小便失禁")
        assert result.level == SafetyLevel.L1_EMERGENCY

    def test_l1_spinal_cord_injury(self):
        result = self.gate.check("车祸后脊柱剧痛怀疑脊柱损伤")
        assert result.level == SafetyLevel.L1_EMERGENCY

    def test_l1_open_fracture(self):
        result = self.gate.check("伤口可见骨头外露了")
        assert result.level == SafetyLevel.L1_EMERGENCY

    # ── L2 高风险信号 ──

    def test_l2_high_pain_persistent(self):
        result = self.gate.check("疼痛评分9分持续三天了")
        assert result.level == SafetyLevel.L2_REFER
        assert result.notify_coach is True

    def test_l2_night_pain_2weeks(self):
        result = self.gate.check("夜间痛影响睡眠已经超过两周了")
        assert result.level == SafetyLevel.L2_REFER

    def test_l2_progressive_pain(self):
        result = self.gate.check("最近三个月疼痛进行性加重")
        assert result.level == SafetyLevel.L2_REFER

    def test_l2_fever_joint_pain(self):
        result = self.gate.check("发热伴关节疼痛红肿")
        assert result.level == SafetyLevel.L2_REFER

    def test_l2_pain_score_trigger(self):
        result = self.gate.check("腰疼不舒服", pain_score=8)
        assert result.level == SafetyLevel.L2_REFER

    # ── L3 边界约束 ──

    def test_l3_request_prescription(self):
        result = self.gate.check("能不能帮我开个中药方")
        assert result.level == SafetyLevel.L3_BOUNDARY

    def test_l3_request_diagnosis(self):
        result = self.gate.check("我这到底诊断是什么病")
        assert result.level == SafetyLevel.L3_BOUNDARY

    def test_l3_surgery_advice(self):
        result = self.gate.check("手术方案选择微创还是开放好")
        assert result.level == SafetyLevel.L3_BOUNDARY

    def test_l3_injection(self):
        result = self.gate.check("封闭注射效果怎么样")
        assert result.level == SafetyLevel.L3_BOUNDARY

    # ── L4 特殊人群 ──

    def test_l4_pregnant_tag(self):
        result = self.gate.check("肩膀疼", user_tags=["pregnant"])
        assert result.level == SafetyLevel.L4_SPECIAL_POP
        assert len(result.contraindications) > 0

    def test_l4_pregnant_text(self):
        result = self.gate.check("我怀孕5个月了腰疼怎么办")
        assert result.level == SafetyLevel.L4_SPECIAL_POP

    def test_l4_osteoporosis(self):
        # 严重骨质疏松同时触发L2(就医)和L4(特殊人群), L2优先级更高
        result = self.gate.check("骨密度检查T值-3.0严重骨质疏松")
        assert result.level == SafetyLevel.L2_REFER  # L2优先于L4
        assert "osteoporosis_severe" in str(result.triggered_rules)  # L4也被检出

    def test_l4_tumor(self):
        result = self.gate.check("有骨转移癌症患者可以按摩吗")
        assert result.level == SafetyLevel.L4_SPECIAL_POP

    def test_l4_coagulation(self):
        result = self.gate.check("长期服用华法林可以拔罐吗")
        assert result.level == SafetyLevel.L4_SPECIAL_POP

    # ── SAFE 正常情况 ──

    def test_safe_normal_query(self):
        result = self.gate.check("颈椎不舒服有什么日常保健方法")
        assert result.level == SafetyLevel.SAFE

    def test_safe_gongfa_query(self):
        result = self.gate.check("八段锦第一式怎么做")
        assert result.level == SafetyLevel.SAFE

    def test_safe_daily_care(self):
        result = self.gate.check("办公室坐姿怎样对腰好")
        assert result.level == SafetyLevel.SAFE

    # ── 优先级测试 ──

    def test_priority_l1_over_l4(self):
        """L1应优先于L4"""
        result = self.gate.check(
            "我怀孕了现在剧烈头痛伴呕吐意识模糊",
            user_tags=["pregnant"]
        )
        assert result.level == SafetyLevel.L1_EMERGENCY

    def test_priority_l1_over_l3(self):
        """L1应优先于L3"""
        result = self.gate.check("能帮我诊断吗我现在肢体突发无力")
        assert result.level == SafetyLevel.L1_EMERGENCY


# ================================================================
# 2. 评估引擎测试
# ================================================================

class TestPainScaleEngine:
    """疼痛评分引擎测试"""

    def setup_method(self):
        self.engine = PainScaleEngine()

    def test_classify_no_pain(self):
        assert self.engine.classify_intensity(0) == PainIntensity.NONE

    def test_classify_mild(self):
        assert self.engine.classify_intensity(2) == PainIntensity.MILD

    def test_classify_moderate(self):
        assert self.engine.classify_intensity(5) == PainIntensity.MODERATE

    def test_classify_severe(self):
        assert self.engine.classify_intensity(7) == PainIntensity.SEVERE

    def test_classify_extreme(self):
        assert self.engine.classify_intensity(9) == PainIntensity.EXTREME

    def test_evaluate_basic(self):
        result = self.engine.evaluate(nrs=6, location="腰部", duration_days=30)
        assert result.scores["nrs"] == 6
        assert result.scores["intensity"] == "中度"
        assert result.scores["is_chronic"] is False

    def test_evaluate_chronic(self):
        result = self.engine.evaluate(nrs=5, location="膝关节", duration_days=100)
        assert result.scores["is_chronic"] is True

    def test_evaluate_high_pain_recommendation(self):
        result = self.engine.evaluate(nrs=9, location="腰部")
        assert any("就诊" in r for r in result.recommendations)

    def test_evaluate_clamp(self):
        result = self.engine.evaluate(nrs=15, location="测试")
        assert result.scores["nrs"] == 10

    def test_functional_impact(self):
        result = self.engine.evaluate(
            nrs=6, location="腰",
            functional_impact={"sleep": 8, "walking": 7, "work": 9}
        )
        assert result.scores["functional_impact_avg"] > 0


class TestPainAssessEngine:
    """多维疼痛评估引擎测试"""

    def setup_method(self):
        self.engine = PainAssessEngine()

    def test_classify_nociceptive(self):
        t = self.engine.classify_pain_type("腰部酸痛胀痛活动后加重")
        assert t == PainType.NOCICEPTIVE

    def test_classify_neuropathic(self):
        t = self.engine.classify_pain_type("放射到腿部有触电感和麻木烧灼感")
        assert t == PainType.NEUROPATHIC

    def test_classify_mixed(self):
        t = self.engine.classify_pain_type("腰部刺痛伴下肢放射痛和麻木")
        assert t == PainType.MIXED

    def test_pcs_scoring(self):
        pcs = PainCatastrophizingScore.from_answers({
            "rum1": 3, "rum2": 4, "mag1": 3, "mag2": 2,
            "hlp1": 4, "hlp2": 3
        })
        assert pcs.total == 19
        assert pcs.level == "临床显著"

    def test_pcs_normal(self):
        pcs = PainCatastrophizingScore.from_answers({
            "rum1": 1, "rum2": 1, "mag1": 1, "mag2": 0,
            "hlp1": 1, "hlp2": 0
        })
        assert pcs.level == "正常"

    def test_pseq_high(self):
        pseq = PainSelfEfficacyScore.from_answers([5, 5, 4, 5])
        assert pseq.level == "高"

    def test_pseq_low(self):
        pseq = PainSelfEfficacyScore.from_answers([1, 2, 1, 2])
        assert pseq.level == "低"

    def test_full_evaluation(self):
        result = self.engine.evaluate(
            pain_description="腰部刺痛伴下肢放射痛",
            nrs_score=7,
            pcs_answers={"rum1": 3, "rum2": 3, "mag1": 2, "mag2": 2,
                          "hlp1": 3, "hlp2": 3},
            pseq_answers=[2, 2, 3, 2],
        )
        assert result.scores["risk_level"] in ["低", "中", "高"]
        assert len(result.recommendations) > 0


class TestTCMSyndromeEngine:
    """中医辨证引擎测试"""

    def setup_method(self):
        self.engine = TCMSyndromeEngine()

    def test_qi_zhi_xue_yu(self):
        candidates = self.engine.preliminary_classify(
            ["刺痛", "固定", "拒按", "夜间加重", "外伤后"]
        )
        assert candidates[0][0] == "气滞血瘀"

    def test_feng_han_shi_bi(self):
        candidates = self.engine.preliminary_classify(
            ["遇冷加重", "游走性", "沉重", "关节僵硬"]
        )
        assert candidates[0][0] == "风寒湿痹"

    def test_gan_shen_kui_xu(self):
        candidates = self.engine.preliminary_classify(
            ["腰膝酸软", "乏力", "绵绵作痛", "久病"]
        )
        assert candidates[0][0] == "肝肾亏虚"

    def test_acupoint_prescription(self):
        aps = self.engine.get_acupoint_prescription("气滞血瘀")
        assert len(aps) > 0
        assert all("name" in ap for ap in aps)

    def test_external_prescription(self):
        exts = self.engine.get_external_prescription("风寒湿痹")
        assert len(exts) > 0

    def test_local_acupoints_lumbar(self):
        local = self.engine._get_local_acupoints("腰部")
        assert any("肾俞" in ap["name"] for ap in local)

    def test_local_acupoints_knee(self):
        local = self.engine._get_local_acupoints("膝关节")
        assert any("膝眼" in ap["name"] for ap in local)

    def test_full_evaluate(self):
        result = self.engine.evaluate(
            symptoms=["刺痛", "固定", "拒按", "外伤后"],
            location="腰部",
        )
        assert result.classification == "气滞血瘀"
        assert result.metadata["acupoints"]
        assert result.metadata["local_acupoints"]


class TestRehabStageEngine:
    """康复分期引擎测试"""

    def setup_method(self):
        self.engine = RehabStageEngine()

    def test_acute_stage(self):
        s = self.engine.determine_stage(onset_days=2)
        assert s == RehabStage.ACUTE

    def test_subacute_stage(self):
        s = self.engine.determine_stage(onset_days=10)
        assert s == RehabStage.SUBACUTE

    def test_recovery_stage(self):
        s = self.engine.determine_stage(onset_days=28)
        assert s == RehabStage.RECOVERY

    def test_strengthening_stage(self):
        s = self.engine.determine_stage(onset_days=60)
        assert s == RehabStage.STRENGTHENING

    def test_maintenance_stage(self):
        s = self.engine.determine_stage(
            onset_days=100, nrs_current=2, rom_pct=90, strength_pct=85
        )
        assert s == RehabStage.MAINTENANCE

    def test_postop_acute_extended(self):
        """术后急性期延长到7天"""
        s = self.engine.determine_stage(onset_days=5, is_postop=True)
        assert s == RehabStage.ACUTE

    def test_regression_high_pain(self):
        """高疼痛时不应进入恢复期"""
        s = self.engine.determine_stage(
            onset_days=30, nrs_current=8, rom_pct=60, strength_pct=50
        )
        assert s == RehabStage.SUBACUTE

    def test_regression_low_function(self):
        """功能恢复差时不应进入维持期"""
        s = self.engine.determine_stage(
            onset_days=100, nrs_current=3, rom_pct=50, strength_pct=40
        )
        assert s == RehabStage.STRENGTHENING

    def test_full_evaluate(self):
        result = self.engine.evaluate(
            onset_days=21,
            diagnosis="腰椎间盘突出",
            nrs_current=4,
            rom_pct=55,
            strength_pct=45,
        )
        assert result.classification == "恢复期"
        assert result.scores["progress_pct"] > 0
        assert result.metadata["rehab_detail"]["allowed_activities"]
        assert result.metadata["rehab_detail"]["tcm_methods"]


# ================================================================
# 3. 路由注册测试
# ================================================================

class TestRouteRegistry:
    """路由注册完整性测试"""

    def test_total_new_agents(self):
        assert len(TCM_ORTHO_AGENT_REGISTRY) == 5

    def test_user_layer_count(self):
        assert len(get_user_layer_agents()) == 2

    def test_coach_layer_count(self):
        assert len(get_coach_layer_agents()) == 3

    def test_agent_ids_sequential(self):
        ids = [v["id"] for v in TCM_ORTHO_AGENT_REGISTRY.values()]
        assert ids == [29, 30, 31, 32, 33]

    def test_coach_agents_review_required(self):
        for agent in get_coach_layer_agents():
            assert agent["review_required"] is True

    def test_user_agents_no_review(self):
        for agent in get_user_layer_agents():
            assert agent["review_required"] is False

    def test_all_agents_have_required_fields(self):
        required = ["id", "name", "layer", "domain", "description",
                     "module", "class_name", "review_required"]
        for name, agent in TCM_ORTHO_AGENT_REGISTRY.items():
            for field in required:
                assert field in agent, f"{name} missing {field}"

    def test_gateway_extensions(self):
        assert len(GATEWAY_EXTENSIONS) == 5

    def test_gateway_auth_matrix(self):
        for endpoint, config in GATEWAY_EXTENSIONS.items():
            assert "method" in config
            assert "auth" in config
            assert "Admin" in config["auth"]


# ================================================================
# 运行统计
# ================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
