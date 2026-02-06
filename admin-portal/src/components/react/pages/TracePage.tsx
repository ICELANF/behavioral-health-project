import React, { useState, useEffect } from 'react';
import { TraceGraph } from '../Trace/TraceGraph';
import { TraceDetail } from '../Trace/TraceDetail';
import { DecisionTrace } from '../Trace/DecisionTrace';
import { LogicFlowBridge } from '../Expert/LogicFlowBridge';
import { TraceNode, TraceLink, TraceSession } from '../../../types/react-types';
import { supabase } from '../../../lib/supabase';
import { GitBranch, RefreshCw, AlertCircle, LayoutGrid, Workflow } from 'lucide-react';

const mockRuleJson = `{
  "trigger": "PHQ9_DEPRESSION_CHECK",
  "conditions": [
    {
      "field": "phq9_score",
      "operator": ">=",
      "value": 15,
      "label": "中重度抑郁阈值"
    },
    {
      "field": "cgm_volatility",
      "operator": ">",
      "value": 3.9,
      "label": "血糖波动过大"
    }
  ],
  "logic": "IF phq9 >= 15 AND cgm_volatility > 3.9 THEN SET RISK = R3",
  "actions": [
    {
      "type": "ASSESSMENT",
      "value": "启动抗抑郁筛查"
    },
    {
      "type": "INTERVENTION",
      "value": "限制碳水摄入"
    }
  ],
  "octopus_clamp": "LIMIT_TASKS = 1",
  "narrative_override": "CONVERT_TO_EMPATHY",
  "ttm_stage": "S3_ACTION",
  "output_layer": {
    "L5": "专业医学语言",
    "L6": "共情叙事语言"
  }
}`;

const mockDecisionRules = {
  trigger: "CGM_HIGH_VOLATILITY",
  logic: "IF val > 10.0 AND trend == 'UP' THEN SET RISK = R3",
  octopus_clamp: "LIMIT_TASKS = 1",
  narrative_override: "CONVERT_TO_EMPATHY"
};

const mockTraceData: TraceSession = {
  id: 'session_001',
  caseId: 'tr_7721',
  patientId: 'PT-8821',
  nodes: [
    {
      id: 'input_phq9',
      type: 'INPUT',
      label: 'PHQ-9评分',
      value: '18分',
      timestamp: new Date().toISOString(),
    },
    {
      id: 'input_cgm',
      type: 'INPUT',
      label: 'CGM趋势',
      value: '波动剧烈',
      timestamp: new Date().toISOString(),
    },
    {
      id: 'rule_depression',
      type: 'RULE',
      label: '抑郁评估规则',
      value: 'PHQ-9 >= 15: 中重度抑郁',
      timestamp: new Date().toISOString(),
    },
    {
      id: 'rule_glucose',
      type: 'RULE',
      label: '血糖评估规则',
      value: 'CGM波动 > 3.9: 控制不佳',
      timestamp: new Date().toISOString(),
    },
    {
      id: 'decision_risk',
      type: 'DECISION',
      label: '风险等级判定',
      value: 'R3 - 需要立即干预',
      timestamp: new Date().toISOString(),
    },
    {
      id: 'decision_intervention',
      type: 'DECISION',
      label: '干预方案决策',
      value: '启动抗抑郁筛查 + 饮食调整',
      timestamp: new Date().toISOString(),
    },
    {
      id: 'output_l5',
      type: 'OUTPUT',
      label: 'L5专业输出',
      value: '检测到中重度抑郁倾向及餐后血糖控制不佳。建议立即启动抗抑郁筛查并限制碳水摄入。',
      timestamp: new Date().toISOString(),
    },
    {
      id: 'output_l6',
      type: 'OUTPUT',
      label: 'L6叙事输出',
      value: '最近似乎感到身体有些沉重？没关系，这是身体在提醒我们需要一点小小的调整。',
      timestamp: new Date().toISOString(),
    },
  ],
  links: [
    { source: 'input_phq9', target: 'rule_depression', weight: 1.0 },
    { source: 'input_cgm', target: 'rule_glucose', weight: 1.0 },
    { source: 'rule_depression', target: 'decision_risk', weight: 0.8 },
    { source: 'rule_glucose', target: 'decision_risk', weight: 0.6 },
    { source: 'decision_risk', target: 'decision_intervention', weight: 1.0 },
    { source: 'decision_intervention', target: 'output_l5', weight: 1.0 },
    { source: 'decision_intervention', target: 'output_l6', weight: 0.9 },
  ],
  createdAt: new Date(),
};

