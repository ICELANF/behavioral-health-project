/**
 * fix-and-setup-h5.js
 * 
 * 三合一修复脚本:
 * 1. 修复 pages.json 路由冲突（主包/分包重复）
 * 2. 配置 H5 模式（浏览器直接访问，无需微信审核）
 * 3. 生成热启动脚本（一键启动 + 自动刷新）
 *
 * 用法: node fix-and-setup-h5.js
 */

const fs = require('fs');
const path = require('path');

console.log('╔══════════════════════════════════════════════╗');
console.log('║  路由修复 + H5模式配置 + 热启动             ║');
console.log('╚══════════════════════════════════════════════╝\n');

// ============================================================
// 1. 修复 pages.json — 去除主包/分包路由冲突
// ============================================================
console.log('── 步骤1: 修复 pages.json 路由冲突 ──\n');

const pagesJsonPath = 'src/pages.json';
if (!fs.existsSync(pagesJsonPath)) {
  console.log('  ⚠️  未找到 src/pages.json，跳过路由修复');
} else {
  const pagesJson = JSON.parse(fs.readFileSync(pagesJsonPath, 'utf-8'));

  // 收集所有 subPackages 中的页面路径
  const subPagePaths = new Set();
  if (pagesJson.subPackages) {
    for (const pkg of pagesJson.subPackages) {
      const root = pkg.root || '';
      if (pkg.pages) {
        for (const p of pkg.pages) {
          const pagePath = p.path || p;
          // 完整路径 = root + pagePath
          const fullPath = root ? `${root}/${pagePath}` : pagePath;
          subPagePaths.add(fullPath);
          // 也添加 pages/ 前缀版本
          subPagePaths.add(`pages/${fullPath}`);
        }
      }
    }
  }

  // 从主包 pages 中移除已在 subPackages 中的页面
  const before = pagesJson.pages.length;
  const removed = [];
  pagesJson.pages = pagesJson.pages.filter(p => {
    const pagePath = typeof p === 'string' ? p : p.path;
    if (subPagePaths.has(pagePath)) {
      removed.push(pagePath);
      return false;
    }
    return true;
  });

  if (removed.length > 0) {
    console.log(`  ✅ 从主包移除 ${removed.length} 个冲突页面:`);
    removed.forEach(p => console.log(`     - ${p}`));
  } else {
    console.log('  ✅ 无路由冲突');
  }

  // 确保评估页面在正确的位置
  // 检查是否有 assessment 分包
  let assessmentInSub = false;
  if (pagesJson.subPackages) {
    for (const pkg of pagesJson.subPackages) {
      if (pkg.pages) {
        for (const p of pkg.pages) {
          const pp = p.path || p;
          if (pp.includes('assessment')) {
            assessmentInSub = true;
            break;
          }
        }
      }
    }
  }

  // 如果评估页面不在任何分包中，添加到主包
  if (!assessmentInSub) {
    const assessmentPages = [
      { path: 'pages/assessment/pending', style: { navigationBarTitleText: '我的评估', navigationStyle: 'custom' } },
      { path: 'pages/assessment/do', style: { navigationBarTitleText: '评估作答', navigationStyle: 'custom' } },
      { path: 'pages/assessment/result', style: { navigationBarTitleText: '评估结果', navigationStyle: 'custom' } },
    ];
    for (const ap of assessmentPages) {
      if (!pagesJson.pages.some(p => (p.path || p) === ap.path)) {
        pagesJson.pages.push(ap);
        console.log(`  ✅ 添加到主包: ${ap.path}`);
      }
    }
  } else {
    console.log('  ✅ 评估页面已在分包中，主包不再重复添加');
  }

  fs.writeFileSync(pagesJsonPath, JSON.stringify(pagesJson, null, 2));
  console.log(`  ✅ pages.json 已更新 (${before} → ${pagesJson.pages.length} 主包页面)\n`);
}

// ============================================================
// 2. 配置 H5 模式
// ============================================================
console.log('── 步骤2: 配置 H5 模式 ──\n');

// 2a. 更新 manifest.json 添加 H5 配置
const manifestPath = 'src/manifest.json';
if (fs.existsSync(manifestPath)) {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));

  manifest.h5 = {
    title: '行健平台 · 行为健康教练体系',
    router: {
      mode: 'hash',           // hash模式，部署最简单，不需要服务器配置
      base: '/'
    },
    devServer: {
      port: 5173,
      host: '0.0.0.0',        // 允许局域网访问（手机测试）
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true
        }
      }
    },
    optimization: {
      treeShaking: {
        enable: true
      }
    },
    sdkConfigs: {},
    ...manifest.h5             // 保留已有配置
  };

  // 确保 vueVersion 是 3
  manifest.vueVersion = '3';

  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  console.log('  ✅ manifest.json H5 配置已更新');
  console.log('     - 路由模式: hash');
  console.log('     - 开发端口: 5173');
  console.log('     - API代理: /api → localhost:8000');
} else {
  console.log('  ⚠️  未找到 manifest.json');
}

