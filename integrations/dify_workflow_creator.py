# -*- coding: utf-8 -*-
"""
dify_workflow_creator.py - Dify 工作流创建器

通过 Dify API 创建和配置工作流应用，支持：
- TTM 行为阶段评估
- 专业处方生成
- 多 Agent 协同工作流
"""

import json
import uuid
import os
from typing import Dict, Any, List, Optional

# Optional import for API functionality
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = None
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# --- Configuration ---
DIFY_API_KEY = os.environ.get('DIFY_API_KEY', 'your_dify_api_key_here')
DIFY_BASE_URL = os.environ.get('DIFY_BASE_URL', 'http://localhost/console/api')

# Model Configuration
MODEL_PROVIDER = 'tongyi'  # or 'ollama', etc.
MODEL_NAME = 'qwen2.5:0.5b'


class WorkflowNodeType(Enum):
    """工作流节点类型"""
    START = "start"
    END = "end"
    LLM = "llm"
    CODE = "code"
    CONDITION = "condition"
    VARIABLE = "variable"
    HTTP_REQUEST = "http_request"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"


@dataclass
class WorkflowNode:
    """工作流节点"""
    node_id: str
    node_type: WorkflowNodeType
    title: str
    description: str = ""
    model_provider: str = MODEL_PROVIDER
    model_name: str = MODEL_NAME
    prompt_template: str = ""
    variables: List[Dict[str, Any]] = field(default_factory=list)
    temperature: float = 0.7
    position: Dict[str, int] = field(default_factory=lambda: {"x": 0, "y": 0})

    def to_dify_node(self) -> Dict[str, Any]:
        """转换为 Dify 节点格式"""
        if self.node_type == WorkflowNodeType.START:
            return {
                "id": self.node_id,
                "position": self.position,
                "data": {
                    "type": "start",
                    "title": self.title,
                    "desc": self.description
                }
            }
        elif self.node_type == WorkflowNodeType.END:
            return {
                "id": self.node_id,
                "position": self.position,
                "data": {
                    "type": "end",
                    "title": self.title,
                    "desc": self.description
                }
            }
        elif self.node_type == WorkflowNodeType.LLM:
            return {
                "id": self.node_id,
                "position": self.position,
                "data": {
                    "title": self.title,
                    "type": "llm",
                    "desc": self.description,
                    "model": {
                        "provider": self.model_provider,
                        "name": self.model_name,
                        "mode": "chat"
                    },
                    "variables": self.variables,
                    "prompt_template": {"prompt": self.prompt_template},
                    "completion_params": {"temperature": self.temperature}
                }
            }
        return {}


@dataclass
class WorkflowEdge:
    """工作流边（连接）"""
    source_id: str
    target_id: str
    edge_id: str = ""

    def __post_init__(self):
        if not self.edge_id:
            self.edge_id = f"edge-{uuid.uuid4().hex[:8]}"

    def to_dify_edge(self) -> Dict[str, Any]:
        return {
            "id": self.edge_id,
            "source": self.source_id,
            "target": self.target_id
        }


# ============================================================================
# Prompt Templates - 行为健康评估与处方
# ============================================================================

PROMPT_TTM_ASSESSOR = """
# Role
You are a professional behavioral health assessment expert, proficient in the "Transtheoretical Model (TTM)" and the proprietary "Five-Level Psychological Readiness Model". Your task is to analyze the user's input and determine their stage of behavior change.

# Context
The user is using a behavioral health coaching application. You need to assess their psychological readiness for health behavior change based on their input.

# Five-Level Psychological Readiness Model (Primary Reference)
1. **完全对抗 (Full Resistance)**: User sees change as a threat. Shows denial, defensiveness. SPI coefficient: 0.3
2. **抗拒与反思 (Resistance & Reflection)**: Doesn't want to change but starting to see necessity. Ambivalent. SPI coefficient: 0.5
3. **妥协与接受 (Compromise & Acceptance)**: Accepts change is necessary but wants control. Ready for small steps. SPI coefficient: 0.7
4. **顺应与调整 (Adaptation & Adjustment)**: Views change as reasonable, willing to adapt. SPI coefficient: 0.9
5. **全面臣服 (Full Integration)**: Change has become part of identity. SPI coefficient: 1.0

# TTM Stages (Secondary Reference)
- Precontemplation, Contemplation, Preparation, Action, Maintenance

# Constraints
- Remain objective, inferring only from the text provided by the user.
- If the user's input is ambiguous, prioritize classifying as "抗拒与反思" with Low confidence.
- Map to both Five-Level and TTM stages.

# Output Format
Output JSON directly without code block markers:
{
    "five_level_stage": "Stage Name in Chinese",
    "five_level_stage_en": "Stage Name in English",
    "ttm_stage": "TTM Stage Name",
    "spi_coefficient": 0.3-1.0,
    "reasoning": "Brief justification (under 80 words)",
    "confidence": "High/Medium/Low",
    "risk_level": "low/moderate/high/critical",
    "recommended_approach": "Brief intervention approach suggestion"
}
"""

