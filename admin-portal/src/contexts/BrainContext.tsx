import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { SPIMapping } from '../hooks/useBrain';
import { TraceNode } from '../types';

const defaultSPIMapping: SPIMapping = {
  phq9: {
    weight: 0.4,
    threshold: { low: 5, medium: 10, high: 15 },
  },
  cgmVariability: {
    weight: 0.35,
    threshold: { low: 20, medium: 33, high: 45 },
  },
  behaviorConsistency: {
    weight: 0.25,
    threshold: { low: 0.3, medium: 0.5, high: 0.7 },
  },
};

interface BrainContextType {
  spiMapping: SPIMapping;
  updateWeight: (metric: keyof SPIMapping, newWeight: number) => void;
  updateThreshold: (metric: keyof SPIMapping, level: 'low' | 'medium' | 'high', value: number) => void;
  resetToDefault: () => void;
  calculateRiskScore: (metrics: { phq9: number; cgmCV: number; consistency: number }) => {
    score: number;
    level: string;
  };
  decisionTraces: TraceNode[];
  addDecisionTrace: (trace: TraceNode) => void;
  clearDecisionTraces: () => void;
}

const BrainContext = createContext<BrainContextType | undefined>(undefined);

export const BrainProvider = ({ children }: { children: ReactNode }) => {
  const [spiMapping, setSpiMapping] = useState<SPIMapping>(defaultSPIMapping);
  const [decisionTraces, setDecisionTraces] = useState<TraceNode[]>([]);

  const updateWeight = useCallback((metric: keyof SPIMapping, newWeight: number) => {
    setSpiMapping((prev) => ({
      ...prev,
      [metric]: {
        ...prev[metric],
        weight: newWeight,
      },
    }));
  }, []);

  const updateThreshold = useCallback(
    (metric: keyof SPIMapping, level: 'low' | 'medium' | 'high', value: number) => {
      setSpiMapping((prev) => ({
        ...prev,
        [metric]: {
          ...prev[metric],
          threshold: {
            ...prev[metric].threshold,
            [level]: value,
          },
        },
      }));
    },
    []
  );

  const resetToDefault = useCallback(() => {
    setSpiMapping(defaultSPIMapping);
  }, []);

  const calculateRiskScore = useCallback(
    (metrics: { phq9: number; cgmCV: number; consistency: number }) => {
      const phq9Score = metrics.phq9 >= spiMapping.phq9.threshold.high ? 3
        : metrics.phq9 >= spiMapping.phq9.threshold.medium ? 2
        : metrics.phq9 >= spiMapping.phq9.threshold.low ? 1
        : 0;

      const cgmScore = metrics.cgmCV >= spiMapping.cgmVariability.threshold.high ? 3
        : metrics.cgmCV >= spiMapping.cgmVariability.threshold.medium ? 2
        : metrics.cgmCV >= spiMapping.cgmVariability.threshold.low ? 1
        : 0;

      const behaviorScore = metrics.consistency <= spiMapping.behaviorConsistency.threshold.low ? 3
        : metrics.consistency <= spiMapping.behaviorConsistency.threshold.medium ? 2
        : metrics.consistency <= spiMapping.behaviorConsistency.threshold.high ? 1
        : 0;

      const totalScore =
        phq9Score * spiMapping.phq9.weight +
        cgmScore * spiMapping.cgmVariability.weight +
        behaviorScore * spiMapping.behaviorConsistency.weight;

      return {
        score: totalScore,
        level: totalScore >= 2.4 ? 'R3' : totalScore >= 1.5 ? 'R2' : totalScore >= 0.6 ? 'R1' : 'R0',
      };
    },
    [spiMapping]
  );

  const addDecisionTrace = useCallback((trace: TraceNode) => {
    setDecisionTraces((prev) => [...prev, trace]);
  }, []);

  const clearDecisionTraces = useCallback(() => {
    setDecisionTraces([]);
  }, []);

  return (
    <BrainContext.Provider
      value={{
        spiMapping,
        updateWeight,
        updateThreshold,
        resetToDefault,
        calculateRiskScore,
        decisionTraces,
        addDecisionTrace,
        clearDecisionTraces,
      }}
    >
      {children}
    </BrainContext.Provider>
  );
};

export const useBrainContext = () => {
  const context = useContext(BrainContext);
  if (context === undefined) {
    throw new Error('useBrainContext must be used within a BrainProvider');
  }
  return context;
};
