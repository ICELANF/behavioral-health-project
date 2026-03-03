const fs = require("fs");
const f = "src/pages/auth/login.vue";
let c = fs.readFileSync(f, "utf8");
const lines = c.split("\n");

// ÏÔÊ¾ script ±êÇ©¸½½ü
lines.forEach((line, i) => {
  if (line.includes("script") || line.includes("import") || line.includes("onLoad")) {
    console.log((i+1) + ": " + line);
  }
});
