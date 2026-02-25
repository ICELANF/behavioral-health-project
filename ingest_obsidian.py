# -*- coding: utf-8 -*-
"""
ingest_obsidian.py - Obsidian 知识库集成器

功能:
1. 扫描 data/assessments 中的评估报告
2. 为每个用户自动创建 Markdown 档案
3. 自动引用 knowledge/ 下的干预建议
4. 生成可在 Obsidian 中卡片预览的行为处方
5. 向量化知识库用于 RAG 检索

使用方法:
    # 完整流程：扫描数据 + 生成档案 + 向量化
    python ingest_obsidian.py

    # 仅生成用户档案
    python ingest_obsidian.py --generate-profiles

    # 仅向量化知识库
    python ingest_obsidian.py --vectorize-only

    # 指定用户
    python ingest_obsidian.py --user FDBC03D79348
"""

import json
import yaml
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# LlamaIndex (向量化)
try:
    from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
    from llama_index.embeddings.ollama import OllamaEmbedding
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False


# ============ 配置 ============

@dataclass
class ObsidianConfig:
    """Obsidian 配置"""
    vault_path: Path
    users_folder: str = "用户档案"
    prescriptions_folder: str = "行为处方"
    knowledge_folder: str = "knowledge"
    templates_folder: str = "_templates"


# ============ 干预建议映射 ============

# 根据风险等级和指标异常映射到知识库文章
INTERVENTION_MAPPINGS = {
    "stress_high": {
        "knowledge_link": "[[kb_theory/压力管理|压力管理指南]]",
        "tags": ["#压力管理", "#放松技术"],
        "interventions": [
            "深呼吸练习 (4-7-8 呼吸法)",
            "渐进性肌肉放松",
            "正念冥想入门"
        ]
    },
    "fatigue_high": {
        "knowledge_link": "[[kb_theory/疲劳恢复|疲劳恢复策略]]",
        "tags": ["#疲劳管理", "#睡眠优化"],
        "interventions": [
            "睡眠卫生改善",
            "能量管理策略",
            "微休息技术"
        ]
    },
    "mood_low": {
        "knowledge_link": "[[kb_theory/情绪调节|情绪调节方法]]",
        "tags": ["#情绪管理", "#积极心理"],
        "interventions": [
            "行为激活技术",
            "感恩日记",
            "社交连接"
        ]
    },
    "hrv_low": {
        "knowledge_link": "[[kb_theory/HRV优化|心率变异性优化]]",
        "tags": ["#HRV", "#自主神经"],
        "interventions": [
            "心脏相干性训练",
            "有氧运动",
            "压力源识别"
        ]
    },
    "hidden_fatigue": {
        "knowledge_link": "[[kb_theory/隐性疲劳|隐性疲劳识别与应对]]",
        "tags": ["#隐性疲劳", "#早期预警"],
        "interventions": [
            "主动休息安排",
            "工作节奏调整",
            "身体信号觉察"
        ]
    },
    "balanced": {
        "knowledge_link": "[[kb_theory/健康维护|健康状态维护]]",
        "tags": ["#健康维护", "#习惯巩固"],
        "interventions": [
            "继续保持当前习惯",
            "定期自我评估",
            "社交支持网络"
        ]
    }
}


# ============ Obsidian 生成器 ============

