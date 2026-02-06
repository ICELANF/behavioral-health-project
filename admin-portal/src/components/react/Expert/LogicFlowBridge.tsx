import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Lightbulb, Code2, ArrowRight } from 'lucide-react';

interface LogicFlowBridgeProps {
  decisionRules?: {
    trigger: string;
    logic: string;
    octopus_clamp: string;
    narrative_override: string;
  };
}

export const LogicFlowBridge: React.FC<LogicFlowBridgeProps> = ({ decisionRules }) => {
  const [activeKey, setActiveKey] = useState<string | null>(null);

  const DEFAULT_JSON = {
    "trigger": "CGM_HIGH_VOLATILITY",
    "logic": "IF val > 10.0 AND trend == 'UP' THEN SET RISK = R3",
    "octopus_clamp": "LIMIT_TASKS = 1",
    "narrative_override": "CONVERT_TO_EMPATHY"
  };

  const RAW_JSON = decisionRules || DEFAULT_JSON;

  const interpretations = [
    {
      key: 'trigger',
      icon: <Lightbulb className="w-4 h-4" />,
      title: '感知层：识别异常',
      desc: '系统通过传感器发现用户的血糖正在剧烈波动。',
      color: 'text-blue-500',
      bg: 'bg-blue-50'
    },
    {
      key: 'logic',
      icon: <Code2 className="w-4 h-4" />,
      title: '判定层：风险分级',
      desc: '基于临床规则，判定当前处于中高风险(R3)状态。',
      color: 'text-amber-500',
      bg: 'bg-amber-50'
    },
    {
      key: 'octopus_clamp',
      icon: <ArrowRight className="w-4 h-4" />,
      title: '保护层：效能钳制',
      desc: 'Octopus 引擎介入，自动隐藏复杂任务，为用户减负。',
      color: 'text-purple-500',
      bg: 'bg-purple-50'
    },
    {
      key: 'narrative_override',
      icon: <ArrowRight className="w-4 h-4" />,
      title: '叙事层：语境转换',
      desc: '强制切换为"陪伴式"话术，用关怀替代医疗指令。',
      color: 'text-growth-500',
      bg: 'bg-growth-50'
    }
  ];

  return (
    <div className="flex flex-col lg:flex-row gap-6 p-6 bg-slate-50 rounded-3xl border border-slate-200 shadow-lg">

      <div className="flex-1 bg-[#1e1e1e] rounded-2xl p-6 font-mono text-sm relative overflow-hidden shadow-inner">
        <div className="flex items-center gap-2 mb-4 border-b border-white/10 pb-2">
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
            <div className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
          </div>
          <span className="text-white/40 text-xs ml-2">spi_mapping.json</span>
        </div>

        <div className="space-y-1">
          <code className="text-white/40 leading-relaxed">{`{`}</code>
          {Object.entries(RAW_JSON).map(([key, value]) => (
            <motion.div
              key={key}
              animate={{
                backgroundColor: activeKey === key ? 'rgba(74, 222, 128, 0.15)' : 'transparent',
                x: activeKey === key ? 4 : 0,
                borderLeft: activeKey === key ? '3px solid #4ade80' : '3px solid transparent'
              }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="py-1 px-2 rounded-md group transition-all"
            >
              <span className="text-blue-400">  "{key}"</span>
              <span className="text-white">: </span>
              <span className="text-amber-200">"{value}"</span>
              <span className="text-white">,</span>
              {activeKey === key && (
                <motion.span
                  layoutId="indicator"
                  initial={{ opacity: 0, scale: 0.5 }}
                  animate={{
                    opacity: 1,
                    scale: [1, 1.3, 1],
                    boxShadow: [
                      '0 0 8px #4ade80',
                      '0 0 16px #4ade80',
                      '0 0 8px #4ade80'
                    ]
                  }}
                  transition={{
                    scale: { duration: 1.5, repeat: Infinity, ease: "easeInOut" },
                    boxShadow: { duration: 1.5, repeat: Infinity, ease: "easeInOut" }
                  }}
                  className="ml-2 inline-block w-1.5 h-1.5 bg-growth-500 rounded-full"
                />
              )}
            </motion.div>
          ))}
          <code className="text-white/40 leading-relaxed">{`}`}</code>
        </div>
      </div>

      <div className="flex-1 space-y-3">
        {interpretations.map((item, index) => (
          <motion.div
            key={item.key}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1, duration: 0.4 }}
            onMouseEnter={() => setActiveKey(item.key)}
            onMouseLeave={() => setActiveKey(null)}
            className={`cursor-pointer transition-all duration-300 p-4 rounded-xl border-2 ${
              activeKey === item.key
                ? `border-growth-500 ${item.bg} shadow-md scale-[1.02]`
                : 'border-white bg-white hover:border-slate-200 shadow-sm'
            }`}
          >
            <div className="flex items-center gap-3 mb-1">
              <motion.div
                animate={{
                  scale: activeKey === item.key ? 1.1 : 1,
                  rotate: activeKey === item.key ? 5 : 0
                }}
                transition={{ duration: 0.2 }}
                className={`${activeKey === item.key ? item.color : 'text-slate-400'}`}
              >
                {item.icon}
              </motion.div>
              <h4 className={`text-sm font-bold transition-colors ${activeKey === item.key ? 'text-slate-900' : 'text-slate-600'}`}>
                {item.title}
              </h4>
            </div>
            <p className={`text-xs ml-7 leading-relaxed transition-colors ${activeKey === item.key ? 'text-slate-700' : 'text-slate-500'}`}>
              {item.desc}
            </p>
          </motion.div>
        ))}

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-4 p-3 bg-slate-900 rounded-lg flex items-center justify-between"
        >
          <div className="flex items-center gap-2">
            <motion.span
              animate={{ opacity: [1, 0.5, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="w-1.5 h-1.5 bg-growth-500 rounded-full"
            />
            <span className="text-[10px] text-slate-500 font-mono">STATUS: DECISION_TRACE_ACTIVE</span>
          </div>
          <button className="text-[10px] text-growth-500 font-bold hover:underline hover:text-growth-400 transition-colors">
            查看完整回溯链路 →
          </button>
        </motion.div>
      </div>
    </div>
  );
};
