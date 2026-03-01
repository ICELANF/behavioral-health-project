/**
 * Environment config - single source of truth for API base URL
 */

// In WeChat miniprogram, import.meta.env may not work.
// Use compile-time replacement or manual switch.
const isDev = process.env.NODE_ENV !== "production";

export const API_BASE = isDev
  ? "http://localhost:8000/api"
  : "https://api.xingjian.health/api";

export const API_V1 = API_BASE + "/v1";
