# -*- coding: utf-8 -*-
"""
八爪鱼健康引擎 (Octopus Health Engine)

功能:
1. PDF 解析器 - 从测评报告中提取关键生理指标
2. 八爪鱼归因模型 - 基于 HRV/ANS 数据判定健康状态
3. 可视化看板 - 生成 Matplotlib 图表保存到 dashboards
"""

import os
import re
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

import pdfplumber
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


# =============================================================================
# 数据模型
# =============================================================================

@dataclass
class HRVMetrics:
    """心率变异性 (HRV) 指标"""
    sdnn: Optional[float] = None          # SDNN (ms) - 总体变异性
    rmssd: Optional[float] = None         # RMSSD (ms) - 副交感活性
    pnn50: Optional[float] = None         # pNN50 (%) - 副交感指标
    lf_power: Optional[float] = None      # LF 功率 (ms²) - 交感+副交感
    hf_power: Optional[float] = None      # HF 功率 (ms²) - 副交感
    lf_hf_ratio: Optional[float] = None   # LF/HF 比值 - 交感/副交感平衡
    total_power: Optional[float] = None   # 总功率 (ms²)


@dataclass
class ANSBalance:
    """自主神经系统平衡度"""
    sympathetic: Optional[float] = None   # 交感神经活性 (%)
    parasympathetic: Optional[float] = None  # 副交感神经活性 (%)
    balance_index: Optional[float] = None    # 平衡指数 (-100 ~ +100)
    stress_index: Optional[float] = None     # 应激指数


@dataclass
class PsychMetrics:
    """心理测评指标"""
    anxiety_score: Optional[float] = None     # 焦虑分数
    depression_score: Optional[float] = None  # 抑郁分数
    stress_score: Optional[float] = None      # 压力分数
    sleep_quality: Optional[float] = None     # 睡眠质量分
    efficacy_score: Optional[float] = None    # 效能感分数


@dataclass
class HealthReport:
    """完整健康报告"""
    report_id: str = ""
    user_id: str = ""
    report_date: str = ""
    hrv: HRVMetrics = field(default_factory=HRVMetrics)
    ans: ANSBalance = field(default_factory=ANSBalance)
    psych: PsychMetrics = field(default_factory=PsychMetrics)
    raw_text: str = ""


# =============================================================================
# PDF 解析器
# =============================================================================

