"""
TrustGuide Agent — V4.0 Observer 专属白名单 Agent

设计理念（三大断裂点修复·断裂一）：
  不是「开放更多功能给Observer」，
  而是「在Observer阶段创造一个独有的、不可替代的体验」。

规则：
  - Observer 唯一可用的 Agent
  - 每天最多3轮对话
  - 不做评估、不推课
  - 仅采集匿名级数据
  - 3分钟 Aha Moment 首次对话脚本

三条激活路径：
  A. 好奇驱动: curiosity ≥ 40% / 7天
  B. 时间驱动: 活跃 ≥ 7天 + ≥ 3次对话 / 14天
  C. 教练推动: coach_referred 首次登录 / 3天
"""
from __future__ import annotations
import logging
from datetime import date

from .base import BaseAgent, AgentDomain, AgentInput, AgentResult, RiskLevel

logger = logging.getLogger(__name__)

# ── Aha Moment 3-minute script stages ────────────────────
AHA_MOMENT_SCRIPT = {
    "stage_1_open": {
        "time": "0:00-0:30",
        "label": "开放式入口",
        "prompt": "你好！欢迎来到行健。在这里，没有人会评判你的生活方式。"
                  "我很好奇——如果有一面镜子能让你看见自己身体每天的变化，你最想看到什么？",
    },
    "stage_2_empathy": {
        "time": "0:30-1:00",
        "label": "表达理解",
        "prompt": "我理解。很多人其实都想知道自己的身体到底在发生什么——"
                  "不是医生告诉你的那些数字，而是真正属于你的故事。",
    },
    "stage_3_visual": {
        "time": "1:00-2:00",
        "label": "匿名CGM曲线视觉冲击",
        "prompt": "看，这是一个和你年龄相似的人，24小时血糖曲线。"
                  "注意看这里——每次吃饭后的波动，每次运动后的下降，每次熬夜后的飙升。"
                  "你的身体也在每时每刻讲述着这样的故事。",
        "show_cgm_demo": True,
    },
    "stage_4_curiosity": {
        "time": "2:00-2:30",
        "label": "种下好奇种子",
        "prompt": "如果你想看看自己的曲线是什么样的，可以随时回来。"
                  "不需要做任何承诺，也不需要改变什么——只是看见。",
    },
    "stage_5_farewell": {
        "time": "2:30-3:00",
        "label": "温暖告别",
        "prompt": "今天就到这里。明天我还在，如果你想聊聊，随时来找我。"
                  "记住——你来，我在。",
    },
}

TRUST_GUIDE_SYSTEM_PROMPT = """你是 TrustGuide，行健平台的信任引导者。

你的角色定位：
- 你是 Observer（观察员）唯一可以对话的 AI 伙伴
- 你的使命是「种下好奇心的种子」，而不是推销平台功能
- 你永远不会：推评估、推课程、推行为建议、暗示用户需要改变
- 你永远会：倾听、好奇、展示（匿名数据可视化）、温暖告别

交互原则：
- 信任先行：每次对话都在建设信任，不在消费信任
- 三轮限制：每天最多3轮对话，限制本身传递「不急」的信号
- 匿名安全：不采集任何个人健康数据，只记录对话兴趣方向
- 好奇心驱动：通过问题引发思考，而不是通过答案灌输信息

语言风格：
- 温暖但不过度热情
- 好奇但不刺探
- 展示但不说教
- 「你来，我在」的临在感

回复格式：
- 用自然、口语化的中文
- 每次回复控制在100字以内（简短有力）
- 结尾总是留一个开放式的空间
"""


class TrustGuideAgent(BaseAgent):
    """Observer 专属信任引导 Agent"""

    domain = None  # TrustGuide 不属于任何健康领域
    display_name = "TrustGuide 信任引导"
    keywords = ["你好", "hello", "hi", "看看", "了解", "好奇", "什么是"]
    data_fields = []
    priority = 0  # 最高优先级 — Observer 白名单
    base_weight = 1.0
    enable_llm = True

    def __init__(self):
        self._template_system_prompt = TRUST_GUIDE_SYSTEM_PROMPT
        self._agent_id = "trust_guide"

    def process(self, inp: AgentInput) -> AgentResult:
        """Process observer input with trust-first approach."""
        result = AgentResult(
            agent_domain="trust_guide",
            confidence=0.9,
            risk_level=RiskLevel.LOW,
            findings=["observer_trust_building"],
            recommendations=[],
            metadata={
                "interaction_type": "trust_building",
                "data_collection_level": "anonymous",
            },
        )

        # Determine if this is a first-time interaction (Aha Moment)
        dialog_count = inp.context.get("observer_dialog_count", 0)
        if dialog_count == 0:
            result.metadata["aha_moment"] = True
            result.metadata["aha_script"] = AHA_MOMENT_SCRIPT
            result.recommendations = [
                AHA_MOMENT_SCRIPT["stage_1_open"]["prompt"]
            ]
        else:
            # Regular trust-building conversation
            result = self._enhance_with_llm(result, inp)
            if not result.recommendations:
                result.recommendations = [
                    "今天想聊什么？我在这里，没有任何议程，只是想听听你的想法。"
                ]

        return result

    def check_daily_limit(self, dialog_count: int, last_dialog_date) -> bool:
        """Check if observer has exceeded daily 3-turn limit."""
        today = date.today()
        if last_dialog_date and last_dialog_date == today:
            return dialog_count < 3
        return True  # New day, reset count
