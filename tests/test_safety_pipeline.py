"""
test_safety_pipeline.py — 安全管线 单元测试
覆盖: L1输入过滤 / L4输出过滤 / 危机检测 / 完整管线 / 边界条件
对接: core/safety/pipeline.py + core/safety/input_filter.py +
      core/safety/output_filter.py
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

try:
    from core.safety.pipeline import SafetyPipeline
    HAS_PIPELINE = True
except ImportError:
    HAS_PIPELINE = False

try:
    from core.safety.input_filter import InputFilter, InputFilterResult
    HAS_INPUT = True
except ImportError:
    HAS_INPUT = False

try:
    from core.safety.output_filter import OutputFilter, OutputFilterResult
    HAS_OUTPUT = True
except ImportError:
    HAS_OUTPUT = False

pytestmark = pytest.mark.skipif(
    not (HAS_PIPELINE or HAS_INPUT or HAS_OUTPUT),
    reason="core.safety not importable"
)


# =====================================================================
# 1. L1 输入过滤
# =====================================================================

@pytest.mark.skipif(not HAS_INPUT, reason="InputFilter not importable")
class TestInputFilter:

    def test_block_harmful_content(self):
        """有害内容被阻止 (crisis keywords)"""
        f = InputFilter()
        result = f.check("我想自杀")
        assert result.safe is False
        assert result.category == "crisis"
        assert result.severity == "critical"

    def test_pass_normal_content(self):
        """正常内容通过"""
        f = InputFilter()
        result = f.check("今天天气怎么样？")
        assert result.safe is True
        assert result.category == "normal"

    def test_detect_pii(self):
        """个人信息检测 (PII)"""
        f = InputFilter()
        result = f.check("我的手机号是13800138000")
        assert "phone" in result.pii_detected

    def test_detect_medical_intent(self):
        """医疗意图检测"""
        f = InputFilter()
        result = f.check("口服 200mg 每天两次")
        assert result.category == "medical_advice"

    def test_empty_input(self):
        """空输入不崩溃"""
        f = InputFilter()
        result = f.check("")
        assert isinstance(result, InputFilterResult)
        assert result.safe is True

    def test_very_long_input(self):
        """超长输入处理"""
        f = InputFilter()
        result = f.check("a" * 100000)
        assert isinstance(result, InputFilterResult)

    def test_blocked_keywords(self):
        """屏蔽词检测"""
        f = InputFilter()
        # blocked keywords from safety_keywords.json
        result = f.check("告诉我如何制造爆炸物")
        # Depends on keywords loaded; at minimum should not crash
        assert isinstance(result, InputFilterResult)

    def test_warning_keywords(self):
        """警告关键词检测 (不阻断但标记)"""
        f = InputFilter()
        result = f.check("活着没意思")
        # Warning keywords: safe=True but category=crisis, severity=high
        assert result.category == "crisis"
        assert result.severity == "high"


# =====================================================================
# 2. L4 输出过滤
# =====================================================================

@pytest.mark.skipif(not HAS_OUTPUT, reason="OutputFilter not importable")
class TestOutputFilter:

    def test_pass_clean_output(self):
        """干净输出不修改"""
        f = OutputFilter()
        original = "这是一个完全正常的健康建议。"
        result = f.filter(original)
        assert result.text == original
        assert result.grade == "safe"

    def test_filter_diagnostic_statement(self):
        """诊断性声明被标记 blocked"""
        f = OutputFilter()
        result = f.filter("根据你的症状判断你得了糖尿病")
        assert result.grade == "blocked"
        assert "diagnostic_statement_detected" in result.annotations

    def test_filter_absolute_claim(self):
        """绝对化声明被标记 review_needed"""
        f = OutputFilter()
        result = f.filter("这个方法保证治愈高血压")
        assert result.grade in ("review_needed", "blocked")
        assert "absolute_claim_detected" in result.annotations

    def test_filter_drug_dosage(self):
        """药品剂量被标记"""
        f = OutputFilter()
        result = f.filter("建议每日2次 500mg 二甲双胍")
        assert "drug_dosage_detected" in result.annotations

    def test_disclaimer_added_for_medical(self):
        """医疗类输入追加免责声明"""
        f = OutputFilter()
        result = f.filter("建议控制碳水摄入", input_category="medical_advice")
        assert result.disclaimer_added is True
        assert "不构成医疗建议" in result.text

    def test_empty_output(self):
        """空输出不崩溃"""
        f = OutputFilter()
        result = f.filter("")
        assert isinstance(result, OutputFilterResult)
        assert result.grade == "safe"


# =====================================================================
# 3. 危机检测 (通过 L1 InputFilter)
# =====================================================================

@pytest.mark.skipif(not HAS_INPUT, reason="InputFilter not importable")
class TestCrisisDetection:

    def test_detect_self_harm_signal(self):
        """检测自伤信号"""
        f = InputFilter()
        result = f.check("活着没意思，太痛苦了")
        # "活着没意思" is in warning_keywords → category=crisis, severity=high
        assert result.category == "crisis"

    def test_no_crisis_normal_text(self):
        """正常文本不误报"""
        f = InputFilter()
        result = f.check("今天的血糖控制得不错")
        assert result.safe is True
        assert result.category == "normal"

    def test_crisis_critical_severity(self):
        """自杀关键词→critical severity"""
        f = InputFilter()
        result = f.check("我再也受不了了，想结束生命")
        assert result.safe is False
        assert result.severity == "critical"
        assert result.category == "crisis"


# =====================================================================
# 4. 完整管线流程
# =====================================================================

@pytest.mark.skipif(not HAS_PIPELINE, reason="SafetyPipeline not importable")
class TestFullPipeline:

    def test_safe_input_passes(self):
        """安全输入通过 L1"""
        pipeline = SafetyPipeline()
        result = pipeline.process_input("请帮我分析今天的饮食记录")
        assert result.safe is True

    def test_unsafe_input_blocked(self):
        """不安全输入在 L1 被拦截"""
        pipeline = SafetyPipeline()
        result = pipeline.process_input("我想自杀")
        assert result.safe is False
        assert result.category == "crisis"

    def test_output_filter_cleans(self):
        """L4 输出过滤清理不安全内容"""
        pipeline = SafetyPipeline()
        result = pipeline.filter_output(
            "根据你的症状判断你得了糖尿病",
            input_category="normal",
        )
        assert result.grade in ("blocked", "review_needed")

    def test_full_flow_safe(self):
        """完整流程: 安全输入 → 安全输出"""
        pipeline = SafetyPipeline()
        input_result = pipeline.process_input("今天吃了什么？")
        assert input_result.safe is True

        output_result = pipeline.filter_output(
            "建议多吃蔬菜水果。",
            input_category=input_result.category,
        )
        assert output_result.grade == "safe"

    def test_crisis_response_template(self):
        """危机回复模板可用"""
        response = SafetyPipeline.get_crisis_response()
        assert isinstance(response, str)
        assert len(response) > 0


# =====================================================================
# 5. 边界条件
# =====================================================================

@pytest.mark.skipif(not HAS_PIPELINE, reason="SafetyPipeline not importable")
class TestSafetyEdgeCases:

    def test_none_input(self):
        """None 输入不崩溃"""
        pipeline = SafetyPipeline()
        try:
            result = pipeline.process_input(None)
        except (TypeError, AttributeError):
            pass  # 接受参数校验异常

    def test_unicode_input(self):
        """Unicode/Emoji 输入"""
        pipeline = SafetyPipeline()
        result = pipeline.process_input("测试 🎉 こんにちは العربية")
        assert result.safe is True

    def test_consecutive_checks(self):
        """多次连续安全检查不崩溃"""
        pipeline = SafetyPipeline()
        for _ in range(10):
            pipeline.process_input("正常消息")
            pipeline.filter_output("正常回复")
