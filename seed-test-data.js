#!/usr/bin/env node
// seed-test-data.js — 行健平台模拟数据种子脚本
// 用途: 为小程序全流程测试插入必要的演示数据
// 执行: node seed-test-data.js

const { Client } = require('pg');

const client = new Client({
  host: 'localhost',
  port: 5432,
  database: 'bhp_db',
  user: 'bhp_user',
  password: 'bhp_password',
});

function log(msg) { console.log('[seed]', msg); }
function ok(msg)  { console.log('  ✅', msg); }
function skip(msg){ console.log('  ⏭ ', msg, '(already exists, skipping)'); }

async function seed() {
  await client.connect();
  log('Connected to PostgreSQL');

  // Set search_path to include coach_schema
  await client.query("SET search_path = public, coach_schema");
  log('search_path set to: public, coach_schema');

  // ─────────────────────────────────────────────────
  // 1. 更新学员名称 & 头像
  // ─────────────────────────────────────────────────
  log('1. Updating student profiles...');
  await client.query(
    `UPDATE users SET full_name='李梅', avatar_url='https://picsum.photos/seed/lm/100/100'
     WHERE id=4`
  );
  await client.query(
    `UPDATE users SET full_name='王浩', avatar_url='https://picsum.photos/seed/wh/100/100'
     WHERE id=64`
  );
  await client.query(
    `UPDATE users SET full_name='张健康', avatar_url='https://picsum.photos/seed/zjk/100/100'
     WHERE id=71`
  );
  await client.query(
    `UPDATE users SET full_name='陈慧敏', avatar_url='https://picsum.photos/seed/chm/100/100'
     WHERE id=145`
  );
  ok('Student profiles updated: 李梅(4), 王浩(64), 张健康(71), 陈慧敏(145)');

  // ─────────────────────────────────────────────────
  // 2. assessment_assignments → 设2条为 submitted
  // ─────────────────────────────────────────────────
  log('2. Setting assessment_assignments to submitted...');
  const aaRes = await client.query(
    `SELECT id FROM assessment_assignments WHERE status='completed' LIMIT 1`
  );
  if (aaRes.rows.length > 0) {
    skip('assessment_assignments already have submitted entries');
  } else {
    await client.query(
      `UPDATE assessment_assignments
       SET status='completed',
           completed_at=NOW()-INTERVAL '2 hours',
           pipeline_result='{"ttm_stage":"S2","spi_score":42,"risk_level":"moderate","summary":"需关注饮食干预，建议增加蔬菜比例"}'::json
       WHERE id=1`
    );
    await client.query(
      `UPDATE assessment_assignments
       SET status='completed',
           completed_at=NOW()-INTERVAL '3 hours',
           pipeline_result='{"ttm_stage":"S3","spi_score":68,"risk_level":"high","summary":"存在高风险饮食行为，建议加强行为干预"}'::json
       WHERE id=2`
    );
    ok('Set assignment IDs 1,2 to submitted with pipeline_result');
  }

  // ─────────────────────────────────────────────────
  // 3. coach_push_queue — 插入4条带标题的推送项
  // ─────────────────────────────────────────────────
  log('3. Inserting coach_push_queue items...');
  const pushCheck = await client.query(
    `SELECT COUNT(*) FROM coach_push_queue
     WHERE coach_id=3 AND status='pending'
     AND title NOT LIKE '%Test%' AND title !~ '^[^\\x00-\\x7F\\u4E00-\\u9FFF]'`
  );
  // Clean up the garbled item from previous test
  await client.query(
    `DELETE FROM coach_push_queue WHERE id=8 AND title NOT LIKE '%推送%'`
  );
  const pushCount = await client.query(
    `SELECT COUNT(*) FROM coach_push_queue WHERE coach_id=3 AND status='pending'`
  );
  if (parseInt(pushCount.rows[0].count) >= 3) {
    skip('coach_push_queue already has pending items');
  } else {
    await client.query(
      `INSERT INTO coach_push_queue
         (coach_id, student_id, source_type, title, content, priority, status, created_at)
       VALUES
         (3, 4,   'ai_recommendation', '行为处方推送 - 李梅',
          '建议本周尝试3次10分钟晨走，从低强度开始建立运动习惯',
          'high', 'pending', NOW()-INTERVAL '1 hour'),
         (3, 64,  'content',           '学习内容推送 - 王浩',
          '代谢综合征认知改变课程已准备好，预计8分钟完成阅读',
          'normal', 'pending', NOW()-INTERVAL '2 hours'),
         (3, 71,  'system',            '评估提醒推送 - 张健康',
          '请完成本周行为评估，仅需10分钟，了解当前改变阶段',
          'high', 'pending', NOW()-INTERVAL '30 minutes'),
         (3, 145, 'ai_recommendation', '督导确认推送 - 陈慧敏',
          '昨日打卡记录已收到，本周坚持良好，继续保持',
          'normal', 'pending', NOW()-INTERVAL '3 hours')`
    );
    ok('Inserted 4 push queue items for students 4,64,71,145');
  }

  // ─────────────────────────────────────────────────
  // 4. notifications — 为 coach(user_id=3) 插入5条
  // ─────────────────────────────────────────────────
  log('4. Inserting notifications for coach...');
  const notifCheck = await client.query(
    `SELECT COUNT(*) FROM notifications WHERE user_id=3`
  );
  if (parseInt(notifCheck.rows[0].count) >= 3) {
    skip('notifications already has data for coach');
  } else {
    await client.query(
      `INSERT INTO notifications (user_id, title, body, type, priority, is_read, created_at)
       VALUES
         (3, '学员评估已提交',
          '张健康提交了行为评估，请查看并审核评估结果',
          'review', 'high', false, NOW()-INTERVAL '1 hour'),
         (3, '新评估待分配',
          '本周建议对李梅安排SPI量表评估，当前心理准备度评分需更新',
          'assessment', 'normal', false, NOW()-INTERVAL '2 hours'),
         (3, '平台公告',
          '行健平台3月功能更新：新增AI飞轮分析模块，支持学员行为趋势预测',
          'system', 'normal', true, NOW()-INTERVAL '1 day'),
         (3, '课程学习提醒',
          '教练培养体系第3章《动机访谈技术》已解锁，建议本周完成学习',
          'learning', 'normal', false, NOW()-INTERVAL '3 hours'),
         (3, '处方审批通过',
          '陈慧敏的行为处方已通过督导审核，将于明日推送至学员端',
          'review', 'normal', true, NOW()-INTERVAL '2 days')`
    );
    ok('Inserted 5 notifications for coach user_id=3');
  }

  // ─────────────────────────────────────────────────
  // 5. exam_definitions + question_bank
  // ─────────────────────────────────────────────────
  log('5. Inserting exam definitions...');
  const examCheck = await client.query(
    `SELECT id FROM exam_definitions WHERE exam_id='coach_basic_v1'`
  );
  if (examCheck.rows.length > 0) {
    skip(`exam_definitions coach_basic_v1 (id=${examCheck.rows[0].id})`);
  } else {
    // Insert 3 questions first
    await client.query(
      `INSERT INTO question_bank
         (question_id, content, question_type, options, answer, domain, difficulty, created_by)
       VALUES
         ('qb_coach_001',
          'TTM跨理论模型中，"准备期"的特征是？',
          'single',
          '["A. 从未考虑改变", "B. 考虑改变但未行动", "C. 已计划在1个月内开始行动", "D. 已持续改变6个月以上"]'::json,
          '"C"'::json, 'behavior_change', 'easy', 3),
         ('qb_coach_002',
          'SPI（改变阶段指标）评分低于30分意味着？',
          'single',
          '["A. 心理准备度高，可以开始行动", "B. 心理准备度低，处于无意图期", "C. 行为已完全固化", "D. 需要立即进行危机干预"]'::json,
          '"B"'::json, 'assessment', 'easy', 3),
         ('qb_coach_003',
          '动机访谈（MI）的核心精神不包括以下哪项？',
          'single',
          '["A. 接纳", "B. 同理心", "C. 强制性建议", "D. 唤起"]'::json,
          '"C"'::json, 'coaching', 'medium', 3)
       ON CONFLICT (question_id) DO NOTHING`
    );

    const qRes = await client.query(
      `SELECT id FROM question_bank
       WHERE question_id IN ('qb_coach_001','qb_coach_002','qb_coach_003')
       ORDER BY id`
    );
    const qIds = qRes.rows.map(r => r.id);

    const examRes = await client.query(
      `INSERT INTO exam_definitions
         (exam_id, exam_name, description, level, exam_type, passing_score,
          duration_minutes, max_attempts, question_ids, status, created_by, created_at)
       VALUES
         ('coach_basic_v1', '教练认证基础考试',
          '教练培养体系初级认证考试，共3题示例，60分通过，考查TTM、SPI、MI等核心理论',
          'L1', 'certification', 60, 30, 3,
          $1::json, 'active', 3, NOW())
       RETURNING id`,
      [JSON.stringify(qIds)]
    );
    ok(`Inserted exam coach_basic_v1 (id=${examRes.rows[0].id}) with ${qIds.length} questions`);
  }

  // ─────────────────────────────────────────────────
  // 6. coach_review_queue — 插入2条 pending 供审核
  // ─────────────────────────────────────────────────
  log('6. Inserting coach_review_queue pending items...');
  const reviewCheck = await client.query(
    `SELECT COUNT(*) FROM coach_review_queue WHERE status='pending'`
  );
  if (parseInt(reviewCheck.rows[0].count) >= 2) {
    skip('coach_review_queue already has pending items');
  } else {
    const ts = Date.now();
    await client.query(
      `INSERT INTO coach_review_queue
         (id, coach_id, student_id, type, priority, status, ai_summary, ai_draft,
          push_type, push_content, created_at)
       VALUES
         ($1, 3, 4, 'rx_push', 'high', 'pending',
          'AI分析：李梅本周饮食记录显示精制碳水摄入偏高，建议行为处方干预',
          '建议本周减少精制碳水摄入，将主食替换为全谷物，增加蔬菜比例至50%',
          'message',
          '建议本周减少精制碳水摄入，将主食替换为全谷物，增加蔬菜比例至50%',
          NOW()-INTERVAL '1 hour'),
         ($2, 3, 71, 'assessment', 'normal', 'pending',
          'AI分析：张健康7日行为追踪显示运动频率良好，但睡眠质量待改善',
          '建议继续保持运动习惯，同时关注就寝时间，目标晚10点前入睡',
          'message',
          '建议继续保持运动习惯，同时关注就寝时间，目标晚10点前入睡',
          NOW()-INTERVAL '2 hours')`,
      [`seed-${ts}-rx`, `seed-${ts}-asm`]
    );
    ok('Inserted 2 pending coach_review_queue items');
  }

  // ─────────────────────────────────────────────────
  // 7. 确认 content_items 有 published 内容
  // ─────────────────────────────────────────────────
  log('7. Verifying published content...');
  const contentRes = await client.query(
    `SELECT COUNT(*) FROM content_items WHERE status='published'`
  );
  const cnt = parseInt(contentRes.rows[0].count);
  if (cnt >= 3) {
    ok(`${cnt} published content_items found — OK`);
  } else {
    log('  Inserting placeholder content items...');
    await client.query(
      `INSERT INTO content_items (content_type, title, body, cover_url, domain, level, status, created_at)
       VALUES
         ('article', '代谢综合征行为改变：TTM五阶段解析',
          '跨理论模型（TTM）将行为改变分为5个阶段：无意图期、意图期、准备期、行动期、维持期。了解学员所处阶段是制定干预策略的基础。',
          'https://picsum.photos/seed/c1/400/300',
          'behavior_change', 'beginner', 'published', NOW()),
         ('article', '情绪饮食的神经机制与干预策略',
          '情绪饮食是指在非饥饿状态下因情绪刺激而进食的行为，与前额叶-杏仁核回路的失调密切相关。行为干预应从情绪识别入手。',
          'https://picsum.photos/seed/c2/400/300',
          'nutrition', 'intermediate', 'published', NOW()),
         ('article', '教练辅导技巧：动机访谈入门',
          '动机访谈（MI）是一种以人为中心的咨询技术，核心技术包括：开放式问题、反映聆听、肯定认可、概括总结（OARS）。',
          'https://picsum.photos/seed/c3/400/300',
          'coaching', 'beginner', 'published', NOW())`
    );
    ok('Inserted 3 published content items');
  }

  // ─────────────────────────────────────────────────
  // 完成 — 打印摘要
  // ─────────────────────────────────────────────────
  console.log('\n──────────────────────────────────────');
  log('Seed complete! Summary:');
  const summary = await client.query(`
    SELECT
      (SELECT COUNT(*) FROM coach_push_queue WHERE coach_id=3 AND status='pending') AS push_pending,
      (SELECT COUNT(*) FROM notifications WHERE user_id=3) AS notif_count,
      (SELECT COUNT(*) FROM assessment_assignments WHERE status='completed') AS aa_submitted,
      (SELECT COUNT(*) FROM exam_definitions WHERE status='active') AS exam_active,
      (SELECT COUNT(*) FROM question_bank) AS question_count,
      (SELECT COUNT(*) FROM coach_review_queue WHERE status='pending') AS review_pending,
      (SELECT COUNT(*) FROM content_items WHERE status='published') AS content_published
  `);
  const s = summary.rows[0];
  console.log(`  coach_push_queue pending : ${s.push_pending}`);
  console.log(`  notifications (coach)    : ${s.notif_count}`);
  console.log(`  assessment_assignments   : ${s.aa_submitted} submitted`);
  console.log(`  exam_definitions active  : ${s.exam_active}`);
  console.log(`  question_bank total      : ${s.question_count}`);
  console.log(`  coach_review_queue pend  : ${s.review_pending}`);
  console.log(`  content_items published  : ${s.content_published}`);
  console.log('──────────────────────────────────────\n');

  await client.end();
}

seed().catch(err => {
  console.error('❌ Seed error:', err.message);
  process.exit(1);
});