PROMPT_INTERVENTION_PRESCRIBER = """
# Role
You are a senior behavioral health coach specializing in personalized intervention plans. You have received the user's behavior change stage assessment.

# Task
Based on the user's psychological readiness stage, provide a targeted behavioral intervention "prescription" with specific, actionable tasks.

# Input Data
- User Stage: {{stage}}
- SPI Coefficient: {{spi_coefficient}}
- User Query: {{query}}
- Focus Domain: {{focus_domain}}

# Four-Phase Cultivation Strategy
1. **启动期 (Startup Phase)**: Weeks 1-2, daily support, establish routine
2. **适应期 (Adaptation Phase)**: Weeks 3-8, weekly support, build automaticity
3. **稳定期 (Stability Phase)**: Months 2-4, monthly support, reduce dependency
4. **内化期 (Internalization Phase)**: 4+ months, as-needed support, identity integration

# Strategy by Five-Level Stage
1. **完全对抗**: Strategy = "建立安全感". Gentle tone, don't push, validate concerns, recommend only observation task.
2. **抗拒与反思**: Strategy = "矛盾处理". Acknowledge ambivalence, explore pros/cons, recommend reflection task.
3. **妥协与接受**: Strategy = "门槛降低". Lower barriers, micro-habits, recommend one simple action.
4. **顺应与调整**: Strategy = "习惯强化". Build on momentum, gradual increase, recommend routine task.
5. **全面臣服**: Strategy = "身份巩固". Affirm identity, advanced challenges, recommend mentorship.

# Efficacy-Based Task Limits
- Efficacy < 20: Max 1 task, difficulty 1
- Efficacy < 50: Max 2 tasks, difficulty 2
- Efficacy >= 50: Max 3 tasks, difficulty up to 5

# Output Format
Provide response including:
1. **[共情回应]**: Acknowledge their psychological state (1-2 sentences)
2. **[行为处方]**:
   - 今日任务 (1-3 specific tasks with timing)
   - 任务难度 (1-5 stars)
   - 预计时长
3. **[知识要点]**: One key insight related to their situation
4. **[安全提醒]**: If applicable
5. **[下次跟进]**: When to check in next
"""

PROMPT_SLEEP_AGENT = """
# Role
You are a Sleep Health Specialist Agent, expert in sleep science, circadian rhythms, and the relationship between sleep and metabolic health.

# Task
Analyze the user's sleep-related concerns and provide evidence-based recommendations.

# Input Data
- User Query: {{query}}
- Sleep Data (if available): {{sleep_data}}
- Glucose Data (if available): {{glucose_data}}
- Current Stage: {{stage}}

# Key Assessment Areas
1. Sleep duration and timing
2. Sleep quality indicators
3. Sleep-glucose relationship
4. Circadian rhythm alignment
5. Sleep hygiene practices

# Output Format
{
    "analysis": "Summary of findings",
    "risk_level": "low/moderate/high",
    "key_findings": ["finding1", "finding2"],
    "recommendations": [
        {"type": "behavior", "action": "specific action", "timing": "when", "priority": 1-3}
    ],
    "sleep_glucose_correlation": "explanation if relevant",
    "tags": ["relevant", "tags"]
}
"""

PROMPT_GLUCOSE_AGENT = """
# Role
You are a Metabolic Health Specialist Agent, expert in glucose management, CGM data interpretation, and diabetes prevention.

# Task
Analyze the user's glucose-related concerns and CGM data patterns.

# Input Data
- User Query: {{query}}
- CGM Summary: {{cgm_data}}
- Current Stage: {{stage}}

# Key Assessment Areas
1. Time in Range (TIR) analysis
2. Glucose variability (CV%)
3. Post-meal patterns
4. Overnight glucose trends
5. Hypoglycemia/hyperglycemia events

# Output Format
{
    "analysis": "Summary of glucose patterns",
    "risk_level": "low/moderate/high/critical",
    "tir_assessment": "Time in range evaluation",
    "key_findings": ["finding1", "finding2"],
    "recommendations": [
        {"type": "nutrition/behavior/monitoring", "action": "specific action", "rationale": "why"}
    ],
    "urgent_flags": [],
    "tags": ["relevant", "tags"]
}
"""


