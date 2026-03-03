const fs = require("fs");
const f = "src/pages/auth/login.vue";
let c = fs.readFileSync(f, "utf8");
if (c.includes("@dcloudio/uni-app")) {
  console.log("ALREADY HAS IMPORT");
} else if (c.includes("onLoad")) {
  c = c.replace(/<script setup[^>]*>/, m => m + "\nimport { onLoad } from '@dcloudio/uni-app'");
  fs.writeFileSync(f, c);
  console.log("FIXED");
} else {
  console.log("NO onLoad FOUND");
}
