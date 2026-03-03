const fs = require("fs");
const path = require("path");
const hooks = ["onLoad","onShow","onHide","onPullDownRefresh","onReachBottom","onShareAppMessage","onPageScroll"];

function fixDir(dir) {
  if (!fs.existsSync(dir)) return;
  fs.readdirSync(dir).forEach(f => {
    const full = path.join(dir, f);
    if (fs.statSync(full).isDirectory()) return fixDir(full);
    if (!f.endsWith(".vue")) return;
    let c = fs.readFileSync(full, "utf8");
    const used = hooks.filter(h => {
      const re = new RegExp("\\b" + h + "\\s*\\(");
      return re.test(c);
    });
    if (used.length === 0) return;
    if (c.includes("@dcloudio/uni-app")) return;
    const imp = "import { " + used.join(", ") + " } from '@dcloudio/uni-app'";
    c = c.replace(/<script setup[^>]*>/, m => m + "\n" + imp);
    fs.writeFileSync(full, c);
    console.log("FIXED:", full, "->", used.join(", "));
  });
}
fixDir("src/pages");
console.log("DONE");
