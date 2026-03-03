// 移除 pages.json 中未实现的 sharer/dashboard 页面
const fs = require('fs'), path = require('path')
const p = path.join(__dirname, 'coach-miniprogram/src/pages.json')
const data = JSON.parse(fs.readFileSync(p, 'utf8'))

const sharer = data.subPackages.find(s => s.root === 'pages/sharer')
if (sharer) {
  sharer.pages = sharer.pages.filter(pg => pg.path !== 'dashboard')
  console.log('✓ sharer/dashboard removed from pages.json')
}

fs.writeFileSync(p, JSON.stringify(data, null, 2), { encoding: 'utf8' })
console.log('Done')
