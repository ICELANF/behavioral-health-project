# -*- coding: utf-8 -*-
"""
report_generator.py - 处方测试报告生成器

功能:
1. 读取 prescription_engine.py 的测试输出
2. 格式化保存为美观的 Markdown 报告
3. 保存到 notes/test_reports/ 目录

使用方法:
    # 生成所有测试场景的报告
    python scripts/report_generator.py

    # 生成指定场景的报告
    python scripts/report_generator.py --scenario hidden_fatigue

    # 自定义输出目录
    python scripts/report_generator.py --output-dir notes/custom_reports
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

# 确保可以导入同目录下的模块
sys.path.insert(0, str(Path(__file__).parent))

try:
    from prescription_engine import generate_prescription, BehaviorMode, ChangeStage, InterventionStrategy
    PRESCRIPTION_ENGINE_AVAILABLE = True
except ImportError:
    PRESCRIPTION_ENGINE_AVAILABLE = False
    print("[警告] 无法导入 prescription_engine，部分功能可能受限")


# ============ 测试场景定义 ============

TEST_SCENARIOS = {
    "exhaustion": {
        "name": "机体耗竭",
        "description": "SDNN<30 + 疲劳度>70，身体进入紧急保护状态",
        "physio": {"SDNN": 25, "RMSSD": 15, "heart_rate": 85},
        "psych": {"fatigue_index": 80, "energy": 30, "mood": 40, "anxiety_score": 60, "stress_index": 70}
    },
    "hidden_fatigue": {
        "name": "隐性疲劳",
        "description": "HRV恢复能力低但主观压力低，身体已疲劳但心理尚未察觉",
        "physio": {"SDNN": 42, "RMSSD": 25, "heart_rate": 72},
        "psych": {"fatigue_index": 45, "energy": 55, "mood": 60, "anxiety_score": 35, "stress_index": 41}
    },
    "low_energy": {
        "name": "低能量状态",
        "description": "精力<40，建议微习惯启动策略",
        "physio": {"SDNN": 45, "RMSSD": 25, "heart_rate": 72},
        "psych": {"fatigue_index": 60, "energy": 35, "mood": 50, "anxiety_score": 40, "stress_index": 55}
    },
    "normal": {
        "name": "正常状态",
        "description": "各项指标正常，可进行渐进式提升",
        "physio": {"SDNN": 55, "RMSSD": 35, "heart_rate": 70},
        "psych": {"fatigue_index": 45, "energy": 60, "mood": 65, "anxiety_score": 35, "stress_index": 45}
    },
    "action": {
        "name": "行动期",
        "description": "已建立习惯，进入习惯强化阶段",
        "physio": {"SDNN": 70, "RMSSD": 45, "heart_rate": 68},
        "psych": {"fatigue_index": 30, "energy": 75, "mood": 80, "anxiety_score": 25, "stress_index": 30},
        "history": {"assessment_count": 8, "consecutive_improvement_weeks": 4, "task_completion_rate": 0.85}
    }
}


# ============ Markdown 报告生成器 ============

class MarkdownReportGenerator:
    """Markdown 报告生成器"""

    def __init__(self, output_dir: Path = None):
        """
        初始化报告生成器

        Args:
            output_dir: 输出目录
        """
        self.project_root = Path("D:/behavioral-health-project")
        self.output_dir = output_dir or self.project_root / "notes" / "test_reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        prescription: Dict[str, Any],
        scenario_name: str,
        scenario_info: Dict[str, Any]
    ) -> str:
        """
        生成 Markdown 报告

        Args:
            prescription: 处方 JSON 数据
            scenario_name: 场景名称 (如 hidden_fatigue)
            scenario_info: 场景信息 (包含 name, description, physio, psych)

        Returns:
            Markdown 内容
        """
        profile = prescription.get("behavioral_profile", {})
        meta = prescription.get("prescription_meta", {})
        content = prescription.get("prescription_content", {})
        guidance = prescription.get("agent_guidance", {})

        # 获取原始指标
        raw_metrics = profile.get("raw_metrics", {})
        analysis = profile.get("analysis", {})
        scores = profile.get("scores", {})
        flags = profile.get("flags", {})

        # 生成 Markdown
        md = f"""---