class ObsidianGenerator:
    """Obsidian 档案生成器"""

    def __init__(self, project_root: Path = None):
        """
        初始化生成器

        Args:
            project_root: 项目根目录 (同时也是 Obsidian Vault)
        """
        self.project_root = project_root or Path("D:/behavioral-health-project")
        self.data_dir = self.project_root / "data" / "assessments"
        self.processed_dir = self.data_dir / "processed"
        self.knowledge_dir = self.project_root / "knowledge"

        # Obsidian 目录
        self.users_dir = self.project_root / "用户档案"
        self.prescriptions_dir = self.project_root / "行为处方"
        self.templates_dir = self.project_root / "_templates"

        # 确保目录存在
        self.users_dir.mkdir(exist_ok=True)
        self.prescriptions_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)

        # 加载配置
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """加载配置文件"""
        config_path = self.project_root / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    # ============ 扫描数据 ============

    def scan_assessments(self) -> List[Dict]:
        """扫描所有评估数据"""
        users_dir = self.processed_dir / "users"
        if not users_dir.exists():
            print(f"[警告] 用户数据目录不存在: {users_dir}")
            return []

        all_data = []

        for user_dir in users_dir.iterdir():
            if not user_dir.is_dir():
                continue

            user_id = user_dir.name
            user_data = {
                "user_id": user_id,
                "assessments": [],
                "prescriptions": [],
                "profile": {}
            }

            # 读取用户档案
            profile_file = user_dir / "profile.json"
            if profile_file.exists():
                with open(profile_file, 'r', encoding='utf-8') as f:
                    user_data["profile"] = json.load(f)

            # 读取所有评估
            assessments_dir = user_dir / "assessments"
            if assessments_dir.exists():
                for f in sorted(assessments_dir.glob("*.json")):
                    with open(f, 'r', encoding='utf-8') as fp:
                        user_data["assessments"].append(json.load(fp))

            # 读取所有处方
            prescriptions_dir = user_dir / "prescriptions"
            if prescriptions_dir.exists():
                for f in sorted(prescriptions_dir.glob("*.json")):
                    with open(f, 'r', encoding='utf-8') as fp:
                        user_data["prescriptions"].append(json.load(fp))

            if user_data["assessments"]:
                all_data.append(user_data)

        return all_data

    def scan_raw_reports(self) -> List[Path]:
        """扫描 data/raw 中的新报告"""
        raw_dir = self.data_dir / "raw"
        if not raw_dir.exists():
            return []

        reports = []
        for batch_dir in raw_dir.iterdir():
            if batch_dir.is_dir() and batch_dir.name.startswith("batch_"):
                for user_dir in batch_dir.iterdir():
                    if user_dir.is_dir():
                        reports.append(user_dir)

        return reports

    # ============ 生成用户档案 ============

    def generate_user_profile(self, user_data: Dict) -> str:
        """
        生成用户档案 Markdown

        Args:
            user_data: 用户数据 (包含 assessments, prescriptions, profile)

        Returns:
            Markdown 内容
        """
        user_id = user_data["user_id"]
        profile = user_data.get("profile", {})
        assessments = user_data.get("assessments", [])
        prescriptions = user_data.get("prescriptions", [])

        # 获取最新评估
        latest = assessments[-1] if assessments else {}
        psych = latest.get("psych_data", {})
        physio = latest.get("physio_data", {})
        risk = latest.get("risk_assessment", {})

        # 确定干预映射
        interventions = self._get_interventions(latest)

        # 生成 Markdown
        md = f"""---
user_id: "{user_id}"
device_id: "{profile.get('device_id', user_id)}"
created: {datetime.now().strftime('%Y-%m-%d')}
updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
tags:
  - 用户档案
  - {risk.get('level', 'medium')}_risk
{self._format_tags(interventions.get('tags', []))}
aliases:
  - {user_id[-4:]}
---

# {user_id[-4:]} 健康档案

> [!info] 基本信息
> - **用户 ID**: `{user_id}`
> - **设备 ID**: `{profile.get('device_id', 'N/A')}`
> - **首次评估**: {profile.get('first_assessment', 'N/A')}
> - **最近评估**: {profile.get('last_assessment', 'N/A')}
> - **评估次数**: {profile.get('total_assessments', len(assessments))}

---

## 最新状态概览

```dataview
TABLE WITHOUT ID
  composite_score as "综合得分",
  stress_index as "压力指数",
  fatigue_index as "疲劳指数",
  mood_index as "心情指数"
FROM "用户档案"
WHERE user_id = "{user_id}"
```

### 当前指标 ({latest.get('assessment_date', 'N/A')})

| 指标 | 数值 | 状态 |
|------|------|------|
| 综合得分 | {psych.get('composite_score', 0):.0f} | {self._score_emoji(psych.get('composite_score', 70))} |
| 压力指数 | {psych.get('stress_index', 0):.0f} | {self._index_emoji(psych.get('stress_index', 50), reverse=True)} |
| 疲劳指数 | {psych.get('fatigue_index', 0):.0f} | {self._index_emoji(psych.get('fatigue_index', 50), reverse=True)} |
| 心情指数 | {psych.get('mood_index', 0):.0f} | {self._index_emoji(psych.get('mood_index', 50))} |
| SDNN | {physio.get('hrv', {}).get('sdnn', 0):.0f} ms | {self._hrv_emoji(physio.get('hrv', {}).get('sdnn', 50))} |
| RMSSD | {physio.get('hrv', {}).get('rmssd', 0):.0f} ms | {self._hrv_emoji(physio.get('hrv', {}).get('rmssd', 40))} |

### 风险评估

> [!{self._risk_callout_type(risk.get('level', 'medium'))}] 风险等级: {self._risk_label(risk.get('level', 'medium'))}
{self._format_risk_flags(risk.get('flags', []))}

---

## 干预建议

{interventions.get('knowledge_link', '')}

### 推荐干预措施

{self._format_interventions_list(interventions.get('interventions', []))}

---

## 历史评估记录

{self._generate_assessment_history(assessments)}

---

## 行为处方

{self._generate_prescription_cards(prescriptions, user_id)}

---

## 相关知识

- {interventions.get('knowledge_link', '[[knowledge/kb_theory/README|理论知识库]]')}
- [[knowledge/kb_case_studies/README|案例库]]
- [[knowledge/kb_products/README|产品推荐]]

---

## 笔记与观察

> [!note] 教练笔记
> _在此添加个案观察和跟进记录..._

---

*档案生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*由 [[行健行为教练]] 系统自动生成*
"""
        return md

    def _get_interventions(self, assessment: Dict) -> Dict:
        """根据评估数据获取干预建议"""
        psych = assessment.get("psych_data", {})
        physio = assessment.get("physio_data", {})

        stress = psych.get("stress_index", 50)
        fatigue = psych.get("fatigue_index", 50)
        mood = psych.get("mood_index", 50)
        sdnn = physio.get("hrv", {}).get("sdnn", 50)
        rmssd = physio.get("hrv", {}).get("rmssd", 40)

        # 检测隐性疲劳
        if sdnn < 50 and stress < 50 and fatigue < 60:
            return INTERVENTION_MAPPINGS["hidden_fatigue"]

        # 优先级判断
        if stress > 70:
            return INTERVENTION_MAPPINGS["stress_high"]
        if fatigue > 70:
            return INTERVENTION_MAPPINGS["fatigue_high"]
        if mood < 40:
            return INTERVENTION_MAPPINGS["mood_low"]
        if sdnn < 40 or rmssd < 30:
            return INTERVENTION_MAPPINGS["hrv_low"]

        return INTERVENTION_MAPPINGS["balanced"]

    def _format_tags(self, tags: List[str]) -> str:
        """格式化标签为 YAML 列表"""
        return "\n".join(f"  - {tag.replace('#', '')}" for tag in tags)

    def _score_emoji(self, score: float) -> str:
        if score >= 80:
            return "🟢 良好"
        elif score >= 60:
            return "🟡 一般"
        else:
            return "🔴 需关注"

    def _index_emoji(self, index: float, reverse: bool = False) -> str:
        if reverse:
            if index < 40:
                return "🟢 良好"
            elif index < 60:
                return "🟡 一般"
            else:
                return "🔴 偏高"
        else:
            if index >= 60:
                return "🟢 良好"
            elif index >= 40:
                return "🟡 一般"
            else:
                return "🔴 偏低"

    def _hrv_emoji(self, value: float) -> str:
        if value >= 50:
            return "🟢 良好"
        elif value >= 30:
            return "🟡 一般"
        else:
            return "🔴 偏低"

    def _risk_callout_type(self, level: str) -> str:
        return {"high": "danger", "medium": "warning", "low": "success"}.get(level, "info")

    def _risk_label(self, level: str) -> str:
        return {"high": "高风险", "medium": "中等风险", "low": "低风险"}.get(level, "未知")

    def _format_risk_flags(self, flags: List[str]) -> str:
        if not flags:
            return "> 暂无风险提示"
        return "\n".join(f"> - {flag}" for flag in flags)

    def _format_interventions_list(self, interventions: List[str]) -> str:
        return "\n".join(f"- [ ] {item}" for item in interventions)

    def _generate_assessment_history(self, assessments: List[Dict]) -> str:
        """生成评估历史表格"""
        if not assessments:
            return "> 暂无历史记录"

        lines = ["| 日期 | 综合得分 | 压力 | 疲劳 | 心情 | SDNN |",
                 "|------|----------|------|------|------|------|"]

        for ass in assessments[-10:]:  # 最近10条
            psych = ass.get("psych_data", {})
            physio = ass.get("physio_data", {})
            lines.append(
                f"| {ass.get('assessment_date', 'N/A')} | "
                f"{psych.get('composite_score', 0):.0f} | "
                f"{psych.get('stress_index', 0):.0f} | "
                f"{psych.get('fatigue_index', 0):.0f} | "
                f"{psych.get('mood_index', 0):.0f} | "
                f"{physio.get('hrv', {}).get('sdnn', 0):.0f} |"
            )

        return "\n".join(lines)

    def _generate_prescription_cards(self, prescriptions: List[Dict], user_id: str) -> str:
        """生成处方卡片"""
        if not prescriptions:
            return "> 暂无行为处方"

        cards = []
        for rx in prescriptions[-3:]:  # 最近3个处方
            meta = rx.get("prescription_meta", {})
            cards.append(f"![[行为处方/{user_id}_{meta.get('prescription_id', 'rx')}|处方卡片]]")

        return "\n\n".join(cards)

    # ============ 生成处方卡片 ============

    def generate_prescription_card(self, prescription: Dict, user_id: str) -> str:
        """
        生成处方卡片 Markdown (Obsidian Callout 格式)

        Args:
            prescription: 处方数据
            user_id: 用户ID

        Returns:
            Markdown 内容
        """
        meta = prescription.get("prescription_meta", {})
        profile = prescription.get("behavioral_profile", {})
        tasks = prescription.get("tasks", [])
        components = prescription.get("components", {})

        rx_id = meta.get("prescription_id", f"RX-{datetime.now().strftime('%Y%m%d')}")

        md = f"""---
prescription_id: "{rx_id}"
user_id: "{user_id}"
created: {meta.get('created_at', datetime.now().isoformat())[:10]}
behavior_mode: "{profile.get('behavior_mode', 'unknown')}"
change_stage: "{profile.get('change_stage', 'unknown')}"
tags:
  - 行为处方
  - {profile.get('behavior_mode', 'unknown')}
  - {profile.get('change_stage', 'unknown')}
cssclass: prescription-card
---

# 行为处方 {rx_id[-8:]}

> [!abstract] 处方概览
> - **处方名称**: {meta.get('name', '行为健康处方')}
> - **干预策略**: {meta.get('intervention_strategy', 'N/A')}
> - **生成时间**: {meta.get('created_at', 'N/A')[:10]}
> - **关联用户**: [[用户档案/{user_id}|{user_id[-4:]}]]

---

## 行为画像

> [!tip] 当前状态分析
> - **行为模式**: {self._behavior_mode_label(profile.get('behavior_mode', ''))}
> - **改变阶段**: {self._change_stage_label(profile.get('change_stage', ''))}
> - **动机强度**: {profile.get('motivation_strength', 'N/A')}
> - **综合得分**: {profile.get('composite_score', 'N/A')}

---

## 推荐任务

{self._generate_task_cards(tasks)}

---

## 知识科普

> [!book] 相关知识
{self._format_knowledge_items(components.get('knowledge', []))}

---

## 示范视频

> [!video] 教学视频
{self._format_video_items(components.get('videos', []))}

---

## 产品推荐

> [!shopping-cart] 健康产品
{self._format_product_items(components.get('products', []))}

---

## Coach 指导

> [!quote] 教练话术
> {prescription.get('agent_guidance', {}).get('opening_message', '欢迎开始您的健康之旅！')}

### 沟通要点
{self._format_talking_points(prescription.get('agent_guidance', {}).get('talking_points', []))}

---

## 注意事项

> [!warning] 重要提醒
{self._format_warnings(prescription.get('warnings', []))}

---

*处方由 [[行健行为教练]] 系统自动生成*
*本处方仅供参考，如有健康问题请咨询专业医疗人员*
"""
        return md

    def _behavior_mode_label(self, mode: str) -> str:
        labels = {
            "exhaustion": "机体耗竭",
            "hidden_fatigue": "隐性疲劳",
            "overcompensation": "过度补偿",
            "stress_avoidance": "应激逃避",
            "somatization": "躯体化",
            "emotional_dysregulation": "情绪失调",
            "balanced": "平衡状态"
        }
        return labels.get(mode, mode)

    def _change_stage_label(self, stage: str) -> str:
        labels = {
            "precontemplation": "完全对抗",
            "contemplation": "抗拒与反思",
            "preparation": "妥协与接受",
            "action": "顺应与调整",
            "maintenance": "全面臣服"
        }
        return labels.get(stage, stage)

    def _generate_task_cards(self, tasks: List[Dict]) -> str:
        if not tasks:
            return "> 暂无任务"

        cards = []
        for i, task in enumerate(tasks[:5], 1):
            card = f"""
> [!todo] 任务 {i}: {task.get('name', '未命名任务')}
> **描述**: {task.get('description', 'N/A')}
> **难度**: {'⭐' * task.get('difficulty', 1)}
> **频率**: {task.get('frequency', 'N/A')}
> **时长**: {task.get('duration', 'N/A')}
"""
            cards.append(card)

        return "\n".join(cards)

    def _format_knowledge_items(self, items: List[Dict]) -> str:
        if not items:
            return "> 暂无知识点"
        lines = []
        for item in items:
            if isinstance(item, dict):
                lines.append(f"> - [[{item.get('link', '')}|{item.get('title', '知识点')}]]")
            else:
                lines.append(f"> - {item}")
        return "\n".join(lines)

    def _format_video_items(self, items: List[Dict]) -> str:
        if not items:
            return "> 暂无视频"
        lines = []
        for item in items:
            if isinstance(item, dict):
                lines.append(f"> - {item.get('title', '视频')}: `{item.get('path', 'N/A')}`")
            else:
                lines.append(f"> - {item}")
        return "\n".join(lines)

    def _format_product_items(self, items: List[Dict]) -> str:
        if not items:
            return "> 暂无产品"
        lines = []
        for item in items:
            if isinstance(item, dict):
                lines.append(f"> - **{item.get('name', '产品')}**: {item.get('description', 'N/A')}")
            else:
                lines.append(f"> - {item}")
        return "\n".join(lines)

    def _format_talking_points(self, points: List[str]) -> str:
        if not points:
            return "- 建立信任关系\n- 倾听用户需求"
        return "\n".join(f"- {point}" for point in points)

    def _format_warnings(self, warnings: List[str]) -> str:
        if not warnings:
            return "> - 请遵循医生建议\n> - 如有不适请停止练习"
        return "\n".join(f"> - {w}" for w in warnings)

    # ============ 批量生成 ============

    def generate_all_profiles(self, user_id: str = None):
        """
        生成所有用户档案

        Args:
            user_id: 可选，指定单个用户
        """
        print("\n" + "=" * 60)
        print("Obsidian 档案生成器")
        print("=" * 60)

        all_data = self.scan_assessments()
        print(f"扫描到 {len(all_data)} 个用户数据")

        if user_id:
            all_data = [d for d in all_data if d["user_id"] == user_id]
            if not all_data:
                print(f"[错误] 未找到用户: {user_id}")
                return

        generated = 0
        for user_data in all_data:
            uid = user_data["user_id"]

            # 生成用户档案
            profile_md = self.generate_user_profile(user_data)
            profile_path = self.users_dir / f"{uid}.md"
            with open(profile_path, 'w', encoding='utf-8') as f:
                f.write(profile_md)
            print(f"  [生成] 用户档案: {profile_path.name}")

            # 生成处方卡片
            for rx in user_data.get("prescriptions", []):
                rx_id = rx.get("prescription_meta", {}).get("prescription_id", "rx")
                rx_md = self.generate_prescription_card(rx, uid)
                rx_path = self.prescriptions_dir / f"{uid}_{rx_id}.md"
                with open(rx_path, 'w', encoding='utf-8') as f:
                    f.write(rx_md)
                print(f"  [生成] 处方卡片: {rx_path.name}")

            generated += 1

        print(f"\n完成！生成 {generated} 个用户档案")
        print(f"档案目录: {self.users_dir}")
        print(f"处方目录: {self.prescriptions_dir}")

    # ============ 创建干预知识库 ============

    def create_intervention_knowledge(self):
        """创建干预建议知识库文件"""
        kb_theory = self.knowledge_dir / "kb_theory"
        kb_theory.mkdir(parents=True, exist_ok=True)

        knowledge_files = {
            "压力管理.md": self._create_stress_management_kb(),
            "疲劳恢复.md": self._create_fatigue_recovery_kb(),
            "情绪调节.md": self._create_emotion_regulation_kb(),
            "HRV优化.md": self._create_hrv_optimization_kb(),
            "隐性疲劳.md": self._create_hidden_fatigue_kb(),
            "健康维护.md": self._create_health_maintenance_kb(),
        }

        for filename, content in knowledge_files.items():
            filepath = kb_theory / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  [创建] 知识库文件: {filename}")

        print(f"\n知识库文件已创建于: {kb_theory}")

    def _create_stress_management_kb(self) -> str:
        return """---
tags:
  - 压力管理
  - 放松技术
  - 知识库
aliases:
  - 压力管理指南
---

# 压力管理指南

## 概述

压力是身体对外界刺激的自然反应，适度压力有助于提高工作效率，但长期高压力状态会损害身心健康。

## 核心技术

### 1. 4-7-8 呼吸法

> [!tip] 操作步骤
> 1. 用鼻子吸气 4 秒
> 2. 屏住呼吸 7 秒
> 3. 用嘴呼气 8 秒
> 4. 重复 3-4 个循环

**原理**: 激活副交感神经，降低心率和血压

### 2. 渐进性肌肉放松 (PMR)

从脚趾开始，依次紧张和放松身体各部位肌肉群：
- 紧张 5 秒 → 放松 10 秒
- 从下往上：脚 → 小腿 → 大腿 → 腹部 → 胸部 → 手 → 肩 → 脸

### 3. 正念冥想

- **专注呼吸**: 将注意力集中在呼吸上
- **身体扫描**: 觉察身体各部位的感受
- **观察思绪**: 不评判地观察思绪来去

## 日常策略

- [ ] 每天安排 10 分钟放松时间
- [ ] 识别压力触发因素
- [ ] 建立规律作息
- [ ] 保持社交连接
- [ ] 适量运动

## 相关链接

- [[疲劳恢复]]
- [[情绪调节]]
- [[HRV优化]]

---

*来源: 行健行为教练知识库*
"""

    def _create_fatigue_recovery_kb(self) -> str:
        return """---
tags:
  - 疲劳管理
  - 睡眠优化
  - 知识库
aliases:
  - 疲劳恢复策略
---

# 疲劳恢复策略

## 概述

疲劳分为生理疲劳和心理疲劳，两者常相互影响。科学的恢复策略有助于快速恢复精力。

## 睡眠优化

### 睡眠卫生原则

> [!important] 核心要点
> - 固定作息时间 (误差 < 30 分钟)
> - 睡前 1 小时远离蓝光屏幕
> - 卧室温度保持 18-22°C
> - 避免睡前 4 小时内摄入咖啡因

### 睡眠周期

一个完整睡眠周期约 90 分钟，建议睡眠时长为 90 分钟的倍数 (如 6h, 7.5h)。

## 能量管理

### 番茄工作法

- 工作 25 分钟 → 休息 5 分钟
- 每 4 个番茄钟后休息 15-30 分钟

### 微休息技术

每 1-2 小时进行 2-5 分钟的微休息：
- 站起来伸展
- 看远处放松眼睛
- 深呼吸几次

## 恢复清单

- [ ] 保证每晚 7-8 小时睡眠
- [ ] 午间小憩 10-20 分钟
- [ ] 每小时起身活动
- [ ] 保持水分摄入
- [ ] 减少加工食品

## 相关链接

- [[压力管理]]
- [[隐性疲劳]]
- [[健康维护]]

---

*来源: 行健行为教练知识库*
"""

    def _create_emotion_regulation_kb(self) -> str:
        return """---
tags:
  - 情绪管理
  - 积极心理
  - 知识库
aliases:
  - 情绪调节方法
---

# 情绪调节方法

## 概述

情绪调节是管理和改变情绪体验的能力，健康的情绪调节有助于心理韧性和幸福感。

## 核心技术

### 1. 行为激活

> [!tip] 核心原则
> 先行动，后感受。通过增加积极活动来改善情绪。

**步骤**:
1. 列出过去带来愉悦感的活动
2. 每天安排至少一项积极活动
3. 记录活动后的情绪变化

### 2. 感恩日记

每天记录 3 件感恩的事：
- 具体描述事件
- 反思为什么感恩
- 体会感恩的情绪

### 3. 认知重评

改变对事件的解读方式：
- 识别负面自动思维
- 寻找替代解释
- 评估证据

## 社交连接

- 主动联系朋友或家人
- 参与社交活动
- 寻求支持时明确表达需求

## 每日练习

- [ ] 晨间积极意图设定
- [ ] 记录 3 件感恩的事
- [ ] 至少一次有意义的社交互动
- [ ] 睡前回顾当日小确幸

## 相关链接

- [[压力管理]]
- [[健康维护]]

---

*来源: 行健行为教练知识库*
"""

    def _create_hrv_optimization_kb(self) -> str:
        return """---
tags:
  - HRV
  - 自主神经
  - 知识库
aliases:
  - 心率变异性优化
---

# 心率变异性 (HRV) 优化

## 概述

心率变异性 (HRV) 是指心跳间隔的变化程度，是自主神经系统功能的重要指标。

## 关键指标

| 指标 | 含义 | 健康范围 |
|------|------|----------|
| SDNN | 心脏整体调节能力 | > 50 ms |
| RMSSD | 副交感神经活性/恢复能力 | > 30 ms |
| LF/HF | 交感/副交感平衡 | 0.5 - 2.0 |

## 提升 HRV 的方法

### 1. 心脏相干性训练

> [!tip] 呼吸模式
> 以每分钟 5-7 次的频率进行深呼吸 (约 10 秒一个呼吸周期)

**效果**: 使心率变化与呼吸同步，提升 HRV

### 2. 有氧运动

- 每周 3-5 次，每次 30-60 分钟
- 中等强度 (心率 60-70% 最大心率)
- 推荐: 快走、游泳、骑车

### 3. 压力管理

慢性压力会降低 HRV：
- 练习正念冥想
- 保证充足睡眠
- 减少咖啡因和酒精

## 监测建议

- 每日晨起测量 (固定时间、姿势)
- 关注长期趋势而非单次数值
- 使用可靠的 HRV 监测设备

## 影响因素

**正面影响**: 运动、深呼吸、优质睡眠、放松
**负面影响**: 压力、熬夜、酒精、疾病、过度训练

## 相关链接

- [[压力管理]]
- [[疲劳恢复]]
- [[隐性疲劳]]

---

*来源: 行健行为教练知识库*
"""

    def _create_hidden_fatigue_kb(self) -> str:
        return """---
tags:
  - 隐性疲劳
  - 早期预警
  - 知识库
aliases:
  - 隐性疲劳识别与应对
---

# 隐性疲劳识别与应对

## 概述

> [!warning] 什么是隐性疲劳？
> 隐性疲劳是指 **主观感受良好** 但 **生理指标已显示疲劳** 的状态。
> 这是一种早期预警信号，如不及时处理可能发展为明显的身心问题。

## 识别特征

### 生理信号 (HRV 层面)

- SDNN < 50 ms (心脏调节能力下降)
- RMSSD < 30 ms (恢复能力不足)
- 晨脉偏高

### 主观感受

- 自我感觉压力不大
- 认为自己精力充沛
- 否认疲劳感

### 行为表现

- 工作效率下降但未察觉
- 睡眠质量变差
- 容易忘事

## 为什么会出现隐性疲劳？

1. **适应性麻木**: 长期压力下身体适应，感觉阈值提高
2. **认知偏差**: 过度乐观评估自身状态
3. **忽视身体信号**: 工作繁忙时忽略身体反馈

## 应对策略

### 1. 主动休息安排

> [!tip] 不要等累了再休息
> - 每工作 90 分钟主动休息 15 分钟
> - 每周安排一天完全放松
> - 睡前 1 小时进入放松模式

### 2. 身体信号觉察

- 每天 3 次身体扫描 (早、中、晚)
- 记录睡眠质量和晨起状态
- 定期测量 HRV

### 3. 工作节奏调整

- 避免连续高强度工作
- 设置工作时间边界
- 学会说"不"

## 预防清单

- [ ] 每日固定时间监测 HRV
- [ ] 每周安排一天恢复日
- [ ] 建立规律的睡眠时间
- [ ] 每天至少 30 分钟户外活动
- [ ] 每周进行一次自我状态评估

## 何时需要关注？

> [!danger] 警示信号
> - HRV 连续 3 天低于个人基线
> - 睡眠时间足够但仍感疲惫
> - 工作效率明显下降
> - 情绪波动增加

## 相关链接

- [[疲劳恢复]]
- [[HRV优化]]
- [[压力管理]]

---

*来源: 行健行为教练知识库*
"""

    def _create_health_maintenance_kb(self) -> str:
        return """---
tags:
  - 健康维护
  - 习惯巩固
  - 知识库
aliases:
  - 健康状态维护
---

# 健康状态维护

## 概述

当各项健康指标处于良好范围时，重点是维护现有状态，防止退步。

## 维护原则

> [!success] 三个关键
> 1. **一致性**: 保持健康习惯的规律性
> 2. **监测性**: 定期追踪关键指标
> 3. **适应性**: 根据变化调整策略

## 日常健康习惯

### 睡眠

- 固定就寝和起床时间
- 保证 7-8 小时睡眠
- 创造良好睡眠环境

### 运动

- 每周至少 150 分钟中等强度运动
- 包含有氧和力量训练
- 避免久坐 (每小时起身活动)

### 营养

- 均衡饮食，多蔬果
- 充足水分摄入
- 限制加工食品和糖

### 心理

- 保持社交连接
- 培养兴趣爱好
- 定期自我反思

## 定期评估

| 频率 | 评估内容 |
|------|----------|
| 每日 | 睡眠质量、精力状态、情绪 |
| 每周 | HRV 趋势、运动完成情况 |
| 每月 | 综合健康评估、习惯执行率 |
| 每季 | 健康目标回顾与调整 |

## 预防退步

### 识别早期信号

- HRV 下降趋势
- 睡眠质量变差
- 精力下降
- 情绪波动增加

### 应对策略

- 及时识别压力源
- 调整生活节奏
- 寻求支持
- 回顾有效的应对方法

## 进阶目标

当基础稳固后，可考虑：
- 挑战更高的运动目标
- 学习新的放松技术
- 建立更深的社交连接
- 培养正念习惯

## 相关链接

- [[压力管理]]
- [[情绪调节]]
- [[HRV优化]]

---

*来源: 行健行为教练知识库*
"""

    # ============ 向量化 ============

    def vectorize_knowledge(self):
        """向量化知识库"""
        if not LLAMAINDEX_AVAILABLE:
            print("[错误] llama_index 未安装，无法向量化")
            return

        print("\n正在向量化知识库...")

        # 设置 Embedding 模型
        embed_model = self.config.get("model", {}).get("embed", "mxbai-embed-large:latest")
        Settings.embed_model = OllamaEmbedding(model_name=embed_model)

        # 扫描所有 Markdown 文件
        scan_dirs = [
            self.knowledge_dir,
            self.users_dir,
            self.prescriptions_dir
        ]

        all_docs = []
        for dir_path in scan_dirs:
            if dir_path.exists():
                reader = SimpleDirectoryReader(
                    input_dir=str(dir_path),
                    recursive=True,
                    required_exts=[".md"]
                )
                docs = reader.load_data()
                all_docs.extend(docs)
                print(f"  扫描 {dir_path.name}: {len(docs)} 个文档")

        if not all_docs:
            print("[警告] 未找到任何文档")
            return

        print(f"\n总计 {len(all_docs)} 个文档，正在生成向量索引...")

        # 生成索引
        index = VectorStoreIndex.from_documents(all_docs)

        # 保存
        vectordb_path = self.config.get("paths", {}).get("vectordb", "data/vectordb")
        index.storage_context.persist(persist_dir=vectordb_path)

        print(f"✅ 向量化完成！索引保存至: {vectordb_path}")


