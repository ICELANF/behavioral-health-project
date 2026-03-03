// update-pages.js — 无BOM UTF-8，安全更新 pages.json
const fs = require('fs')
const path = require('path')

const pagesPath = path.join(__dirname, 'coach-miniprogram/src/pages.json')
const data = JSON.parse(fs.readFileSync(pagesPath, 'utf8'))

// 新增子包定义
const newPackages = [
  {
    root: 'pages/health',
    name: 'health',
    pages: [
      { path: 'index',       style: { navigationBarTitleText: '健康数据' } },
      { path: 'blood-glucose', style: { navigationBarTitleText: '血糖记录' } },
      { path: 'weight',      style: { navigationBarTitleText: '体重体成分' } },
      { path: 'exercise',    style: { navigationBarTitleText: '运动记录' } },
      { path: 'device-bind', style: { navigationBarTitleText: '设备管理' } },
    ],
  },
  {
    root: 'pages/food',
    name: 'food',
    pages: [
      { path: 'scan',  style: { navigationBarTitleText: '饮食记录' } },
      { path: 'diary', style: { navigationBarTitleText: '饮食日记' } },
    ],
  },
  {
    root: 'pages/sharer',
    name: 'sharer',
    pages: [
      { path: 'dashboard',     style: { navigationBarTitleText: '分享者工作台' } },
      { path: 'mentees',       style: { navigationBarTitleText: '我的学员' } },
      { path: 'share-content', style: { navigationBarTitleText: '内容分享' } },
    ],
  },
  {
    root: 'pages/supervisor',
    name: 'supervisor',
    pages: [
      { path: 'dashboard',    style: { navigationBarTitleText: '督导工作台' } },
      { path: 'coaches',      style: { navigationBarTitleText: '教练管理' } },
      { path: 'review-queue', style: { navigationBarTitleText: '健康数据审核' } },
    ],
  },
  {
    root: 'pages/master',
    name: 'master',
    pages: [
      { path: 'dashboard',       style: { navigationBarTitleText: '专家工作台' } },
      { path: 'critical-review', style: { navigationBarTitleText: '危急病例' } },
      { path: 'knowledge',       style: { navigationBarTitleText: '知识库管理' } },
    ],
  },
]

// 给 coach 子包追加 health-review 页面
const coachPkg = data.subPackages.find(p => p.root === 'pages/coach')
if (coachPkg && !coachPkg.pages.find(p => p.path === 'health-review/index')) {
  coachPkg.pages.push({
    path: 'health-review/index',
    style: { navigationBarTitleText: '健康数据审核' },
  })
  console.log('✓ coach/health-review/index added')
}

// 追加新子包（防重复）
for (const pkg of newPackages) {
  if (!data.subPackages.find(p => p.root === pkg.root)) {
    data.subPackages.push(pkg)
    console.log('✓ subPackage added:', pkg.root)
  } else {
    console.log('  skip (exists):', pkg.root)
  }
}

fs.writeFileSync(pagesPath, JSON.stringify(data, null, 2), { encoding: 'utf8' })
console.log('\npages.json updated successfully')
