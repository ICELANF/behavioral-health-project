import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, AlertCircle } from 'lucide-react';
import { AuditCase } from '../../../types/react-types';
import { CGMChart } from './CGMChart';
import { sendBehaviorEvent } from '../../../lib/supabase';

export const DualSignPanel = ({ auditCase }: { auditCase: AuditCase }) => {
  const [signs, setSigns] = useState({ master: false, secondary: false });
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishStatus, setPublishStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handlePublish = async () => {
    if (!signs.master || !signs.secondary) return;

    setIsPublishing(true);
    setPublishStatus('idle');

    try {
      await sendBehaviorEvent({
        trace_id: auditCase.id,
        patient_id: auditCase.patientId,
        master_signer_id: 'expert_001',
        secondary_signer_id: 'expert_002',
        original_l5_output: auditCase.originalL5Output,
        approved_l6_output: auditCase.narrativeL6Preview,
        risk_level: auditCase.rawMetrics.riskLevel,
        approved_at: new Date().toISOString(),
      });

      setPublishStatus('success');
      setTimeout(() => setPublishStatus('idle'), 3000);
    } catch (error) {
      console.error('Failed to publish:', error);
      setPublishStatus('error');
      setTimeout(() => setPublishStatus('idle'), 3000);
    } finally {
      setIsPublishing(false);
    }
  };

  return (
    <div className="grid grid-cols-2 gap-0 h-[calc(100vh-120px)] shadow-2xl rounded-3xl overflow-hidden">
      <div className="flex flex-col bg-gradient-to-br from-slate-600 via-slate-500 to-slate-600 p-8 overflow-y-auto relative">
        <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-red-400/15 via-transparent to-transparent pointer-events-none"></div>

        <div className="flex justify-between items-center mb-8 relative z-10">
          <h2 className="text-white font-bold text-xl flex items-center gap-3">
            <span className="w-3 h-3 bg-red-500 rounded-full animate-pulse shadow-lg shadow-red-500/50" />
            底层行为证据
            <span className="text-slate-400 text-sm font-normal">Raw Truth</span>
          </h2>
          <motion.span
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="px-4 py-1.5 bg-red-600 text-white text-xs font-black rounded-lg shadow-lg shadow-red-500/30 tracking-wider"
          >
            RISK: {auditCase.rawMetrics.riskLevel}
          </motion.span>
        </div>

        <div className="space-y-5 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-slate-700/50 backdrop-blur-sm p-5 rounded-xl shadow-xl border border-red-400/40"
          >
            <p className="text-xs text-red-400 uppercase mb-3 tracking-wider font-bold">
              原始诊断建议 (L5 Output)
            </p>
            <p className="text-sm font-mono text-slate-200 leading-relaxed">
              {auditCase.originalL5Output}
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <CGMChart />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="grid grid-cols-2 gap-4"
          >
            <MetricCard label="PHQ-9 原始分" value={auditCase.rawMetrics.phq9} unit="分" />
            <MetricCard label="CGM 节律" value={auditCase.rawMetrics.cgmTrend} unit="" />
          </motion.div>
        </div>
      </div>

      <div className="flex flex-col bg-gradient-to-br from-growth-50 via-white to-growth-50 p-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-full h-full bg-[radial-gradient(circle_at_top_left,_var(--tw-gradient-stops))] from-growth-200/30 via-transparent to-transparent pointer-events-none"></div>
        <div className="absolute top-4 right-8">
           <span className="text-[120px] font-black text-growth-100 opacity-20 select-none">L6</span>
        </div>

        <div className="relative z-10">
          <motion.h2
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-growth-900 font-bold text-xl mb-3 flex items-center gap-3"
          >
            叙事改写预览
            <span className="text-growth-600 text-sm font-normal">Growth Journey</span>
          </motion.h2>
          <div className="h-1 w-20 bg-gradient-to-r from-growth-500 to-growth-300 rounded-full mb-8"></div>
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="flex-1 bg-gradient-to-br from-growth-100/50 to-white p-10 rounded-3xl border-2 border-growth-200/50 shadow-inner relative z-10"
        >
          <div className="text-2xl text-growth-900 leading-loose font-light">
            <span className="text-4xl text-growth-600 font-serif">"</span>
            <span className="italic">{auditCase.narrativeL6Preview}</span>
            <span className="text-4xl text-growth-600 font-serif">"</span>
          </div>
        </motion.div>

        <div className="mt-8 pt-8 border-t-2 border-growth-200 relative z-10">
          <p className="text-xs text-slate-500 mb-4 tracking-wide uppercase font-bold">双专家审核签名</p>
          <div className="flex gap-4 mb-6">
            <SignButton
              active={signs.master}
              label="主签专家 (专业性)"
              onClick={() => setSigns(s => ({...s, master: !s.master}))}
            />
            <SignButton
              active={signs.secondary}
              label="副签专家 (合规性)"
              onClick={() => setSigns(s => ({...s, secondary: !s.secondary}))}
            />
          </div>

          <motion.button
            disabled={!signs.master || !signs.secondary || isPublishing}
            onClick={handlePublish}
            whileHover={signs.master && signs.secondary ? { scale: 1.02 } : {}}
            whileTap={signs.master && signs.secondary ? { scale: 0.98 } : {}}
            animate={
              signs.master && signs.secondary && publishStatus === 'idle'
                ? {
                    boxShadow: [
                      '0 10px 40px rgba(34, 197, 94, 0.3)',
                      '0 10px 60px rgba(34, 197, 94, 0.5)',
                      '0 10px 40px rgba(34, 197, 94, 0.3)',
                    ],
                  }
                : {}
            }
            transition={
              signs.master && signs.secondary && publishStatus === 'idle'
                ? { duration: 2, repeat: Infinity }
                : {}
            }
            className={`w-full py-5 rounded-2xl font-bold transition-all relative flex items-center justify-center gap-2 text-lg ${
              signs.master && signs.secondary
              ? 'bg-gradient-to-r from-growth-600 to-growth-500 text-white shadow-2xl disabled:opacity-50'
              : 'bg-slate-200 text-slate-400 cursor-not-allowed'
            }`}
          >
            {isPublishing ? (
              <>
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                />
                发布中...
              </>
            ) : publishStatus === 'success' ? (
              <>
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 200 }}
                >
                  <CheckCircle className="w-6 h-6" />
                </motion.div>
                发布成功
              </>
            ) : publishStatus === 'error' ? (
              <>
                <AlertCircle className="w-5 h-5" />
                发布失败
              </>
            ) : (
              <>
                发布至用户终端
                {signs.master && signs.secondary && (
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="text-sm font-normal"
                  >
                    (Release to Octopus)
                  </motion.span>
                )}
              </>
            )}
          </motion.button>
        </div>
      </div>
    </div>
  );
};