# ============ 创建模板 ============

def create_obsidian_templates(project_root: Path):
    """创建 Obsidian 模板文件"""
    templates_dir = project_root / "_templates"
    templates_dir.mkdir(exist_ok=True)

    # 用户档案模板
    user_template = """---
user_id: "{{user_id}}"
device_id: "{{device_id}}"
created: {{date}}
tags:
  - 用户档案
---

# {{user_id}} 健康档案

## 基本信息

- **用户 ID**: `{{user_id}}`
- **设备 ID**: `{{device_id}}`

## 评估记录

> 在此添加评估数据...

## 行为处方

> 在此添加处方链接...

## 笔记

> 在此添加观察笔记...
"""

    # 处方卡片模板
    rx_template = """---
prescription_id: "{{rx_id}}"
user_id: "{{user_id}}"
created: {{date}}
tags:
  - 行为处方
cssclass: prescription-card
---

# 行为处方 {{rx_id}}

## 处方概览

- **名称**: {{name}}
- **策略**: {{strategy}}

## 推荐任务

> [!todo] 任务列表
> - [ ] 任务 1
> - [ ] 任务 2

## 相关知识

- [[知识链接]]

## Coach 指导

> 教练话术...
"""

    with open(templates_dir / "用户档案模板.md", 'w', encoding='utf-8') as f:
        f.write(user_template)

    with open(templates_dir / "处方卡片模板.md", 'w', encoding='utf-8') as f:
        f.write(rx_template)

    print(f"模板文件已创建于: {templates_dir}")


