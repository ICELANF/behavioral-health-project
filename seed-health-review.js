// seed-health-review.js — 创建 health_review_queue 表 + 种子数据
// 用法: node seed-health-review.js
const { Client } = require('pg')

const client = new Client({
  host: 'localhost', port: 5432,
  database: 'bhp_db', user: 'bhp_user', password: 'bhp_password',
})

async function run() {
  await client.connect()
  console.log('Connected to PostgreSQL')

  // 1. 创建 health_review_queue 表
  await client.query(`
    CREATE TABLE IF NOT EXISTS health_review_queue (
      id               SERIAL PRIMARY KEY,
      user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      reviewer_id      INTEGER REFERENCES users(id),
      data_type        VARCHAR(50) DEFAULT 'health_data',
      risk_level       VARCHAR(20) DEFAULT 'medium' CHECK (risk_level IN ('critical','high','medium','low')),
      reviewer_role    VARCHAR(20) DEFAULT 'coach'  CHECK (reviewer_role IN ('coach','supervisor','master')),
      status           VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','revised')),
      ai_summary       TEXT,
      ai_recommendation TEXT,
      reviewer_note    TEXT,
      final_content    TEXT,
      push_target_role VARCHAR(20) DEFAULT 'grower',
      created_at       TIMESTAMP DEFAULT NOW(),
      reviewed_at      TIMESTAMP
    )
  `)
  console.log('✓ health_review_queue 表已创建/确认')

  // 2. 创建索引
  await client.query(`
    CREATE INDEX IF NOT EXISTS idx_hrq_status ON health_review_queue(status);
    CREATE INDEX IF NOT EXISTS idx_hrq_reviewer_role ON health_review_queue(reviewer_role);
    CREATE INDEX IF NOT EXISTS idx_hrq_risk_level ON health_review_queue(risk_level);
    CREATE INDEX IF NOT EXISTS idx_hrq_user_id ON health_review_queue(user_id);
  `)
  console.log('✓ 索引已创建')

  // 3. 插入种子数据（学员4:李梅, 64:王浩, 71:张健康, 145:陈慧敏）
  const seeds = [
    {
      user_id: 71, risk_level: 'high', reviewer_role: 'supervisor',
      data_type: 'glucose',
      ai_summary: '张健康近7天血糖波动较大，餐后2h峰值达11.2 mmol/L，建议调整饮食结构',
      ai_recommendation: '减少精制碳水摄入，增加膳食纤维，考虑餐前血糖监测频率提升至每日2次',
    },
    {
      user_id: 4, risk_level: 'medium', reviewer_role: 'coach',
      data_type: 'activity',
      ai_summary: '李梅本周运动量不足，平均每日步数仅3200步，睡眠质量评分6.2/10',
      ai_recommendation: '建议增加晨间步行20分钟，设置21:00睡前提醒，减少屏幕时间',
    },
    {
      user_id: 145, risk_level: 'critical', reviewer_role: 'master',
      data_type: 'glucose',
      ai_summary: '陈慧敏今晨空腹血糖3.2 mmol/L（低血糖），心率数据异常（HR 112 bpm at rest）',
      ai_recommendation: '【危急】建议立即联系教练确认状态，考虑暂停当前运动处方，安排医院检测',
    },
    {
      user_id: 64, risk_level: 'medium', reviewer_role: 'coach',
      data_type: 'sleep',
      ai_summary: '王浩近两周睡眠分析：深睡时间平均仅45分钟，HRV偏低（RMSSD 18ms），提示压力状态',
      ai_recommendation: '推荐正念放松练习（5分钟/天），避免睡前1h使用手机，评估工作压力来源',
    },
  ]

  for (const s of seeds) {
    await client.query(`
      INSERT INTO health_review_queue
        (user_id, risk_level, reviewer_role, data_type, ai_summary, ai_recommendation, status, created_at)
      VALUES ($1,$2,$3,$4,$5,$6,'pending',NOW())
    `, [s.user_id, s.risk_level, s.reviewer_role, s.data_type, s.ai_summary, s.ai_recommendation])
  }
  console.log(`✓ 已插入 ${seeds.length} 条审核队列种子数据`)

  // 4. 验证
  const { rows } = await client.query(
    "SELECT id, risk_level, reviewer_role, status FROM health_review_queue ORDER BY id"
  )
  console.log('\n health_review_queue 当前数据:')
  rows.forEach(r => console.log(`  #${r.id} [${r.risk_level}] → ${r.reviewer_role} (${r.status})`))

  await client.end()
  console.log('\nDone!')
}

run().catch(e => { console.error(e); process.exit(1) })
