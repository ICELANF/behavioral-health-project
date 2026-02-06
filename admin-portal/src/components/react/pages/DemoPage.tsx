import React, { useState } from 'react';
import { LogicFlowBridge } from '../Expert/LogicFlowBridge';
import { DecisionRules } from '../../../types/react-types';
import { Sparkles, Code, AlertTriangle } from 'lucide-react';

const DemoPage = () => {
  const [selectedScenario, setSelectedScenario] = useState<string>('cgm');

  const scenarios: Record<string, { title: string; rules: DecisionRules; description: string }> = {
    cgm: {
      title: '血糖波动监测',
      description: '检测到用户血糖剧烈波动，系统自动启动保护机制',
      rules: {
        trigger: 'CGM_HIGH_VOLATILITY',
        logic: 'IF val > 10.0 AND trend == "UP" THEN SET RISK = R3',
        octopus_clamp: 'LIMIT_TASKS = 1',
        narrative_override: 'CONVERT_TO_EMPATHY'
      }
    },
    activity: {
      title: '静坐行为预警',
      description: '用户长时间静坐，系统建议适当活动',
      rules: {
        trigger: 'LOW_ACTIVITY_DETECTED',
        logic: 'IF sedentary_time > 240 THEN SET RISK = R2',
        octopus_clamp: 'HIDE_COMPLEX_EXERCISES',
        narrative_override: 'USE_GENTLE_ENCOURAGEMENT'
      }
    },
    heartrate: {
      title: '心率异常监测',
      description: '检测到心率异常升高，需要立即干预',
      rules: {
        trigger: 'HEART_RATE_SPIKE',
        logic: 'IF hr > 140 AND duration > 10 THEN SET RISK = R4',
        octopus_clamp: 'EMERGENCY_MODE',
        narrative_override: 'CALM_REASSURANCE'
      }
    },
    depression: {
      title: '抑郁倾向评估',
      description: 'PHQ-9 评分显示中重度抑郁倾向',
      rules: {
        trigger: 'PHQ9_DEPRESSION_CHECK',
        logic: 'IF phq9 >= 15 AND cgm_volatility > 3.9 THEN SET RISK = R3',
        octopus_clamp: 'LIMIT_TASKS = 1',
        narrative_override: 'CONVERT_TO_EMPATHY'
      }
    }
  };

  const currentScenario = scenarios[selectedScenario];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100">
      <nav className="h-20 bg-gradient-to-r from-blue-600 via-blue-500 to-blue-600 flex items-center justify-between px-8 text-white shadow-2xl border-b-2 border-blue-400">
        <div className="flex items-center gap-6">
          <Sparkles className="w-8 h-8" />
          <div className="flex flex-col">
            <span className="font-bold tracking-tight text-2xl bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">
              LogicFlowBridge 演示中心
            </span>
            <span className="text-xs text-blue-200 tracking-wider">Decision Logic Interactive Demo</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs bg-white/20 px-3 py-1 rounded-full border border-white/30">
            v16.1.0
          </span>
        </div>
      </nav>

      <div className="max-w-[1600px] mx-auto p-8">
        <div className="mb-8 bg-gradient-to-r from-blue-50 to-slate-50 rounded-2xl border border-blue-200 p-6">
          <div className="flex items-start gap-4">
            <Code className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
            <div>
              <h2 className="text-xl font-bold text-slate-800 mb-2">
                欢迎来到 LogicFlowBridge 交互演示
              </h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                本页面展示了决策回溯联动组件的各种应用场景。选择不同的场景，体验代码与自然语言的实时联动效果。
                鼠标悬停在右侧的解释卡片上，左侧的代码将自动高亮对应行。
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-8">
          {Object.entries(scenarios).map(([key, scenario]) => (
            <button
              key={key}
              onClick={() => setSelectedScenario(key)}
              className={`p-4 rounded-xl border-2 transition-all text-left ${
                selectedScenario === key
                  ? 'border-blue-500 bg-blue-50 shadow-md'
                  : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
            >
              <h3 className={`text-sm font-bold mb-1 ${
                selectedScenario === key ? 'text-blue-700' : 'text-slate-700'
              }`}>
                {scenario.title}
              </h3>
              <p className="text-xs text-slate-500 line-clamp-2">
                {scenario.description}
              </p>
            </button>
          ))}
        </div>

        <div className="mb-6 bg-white rounded-lg border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            <div>
              <h3 className="text-sm font-bold text-slate-800">当前场景：{currentScenario.title}</h3>
              <p className="text-xs text-slate-600 mt-1">{currentScenario.description}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-lg">
          <LogicFlowBridge decisionRules={currentScenario.rules} />
        </div>

        <div className="mt-8 grid grid-cols-2 gap-6">
          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <h3 className="text-sm font-bold text-slate-800 mb-4 uppercase tracking-wide">
              技术特性
            </h3>
            <ul className="space-y-2 text-sm text-slate-600">
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-growth-500 rounded-full" />
                实时高亮联动（300ms 过渡）
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-growth-500 rounded-full" />
                呼吸灯指示器（1.5s 循环）
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-growth-500 rounded-full" />
                Framer Motion 流畅动画
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-growth-500 rounded-full" />
                VSCode 深色主题模拟
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-growth-500 rounded-full" />
                响应式左右分栏布局
              </li>
            </ul>
          </div>

          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <h3 className="text-sm font-bold text-slate-800 mb-4 uppercase tracking-wide">
              使用示例
            </h3>
            <pre className="text-xs bg-slate-900 text-slate-300 p-4 rounded-lg overflow-x-auto">
{`<LogicFlowBridge
  decisionRules={{
    trigger: "${currentScenario.rules.trigger}",
    logic: "${currentScenario.rules.logic}",
    octopus_clamp: "${currentScenario.rules.octopus_clamp}",
    narrative_override: "${currentScenario.rules.narrative_override}"
  }}
/>`}
            </pre>
          </div>
        </div>

        <div className="mt-6 bg-gradient-to-r from-slate-900 to-slate-800 rounded-lg p-6 text-white">
          <div className="grid grid-cols-3 gap-6 text-sm">
            <div>
              <p className="text-slate-400 mb-1">组件路径</p>
              <p className="font-mono text-xs">src/components/Expert/LogicFlowBridge.tsx</p>
            </div>
            <div>
              <p className="text-slate-400 mb-1">接口定义</p>
              <p className="font-mono text-xs">src/types.ts → DecisionRules</p>
            </div>
            <div>
              <p className="text-slate-400 mb-1">数据库表</p>
              <p className="font-mono text-xs">trace_sessions.decision_rules</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DemoPage;
