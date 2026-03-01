const fs = require("fs");
const path = require("path");

// 创建 src/config 目录
const configDir = path.join("src", "config");
if (!fs.existsSync(configDir)) fs.mkdirSync(configDir, { recursive: true });

// 写 env.ts
fs.writeFileSync(path.join(configDir, "env.ts"), `/**
 * Environment config - single source of truth for API base URL
 */

// In WeChat miniprogram, import.meta.env may not work.
// Use compile-time replacement or manual switch.
const isDev = process.env.NODE_ENV !== "production";

export const API_BASE = isDev
  ? "http://localhost:8000/api"
  : "https://api.xingjian.health/api";

export const API_V1 = API_BASE + "/v1";
`);
console.log("OK: src/config/env.ts created");

// 更新 request.ts: 替换硬编码为 import
let req = fs.readFileSync("src/api/request.ts", "utf8");
if (req.includes("const BASE_URL = 'http://localhost:8000/api'")) {
  req = req.replace(
    "const BASE_URL = 'http://localhost:8000/api'",
    "import { API_BASE } from '@/config/env'\n\nconst BASE_URL = API_BASE"
  );
  fs.writeFileSync("src/api/request.ts", req);
  console.log("OK: request.ts updated to use config/env.ts");
} else {
  console.log("SKIP: request.ts BASE_URL already modified");
}