// 2b. 创建 H5 适配的请求封装
const h5RequestPatch = `
/**
 * H5 模式 API 请求适配
 * 
 * H5 模式下:
 * - 开发环境: 通过 devServer proxy 转发到 localhost:8000
 * - 生产环境: 需要配置 nginx 反向代理或修改 BASE_URL
 * 
 * 小程序模式下:
 * - 直接请求 localhost:8000（开发）或正式域名（生产）
 */

// 自动检测运行环境
export function getBaseUrl(): string {
  // #ifdef H5
  // H5 模式: 开发环境用代理，生产环境用完整URL
  if (import.meta.env.DEV) {
    return ''  // 通过 devServer proxy 转发
  }
  return import.meta.env.VITE_API_BASE || 'https://your-domain.com'
  // #endif

  // #ifdef MP-WEIXIN
  // 小程序模式
  return 'http://localhost:8000'
  // #endif

  // 默认
  return 'http://localhost:8000'
}
`.trim();

const utilsDir = 'src/utils';
if (!fs.existsSync(utilsDir)) fs.mkdirSync(utilsDir, { recursive: true });
fs.writeFileSync(path.join(utilsDir, 'env.ts'), h5RequestPatch);
console.log('  ✅ src/utils/env.ts 环境适配工具已创建\n');

// ============================================================
// 3. 生成启动脚本
// ============================================================
console.log('── 步骤3: 生成启动脚本 ──\n');

// 3a. dev.bat — Windows 一键启动（H5模式）
const devBat = `@echo off
chcp 65001 >nul
echo ╔══════════════════════════════════════╗
echo ║  行健平台 H5 开发模式启动           ║
echo ╚══════════════════════════════════════╝
echo.

:: 检查 node_modules
if not exist "node_modules" (
    echo [1/3] 安装依赖...
    call npm install
) else (
    echo [1/3] 依赖已就绪
)

:: 检查后端
echo [2/3] 检查后端服务...
curl -s -o nul http://localhost:8000/api/v1/health && (
    echo   ✅ 后端服务正常
) || (
    echo   ⚠️  后端未启动，请确保 Docker 容器正在运行
    echo      docker start bhp_v3_api
)

:: 启动 H5 开发服务器（热更新）
echo [3/3] 启动 H5 开发服务器...
echo.
echo ════════════════════════════════════════
echo   浏览器访问: http://localhost:5173
echo   手机访问:   http://你的IP:5173
echo   热更新已启用，修改代码自动刷新
echo ════════════════════════════════════════
echo.
call npx uni -p h5
`;
fs.writeFileSync('dev.bat', devBat);
console.log('  ✅ dev.bat — 双击启动H5开发（热更新）');

// 3b. dev-mp.bat — 小程序模式
const devMpBat = `@echo off
chcp 65001 >nul
echo ╔══════════════════════════════════════╗
echo ║  行健平台 小程序开发模式启动        ║
echo ╚══════════════════════════════════════╝
echo.
if not exist "node_modules" (
    echo 安装依赖...
    call npm install
)
echo 编译小程序...
call npx uni -p mp-weixin
echo.
echo 编译完成，请在微信开发者工具中打开:
echo   dist/dev/mp-weixin
echo.
pause
`;
fs.writeFileSync('dev-mp.bat', devMpBat);
console.log('  ✅ dev-mp.bat — 双击启动小程序编译');

// 3c. build.bat — 生产构建
const buildBat = `@echo off
chcp 65001 >nul
echo ╔══════════════════════════════════════╗
echo ║  行健平台 生产环境构建              ║
echo ╚══════════════════════════════════════╝
echo.

echo [1/2] 构建 H5 版本...
call npx uni build -p h5
echo   ✅ H5 构建完成 → dist/build/h5/

echo [2/2] 构建小程序版本...
call npx uni build -p mp-weixin
echo   ✅ 小程序构建完成 → dist/build/mp-weixin/

echo.
echo ════════════════════════════════════════
echo   H5 部署: 将 dist/build/h5/ 上传到任意Web服务器
echo   小程序部署: 微信开发者工具上传 dist/build/mp-weixin/
echo ════════════════════════════════════════
pause
`;
fs.writeFileSync('build.bat', buildBat);
console.log('  ✅ build.bat — 一键构建H5+小程序');