# ============ 主函数 ============

def main():
    parser = argparse.ArgumentParser(description="Obsidian 知识库集成器")
    parser.add_argument("--generate-profiles", action="store_true", help="生成用户档案")
    parser.add_argument("--create-knowledge", action="store_true", help="创建干预知识库")
    parser.add_argument("--vectorize-only", action="store_true", help="仅向量化")
    parser.add_argument("--create-templates", action="store_true", help="创建模板文件")
    parser.add_argument("--user", help="指定用户 ID")
    parser.add_argument("--all", action="store_true", help="执行所有操作")

    args = parser.parse_args()

    project_root = Path("D:/behavioral-health-project")
    generator = ObsidianGenerator(project_root)

    # 默认执行所有操作
    if not any([args.generate_profiles, args.create_knowledge,
                args.vectorize_only, args.create_templates, args.all]):
        args.all = True

    if args.all or args.create_knowledge:
        print("\n[1/4] 创建干预知识库...")
        generator.create_intervention_knowledge()

    if args.all or args.create_templates:
        print("\n[2/4] 创建 Obsidian 模板...")
        create_obsidian_templates(project_root)

    if args.all or args.generate_profiles:
        print("\n[3/4] 生成用户档案...")
        generator.generate_all_profiles(user_id=args.user)

    if args.all or args.vectorize_only:
        print("\n[4/4] 向量化知识库...")
        generator.vectorize_knowledge()

    print("\n" + "=" * 60)
    print("Obsidian 集成完成！")
    print("=" * 60)
    print(f"\n在 Obsidian 中打开: {project_root}")
    print("\n目录结构:")
    print(f"  用户档案/  - 用户健康档案 Markdown")
    print(f"  行为处方/  - 处方卡片 Markdown")
    print(f"  knowledge/ - 干预建议知识库")
    print(f"  _templates/ - Obsidian 模板")


if __name__ == "__main__":
    main()
