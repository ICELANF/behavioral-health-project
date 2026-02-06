/**
 * mega_portal_demo.js
 * 行为健康数字平台 - 全平台门户自动化演示脚本
 *
 * 使用 Playwright 依次访问所有前端/后端/门户页面，
 * 截图保存到 scripts/sandbox/screenshots/，并输出验证报告。
 *
 * 用法: node scripts/sandbox/mega_portal_demo.js
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');
const TIMEOUT = 8000;

// ========== 全部测试目标 ==========
const targets = [
  // 前端应用
  { name: '5173_H5行为教练', url: 'http://localhost:5173', category: '前端应用' },
  { name: '5174_Admin管理后台', url: 'http://localhost:5174', category: '前端应用' },
  { name: '5174_公众科普入口', url: 'http://localhost:5174/portal/public', category: '前端应用' },
  { name: '5174_医护处方助手', url: 'http://localhost:5174/portal/medical', category: '前端应用' },
  { name: '5175_H5患者端', url: 'http://localhost:5175', category: '前端应用' },
  { name: '5176_UI组件库', url: 'http://localhost:5176', category: '前端应用' },
  { name: '8888_Django管理', url: 'http://localhost:8888', category: '前端应用' },
  { name: '9000_静态演示页', url: 'http://localhost:9000', category: '前端应用' },

  // 后端 API
  { name: '8000_AgentGateway', url: 'http://localhost:8000/docs', category: '后端API' },
  { name: '8001_BAPS评估API', url: 'http://localhost:8001/docs', category: '后端API' },
  { name: '8002_决策引擎API', url: 'http://localhost:8002/docs', category: '后端API' },

  // 基础设施
  { name: '8080_Dify编排平台', url: 'http://localhost:8080', category: '基础设施' },
  { name: '11434_Ollama_LLM', url: 'http://localhost:11434', category: '基础设施' },
];

// ========== 工具函数 ==========
function timestamp() {
  return new Date().toLocaleTimeString('zh-CN', { hour12: false });
}

function log(msg) {
  console.log(`[${timestamp()}] ${msg}`);
}

// ========== 主流程 ==========
(async () => {
  // 准备截图目录
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  console.log('');
  console.log('='.repeat(60));
  console.log('  行为健康数字平台 - 全平台门户自动化演示');
  console.log('  ' + new Date().toLocaleString('zh-CN'));
  console.log('='.repeat(60));
  console.log('');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    locale: 'zh-CN',
  });

  const results = [];

  for (const target of targets) {
    const page = await context.newPage();
    let status = 'PASS';
    let detail = '';
    let title = '';

    try {
      log(`[${target.category}] 访问 ${target.name} -> ${target.url}`);

      const response = await page.goto(target.url, {
        waitUntil: 'domcontentloaded',
        timeout: TIMEOUT,
      });

      const httpStatus = response ? response.status() : 0;

      // 等待页面渲染
      await page.waitForTimeout(1500);

      title = await page.title();

      // 截图
      const screenshotPath = path.join(SCREENSHOT_DIR, `${target.name}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: true });

      // 判定 HTTP 状态
      if (httpStatus >= 200 && httpStatus < 400) {
        status = 'PASS';
        detail = `HTTP ${httpStatus} | ${title}`;
      } else {
        status = 'WARN';
        detail = `HTTP ${httpStatus} | ${title}`;
      }

      log(`  -> ${status} ${detail}`);
      log(`  -> 截图: screenshots/${target.name}.png`);

    } catch (err) {
      status = 'FAIL';
      detail = err.message.split('\n')[0];
      log(`  -> FAIL ${detail}`);
    }

    results.push({
      name: target.name,
      url: target.url,
      category: target.category,
      status,
      detail,
      title,
    });

    await page.close();
  }

  // ========== 门户路由专项验证 ==========
  log('');
  log('--- 门户路由专项验证 ---');

  const portalPage = await context.newPage();

  // 验证公众端 meta
  try {
    await portalPage.goto('http://localhost:5174/portal/public', {
      waitUntil: 'domcontentloaded',
      timeout: TIMEOUT,
    });
    await portalPage.waitForTimeout(1000);

    const publicTitle = await portalPage.title();
    log(`公众科普入口 title: ${publicTitle}`);

    // 检查页面是否包含科普分类
    const categoryCount = await portalPage.locator('.category-item').count();
    log(`公众端科普分类数量: ${categoryCount}`);

    // 检查自测工具
    const toolCount = await portalPage.locator('.tool-card').count();
    log(`公众端自测工具数量: ${toolCount}`);

  } catch (err) {
    log(`公众端验证异常: ${err.message.split('\n')[0]}`);
  }

  // 验证医护端
  try {
    await portalPage.goto('http://localhost:5174/portal/medical', {
      waitUntil: 'domcontentloaded',
      timeout: TIMEOUT,
    });
    await portalPage.waitForTimeout(1000);

    // 检查处方模板
    const templateCount = await portalPage.locator('.template-item').count();
    log(`医护端处方模板数量: ${templateCount}`);

    // 检查待办
    const todoCount = await portalPage.locator('.todo-item').count();
    log(`医护端今日待办数量: ${todoCount}`);

  } catch (err) {
    log(`医护端验证异常: ${err.message.split('\n')[0]}`);
  }

  await portalPage.close();

  // ========== 输出报告 ==========
  console.log('');
  console.log('='.repeat(60));
  console.log('  验证报告');
  console.log('='.repeat(60));
  console.log('');

  const passed = results.filter(r => r.status === 'PASS').length;
  const warned = results.filter(r => r.status === 'WARN').length;
  const failed = results.filter(r => r.status === 'FAIL').length;

  // 按分类输出
  const categories = ['前端应用', '后端API', '基础设施'];
  for (const cat of categories) {
    console.log(`  [${cat}]`);
    results
      .filter(r => r.category === cat)
      .forEach(r => {
        const icon = r.status === 'PASS' ? 'OK' : r.status === 'WARN' ? '!!' : 'XX';
        console.log(`    [${icon}] ${r.name.padEnd(24)} ${r.detail}`);
      });
    console.log('');
  }

  console.log('-'.repeat(60));
  console.log(`  PASS: ${passed}  |  WARN: ${warned}  |  FAIL: ${failed}  |  TOTAL: ${results.length}`);
  console.log(`  截图目录: ${SCREENSHOT_DIR}`);
  console.log('-'.repeat(60));
  console.log('');

  // 写入 JSON 报告
  const reportPath = path.join(SCREENSHOT_DIR, 'report.json');
  fs.writeFileSync(reportPath, JSON.stringify({
    timestamp: new Date().toISOString(),
    summary: { passed, warned, failed, total: results.length },
    results,
  }, null, 2));
  log(`JSON 报告已写入: ${reportPath}`);

  await browser.close();
  log('浏览器已关闭，演示完成。');
})();