title: "{scenario_info['name']}场景测试报告"
scenario: "{scenario_name}"
generated: "{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
tags:
  - 测试报告
  - {scenario_name}
  - {analysis.get('behavior_mode', 'unknown')}
---

# {scenario_info['name']}场景测试报告

> **场景描述**: {scenario_info['description']}
> **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> **处方编号**: `{prescription.get('prescription_id', 'N/A')}`

---

## 一、行为画像分析

### 1.1 核心诊断

| 维度 | 结果 | 说明 |
|------|------|------|
| **行为模式** | {self._get_mode_label(analysis.get('behavior_mode', ''))} | {self._get_mode_description(analysis.get('behavior_mode', ''))} |
| **动机水平** | {self._get_motivation_label(analysis.get('motivation_level', ''))} | 动机分数: {scores.get('motivation_score', 0):.1f} |
| **改变阶段** | {self._get_stage_label(analysis.get('change_stage', ''))} | SPI系数: {scores.get('spi_coefficient', 0.7)} |
| **干预策略** | {self._get_strategy_label(analysis.get('intervention_strategy', ''))} | - |
| **风险等级** | {self._get_risk_badge(analysis.get('risk_level', 'medium'))} | - |

### 1.2 风险提示

{self._format_risk_flags(flags)}

---

## 二、生理指标

{self._generate_physio_table(scenario_info.get('physio', {}), raw_metrics)}

### HRV 解读

{self._generate_hrv_interpretation(scenario_info.get('physio', {}))}

---

## 三、心理指标

{self._generate_psych_table(scenario_info.get('psych', {}), raw_metrics)}

### 心理状态解读

{self._generate_psych_interpretation(scenario_info.get('psych', {}))}

---

## 四、处方信息

| 项目 | 内容 |
|------|------|
| **处方名称** | {meta.get('name', 'N/A')} |
| **干预策略** | {meta.get('intervention_strategy', 'N/A')} |
| **优先级** | {meta.get('priority', 'normal')} |
| **最大任务数** | {meta.get('max_tasks', 3)} |
| **最大难度** | {meta.get('max_difficulty', 3)} |
| **有效期** | {prescription.get('valid_until', 'N/A')[:10]} |

---

## 五、任务清单

{self._generate_tasks_section(content.get('tasks', []))}

---

## 六、Coach 指导话术

{self._generate_coach_section(guidance)}

---

## 七、知识科普

{self._generate_knowledge_section(content.get('knowledge', []))}

---

## 八、推荐视频

{self._generate_videos_section(content.get('videos', []))}

---

## 九、推荐产品

{self._generate_products_section(content.get('products', []))}

---

## 十、原始数据

<details>
<summary>点击展开完整 JSON</summary>

```json
{json.dumps(prescription, ensure_ascii=False, indent=2)}
```

</details>

---

