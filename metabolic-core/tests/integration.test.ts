/**
 * Integration Tests - 集成测试
 */

import { orchestrator } from '../src/orchestrator/Orchestrator';
import { libraryManager } from '../src/registry/LibraryManager';
import { signalNormalizationService } from '../src/signal/SignalNormalizationService';
import { trajectoryService } from '../src/trajectory/TrajectoryService';
import { phenotypeMappingService } from '../src/libraries/PhenotypeMapping';

describe('Metabolic Core Integration Tests', () => {
  beforeAll(async () => {
    await orchestrator.initialize();
  });

  describe('Signal Processing', () => {
    it('should normalize raw signals', () => {
      const result = signalNormalizationService.normalize({
        user_id: 'test-user',
        device_type: 'cgm',
        metric: 'glucose',
        value: 7.5,
        timestamp: new Date().toISOString()
      });

      expect(result.success).toBe(true);
      expect(result.record).toBeDefined();
      expect(result.record?.value).toBe(7.5);
    });

    it('should reject invalid values', () => {
      const result = signalNormalizationService.normalize({
        user_id: 'test-user',
        device_type: 'cgm',
        metric: 'glucose',
        value: 'invalid',
        timestamp: new Date().toISOString()
      });

      expect(result.success).toBe(false);
    });
  });

  describe('Trajectory Building', () => {
    it('should build trajectory from signals', () => {
      const signals = [
        {
          signal_id: '1',
          user_id: 'test-user',
          device_type: 'cgm' as const,
          metric: 'glucose' as const,
          value: 6.5,
          unit: 'mmol/L',
          timestamp: new Date().toISOString(),
          context: { fasting: true },
          quality_flag: 'valid' as const
        },
        {
          signal_id: '2',
          user_id: 'test-user',
          device_type: 'cgm' as const,
          metric: 'glucose' as const,
          value: 10.5,
          unit: 'mmol/L',
          timestamp: new Date().toISOString(),
          context: { post_meal_minutes: 90 },
          quality_flag: 'valid' as const
        }
      ];

      const trajectory = trajectoryService.buildTrajectory('test-user', signals);

      expect(trajectory).toBeDefined();
      expect(trajectory.user_id).toBe('test-user');
      expect(trajectory.signals_summary).toBeDefined();
    });
  });

  describe('Phenotype Matching', () => {
    it('should match phenotypes based on signals summary', () => {
      const summary = {
        postprandial_peak: 12.5,
        variability_cv: 38,
        time_in_range: 55
      };

      const matches = phenotypeMappingService.matchPhenotypes(summary);

      expect(Array.isArray(matches)).toBe(true);
    });

    it('should return predefined phenotypes', () => {
      const phenotypes = phenotypeMappingService.getAllPhenotypes();

      expect(phenotypes.length).toBeGreaterThan(0);
      expect(phenotypes[0].mapping_id).toBeDefined();
    });
  });

  describe('Library Manager', () => {
    it('should be initialized', () => {
      expect(libraryManager.isInitialized()).toBe(true);
    });

    it('should return library status', () => {
      const status = libraryManager.getLibraryStatus();

      expect(Array.isArray(status)).toBe(true);
      expect(status.length).toBeGreaterThan(0);
    });

    it('should search knowledge', () => {
      const results = libraryManager.search({
        keyword: '血糖',
        limit: 5
      });

      expect(Array.isArray(results)).toBe(true);
    });
  });

  describe('Orchestrator', () => {
    it('should create user session', () => {
      const session = orchestrator.createSession('test-user-orch');

      expect(session).toBeDefined();
      expect(session.user_id).toBe('test-user-orch');
      expect(session.session_id).toBeDefined();
    });

    it('should process signals', () => {
      const result = orchestrator.processSignals('test-user-2', [
        {
          user_id: 'test-user-2',
          device_type: 'cgm',
          metric: 'glucose',
          value: 8.5,
          timestamp: new Date().toISOString()
        }
      ]);

      expect(result.success).toBe(true);
      expect(result.trajectory).toBeDefined();
    });

    it('should get dashboard', () => {
      const dashboard = orchestrator.getDashboard('test-user-2');

      expect(dashboard).toBeDefined();
    });

    it('should get conversation context', () => {
      const context = orchestrator.getConversationContext('test-user-2');

      expect(context).toBeDefined();
      expect(context.stage).toBeDefined();
      expect(context.suggestedTopics).toBeDefined();
    });
  });
});
