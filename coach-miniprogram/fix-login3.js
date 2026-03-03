const fs = require("fs");
const f = "src/pages/auth/login.vue";
let c = fs.readFileSync(f, "utf8");

// 把 onLoad 换成 onMounted
c = c.replace("import { onLoad } from '@dcloudio/uni-app'", "import { onMounted } from 'vue'");
c = c.replace(/onLoad\s*\(/g, "onMounted(");

fs.writeFileSync(f, c);
console.log("FIXED: onLoad -> onMounted");

// 同时确保 vue import 不重复
const lines = c.split("\n");
lines.forEach((line, i) => {
  if (line.includes("import") && (line.includes("vue") || line.includes("dcloudio"))) {
    console.log((i+1) + ": " + line);
  }
});
