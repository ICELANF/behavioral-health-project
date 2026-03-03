const fs = require("fs");
const files = [
  "src/stores/user.ts",
  "src/api/auth.ts",
  "src/api/request.ts",
  "src/utils/wechat.ts",
  "src/config/env.ts"
];
files.forEach(f => {
  const exists = fs.existsSync(f);
  console.log(exists ? "OK" : "MISSING", f);
});
