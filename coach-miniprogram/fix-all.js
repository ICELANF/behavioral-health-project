const fs = require("fs");
const path = require("path");

// === 1. 修复 project.miniapp.json 自动拷贝 ===
const miniapp = JSON.stringify({
  description: "miniapp",
  setting: { es6: true, enhance: true, minified: true, postcss: true, urlCheck: false, bigPackageSizeSupport: true },
  compileType: "miniprogram",
  appid: "wx5755ae9b2491a04b",
  projectname: "coach-miniprogram"
}, null, 2);
fs.writeFileSync("project.miniapp.json", miniapp);
fs.writeFileSync("src/project.miniapp.json", miniapp);
console.log("OK: project.miniapp.json x2");

// === 2. 修复 TabBar 图标 ===
const tabDir = "src/static/tabs";
fs.mkdirSync(tabDir, { recursive: true });
const png = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAFklEQVR42mP8z8BQz0hBYNQBow4YSg4AAKctH/GjpEYAAAAASUVORK5CYII=", "base64");
["home","home-active","notify","notify-active","profile","profile-active"].forEach(n => {
  fs.writeFileSync(path.join(tabDir, n + ".png"), png);
});
console.log("OK: 6 tab icons");

// === 3. 修复 login.vue (合并vue import + 去掉onLoad) ===
const loginFile = "src/pages/auth/login.vue";
let login = fs.readFileSync(loginFile, "utf8");
// 移除单独的 onMounted/onLoad import
login = login.replace(/import\s*\{\s*onLoad\s*\}\s*from\s*['"]@dcloudio\/uni-app['"]\s*;?\n?/g, "");
login = login.replace(/import\s*\{\s*onMounted\s*\}\s*from\s*['"]vue['"]\s*;?\n?/g, "");
// 把 onMounted 加到现有 vue import 里
login = login.replace(
  /import\s*\{\s*(ref\s*,\s*reactive)\s*\}\s*from\s*['"]vue['"]/,
  "import { $1, onMounted } from 'vue'"
);
// 确保所有 onLoad( 改成 onMounted(
login = login.replace(/\bonLoad\s*\(/g, "onMounted(");
fs.writeFileSync(loginFile, login);
console.log("OK: login.vue fixed");

// === 4. 批量修复所有页面 uni-app hook imports ===
const hooks = ["onLoad","onShow","onHide","onPullDownRefresh","onReachBottom","onShareAppMessage","onPageScroll"];
function fixVue(dir) {
  if (!fs.existsSync(dir)) return;
  fs.readdirSync(dir).forEach(f => {
    const full = path.join(dir, f);
    if (fs.statSync(full).isDirectory()) return fixVue(full);
    if (!f.endsWith(".vue")) return;
    if (full.includes("login.vue")) return; // already fixed above
    let c = fs.readFileSync(full, "utf8");
    const needed = hooks.filter(h => new RegExp("\\b" + h + "\\s*\\(").test(c));
    if (needed.length === 0) return;
    if (c.includes("@dcloudio/uni-app")) return;
    const imp = "import { " + needed.join(", ") + " } from '@dcloudio/uni-app'";
    c = c.replace(/<script setup[^>]*>/, m => m + "\n" + imp);
    fs.writeFileSync(full, c);
    console.log("FIXED:", path.relative("src/pages", full), "->", needed.join(","));
  });
}
fixVue("src/pages");

// === 5. 添加 postbuild 自动拷贝脚本 ===
const postBuild = `
const fs = require("fs");
const src = "project.miniapp.json";
const dst = "dist/dev/mp-weixin/project.miniapp.json";
if (fs.existsSync(src)) { fs.copyFileSync(src, dst); }
const tabSrc = "src/static/tabs";
const tabDst = "dist/dev/mp-weixin/static/tabs";
if (fs.existsSync(tabSrc)) {
  if (!fs.existsSync(tabDst)) fs.mkdirSync(tabDst, { recursive: true });
  fs.readdirSync(tabSrc).forEach(f => fs.copyFileSync(tabSrc + "/" + f, tabDst + "/" + f));
}
`.trim();
fs.writeFileSync("postbuild.js", postBuild);
console.log("OK: postbuild.js created");

console.log("\\nALL DONE. Run: npm run dev:mp-weixin && node postbuild.js");