class HealthPDFParser:
    """
    健康测评报告 PDF 解析器

    支持提取:
    - HRV 指标 (SDNN, RMSSD, LF/HF 等)
    - 自主神经平衡度
    - 心理测评分数
    """

    # 正则表达式模式 - 匹配各类指标
    PATTERNS = {
        # HRV 指标
        'sdnn': [
            r'SDNN[:\s]*(\d+\.?\d*)\s*(?:ms)?',
            r'SDNN指数[:\s]*(\d+\.?\d*)',
            r'标准差[:\s]*(\d+\.?\d*)\s*ms'
        ],
        'rmssd': [
            r'RMSSD[:\s]*(\d+\.?\d*)\s*(?:ms)?',
            r'相邻差值均方根[:\s]*(\d+\.?\d*)'
        ],
        'pnn50': [
            r'pNN50[:\s]*(\d+\.?\d*)\s*(?:%)?',
            r'PNN50[:\s]*(\d+\.?\d*)'
        ],
        'lf_power': [
            r'LF[功率\s]*[:\s]*(\d+\.?\d*)\s*(?:ms²|ms2)?',
            r'低频功率[:\s]*(\d+\.?\d*)'
        ],
        'hf_power': [
            r'HF[功率\s]*[:\s]*(\d+\.?\d*)\s*(?:ms²|ms2)?',
            r'高频功率[:\s]*(\d+\.?\d*)'
        ],
        'lf_hf_ratio': [
            r'LF/HF[:\s]*(\d+\.?\d*)',
            r'LF\/HF比值[:\s]*(\d+\.?\d*)',
            r'交感副交感比[:\s]*(\d+\.?\d*)'
        ],

        # 自主神经指标
        'sympathetic': [
            r'交感神经[活性度\s]*[:\s]*(\d+\.?\d*)\s*(?:%)?',
            r'交感活性[:\s]*(\d+\.?\d*)'
        ],
        'parasympathetic': [
            r'副交感神经[活性度\s]*[:\s]*(\d+\.?\d*)\s*(?:%)?',
            r'副交感活性[:\s]*(\d+\.?\d*)'
        ],
        'balance_index': [
            r'自主神经平衡[度指数\s]*[:\s]*([+-]?\d+\.?\d*)',
            r'ANS平衡[:\s]*([+-]?\d+\.?\d*)'
        ],
        'stress_index': [
            r'应激指数[:\s]*(\d+\.?\d*)',
            r'压力指数[:\s]*(\d+\.?\d*)',
            r'Stress Index[:\s]*(\d+\.?\d*)'
        ],

        # 心理指标
        'anxiety_score': [
            r'焦虑[分数得分\s]*[:\s]*(\d+\.?\d*)',
            r'GAD-?7[:\s]*(\d+\.?\d*)',
            r'焦虑量表[:\s]*(\d+\.?\d*)'
        ],
        'depression_score': [
            r'抑郁[分数得分\s]*[:\s]*(\d+\.?\d*)',
            r'PHQ-?9[:\s]*(\d+\.?\d*)',
            r'抑郁量表[:\s]*(\d+\.?\d*)'
        ],
        'stress_score': [
            r'压力[分数得分\s]*[:\s]*(\d+\.?\d*)',
            r'PSS[:\s]*(\d+\.?\d*)'
        ],
        'sleep_quality': [
            r'睡眠质量[分数\s]*[:\s]*(\d+\.?\d*)',
            r'PSQI[:\s]*(\d+\.?\d*)'
        ],
        'efficacy_score': [
            r'效能[感分数\s]*[:\s]*(\d+\.?\d*)',
            r'自我效能[:\s]*(\d+\.?\d*)'
        ]
    }

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.raw_text = ""
        self.report = HealthReport()

    def _extract_text(self) -> str:
        """从 PDF 中提取全部文本"""
        text_parts = []
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as e:
            print(f"[ERROR] PDF 解析失败: {e}")
            return ""

        return "\n".join(text_parts)

    def _match_pattern(self, text: str, patterns: List[str]) -> Optional[float]:
        """尝试多个正则模式匹配数值"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return None

    def parse(self) -> HealthReport:
        """解析 PDF 并返回结构化报告"""
        self.raw_text = self._extract_text()
        self.report.raw_text = self.raw_text

        if not self.raw_text:
            print("[WARN] PDF 文本为空")
            return self.report

        # 提取 HRV 指标
        self.report.hrv.sdnn = self._match_pattern(self.raw_text, self.PATTERNS['sdnn'])
        self.report.hrv.rmssd = self._match_pattern(self.raw_text, self.PATTERNS['rmssd'])
        self.report.hrv.pnn50 = self._match_pattern(self.raw_text, self.PATTERNS['pnn50'])
        self.report.hrv.lf_power = self._match_pattern(self.raw_text, self.PATTERNS['lf_power'])
        self.report.hrv.hf_power = self._match_pattern(self.raw_text, self.PATTERNS['hf_power'])
        self.report.hrv.lf_hf_ratio = self._match_pattern(self.raw_text, self.PATTERNS['lf_hf_ratio'])

        # 提取自主神经指标
        self.report.ans.sympathetic = self._match_pattern(self.raw_text, self.PATTERNS['sympathetic'])
        self.report.ans.parasympathetic = self._match_pattern(self.raw_text, self.PATTERNS['parasympathetic'])
        self.report.ans.balance_index = self._match_pattern(self.raw_text, self.PATTERNS['balance_index'])
        self.report.ans.stress_index = self._match_pattern(self.raw_text, self.PATTERNS['stress_index'])

        # 提取心理指标
        self.report.psych.anxiety_score = self._match_pattern(self.raw_text, self.PATTERNS['anxiety_score'])
        self.report.psych.depression_score = self._match_pattern(self.raw_text, self.PATTERNS['depression_score'])
        self.report.psych.stress_score = self._match_pattern(self.raw_text, self.PATTERNS['stress_score'])
        self.report.psych.sleep_quality = self._match_pattern(self.raw_text, self.PATTERNS['sleep_quality'])
        self.report.psych.efficacy_score = self._match_pattern(self.raw_text, self.PATTERNS['efficacy_score'])

        # 设置报告元数据
        self.report.report_id = Path(self.pdf_path).stem
        self.report.report_date = datetime.now().strftime("%Y-%m-%d")

        return self.report


# =============================================================================
# 八爪鱼归因模型
# =============================================================================

@dataclass
class AttributionResult:
    """归因分析结果"""
    dimension: str              # 归因维度
    status: str                 # 状态: normal / warning / critical
    score: float                # 归一化分数 (0-100)
    reason: str                 # 归因说明
    recommendation: str         # 干预建议


class OctopusAttributionModel:
    """
    八爪鱼归因模型

    基于生理指标判定健康状态:
    - 生理韧性维度: SDNN < 30ms 判定为韧性不足
    - 应激状态维度: 交感/副交感平衡度判定
    - 心理健康维度: 焦虑、抑郁、压力综合评估
    """

    # 阈值配置
    THRESHOLDS = {
        'sdnn': {
            'critical': 30,    # < 30ms 严重不足
            'warning': 50,     # < 50ms 轻度不足
            'normal': 100      # >= 50ms 正常
        },
        'lf_hf_ratio': {
            'critical_high': 4.0,   # > 4.0 交感过度激活
            'warning_high': 2.5,    # > 2.5 轻度交感优势
            'normal_low': 0.5,      # < 0.5 副交感优势
            'critical_low': 0.2     # < 0.2 副交感过度
        },
        'anxiety': {
            'critical': 15,    # GAD-7 >= 15 重度
            'warning': 10,     # >= 10 中度
            'mild': 5          # >= 5 轻度
        },
        'stress_index': {
            'critical': 150,
            'warning': 100,
            'normal': 50
        }
    }

    def __init__(self, report: HealthReport):
        self.report = report
        self.attributions: List[AttributionResult] = []

    def _evaluate_physiological_resilience(self) -> AttributionResult:
        """评估生理韧性 (基于 SDNN)"""
        sdnn = self.report.hrv.sdnn

        if sdnn is None:
            return AttributionResult(
                dimension="生理韧性",
                status="unknown",
                score=50,
                reason="SDNN 数据缺失，无法评估",
                recommendation="建议进行 HRV 检测"
            )

        thresholds = self.THRESHOLDS['sdnn']

        if sdnn < thresholds['critical']:
            return AttributionResult(
                dimension="生理韧性",
                status="critical",
                score=max(0, sdnn / thresholds['critical'] * 30),
                reason=f"SDNN={sdnn:.1f}ms < 30ms，生理韧性严重不足，自主神经调节能力下降",
                recommendation="建议：1) 规律作息 2) 腹式呼吸训练 3) 适度有氧运动 4) 必要时就医评估"
            )
        elif sdnn < thresholds['warning']:
            return AttributionResult(
                dimension="生理韧性",
                status="warning",
                score=30 + (sdnn - thresholds['critical']) / (thresholds['warning'] - thresholds['critical']) * 30,
                reason=f"SDNN={sdnn:.1f}ms，生理韧性偏低，需要关注",
                recommendation="建议：1) 保证 7-8 小时睡眠 2) 每日 15 分钟冥想 3) 减少咖啡因摄入"
            )
        else:
            return AttributionResult(
                dimension="生理韧性",
                status="normal",
                score=min(100, 60 + (sdnn - thresholds['warning']) / 50 * 40),
                reason=f"SDNN={sdnn:.1f}ms，生理韧性良好",
                recommendation="保持当前健康习惯"
            )

    def _evaluate_stress_state(self) -> AttributionResult:
        """评估应激状态 (基于交感/副交感平衡)"""
        lf_hf = self.report.hrv.lf_hf_ratio
        sympathetic = self.report.ans.sympathetic
        parasympathetic = self.report.ans.parasympathetic

        # 优先使用 LF/HF 比值
        if lf_hf is not None:
            thresholds = self.THRESHOLDS['lf_hf_ratio']

            if lf_hf > thresholds['critical_high']:
                return AttributionResult(
                    dimension="应激状态",
                    status="critical",
                    score=max(0, 100 - (lf_hf - thresholds['critical_high']) * 10),
                    reason=f"LF/HF={lf_hf:.2f} > 4.0，交感神经过度激活，处于高应激状态",
                    recommendation="建议：1) 立即进行放松练习 2) 避免剧烈运动 3) 考虑心理咨询"
                )
            elif lf_hf > thresholds['warning_high']:
                return AttributionResult(
                    dimension="应激状态",
                    status="warning",
                    score=60 - (lf_hf - thresholds['warning_high']) / 1.5 * 30,
                    reason=f"LF/HF={lf_hf:.2f}，轻度交感优势，存在压力累积",
                    recommendation="建议：1) 规律进行深呼吸 2) 减少工作强度 3) 增加休息时间"
                )
            elif lf_hf < thresholds['critical_low']:
                return AttributionResult(
                    dimension="应激状态",
                    status="warning",
                    score=50,
                    reason=f"LF/HF={lf_hf:.2f} < 0.2，副交感过度，可能存在疲劳",
                    recommendation="建议：1) 检查是否过度疲劳 2) 适当增加活动量"
                )
            else:
                return AttributionResult(
                    dimension="应激状态",
                    status="normal",
                    score=80,
                    reason=f"LF/HF={lf_hf:.2f}，交感/副交感平衡良好",
                    recommendation="保持当前状态"
                )

        # 备用：使用交感/副交感百分比
        if sympathetic is not None and parasympathetic is not None:
            balance = sympathetic - parasympathetic
            if balance > 30:
                return AttributionResult(
                    dimension="应激状态",
                    status="critical",
                    score=30,
                    reason=f"交感{sympathetic}% vs 副交感{parasympathetic}%，交感神经明显占优",
                    recommendation="建议进行放松训练，必要时寻求专业帮助"
                )
            elif balance > 10:
                return AttributionResult(
                    dimension="应激状态",
                    status="warning",
                    score=50,
                    reason=f"交感{sympathetic}% vs 副交感{parasympathetic}%，轻度应激",
                    recommendation="建议增加休息和放松活动"
                )
            else:
                return AttributionResult(
                    dimension="应激状态",
                    status="normal",
                    score=80,
                    reason=f"交感{sympathetic}% vs 副交感{parasympathetic}%，自主神经平衡",
                    recommendation="保持健康生活方式"
                )

        return AttributionResult(
            dimension="应激状态",
            status="unknown",
            score=50,
            reason="自主神经数据缺失",
            recommendation="建议进行完整的 HRV 评估"
        )

    def _evaluate_psychological_state(self) -> AttributionResult:
        """评估心理健康状态"""
        anxiety = self.report.psych.anxiety_score
        depression = self.report.psych.depression_score
        stress = self.report.psych.stress_score

        scores = [s for s in [anxiety, depression, stress] if s is not None]

        if not scores:
            return AttributionResult(
                dimension="心理健康",
                status="unknown",
                score=50,
                reason="心理测评数据缺失",
                recommendation="建议完成 GAD-7、PHQ-9 等标准化量表"
            )

        # 取最高风险分数
        max_score = max(scores)
        thresholds = self.THRESHOLDS['anxiety']

        if max_score >= thresholds['critical']:
            return AttributionResult(
                dimension="心理健康",
                status="critical",
                score=max(0, 100 - max_score * 3),
                reason=f"心理测评分数偏高 (焦虑:{anxiety}, 抑郁:{depression}, 压力:{stress})",
                recommendation="建议：1) 立即寻求专业心理咨询 2) 考虑就医评估 3) 避免独处"
            )
        elif max_score >= thresholds['warning']:
            return AttributionResult(
                dimension="心理健康",
                status="warning",
                score=50 - (max_score - thresholds['warning']) * 2,
                reason=f"存在中度心理压力 (焦虑:{anxiety}, 抑郁:{depression}, 压力:{stress})",
                recommendation="建议：1) 规律运动 2) 社交支持 3) 考虑短期心理咨询"
            )
        elif max_score >= thresholds['mild']:
            return AttributionResult(
                dimension="心理健康",
                status="mild",
                score=70,
                reason=f"轻度心理波动 (焦虑:{anxiety}, 抑郁:{depression}, 压力:{stress})",
                recommendation="建议：1) 自我调节 2) 保持社交 3) 定期复测"
            )
        else:
            return AttributionResult(
                dimension="心理健康",
                status="normal",
                score=90,
                reason="心理状态良好",
                recommendation="保持积极心态"
            )

    def run_attribution(self) -> List[AttributionResult]:
        """执行完整归因分析"""
        self.attributions = [
            self._evaluate_physiological_resilience(),
            self._evaluate_stress_state(),
            self._evaluate_psychological_state()
        ]
        return self.attributions

    def get_overall_score(self) -> float:
        """计算综合健康分数"""
        if not self.attributions:
            self.run_attribution()

        scores = [a.score for a in self.attributions if a.status != "unknown"]
        return sum(scores) / len(scores) if scores else 50.0

    def get_primary_concern(self) -> Optional[AttributionResult]:
        """获取主要关注点（分数最低的维度）"""
        if not self.attributions:
            self.run_attribution()

        valid = [a for a in self.attributions if a.status != "unknown"]
        return min(valid, key=lambda x: x.score) if valid else None


# =============================================================================
# 可视化看板
# =============================================================================

class HealthDashboard:
    """
    健康可视化看板生成器

    生成包含以下图表的看板:
    1. 雷达图 - 多维度健康评分
    2. 仪表盘 - 综合健康分数
    3. 柱状图 - HRV 关键指标
    4. 状态卡片 - 归因结果摘要
    """

    # 颜色配置
    COLORS = {
        'critical': '#FF4444',
        'warning': '#FFAA00',
        'mild': '#88CC00',
        'normal': '#00CC66',
        'unknown': '#AAAAAA',
        'primary': '#4A90D9',
        'secondary': '#7B68EE',
        'background': '#F5F7FA'
    }

    def __init__(self, report: HealthReport, attributions: List[AttributionResult], output_dir: str):
        self.report = report
        self.attributions = attributions
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _get_status_color(self, status: str) -> str:
        """根据状态返回颜色"""
        return self.COLORS.get(status, self.COLORS['unknown'])

    def generate_radar_chart(self, ax: plt.Axes):
        """生成雷达图"""
        categories = [a.dimension for a in self.attributions]
        scores = [a.score for a in self.attributions]

        # 添加闭合点
        categories = categories + [categories[0]]
        scores = scores + [scores[0]]

        # 计算角度
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=True)

        # 绘制雷达图
        ax.fill(angles, scores, color=self.COLORS['primary'], alpha=0.25)
        ax.plot(angles, scores, color=self.COLORS['primary'], linewidth=2)
        ax.scatter(angles[:-1], scores[:-1], color=self.COLORS['primary'], s=80, zorder=5)

        # 设置标签
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([a.dimension for a in self.attributions], fontsize=11)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=9)
        ax.set_title('多维度健康评分', fontsize=14, fontweight='bold', pad=20)

        # 添加参考线
        for score in [20, 40, 60, 80]:
            ax.plot(angles, [score] * len(angles), '--', color='gray', alpha=0.3, linewidth=0.5)

    def generate_gauge_chart(self, ax: plt.Axes, score: float):
        """生成仪表盘图"""
        # 清除坐标轴
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-0.2, 1.2)
        ax.axis('off')

        # 绘制背景弧
        theta = np.linspace(np.pi, 0, 100)
        r = 1.0
        x = r * np.cos(theta)
        y = r * np.sin(theta)

        # 分段颜色
        colors = [self.COLORS['critical'], self.COLORS['warning'],
                  self.COLORS['mild'], self.COLORS['normal']]
        segments = [25, 50, 75, 100]

        for i, (seg_end, color) in enumerate(zip(segments, colors)):
            seg_start = segments[i-1] if i > 0 else 0
            start_angle = np.pi - (seg_start / 100) * np.pi
            end_angle = np.pi - (seg_end / 100) * np.pi
            theta_seg = np.linspace(start_angle, end_angle, 25)

            for j in range(len(theta_seg) - 1):
                wedge = mpatches.Wedge((0, 0), 1.0,
                                       np.degrees(theta_seg[j+1]),
                                       np.degrees(theta_seg[j]),
                                       width=0.3, color=color, alpha=0.7)
                ax.add_patch(wedge)

        # 绘制指针
        needle_angle = np.pi - (score / 100) * np.pi
        needle_length = 0.65
        ax.annotate('', xy=(needle_length * np.cos(needle_angle),
                           needle_length * np.sin(needle_angle)),
                   xytext=(0, 0),
                   arrowprops=dict(arrowstyle='->', color='#333333', lw=3))

        # 中心圆点
        circle = plt.Circle((0, 0), 0.08, color='#333333')
        ax.add_patch(circle)

        # 分数文字
        ax.text(0, -0.15, f'{score:.0f}', fontsize=36, fontweight='bold',
               ha='center', va='center', color='#333333')
        ax.text(0, 0.5, '综合健康分数', fontsize=14, fontweight='bold',
               ha='center', va='center', color='#666666')

        # 刻度标签
        for val in [0, 25, 50, 75, 100]:
            angle = np.pi - (val / 100) * np.pi
            x_pos = 1.15 * np.cos(angle)
            y_pos = 1.15 * np.sin(angle)
            ax.text(x_pos, y_pos, str(val), fontsize=10, ha='center', va='center')

    def generate_hrv_bar_chart(self, ax: plt.Axes):
        """生成 HRV 指标柱状图"""
        hrv = self.report.hrv

        metrics = {
            'SDNN': (hrv.sdnn, 100, 'ms'),
            'RMSSD': (hrv.rmssd, 80, 'ms'),
            'pNN50': (hrv.pnn50, 50, '%'),
            'LF/HF': (hrv.lf_hf_ratio, 3, '')
        }

        names = []
        values = []
        colors = []

        for name, (value, threshold, unit) in metrics.items():
            if value is not None:
                names.append(f'{name}\n({value:.1f}{unit})')
                # 归一化到 0-100
                normalized = min(100, (value / threshold) * 100) if threshold > 0 else 50
                values.append(normalized)

                # 根据值确定颜色
                if name == 'SDNN':
                    if value < 30:
                        colors.append(self.COLORS['critical'])
                    elif value < 50:
                        colors.append(self.COLORS['warning'])
                    else:
                        colors.append(self.COLORS['normal'])
                elif name == 'LF/HF':
                    if value > 4:
                        colors.append(self.COLORS['critical'])
                    elif value > 2.5:
                        colors.append(self.COLORS['warning'])
                    else:
                        colors.append(self.COLORS['normal'])
                else:
                    colors.append(self.COLORS['primary'])

        if not names:
            ax.text(0.5, 0.5, 'HRV 数据缺失', ha='center', va='center',
                   fontsize=14, color='gray', transform=ax.transAxes)
            ax.axis('off')
            return

        bars = ax.bar(names, values, color=colors, edgecolor='white', linewidth=1.5)

        # 添加参考线
        ax.axhline(y=60, color='green', linestyle='--', alpha=0.5, label='正常阈值')
        ax.axhline(y=30, color='red', linestyle='--', alpha=0.5, label='警戒阈值')

        ax.set_ylim(0, 120)
        ax.set_ylabel('归一化分数', fontsize=11)
        ax.set_title('HRV 关键指标', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9)

        # 添加数值标签
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
                   f'{val:.0f}', ha='center', va='bottom', fontsize=10)

    def generate_status_cards(self, ax: plt.Axes):
        """生成状态卡片"""
        ax.axis('off')
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)

        y_pos = 9
        ax.text(5, y_pos, '归因分析结果', fontsize=14, fontweight='bold',
               ha='center', va='center')

        y_pos -= 1.5
        for attr in self.attributions:
            color = self._get_status_color(attr.status)

            # 状态指示圆点
            circle = plt.Circle((0.5, y_pos), 0.2, color=color)
            ax.add_patch(circle)

            # 维度名称和状态
            status_text = {'critical': '严重', 'warning': '警告',
                          'mild': '轻度', 'normal': '正常', 'unknown': '未知'}
            ax.text(1.2, y_pos, f'{attr.dimension}: {status_text.get(attr.status, attr.status)}',
                   fontsize=11, fontweight='bold', va='center')

            # 分数
            ax.text(9.5, y_pos, f'{attr.score:.0f}分', fontsize=11,
                   ha='right', va='center', color=color, fontweight='bold')

            # 原因说明
            y_pos -= 0.8
            reason_short = attr.reason[:40] + '...' if len(attr.reason) > 40 else attr.reason
            ax.text(1.2, y_pos, reason_short, fontsize=9, va='center', color='#666666')

            y_pos -= 1.5

    def generate_dashboard(self, filename: str = None) -> str:
        """生成完整看板"""
        fig = plt.figure(figsize=(16, 12), facecolor=self.COLORS['background'])
        fig.suptitle(f'八爪鱼健康评估看板 - {self.report.report_date}',
                    fontsize=18, fontweight='bold', y=0.98)

        # 创建网格布局
        gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3,
                             left=0.05, right=0.95, top=0.92, bottom=0.05)

        # 1. 雷达图 (左上)
        ax_radar = fig.add_subplot(gs[0, 0], projection='polar')
        self.generate_radar_chart(ax_radar)

        # 2. 仪表盘 (中上)
        ax_gauge = fig.add_subplot(gs[0, 1])
        overall_score = sum(a.score for a in self.attributions) / len(self.attributions)
        self.generate_gauge_chart(ax_gauge, overall_score)

        # 3. HRV 柱状图 (右上)
        ax_hrv = fig.add_subplot(gs[0, 2])
        self.generate_hrv_bar_chart(ax_hrv)

        # 4. 状态卡片 (下方跨越)
        ax_cards = fig.add_subplot(gs[1, :])
        self.generate_status_cards(ax_cards)

        # 保存
        if filename is None:
            filename = f"health_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        output_path = os.path.join(self.output_dir, filename)
        fig.savefig(output_path, dpi=150, bbox_inches='tight',
                   facecolor=self.COLORS['background'])
        plt.close(fig)

        print(f"[OK] 看板已保存: {output_path}")
        return output_path


# =============================================================================
# 主函数与便捷接口
# =============================================================================

def parse_health_pdf(pdf_path: str) -> HealthReport:
    """便捷函数：解析健康报告 PDF"""
    parser = HealthPDFParser(pdf_path)
    return parser.parse()


def analyze_health_report(report: HealthReport) -> Tuple[List[AttributionResult], float]:
    """便捷函数：运行八爪鱼归因分析"""
    model = OctopusAttributionModel(report)
    attributions = model.run_attribution()
    overall_score = model.get_overall_score()
    return attributions, overall_score


def generate_health_dashboard(
    report: HealthReport,
    attributions: List[AttributionResult],
    output_dir: str
) -> str:
    """便捷函数：生成可视化看板"""
    dashboard = HealthDashboard(report, attributions, output_dir)
    return dashboard.generate_dashboard()


def process_health_report(pdf_path: str, output_dir: str) -> Dict[str, Any]:
    """
    一站式处理健康报告

    Args:
        pdf_path: PDF 报告路径
        output_dir: 输出目录

    Returns:
        包含报告、归因结果、看板路径的字典
    """
    print(f"\n{'='*60}")
    print("八爪鱼健康引擎 - 开始处理")
    print(f"{'='*60}")

    # 1. 解析 PDF
    print(f"\n[1/3] 解析 PDF: {pdf_path}")
    report = parse_health_pdf(pdf_path)
    print(f"  - SDNN: {report.hrv.sdnn}")
    print(f"  - LF/HF: {report.hrv.lf_hf_ratio}")
    print(f"  - 焦虑分数: {report.psych.anxiety_score}")

    # 2. 归因分析
    print(f"\n[2/3] 运行归因分析...")
    attributions, overall_score = analyze_health_report(report)
    for attr in attributions:
        print(f"  - {attr.dimension}: {attr.status} ({attr.score:.0f}分)")
    print(f"  - 综合分数: {overall_score:.1f}")

    # 3. 生成看板
    print(f"\n[3/3] 生成可视化看板...")
    dashboard_path = generate_health_dashboard(report, attributions, output_dir)

    print(f"\n{'='*60}")
    print("处理完成!")
    print(f"{'='*60}\n")

    return {
        "report": report,
        "attributions": attributions,
        "overall_score": overall_score,
        "dashboard_path": dashboard_path
    }


# =============================================================================
# 测试与演示
# =============================================================================

def demo_with_mock_data():
    """使用模拟数据演示"""
    print("\n" + "=" * 60)
    print("八爪鱼健康引擎 - 模拟数据演示")
    print("=" * 60)

    # 创建模拟报告 (模拟 SDNN=21.05 的低韧性用户)
    report = HealthReport(
        report_id="DEMO_001",
        user_id="test_user",
        report_date=datetime.now().strftime("%Y-%m-%d"),
        hrv=HRVMetrics(
            sdnn=21.05,           # 低于 30ms 阈值
            rmssd=18.5,
            pnn50=3.2,
            lf_power=450,
            hf_power=120,
            lf_hf_ratio=3.75      # 偏高，交感优势
        ),
        ans=ANSBalance(
            sympathetic=68,
            parasympathetic=32,
            balance_index=36,
            stress_index=125
        ),
        psych=PsychMetrics(
            anxiety_score=12,     # 中度焦虑
            depression_score=8,
            stress_score=15,
            efficacy_score=35
        )
    )

    print(f"\n模拟数据:")
    print(f"  - SDNN: {report.hrv.sdnn} ms (阈值: 30ms)")
    print(f"  - LF/HF: {report.hrv.lf_hf_ratio}")
    print(f"  - 交感/副交感: {report.ans.sympathetic}% / {report.ans.parasympathetic}%")
    print(f"  - 焦虑分数: {report.psych.anxiety_score}")

    # 运行归因分析
    print(f"\n归因分析结果:")
    attributions, overall_score = analyze_health_report(report)

    for attr in attributions:
        print(f"\n  [{attr.dimension}]")
        print(f"    状态: {attr.status} | 分数: {attr.score:.0f}")
        print(f"    原因: {attr.reason}")
        print(f"    建议: {attr.recommendation}")

    print(f"\n综合健康分数: {overall_score:.1f}/100")

    # 生成看板
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             "output", "dashboards")

    print(f"\n生成可视化看板...")
    dashboard_path = generate_health_dashboard(report, attributions, output_dir)

    return {
        "report": report,
        "attributions": attributions,
        "overall_score": overall_score,
        "dashboard_path": dashboard_path
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # 处理指定的 PDF 文件
        pdf_path = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "output/dashboards"
        result = process_health_report(pdf_path, output_dir)
    else:
        # 运行演示
        result = demo_with_mock_data()

    print(f"\n看板保存位置: {result['dashboard_path']}")
