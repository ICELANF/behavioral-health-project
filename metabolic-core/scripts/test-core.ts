/**
 * Test Core - 核心功能测试脚本
 * 用于验证metabolic-core各模块功能
 */

import { orchestrator } from '../src/orchestrator/Orchestrator';
import { libraryManager } from '../src/registry/LibraryManager';
import { signalNormalizationService } from '../src/signal/SignalNormalizationService';
import { phenotypeMappingService } from '../src/libraries/PhenotypeMapping';
import { interventionPlaybookService } from '../src/libraries/InterventionPlaybook';
import { behaviorChangeEngineService } from '../src/libraries/BehaviorChangeEngine';

async function runTests() {
  console.log('='.repeat(60));
  console.log('  Metabolic Core - Test Suite');
  console.log('  行健行为教练 - 核心模块测试');
  console.log('='.repeat(60));
  console.log();

  let passed = 0;
  let failed = 0;

  // Helper function
  function test(name: string, fn: () => boolean | Promise<boolean>) {
    try {
      const result = fn();
      const success = result instanceof Promise ? false : result;
      if (success) {
        console.log(`[PASS] ${name}`);
        passed++;
      } else {
        console.log(`[FAIL] ${name}`);
        failed++;
      }
    } catch (error) {
      console.log(`[FAIL] ${name}: ${error}`);
      failed++;
    }
  }

  // Test 1: Initialize Orchestrator
  console.log('\n--- Orchestrator Tests ---');
  try {
    await orchestrator.initialize();
    console.log('[PASS] Orchestrator initialization');
    passed++;
  } catch (error) {
    console.log(`[FAIL] Orchestrator initialization: ${error}`);
    failed++;
  }

  // Test 2: Library Manager
  console.log('\n--- Library Manager Tests ---');
  test('Library Manager initialized', () => libraryManager.isInitialized());

  const status = libraryManager.getLibraryStatus();
  test('All libraries loaded', () => status.every(s => s.loaded));
  console.log(`   - Libraries: ${status.map(s => s.name.split(' ')[0]).join(', ')}`);

  // Test 3: Signal Normalization
  console.log('\n--- Signal Processing Tests ---');
  const signalResult = signalNormalizationService.normalize({
    user_id: 'test-user',
    device_type: 'cgm',
    metric: 'glucose',
    value: 7.5,
    timestamp: new Date().toISOString()
  });
  test('Signal normalization', () => signalResult.success && signalResult.record !== undefined);

  // Test 4: Phenotype Matching
  console.log('\n--- Phenotype Matching Tests ---');
  const phenotypes = phenotypeMappingService.getAllPhenotypes();
  test('Predefined phenotypes loaded', () => phenotypes.length >= 7);
  console.log(`   - Phenotypes: ${phenotypes.length} loaded`);

  const matches = phenotypeMappingService.matchPhenotypes({
    postprandial_peak: 12.5,
    variability_cv: 38
  });
  test('Phenotype matching works', () => Array.isArray(matches));

  // Test 5: Intervention Playbooks
  console.log('\n--- Intervention Tests ---');
  const playbooks = interventionPlaybookService.getAllPlaybooks();
  test('Playbooks loaded', () => playbooks.length >= 5);
  console.log(`   - Playbooks: ${playbooks.length} loaded`);

  const levers = interventionPlaybookService.getAllLevers();
  test('Intervention levers loaded', () => levers.length >= 10);
  console.log(`   - Levers: ${levers.length} loaded`);

  // Test 6: Behavior Change Engine
  console.log('\n--- Behavior Change Tests ---');
  const stageProfiles = behaviorChangeEngineService.getAllStageProfiles();
  test('Stage profiles loaded', () => stageProfiles.length === 5);

  const assessment = behaviorChangeEngineService.assessStage('test-user', {
    awareness_score: 60,
    motivation_score: 70,
    self_efficacy_score: 50,
    action_frequency: 3,
    days_maintained: 14
  });
  test('Stage assessment works', () => assessment.current_stage !== undefined);
  console.log(`   - Assessed stage: ${assessment.current_stage}`);

  // Test 7: Content Service
  console.log('\n--- Content Service Tests ---');
  const contentService = libraryManager.getContentService();
  const contents = contentService.getAllContents();
  test('Content materials loaded', () => contents.length >= 5);
  console.log(`   - Contents: ${contents.length} loaded`);

  const scripts = contentService.getAllScripts();
  test('Coaching scripts loaded', () => scripts.length >= 2);
  console.log(`   - Scripts: ${scripts.length} loaded`);

  // Test 8: Commercial Resources
  console.log('\n--- Commercial Resource Tests ---');
  const resourceService = libraryManager.getCommercialService();
  const resources = resourceService.getAllResources();
  test('Commercial resources loaded', () => resources.length >= 8);
  console.log(`   - Resources: ${resources.length} loaded`);

  // Test 9: Training Service
  console.log('\n--- Training Service Tests ---');
  const trainingService = libraryManager.getTrainingService();
  const modules = trainingService.getAllModules();
  test('Training modules loaded', () => modules.length >= 2);
  console.log(`   - Modules: ${modules.length} loaded`);

  const prompts = trainingService.getAllPromptTemplates();
  test('AI prompts loaded', () => prompts.length >= 2);
  console.log(`   - Prompts: ${prompts.length} loaded`);

  // Test 10: End-to-end Signal Processing
  console.log('\n--- End-to-End Tests ---');
  const e2eResult = orchestrator.processSignals('e2e-test-user', [
    {
      user_id: 'e2e-test-user',
      device_type: 'cgm',
      metric: 'glucose',
      value: 6.5,
      timestamp: '2024-01-15T07:00:00Z',
      context: { fasting: true }
    },
    {
      user_id: 'e2e-test-user',
      device_type: 'cgm',
      metric: 'glucose',
      value: 11.5,
      timestamp: '2024-01-15T09:00:00Z',
      context: { post_meal_minutes: 90 }
    },
    {
      user_id: 'e2e-test-user',
      device_type: 'watch',
      metric: 'steps',
      value: 3500,
      timestamp: '2024-01-15T23:00:00Z'
    }
  ]);
  test('E2E signal processing', () => e2eResult.success && e2eResult.trajectory !== undefined);
  if (e2eResult.phenotypes) {
    console.log(`   - Matched phenotypes: ${e2eResult.phenotypes.length}`);
  }

  // Test 11: Intervention Generation
  const intervention = orchestrator.generateIntervention('e2e-test-user', {
    awareness_score: 55,
    motivation_score: 60,
    self_efficacy_score: 45,
    action_frequency: 2,
    days_maintained: 7
  });
  test('Intervention generation', () => intervention !== null);
  if (intervention) {
    console.log(`   - Stage: ${intervention.stage_assessment.current_stage}`);
    console.log(`   - Recommendations: ${intervention.recommendations.length}`);
  }

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log(`  Test Results: ${passed} passed, ${failed} failed`);
  console.log('='.repeat(60));

  if (failed > 0) {
    process.exit(1);
  }
}

runTests().catch(error => {
  console.error('Test suite failed:', error);
  process.exit(1);
});