# ============================================================================
# Dify Workflow Creator Class
# ============================================================================

class DifyWorkflowCreator:
    """Dify 工作流创建器"""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or DIFY_API_KEY
        self.base_url = base_url or DIFY_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def _check_requests(self) -> bool:
        """检查 requests 模块是否可用"""
        if not HAS_REQUESTS:
            print("Error: 'requests' module not installed. Run: pip install requests")
            return False
        return True

    def create_app(self, name: str, icon: str = "🤖") -> Optional[str]:
        """创建 Dify 应用"""
        if not self._check_requests():
            return None
        if self.api_key == 'your_dify_api_key_here':
            print("Error: Please set DIFY_API_KEY environment variable or provide API key.")
            return None

        payload = {
            "name": name,
            "mode": "workflow",
            "icon": icon
        }
        try:
            response = requests.post(
                f"{self.base_url}/apps",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            app_data = response.json()
            print(f"✅ Application created: {name} (ID: {app_data['id']})")
            return app_data['id']
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to create application: {e}")
            return None

    def get_workflow_draft(self, app_id: str) -> Optional[Dict]:
        """获取工作流草稿"""
        try:
            response = requests.get(
                f"{self.base_url}/apps/{app_id}/workflow-draft",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch workflow draft: {e}")
            return None

    def update_workflow(self, app_id: str, graph: Dict) -> bool:
        """更新工作流"""
        try:
            response = requests.post(
                f"{self.base_url}/apps/{app_id}/workflow-draft",
                headers=self.headers,
                json={"graph": graph}
            )
            response.raise_for_status()
            print("✅ Workflow updated successfully.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to update workflow: {e}")
            return False

    def publish_workflow(self, app_id: str, description: str = "") -> bool:
        """发布工作流"""
        try:
            response = requests.post(
                f"{self.base_url}/apps/{app_id}/workflows/publish",
                headers=self.headers,
                json={"description": description}
            )
            response.raise_for_status()
            print("🚀 Workflow published successfully!")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to publish workflow: {e}")
            return False

    def build_workflow_graph(self,
                             nodes: List[WorkflowNode],
                             edges: List[WorkflowEdge]) -> Dict:
        """构建工作流图"""
        return {
            "nodes": [n.to_dify_node() for n in nodes],
            "edges": [e.to_dify_edge() for e in edges]
        }


# ============================================================================
# Pre-built Workflow Templates
# ============================================================================

def create_ttm_assessment_workflow(creator: DifyWorkflowCreator,
                                   app_name: str = "Behavioral Health TTM Assessment") -> Optional[str]:
    """创建 TTM 行为阶段评估工作流"""

    # Step 1: Create app
    app_id = creator.create_app(app_name, "🧠")
    if not app_id:
        return None

    # Step 2: Get draft to find start/end nodes
    draft = creator.get_workflow_draft(app_id)
    if not draft:
        return None

    graph = draft['graph']
    start_node = next(n for n in graph['nodes'] if n['data']['type'] == 'start')
    end_node = next(n for n in graph['nodes'] if n['data']['type'] == 'end')

    # Step 3: Define nodes
    assessor_id = f"llm-{uuid.uuid4().hex[:8]}"
    prescriber_id = f"llm-{uuid.uuid4().hex[:8]}"

    nodes = [
        WorkflowNode(
            node_id=start_node['id'],
            node_type=WorkflowNodeType.START,
            title="Start",
            position=start_node.get('position', {"x": 0, "y": 0})
        ),
        WorkflowNode(
            node_id=assessor_id,
            node_type=WorkflowNodeType.LLM,
            title="A1 TTM/Five-Level Assessor",
            description="Analyzes user input to determine behavior change stage",
            prompt_template=PROMPT_TTM_ASSESSOR,
            variables=[{"variable": "query", "value_selector": ["sys", "query"]}],
            temperature=0.3,
            position={"x": 300, "y": 0}
        ),
        WorkflowNode(
            node_id=prescriber_id,
            node_type=WorkflowNodeType.LLM,
            title="A2 Intervention Prescriber",
            description="Provides personalized intervention based on stage",
            prompt_template=PROMPT_INTERVENTION_PRESCRIBER,
            variables=[
                {"variable": "stage", "value_selector": [assessor_id, "text"]},
                {"variable": "spi_coefficient", "value_selector": [assessor_id, "text"]},
                {"variable": "query", "value_selector": ["sys", "query"]},
                {"variable": "focus_domain", "value_selector": ["sys", "query"]}
            ],
            temperature=0.7,
            position={"x": 600, "y": 0}
        ),
        WorkflowNode(
            node_id=end_node['id'],
            node_type=WorkflowNodeType.END,
            title="End",
            position=end_node.get('position', {"x": 900, "y": 0})
        )
    ]

    edges = [
        WorkflowEdge(start_node['id'], assessor_id),
        WorkflowEdge(assessor_id, prescriber_id),
        WorkflowEdge(prescriber_id, end_node['id'])
    ]

    # Step 4: Build and update graph
    new_graph = creator.build_workflow_graph(nodes, edges)
    # Keep start/end from original, replace with our nodes
    new_graph['nodes'] = [
        start_node,
        nodes[1].to_dify_node(),
        nodes[2].to_dify_node(),
        end_node
    ]

    if not creator.update_workflow(app_id, new_graph):
        return None

    # Step 5: Publish
    creator.publish_workflow(
        app_id,
        "TTM/Five-Level Assessment + Intervention Prescriber workflow"
    )

    return app_id


def create_multi_agent_workflow(creator: DifyWorkflowCreator,
                                app_name: str = "Behavioral Health Multi-Agent") -> Optional[str]:
    """创建多 Agent 协同工作流（评估→路由→专业Agent→处方）"""

    app_id = creator.create_app(app_name, "🏥")
    if not app_id:
        return None

    draft = creator.get_workflow_draft(app_id)
    if not draft:
        return None

    graph = draft['graph']
    start_node = next(n for n in graph['nodes'] if n['data']['type'] == 'start')
    end_node = next(n for n in graph['nodes'] if n['data']['type'] == 'end')

    # Define node IDs
    assessor_id = f"llm-{uuid.uuid4().hex[:8]}"
    sleep_agent_id = f"llm-{uuid.uuid4().hex[:8]}"
    glucose_agent_id = f"llm-{uuid.uuid4().hex[:8]}"
    synthesizer_id = f"llm-{uuid.uuid4().hex[:8]}"

    # For simplicity, we'll create a linear flow (in production, use condition nodes for routing)
    nodes_data = [
        start_node,
        {
            "id": assessor_id,
            "position": {"x": 250, "y": 0},
            "data": {
                "title": "Stage Assessor",
                "type": "llm",
                "desc": "Assess user's behavior change stage",
                "model": {"provider": MODEL_PROVIDER, "name": MODEL_NAME, "mode": "chat"},
                "variables": [{"variable": "query", "value_selector": ["sys", "query"]}],
                "prompt_template": {"prompt": PROMPT_TTM_ASSESSOR},
                "completion_params": {"temperature": 0.3}
            }
        },
        {
            "id": sleep_agent_id,
            "position": {"x": 500, "y": -100},
            "data": {
                "title": "Sleep Agent",
                "type": "llm",
                "desc": "Analyze sleep-related concerns",
                "model": {"provider": MODEL_PROVIDER, "name": MODEL_NAME, "mode": "chat"},
                "variables": [
                    {"variable": "query", "value_selector": ["sys", "query"]},
                    {"variable": "stage", "value_selector": [assessor_id, "text"]},
                    {"variable": "sleep_data", "value_selector": ["sys", "query"]},
                    {"variable": "glucose_data", "value_selector": ["sys", "query"]}
                ],
                "prompt_template": {"prompt": PROMPT_SLEEP_AGENT},
                "completion_params": {"temperature": 0.5}
            }
        },
        {
            "id": glucose_agent_id,
            "position": {"x": 500, "y": 100},
            "data": {
                "title": "Glucose Agent",
                "type": "llm",
                "desc": "Analyze glucose/metabolic concerns",
                "model": {"provider": MODEL_PROVIDER, "name": MODEL_NAME, "mode": "chat"},
                "variables": [
                    {"variable": "query", "value_selector": ["sys", "query"]},
                    {"variable": "stage", "value_selector": [assessor_id, "text"]},
                    {"variable": "cgm_data", "value_selector": ["sys", "query"]}
                ],
                "prompt_template": {"prompt": PROMPT_GLUCOSE_AGENT},
                "completion_params": {"temperature": 0.5}
            }
        },
        {
            "id": synthesizer_id,
            "position": {"x": 750, "y": 0},
            "data": {
                "title": "Response Synthesizer",
                "type": "llm",
                "desc": "Synthesize agent responses into final prescription",
                "model": {"provider": MODEL_PROVIDER, "name": MODEL_NAME, "mode": "chat"},
                "variables": [
                    {"variable": "stage", "value_selector": [assessor_id, "text"]},
                    {"variable": "sleep_analysis", "value_selector": [sleep_agent_id, "text"]},
                    {"variable": "glucose_analysis", "value_selector": [glucose_agent_id, "text"]},
                    {"variable": "query", "value_selector": ["sys", "query"]}
                ],
                "prompt_template": {"prompt": PROMPT_INTERVENTION_PRESCRIBER},
                "completion_params": {"temperature": 0.7}
            }
        },
        end_node
    ]

    edges_data = [
        {"id": f"e-{uuid.uuid4().hex[:6]}", "source": start_node['id'], "target": assessor_id},
        {"id": f"e-{uuid.uuid4().hex[:6]}", "source": assessor_id, "target": sleep_agent_id},
        {"id": f"e-{uuid.uuid4().hex[:6]}", "source": assessor_id, "target": glucose_agent_id},
        {"id": f"e-{uuid.uuid4().hex[:6]}", "source": sleep_agent_id, "target": synthesizer_id},
        {"id": f"e-{uuid.uuid4().hex[:6]}", "source": glucose_agent_id, "target": synthesizer_id},
        {"id": f"e-{uuid.uuid4().hex[:6]}", "source": synthesizer_id, "target": end_node['id']}
    ]

    new_graph = {"nodes": nodes_data, "edges": edges_data}

    if not creator.update_workflow(app_id, new_graph):
        return None

    creator.publish_workflow(
        app_id,
        "Multi-Agent workflow: Assessor → Sleep/Glucose Agents → Synthesizer"
    )

    return app_id


# ============================================================================
# Workflow Definitions Export (for external use)
# ============================================================================

def get_workflow_definitions() -> Dict[str, Any]:
    """导出工作流定义，供其他模块使用"""
    return {
        "prompts": {
            "ttm_assessor": PROMPT_TTM_ASSESSOR,
            "intervention_prescriber": PROMPT_INTERVENTION_PRESCRIBER,
            "sleep_agent": PROMPT_SLEEP_AGENT,
            "glucose_agent": PROMPT_GLUCOSE_AGENT
        },
        "model_config": {
            "provider": MODEL_PROVIDER,
            "name": MODEL_NAME
        },
        "workflows": {
            "ttm_assessment": {
                "name": "TTM Assessment Workflow",
                "nodes": ["Stage Assessor", "Intervention Prescriber"],
                "description": "Two-node workflow for behavior stage assessment and prescription"
            },
            "multi_agent": {
                "name": "Multi-Agent Workflow",
                "nodes": ["Stage Assessor", "Sleep Agent", "Glucose Agent", "Response Synthesizer"],
                "description": "Four-node workflow with parallel agent processing"
            }
        }
    }


def export_prompts_to_json(output_path: str = "data/dify_prompts.json") -> None:
    """导出 Prompts 到 JSON 文件"""
    prompts = {
        "ttm_assessor": PROMPT_TTM_ASSESSOR,
        "intervention_prescriber": PROMPT_INTERVENTION_PRESCRIBER,
        "sleep_agent": PROMPT_SLEEP_AGENT,
        "glucose_agent": PROMPT_GLUCOSE_AGENT
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)

    print(f"✅ Prompts exported to {output_path}")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """主函数 - 创建示例工作流"""
    print("=" * 60)
    print("Dify Workflow Creator - Behavioral Health System")
    print("=" * 60)

    # Check API key
    if DIFY_API_KEY == 'your_dify_api_key_here':
        print("\n⚠️  DIFY_API_KEY not set. Running in export-only mode.")
        print("   Set environment variable or edit the script to use API features.\n")

        # Export prompts for manual use
        export_prompts_to_json("data/dify_prompts.json")

        print("\n📋 Available workflows:")
        definitions = get_workflow_definitions()
        for wf_id, wf_info in definitions['workflows'].items():
            print(f"   - {wf_info['name']}: {wf_info['description']}")

        return

    # Create workflows
    creator = DifyWorkflowCreator()

    print("\n[1/2] Creating TTM Assessment Workflow...")
    ttm_app_id = create_ttm_assessment_workflow(creator)

    print("\n[2/2] Creating Multi-Agent Workflow...")
    multi_agent_app_id = create_multi_agent_workflow(creator)

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  - TTM Assessment App ID: {ttm_app_id or 'Failed'}")
    print(f"  - Multi-Agent App ID: {multi_agent_app_id or 'Failed'}")
    print("=" * 60)


if __name__ == '__main__':
    main()