*报告由 行健行为教练 报告生成器 自动生成*
*本报告仅供测试和参考使用*
"""
        return md

    # ============ 标签转换 ============

    def _get_mode_label(self, mode: str) -> str:
        """获取行为模式中文标签"""
        labels = {
            "exhaustion": "🔴 机体耗竭",
            "hidden_fatigue": "🟠 隐性疲劳",
            "overcompensation": "🟡 过度补偿",
            "stress_avoidance": "🟡 应激逃避",
            "somatization": "🟠 躯体化",
            "emotional_dysregulation": "🟡 情绪失调",
            "balanced": "🟢 平衡状态"
        }
        return labels.get(mode, mode)

    def _get_mode_description(self, mode: str) -> str:
        """获取行为模式描述"""
        descriptions = {
            "exhaustion": "身体进入紧急保护状态，需强制休息",
            "hidden_fatigue": "身体已疲劳但心理尚未察觉",
            "overcompensation": "焦虑驱动的过度努力",
            "stress_avoidance": "高压力下能量耗尽",
            "somatization": "心理压力转化为躯体症状",
            "emotional_dysregulation": "情绪波动较大",
            "balanced": "身心状态平衡，可正常干预"
        }
        return descriptions.get(mode, "-")

    def _get_motivation_label(self, level: str) -> str:
        """获取动机水平标签"""
        labels = {
            "depleted": "🔴 耗竭",
            "low": "🟠 低",
            "moderate": "🟡 中等",
            "high": "🟢 高"
        }
        return labels.get(level, level)

    def _get_stage_label(self, stage: str) -> str:
        """获取改变阶段标签"""
        labels = {
            "precontemplation": "前意向期",
            "contemplation": "意向期",
            "preparation": "准备期",
            "action": "行动期",
            "maintenance": "维持期"
        }
        return labels.get(stage, stage)

    def _get_strategy_label(self, strategy: str) -> str:
        """获取干预策略标签"""
        labels = {
            "mandatory_recovery": "强制性修复",
            "hidden_fatigue_recovery": "隐性疲劳修复",
            "micro_habit": "微习惯启动",
            "gradual_buildup": "渐进式提升",
            "habit_strengthening": "习惯强化",
            "identity_consolidation": "身份巩固"
        }
        return labels.get(strategy, strategy)

    def _get_risk_badge(self, level: str) -> str:
        """获取风险等级徽章"""
        badges = {
            "high": "🔴 高风险",
            "medium": "🟡 中等风险",
            "low": "🟢 低风险"
        }
        return badges.get(level, level)

    # ============ 表格生成 ============

    def _generate_physio_table(self, physio: Dict, raw: Dict) -> str:
        """生成生理指标表格"""
        sdnn = physio.get("SDNN", raw.get("sdnn", 0))
        rmssd = physio.get("RMSSD", raw.get("rmssd", 0))
        hr = physio.get("heart_rate", raw.get("heart_rate", 0))

        return f"""
| 指标 | 数值 | 正常范围 | 状态 |
|------|------|----------|------|
| **SDNN** (心脏调节能力) | {sdnn} ms | > 50 ms | {self._get_status_emoji(sdnn, 50, higher_better=True)} |
| **RMSSD** (恢复能力) | {rmssd} ms | > 30 ms | {self._get_status_emoji(rmssd, 30, higher_better=True)} |
| **心率** | {hr} bpm | 60-100 bpm | {self._get_hr_status(hr)} |
"""

    def _generate_psych_table(self, psych: Dict, raw: Dict) -> str:
        """生成心理指标表格"""
        fatigue = psych.get("fatigue_index", raw.get("fatigue_index", 50))
        energy = psych.get("energy", raw.get("energy_level", 50))
        mood = psych.get("mood", raw.get("mood_score", 50))
        anxiety = psych.get("anxiety_score", raw.get("anxiety_score", 30))
        stress = psych.get("stress_index", raw.get("stress_index", 50))

        return f"""
