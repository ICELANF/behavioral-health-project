/**
 * six_端_desktop.js
 * 六端桌面展示 - 同时打开 6 个前端页面，保持在桌面可见
 */

const { chromium } = require('playwright');

const frontends = [
  { name: 'H5 行为教练',       url: 'http://localhost:5173' },
  { name: 'Admin 管理后台',    url: 'http://localhost:5174' },
  { name: 'H5 患者端',         url: 'http://localhost:5175' },
  { name: 'UI 组件库',         url: 'http://localhost:5176' },
  { name: 'Django 管理平台',   url: 'http://localhost:8888' },
  { name: '静态演示页',        url: 'http://localhost:9000' },
];

(async () => {
  console.log('');
  console.log('='.repeat(50));
  console.log('  六端桌面展示');
  console.log('  ' + new Date().toLocaleString('zh-CN'));
  console.log('='.repeat(50));
  console.log('');

  const browser = await chromium.launch({ headless: false });

  for (const fe of frontends) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, locale: 'zh-CN' });
    const page = await ctx.newPage();

    try {
      const resp = await page.goto(fe.url, { waitUntil: 'domcontentloaded', timeout: 8000 });
      const status = resp ? resp.status() : 0;
      const title = await page.title();
      console.log(`  [OK] ${fe.name.padEnd(18)} ${fe.url.padEnd(30)} HTTP ${status}  |  ${title}`);
    } catch (err) {
      console.log(`  [XX] ${fe.name.padEnd(18)} ${fe.url.padEnd(30)} ${err.message.split('\n')[0]}`);
    }
  }

  console.log('');
  console.log('  6 个页面已在桌面打开，按 Ctrl+C 关闭。');
  console.log('');

  // 保持浏览器打开
  await new Promise(() => {});
})();