const MetricCard = ({ label, value, unit }: { label: string; value: number | string; unit: string }) => (
  <div className="bg-slate-700/40 backdrop-blur-sm p-4 rounded-lg border border-slate-400/60 shadow-lg">
    <p className="text-[10px] text-slate-300 uppercase tracking-wider mb-1">{label}</p>
    <p className="text-xl font-bold text-white flex items-baseline gap-1">
      {value}
      <span className="text-xs font-normal text-slate-200">{unit}</span>
    </p>
  </div>
);

const SignButton = ({ active, label, onClick }: { active: boolean; label: string; onClick: () => void }) => (
  <motion.button
    onClick={onClick}
    whileHover={{ scale: 1.02 }}
    whileTap={{ scale: 0.98 }}
    animate={active ? { borderColor: '#22c55e' } : { borderColor: '#cbd5e1' }}
    className={`flex-1 p-4 rounded-xl border-2 transition-all flex items-center justify-center gap-3 ${
      active
        ? 'bg-gradient-to-br from-growth-50 to-growth-100 text-growth-800 shadow-lg shadow-growth-200/50'
        : 'bg-slate-50 text-slate-500 hover:bg-slate-100'
    }`}
  >
    <motion.div
      animate={active ? { scale: [1, 1.2, 1] } : { scale: 1 }}
      transition={active ? { duration: 0.3 } : {}}
      className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
        active ? 'bg-growth-500 border-growth-500' : 'border-slate-300'
      }`}
    >
      {active && (
        <motion.svg
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3 }}
          className="w-3 h-3 text-white"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
        >
          <motion.path d="M5 13l4 4L19 7" />
        </motion.svg>
      )}
    </motion.div>
    <span className="text-sm font-bold">{label}</span>
  </motion.button>
);