| 指标 | 数值 | 理想范围 | 状态 |
|------|------|----------|------|
| **疲劳指数** | {fatigue} | < 50 | {self._get_status_emoji(fatigue, 50, higher_better=False)} |
| **精力水平** | {energy} | > 60 | {self._get_status_emoji(energy, 60, higher_better=True)} |
| **心情评分** | {mood} | > 60 | {self._get_status_emoji(mood, 60, higher_better=True)} |
| **焦虑评分** | {anxiety} | < 40 | {self._get_status_emoji(anxiety, 40, higher_better=False)} |
| **压力指数** | {stress} | < 50 | {self._get_status_emoji(stress, 50, higher_better=False)} |
"""

    def _get_status_emoji(self, value: float, threshold: float, higher_better: bool = True) -> str:
        """根据数值和阈值返回状态表情"""
        if higher_better:
            if value >= threshold:
                return "🟢 正常"
            elif value >= threshold * 0.7:
                return "🟡 偏低"
            else:
                return "🔴 过低"
        else:
            if value <= threshold:
                return "🟢 正常"
            elif value <= threshold * 1.4:
                return "🟡 偏高"
            else:
                return "🔴 过高"

    def _get_hr_status(self, hr: float) -> str:
        """获取心率状态"""
        if 60 <= hr <= 100:
            return "🟢 正常"
        elif hr < 60:
            return "🟡 偏低"
        else:
            return "🟠 偏高"

    # ============ 解读生成 ============

    def _generate_hrv_interpretation(self, physio: Dict) -> str:
        """生成 HRV 解读"""
        sdnn = physio.get("SDNN", 50)
        rmssd = physio.get("RMSSD", 30)

        interpretations = []

        if sdnn < 30:
            interpretations.append("- ⚠️ **SDNN 严重偏低**: 心脏调节能力不足，身体处于应激状态，需要立即休息")
        elif sdnn < 50:
            interpretations.append("- 🟡 **SDNN 偏低**: 心脏调节能力下降，建议增加休息和放松活动")
        else:
            interpretations.append("- 🟢 **SDNN 正常**: 心脏调节能力良好")

        if rmssd < 25:
            interpretations.append("- ⚠️ **RMSSD 偏低**: 恢复能力不足，副交感神经活性低")
        elif rmssd < 30:
            interpretations.append("- 🟡 **RMSSD 略低**: 恢复能力一般，建议加强放松训练")
        else:
            interpretations.append("- 🟢 **RMSSD 正常**: 恢复能力良好")

        return "\n".join(interpretations) if interpretations else "> 暂无解读"

    def _generate_psych_interpretation(self, psych: Dict) -> str:
        """生成心理状态解读"""
        fatigue = psych.get("fatigue_index", 50)
        energy = psych.get("energy", 50)
        stress = psych.get("stress_index", 50)

        interpretations = []

        if fatigue > 70:
            interpretations.append("- ⚠️ **疲劳度过高**: 需要优先休息，避免高强度任务")
        elif fatigue > 50:
            interpretations.append("- 🟡 **疲劳度偏高**: 建议适当休息，减少工作负荷")

        if energy < 40:
            interpretations.append("- ⚠️ **精力不足**: 建议采用微习惯策略，从小任务开始")
        elif energy < 60:
            interpretations.append("- 🟡 **精力一般**: 可适度增加活动，但避免过度消耗")

        if stress > 70:
            interpretations.append("- ⚠️ **压力过大**: 需要压力管理干预")
        elif stress > 50:
            interpretations.append("- 🟡 **压力偏高**: 建议增加放松活动")

        if not interpretations:
            interpretations.append("- 🟢 **整体状态良好**: 可以进行正常的行为干预")

        return "\n".join(interpretations)

    # ============ 风险提示 ============

    def _format_risk_flags(self, flags: Dict) -> str:
        """格式化风险标志"""
        lines = []

        if flags.get("is_exhaustion_mode"):
            lines.append("> [!danger] 机体耗竭警告\n> 检测到机体耗竭模式，需要立即进入强制休息状态")

        if flags.get("is_hidden_fatigue_mode"):
            lines.append("> [!warning] 隐性疲劳预警\n> 检测到隐性疲劳模式：HRV显示恢复能力下降，但主观感受良好。这是早期预警信号。")

        if flags.get("is_low_motivation"):
            lines.append("> [!warning] 低动机状态\n> 检测到低动机状态，建议采用微习惯启动策略")

        if not lines:
            lines.append("> [!tip] 状态正常\n> 未检测到特殊风险标志")

        return "\n\n".join(lines)

    # ============ 任务清单 ============

    def _generate_tasks_section(self, tasks: List[Dict]) -> str:
        """生成任务清单"""
        if not tasks:
            return "> 暂无任务"

        lines = ["| 序号 | 任务 | 难度 | 类型 | 频率 | 时长 |",
                 "|------|------|------|------|------|------|"]

        for i, task in enumerate(tasks, 1):
            difficulty = "⭐" * task.get("difficulty", 1)
            lines.append(
                f"| {i} | {task.get('content', '-')} | {difficulty} | "
                f"{task.get('type', '-')} | {task.get('frequency', '-')} | "
                f"{task.get('duration_minutes', 0)}分钟 |"
            )

        # 添加任务描述
        lines.append("\n### 任务详情\n")
        for i, task in enumerate(tasks, 1):
            lines.append(f"**{i}. {task.get('content', '未命名任务')}**")
            if task.get('description'):
                lines.append(f"> {task['description']}")
            lines.append("")

        return "\n".join(lines)

    # ============ Coach 话术 ============

    def _generate_coach_section(self, guidance: Dict) -> str:
        """生成 Coach 指导话术"""
        if not guidance:
            return "> 暂无 Coach 指导"

        coach = guidance.get("coach_script", {})
        motivation = guidance.get("motivation_guidance", {})
        stage = guidance.get("stage_guidance", {})

        lines = []

        # 开场白
        if coach.get("opening"):
            lines.append(f"### 开场白\n\n> {coach['opening']}\n")

        # 状态觉察
        if coach.get("awareness"):
            lines.append(f"### 状态觉察\n\n> {coach['awareness']}\n")

        # 行动提示
        if coach.get("action_prompt"):
            lines.append(f"### 行动提示\n\n> {coach['action_prompt']}\n")

        # 鼓励语
        if coach.get("encouragement"):
            lines.append(f"### 鼓励语\n\n> {coach['encouragement']}\n")

        # 结束语
        if coach.get("closing"):
            lines.append(f"### 结束语\n\n> {coach['closing']}\n")

        # 沟通要点表格
        lines.append("### 沟通要点\n")
        lines.append("| 维度 | 内容 |")
        lines.append("|------|------|")
        lines.append(f"| 动机等级 | {motivation.get('level', '-')} (分数: {motivation.get('score', 0)}) |")
        lines.append(f"| 沟通语气 | {motivation.get('tone', '-')} |")
        lines.append(f"| 改变阶段 | {stage.get('stage', '-')} |")
        lines.append(f"| 阶段目标 | {stage.get('goal', '-')} |")
        lines.append(f"| 沟通风格 | {stage.get('conversation_style', '-')} |")

        return "\n".join(lines) if lines else "> 暂无 Coach 指导"

    # ============ 知识/视频/产品 ============

    def _generate_knowledge_section(self, knowledge: List[Dict]) -> str:
        """生成知识科普"""
        if not knowledge:
            return "> 暂无知识推荐"

        lines = []
        for k in knowledge:
            lines.append(f"### 📚 {k.get('title', '未知标题')}")
            lines.append(f"> {k.get('summary', '暂无摘要')}")
            if k.get('knowledge_id'):
                lines.append(f"> *编号: {k['knowledge_id']}*")
            lines.append("")

        return "\n".join(lines)

    def _generate_videos_section(self, videos: List[Dict]) -> str:
        """生成视频推荐"""
        if not videos:
            return "> 暂无视频推荐"

        lines = ["| 视频名称 | 描述 | 时长 |",
                 "|----------|------|------|"]

        for v in videos:
            duration = v.get("duration_seconds", 0)
            minutes = duration // 60
            seconds = duration % 60
            duration_str = f"{minutes}分{seconds}秒" if duration > 0 else "-"
            lines.append(f"| 🎬 {v.get('title', '-')} | {v.get('description', '-')} | {duration_str} |")

        return "\n".join(lines)

    def _generate_products_section(self, products: List[Dict]) -> str:
        """生成产品推荐"""
        if not products:
            return "> 暂无产品推荐"

        lines = []
        for p in products:
            lines.append(f"### 🛒 {p.get('name', '未知产品')}")
            if p.get('relevance'):
                lines.append(f"> 适用说明: {p['relevance']}")
            lines.append("")

        return "\n".join(lines)

    # ============ 报告保存 ============

    def save_report(
        self,
        prescription: Dict[str, Any],
        scenario_name: str,
        scenario_info: Dict[str, Any]
    ) -> Path:
        """
        保存报告到文件

        Args:
            prescription: 处方数据
            scenario_name: 场景名称
            scenario_info: 场景信息

        Returns:
            保存的文件路径
        """
        # 生成报告内容
        md_content = self.generate_report(prescription, scenario_name, scenario_info)

        # 生成文件名: Report_日期_场景名.md
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"Report_{date_str}_{scenario_name}.md"
        filepath = self.output_dir / filename

        # 保存文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return filepath


# ============ 批量生成 ============

def generate_all_reports(output_dir: Path = None) -> List[Path]:
    """
    生成所有测试场景的报告

    Args:
        output_dir: 输出目录

    Returns:
        生成的文件路径列表
    """
    if not PRESCRIPTION_ENGINE_AVAILABLE:
        print("[错误] 无法导入 prescription_engine，请检查文件路径")
        return []

    generator = MarkdownReportGenerator(output_dir)
    generated_files = []

    print("\n" + "=" * 60)
    print("处方测试报告生成器")
    print("=" * 60)

    for scenario_name, scenario_info in TEST_SCENARIOS.items():
        print(f"\n处理场景: {scenario_info['name']} ({scenario_name})")

        # 生成处方
        prescription = generate_prescription(
            scenario_info["physio"],
            scenario_info["psych"],
            scenario_info.get("history")
        )

        # 保存报告
        filepath = generator.save_report(prescription, scenario_name, scenario_info)
        generated_files.append(filepath)
        print(f"  ✅ 报告已保存: {filepath.name}")

    print(f"\n完成！共生成 {len(generated_files)} 份报告")
    print(f"输出目录: {generator.output_dir}")

    return generated_files


def generate_single_report(scenario_name: str, output_dir: Path = None) -> Optional[Path]:
    """
    生成单个场景的报告

    Args:
        scenario_name: 场景名称
        output_dir: 输出目录

    Returns:
        生成的文件路径
    """
    if not PRESCRIPTION_ENGINE_AVAILABLE:
        print("[错误] 无法导入 prescription_engine，请检查文件路径")
        return None

    if scenario_name not in TEST_SCENARIOS:
        print(f"[错误] 未知场景: {scenario_name}")
        print(f"可用场景: {', '.join(TEST_SCENARIOS.keys())}")
        return None

    generator = MarkdownReportGenerator(output_dir)
    scenario_info = TEST_SCENARIOS[scenario_name]

    print(f"\n处理场景: {scenario_info['name']} ({scenario_name})")

    # 生成处方
    prescription = generate_prescription(
        scenario_info["physio"],
        scenario_info["psych"],
        scenario_info.get("history")
    )

    # 保存报告
    filepath = generator.save_report(prescription, scenario_name, scenario_info)
    print(f"✅ 报告已保存: {filepath}")

    return filepath


# ============ 主函数 ============

def main():
    parser = argparse.ArgumentParser(description="处方测试报告生成器")
    parser.add_argument("--scenario", choices=list(TEST_SCENARIOS.keys()),
                        help="指定测试场景 (不指定则生成全部)")
    parser.add_argument("--output-dir", default=None,
                        help="输出目录 (默认: notes/test_reports)")
    parser.add_argument("--list", action="store_true",
                        help="列出所有可用场景")

    args = parser.parse_args()

    # 列出场景
    if args.list:
        print("\n可用测试场景:")
        print("-" * 40)
        for name, info in TEST_SCENARIOS.items():
            print(f"  {name}: {info['name']}")
            print(f"    {info['description']}")
        return

    # 解析输出目录
    output_dir = Path(args.output_dir) if args.output_dir else None

    # 生成报告
    if args.scenario:
        generate_single_report(args.scenario, output_dir)
    else:
        generate_all_reports(output_dir)


if __name__ == "__main__":
    main()
