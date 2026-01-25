/**
 * Test Certification - 教练认证体系测试脚本
 */

import { certificationService, LEVEL_REQUIREMENTS, PREDEFINED_COURSES, PREDEFINED_EXAMS } from '../src/certification/CertificationService';
import { promotionEngine } from '../src/certification/PromotionEngine';

async function runTests() {
  console.log('='.repeat(60));
  console.log('  教练认证体系测试 (Coach Certification System Test)');
  console.log('='.repeat(60));
  console.log();

  let passed = 0;
  let failed = 0;

  function test(name: string, condition: boolean) {
    if (condition) {
      console.log(`[PASS] ${name}`);
      passed++;
    } else {
      console.log(`[FAIL] ${name}`);
      failed++;
    }
  }

  // Test 1: Level Requirements
  console.log('\n--- 认证等级要求 ---');
  test('5个认证等级已定义', LEVEL_REQUIREMENTS.length === 5);
  console.log('   等级列表:');
  LEVEL_REQUIREMENTS.forEach(r => {
    console.log(`   - ${r.level}: ${r.name} (分成: ${r.revenue_share_ratio * 100}%)`);
  });

  // Test 2: Courses
  console.log('\n--- 课程库 ---');
  test('课程库已加载', PREDEFINED_COURSES.length > 10);
  console.log(`   - 共 ${PREDEFINED_COURSES.length} 门课程`);
  const coursesByLevel: Record<string, number> = {};
  PREDEFINED_COURSES.forEach(c => {
    coursesByLevel[c.level] = (coursesByLevel[c.level] || 0) + 1;
  });
  Object.entries(coursesByLevel).forEach(([level, count]) => {
    console.log(`   - ${level}: ${count} 门`);
  });

  // Test 3: Exams
  console.log('\n--- 考试库 ---');
  test('考试库已加载', PREDEFINED_EXAMS.length > 5);
  console.log(`   - 共 ${PREDEFINED_EXAMS.length} 项考试`);

  // Test 4: Create Coach Profile
  console.log('\n--- 教练档案管理 ---');
  const coach = certificationService.createCoachProfile('user-test-001', '测试教练');
  test('教练档案创建成功', coach.coach_id !== undefined);
  test('初始等级为L0', coach.level === 'L0');
  test('初始评分为C', coach.platform_rating === 'C');
  console.log(`   - 教练ID: ${coach.coach_id.substring(0, 8)}...`);
  console.log(`   - 姓名: ${coach.name}`);
  console.log(`   - 等级: ${coach.level}`);

  // Test 5: Complete Courses
  console.log('\n--- 课程完成 ---');
  const course1Success = certificationService.completeCourse(coach.coach_id, 'CRS-L0-K01', 85);
  test('完成课程CRS-L0-K01', course1Success);
  const course2Success = certificationService.completeCourse(coach.coach_id, 'CRS-L0-K02', 90);
  test('完成课程CRS-L0-K02', course2Success);
  console.log(`   - 已完成 ${coach.completed_courses.length} 门课程`);

  // Test 6: Pass Exam
  console.log('\n--- 考试通过 ---');
  const examSuccess = certificationService.passExam(coach.coach_id, 'EXM-L0-T01', 85);
  test('通过入门考试 (85分)', examSuccess);
  const examFail = certificationService.passExam(coach.coach_id, 'EXM-L0-T01', 70);
  test('低于及格线不通过 (70分)', !examFail);
  console.log(`   - 已通过 ${coach.passed_exams.length} 项考试`);

  // Test 7: Promotion Evaluation
  console.log('\n--- 晋级评估 ---');
  const evaluation = promotionEngine.evaluate(coach);
  test('晋级评估执行成功', evaluation !== null);
  test('目标等级为L1', evaluation.target_level === 'L1');
  console.log(`   - 当前等级: ${evaluation.current_level}`);
  console.log(`   - 目标等级: ${evaluation.target_level}`);
  console.log(`   - 是否符合晋级条件: ${evaluation.eligible}`);
  console.log(`   - 缺失条件: ${evaluation.missing_requirements.length} 项`);
  if (evaluation.missing_requirements.length > 0) {
    console.log('   - 具体缺失:');
    evaluation.missing_requirements.forEach(r => {
      console.log(`     · ${r}`);
    });
  }
  if (evaluation.recommended_modules.length > 0) {
    console.log(`   - 推荐补修模块: ${evaluation.recommended_modules.length} 个`);
  }

  // Test 8: K-M-S-V Competency Model
  console.log('\n--- 能力模型 (K-M-S-V) ---');
  test('能力模型已初始化', coach.competency !== undefined);
  console.log(`   - Knowledge: ${Object.values(coach.competency.knowledge).reduce((a, b) => a + b, 0)} 分`);
  console.log(`   - Method: ${Object.values(coach.competency.method).reduce((a, b) => a + b, 0)} 分`);
  console.log(`   - Skill: ${Object.values(coach.competency.skill).reduce((a, b) => a + b, 0)} 分`);
  console.log(`   - Value: ${Object.values(coach.competency.value).reduce((a, b) => a + b, 0)} 分`);

  // Test 9: Training Session
  console.log('\n--- 智能陪练 ---');
  const session = certificationService.createTrainingSession(
    coach.coach_id,
    'ai_simulation',
    {
      scenario_id: 'SCN-001',
      scenario_name: '首次评估对话',
      difficulty: 'beginner',
      client_profile: '30岁女性，餐后血糖偏高',
      presenting_issue: '想了解如何控制血糖',
      expected_approach: ['开放式提问', '建立信任', '收集信息']
    }
  );
  test('训练会话创建成功', session.session_id !== undefined);
  console.log(`   - 会话ID: ${session.session_id.substring(0, 8)}...`);
  console.log(`   - 类型: ${session.session_type}`);
  console.log(`   - 难度: ${session.scenario.difficulty}`);

  // Test 10: Get All Coaches
  console.log('\n--- 教练列表 ---');
  const allCoaches = certificationService.getAllCoaches();
  test('能获取教练列表', allCoaches.length >= 1);
  console.log(`   - 当前教练数: ${allCoaches.length}`);

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log(`  测试结果: ${passed} 通过, ${failed} 失败`);
  console.log('='.repeat(60));

  if (failed > 0) {
    process.exit(1);
  }
}

runTests().catch(error => {
  console.error('测试失败:', error);
  process.exit(1);
});
