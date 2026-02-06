import { useState, useCallback } from 'react';

export interface SPIMapping {
  phq9: {
    weight: number;
    threshold: {
      low: number;
      medium: number;
      high: number;
    };
  };
  cgmVariability: {
    weight: number;
    threshold: {
      low: number;
      medium: number;
      high: number;
    };
  };
  behaviorConsistency: {
    weight: number;
    threshold: {
      low: number;
      medium: number;
      high: number;
    };
  };
}

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

export const useBrain = () => {
  const [spiMapping, setSpiMapping] = useState<SPIMapping>(defaultSPIMapping);

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

  return {
    spiMapping,
    updateWeight,
    updateThreshold,
    resetToDefault,
    calculateRiskScore,
  };
};