const TracePage: React.FC = () => {
  const [selectedNode, setSelectedNode] = useState<TraceNode | null>(null);
  const [traceData, setTraceData] = useState<TraceSession>(mockTraceData);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'graph' | 'flow'>('flow');

  const loadTraceData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const { data: sessions, error: sessionError } = await supabase
        .from('trace_sessions')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(1)
        .maybeSingle();

      if (sessionError) throw sessionError;

      if (sessions) {
        const { data: nodes, error: nodesError } = await supabase
          .from('trace_nodes')
          .select('*')
          .eq('session_id', sessions.id)
          .order('timestamp', { ascending: true });

        if (nodesError) throw nodesError;

        const { data: links, error: linksError } = await supabase
          .from('trace_links')
          .select('*')
          .eq('session_id', sessions.id);

        if (linksError) throw linksError;

        setTraceData({
          id: sessions.id,
          caseId: sessions.case_id,
          patientId: sessions.patient_id,
          nodes: nodes || [],
          links: links || [],
          decisionRules: sessions.decision_rules || undefined,
          createdAt: new Date(sessions.created_at),
        });
      }
    } catch (err) {
      console.error('加载回溯数据失败:', err);
      setError('加载回溯数据失败，显示模拟数据');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTraceData();
  }, []);

  const handleNodeClick = (nodeId: string) => {
    const node = traceData.nodes.find(n => n.id === nodeId);
    setSelectedNode(node || null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100">
      <nav className="h-20 bg-gradient-to-r from-slate-600 via-slate-500 to-slate-600 flex items-center justify-between px-8 text-white shadow-2xl border-b-2 border-slate-400">
        <div className="flex items-center gap-6">
          <GitBranch className="w-8 h-8" />
          <div className="flex flex-col">
            <span className="font-bold tracking-tight text-2xl bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
              决策回溯系统
            </span>
            <span className="text-xs text-slate-400 tracking-wider">Decision Trace System</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-white/10 rounded-lg p-1">
            <button
              onClick={() => setViewMode('flow')}
              className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${
                viewMode === 'flow'
                  ? 'bg-white/20 text-white'
                  : 'text-white/60 hover:text-white'
              }`}
            >
              <Workflow className="w-4 h-4" />
              流程视图
            </button>
            <button
              onClick={() => setViewMode('graph')}
              className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${
                viewMode === 'graph'
                  ? 'bg-white/20 text-white'
                  : 'text-white/60 hover:text-white'
              }`}
            >
              <LayoutGrid className="w-4 h-4" />
              图形视图
            </button>
          </div>
          <button
            onClick={loadTraceData}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            刷新数据
          </button>
        </div>
      </nav>

      <div className="max-w-[1600px] mx-auto p-8">
        {error && (
          <div className="mb-6 bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-center gap-3 text-amber-800">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        <div className="mb-6 bg-white rounded-lg border border-slate-200 p-4">
          <div className="grid grid-cols-3 gap-6 text-sm">
            <div>
              <span className="text-slate-500">会话ID:</span>
              <span className="ml-2 font-mono font-semibold">{traceData.id}</span>
            </div>
            <div>
              <span className="text-slate-500">案例ID:</span>
              <span className="ml-2 font-mono font-semibold">{traceData.caseId}</span>
            </div>
            <div>
              <span className="text-slate-500">患者ID:</span>
              <span className="ml-2 font-mono font-semibold">{traceData.patientId}</span>
            </div>
          </div>
        </div>

{viewMode === 'flow' ? (
          <div className="space-y-8">
            <div className="mb-6">
              <DecisionTrace nodes={traceData.nodes} ruleJson={mockRuleJson} />
            </div>

            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <h2 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                <GitBranch className="w-5 h-5" />
                决策逻辑解析 · 专家联动视图
              </h2>
              <LogicFlowBridge decisionRules={traceData.decisionRules || mockDecisionRules} />
            </div>

            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <h3 className="text-sm font-bold text-slate-700 mb-4 uppercase tracking-wide">审计日志简要信息</h3>
              <div className="grid grid-cols-4 gap-4 text-sm">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-slate-500 text-xs mb-1">触发时间</p>
                  <p className="font-mono text-slate-800">{new Date().toLocaleString('zh-CN')}</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-slate-500 text-xs mb-1">风险等级</p>
                  <p className="font-bold text-amber-600">R3 - 中高风险</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-slate-500 text-xs mb-1">处理状态</p>
                  <p className="font-medium text-growth-600">已完成改写</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-slate-500 text-xs mb-1">专家审核</p>
                  <p className="font-medium text-slate-600">待审核</p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-2 bg-white rounded-lg border border-slate-200 p-6">
              <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                <GitBranch className="w-5 h-5" />
                决策流程图
              </h2>
              <div
                onClick={(e) => {
                  const target = e.target as HTMLElement;
                  const canvas = target.closest('canvas');
                  if (canvas) {
                    handleNodeClick(traceData.nodes[0]?.id || '');
                  }
                }}
              >
                <TraceGraph nodes={traceData.nodes} links={traceData.links} />
              </div>
            </div>

            <div>
              <h2 className="text-lg font-bold text-slate-800 mb-4">节点详情</h2>
              <TraceDetail node={selectedNode} />

              <div className="mt-6 bg-white rounded-lg border border-slate-200 p-4">
                <h3 className="text-sm font-bold text-slate-700 mb-3">节点列表</h3>
                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                  {traceData.nodes.map((node) => (
                    <button
                      key={node.id}
                      onClick={() => setSelectedNode(node)}
                      className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                        selectedNode?.id === node.id
                          ? 'bg-slate-100 border border-slate-300'
                          : 'hover:bg-slate-50 border border-transparent'
                      }`}
                    >
                      <div className="font-semibold text-slate-800">{node.label}</div>
                      <div className="text-xs text-slate-500">{node.type}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TracePage;
