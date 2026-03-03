/**
 * fix-miniapp-json.js
 * 修复: "非法的多端项目，未找到 project.miniapp.json"
 *
 * 原因: 微信开发者工具要求编译输出目录中必须有 project.miniapp.json
 * 解决: 在项目根目录 + dist输出目录 + src目录 同时放置该文件
 *
 * 用法: node fix-miniapp-json.js
 * 时机: 在 npm run dev:mp-weixin 之前或之后都可以运行
 */

const fs = require('fs');
const path = require('path');

// ═══════════════════════════════════════════
// 1. project.miniapp.json 内容
// ═══════════════════════════════════════════
const miniappConfig = {
  description: "行健平台教练端小程序",
  setting: {
    es6: true,
    enhance: true,
    minified: true,
    postcss: true,
    urlCheck: false,
    bigPackageSizeSupport: true,
    compileHotReLoad: true
  },
  compileType: "miniprogram",
  appid: "wx5755ae9b2491a04b",
  projectname: "coach-miniprogram",
  condition: {}
};

const content = JSON.stringify(miniappConfig, null, 2);

// ═══════════════════════════════════════════
// 2. 所有可能需要放置的路径
// ═══════════════════════════════════════════
const targets = [
  // 项目根目录
  'project.miniapp.json',
  // src 目录
  'src/project.miniapp.json',
  // dev 编译输出 (uni-app 默认)
  'dist/dev/mp-weixin/project.miniapp.json',
  // build 编译输出
  'dist/build/mp-weixin/project.miniapp.json',
  // 有些项目结构是 unpackage
  'unpackage/dist/dev/mp-weixin/project.miniapp.json',
  'unpackage/dist/build/mp-weixin/project.miniapp.json',
];

console.log('=== fix-miniapp-json.js ===\n');

let wrote = 0;
for (const target of targets) {
  const dir = path.dirname(target);
  // 只在目录存在或为根目录时写入
  if (dir === '.' || fs.existsSync(dir)) {
    if (!fs.existsSync(dir) && dir !== '.') {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(target, content);
    wrote++;
    console.log(`  ✅ ${target}`);
  } else {
    console.log(`  ⏭️  ${target} (目录不存在,跳过)`);
  }
}

// ═══════════════════════════════════════════
// 3. 同时检查 project.config.json
//    微信开发者工具也需要这个文件
// ═══════════════════════════════════════════
const projectConfig = {
  description: "项目配置文件。",
  packOptions: {
    ignore: [],
    include: []
  },
  setting: {
    urlCheck: false,
    es6: true,
    enhance: true,
    postcss: true,
    minified: true,
    newFeature: true,
    bigPackageSizeSupport: true,
    babelSetting: {
      ignore: [],
      disablePlugins: [],
      outputPath: ""
    }
  },
  compileType: "miniprogram",
  appid: "wx5755ae9b2491a04b",
  projectname: "coach-miniprogram",
  condition: {
    miniprogram: {
      list: []
    }
  }
};

const pcContent = JSON.stringify(projectConfig, null, 2);
const pcTargets = [
  'project.config.json',
  'src/project.config.json',
  'dist/dev/mp-weixin/project.config.json',
  'unpackage/dist/dev/mp-weixin/project.config.json',
];

console.log('\n--- project.config.json ---');
for (const target of pcTargets) {
  const dir = path.dirname(target);
  if (dir === '.' || fs.existsSync(dir)) {
    // 如果已存在，不覆盖（保留用户自定义配置）
    if (fs.existsSync(target)) {
      console.log(`  ⏩ ${target} (已存在,保留)`);
    } else {
      if (!fs.existsSync(dir) && dir !== '.') fs.mkdirSync(dir, { recursive: true });
      fs.writeFileSync(target, pcContent);
      wrote++;
      console.log(`  ✅ ${target}`);
    }
  }
}

// ═══════════════════════════════════════════
// 4. 自动探测实际编译输出目录
// ═══════════════════════════════════════════
console.log('\n--- 探测编译输出 ---');
const searchDirs = ['dist', 'unpackage/dist', 'build'];
for (const base of searchDirs) {
  if (!fs.existsSync(base)) continue;
  // 递归查找 app.json (小程序入口标志)
  function findAppJson(dir, depth) {
    if (depth > 4) return;
    try {
      const entries = fs.readdirSync(dir);
      for (const e of entries) {
        const full = path.join(dir, e);
        if (e === 'app.json' && fs.statSync(full).isFile()) {
          // 在同级放置 project.miniapp.json
          const target1 = path.join(dir, 'project.miniapp.json');
          const target2 = path.join(dir, 'project.config.json');
          if (!fs.existsSync(target1)) {
            fs.writeFileSync(target1, content);
            wrote++;
            console.log(`  ✅ ${target1} (自动发现)`);
          }
          if (!fs.existsSync(target2)) {
            fs.writeFileSync(target2, pcContent);
            wrote++;
            console.log(`  ✅ ${target2} (自动发现)`);
          }
        }
        if (fs.statSync(full).isDirectory() && !e.startsWith('.') && e !== 'node_modules') {
          findAppJson(full, depth + 1);
        }
      }
    } catch {}
  }
  findAppJson(base, 0);
}

console.log(`\n✅ 共写入 ${wrote} 个文件`);

// ═══════════════════════════════════════════
// 5. 注册 postbuild hook (可选)
// ═══════════════════════════════════════════
const postbuildScript = `
// postbuild-miniapp.js — 编译后自动复制配置文件
const fs = require("fs");
const path = require("path");

const configs = ["project.miniapp.json", "project.config.json"];
const dists = [
  "dist/dev/mp-weixin",
  "dist/build/mp-weixin",
  "unpackage/dist/dev/mp-weixin",
  "unpackage/dist/build/mp-weixin",
];

for (const cfg of configs) {
  if (!fs.existsSync(cfg)) continue;
  for (const dist of dists) {
    if (!fs.existsSync(dist)) continue;
    const target = path.join(dist, cfg);
    fs.copyFileSync(cfg, target);
    console.log("COPY:", cfg, "->", target);
  }
}
`.trim();

fs.writeFileSync('postbuild-miniapp.js', postbuildScript);
console.log('\n📄 已生成 postbuild-miniapp.js');
console.log('   可在 package.json scripts 中追加:');
console.log('   "dev:mp-weixin": "uni -p mp-weixin && node postbuild-miniapp.js"');
console.log('   或编译后手动运行: node postbuild-miniapp.js');

console.log('\n' + '='.repeat(50));
console.log('如果微信开发者工具仍报错，尝试:');
console.log('  1. 关闭工具，删除编译输出目录后重新编译');
console.log('  2. 微信开发者工具 → 项目 → 重新指定目录到 dist/dev/mp-weixin');
console.log('  3. 确认该目录下同时有 app.json + project.miniapp.json + project.config.json');
console.log('='.repeat(50));
