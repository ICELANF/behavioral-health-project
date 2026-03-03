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