// 3d. start.ps1 — PowerShell 增强版
const startPs1 = `# start.ps1 — 行健平台开发启动脚本
param(
    [ValidateSet('h5', 'mp', 'build-h5', 'build-mp')]
    [string]$Mode = 'h5'
)

$Host.UI.RawUI.WindowTitle = "行健平台 - $Mode"

Write-Host ""
Write-Host "  行健平台开发服务器" -ForegroundColor Cyan
Write-Host "  模式: $Mode" -ForegroundColor Yellow
Write-Host ""

# 检查依赖
if (-not (Test-Path "node_modules")) {
    Write-Host "  安装依赖..." -ForegroundColor Yellow
    npm install
}

# 检查后端
try {
    $r = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "  ✅ 后端服务正常" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  后端未启动 (docker start bhp_v3_api)" -ForegroundColor Red
}

Write-Host ""

switch ($Mode) {
    'h5' {
        Write-Host "  🌐 H5 模式 — http://localhost:5173" -ForegroundColor Green
        Write-Host "  📱 手机测试 — http://$(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notmatch 'Loopback'} | Select-Object -First 1 -ExpandProperty IPAddress):5173" -ForegroundColor Green
        Write-Host "  🔥 热更新已启用" -ForegroundColor Yellow
        Write-Host ""
        npx uni -p h5
    }
    'mp' {
        Write-Host "  📦 小程序编译模式" -ForegroundColor Green
        npx uni -p mp-weixin
        # 编译后自动复制 project.miniapp.json
        if (Test-Path "project.miniapp.json") {
            Copy-Item "project.miniapp.json" "dist/dev/mp-weixin/" -Force
            Write-Host "  ✅ project.miniapp.json 已复制" -ForegroundColor Green
        }
    }
    'build-h5' {
        npx uni build -p h5
        Write-Host "  ✅ H5 构建完成 → dist/build/h5/" -ForegroundColor Green
    }
    'build-mp' {
        npx uni build -p mp-weixin
        Write-Host "  ✅ 小程序构建完成 → dist/build/mp-weixin/" -ForegroundColor Green
    }
}
`;
fs.writeFileSync('start.ps1', startPs1);
console.log('  ✅ start.ps1 — PowerShell启动脚本(支持4种模式)');

// 3e. 更新 package.json scripts
const pkgPath = 'package.json';
if (fs.existsSync(pkgPath)) {
  const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
  pkg.scripts = {
    ...pkg.scripts,
    'dev': 'uni -p h5',
    'dev:h5': 'uni -p h5',
    'dev:mp-weixin': 'uni -p mp-weixin',
    'build': 'uni build -p h5',
    'build:h5': 'uni build -p h5',
    'build:mp-weixin': 'uni build -p mp-weixin',
  };
  fs.writeFileSync(pkgPath, JSON.stringify(pkg, null, 2));
  console.log('  ✅ package.json scripts 已更新');
}

// ============================================================
// 4. 输出总结
// ============================================================
console.log('\n' + '═'.repeat(50));
console.log('\n✅ 全部配置完成！\n');

console.log('【立即使用 H5 模式（推荐）】');
console.log('  方式1: 双击 dev.bat');
console.log('  方式2: npm run dev:h5');
console.log('  方式3: .\\start.ps1 -Mode h5');
console.log('  → 浏览器打开 http://localhost:5173');
console.log('  → 修改代码自动热更新，无需手动刷新\n');

console.log('【仍需小程序模式】');
console.log('  方式1: 双击 dev-mp.bat');
console.log('  方式2: npm run dev:mp-weixin');
console.log('  方式3: .\\start.ps1 -Mode mp\n');

console.log('【生产部署】');
console.log('  双击 build.bat 同时构建 H5 + 小程序');
console.log('  H5: 将 dist/build/h5/ 放到任意Web服务器');
console.log('  小程序: 微信开发者工具上传 dist/build/mp-weixin/\n');

console.log('【H5 vs 小程序对比】');
console.log('  ┌──────────┬────────────────────┬────────────────────┐');
console.log('  │          │      H5 网页       │     微信小程序     │');
console.log('  ├──────────┼────────────────────┼────────────────────┤');
console.log('  │ 审核     │ 无需审核           │ 需微信审核         │');
console.log('  │ 热更新   │ ✅ 实时热刷新      │ ❌ 需手动编译      │');
console.log('  │ 调试     │ Chrome DevTools    │ 微信开发者工具     │');
console.log('  │ 部署     │ 任意Web服务器      │ 微信平台           │');
console.log('  │ 访问     │ 浏览器/手机浏览器  │ 微信内              │');
console.log('  │ 上线速度 │ 分钟级             │ 1-7天审核          │');
console.log('  └──────────┴────────────────────┴────────────────────┘');
console.log('═'.repeat(50));
