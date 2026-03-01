const fs = require("fs");
let m = fs.readFileSync("api/main.py", "utf8");
if (m.includes("route_audit")) { console.log("SKIP: already injected"); process.exit(0); }
const inject = `
# === S1: Route Audit ===
try:
    from api.route_audit import router as audit_router, audit_startup
    app.include_router(audit_router)
    audit_startup(app)
    print("[API] S1 Route Audit: ACTIVE")
except ImportError as e:
    print(f"[API] S1 FAILED: {e}")

# === S2: Frontend Stubs ===
try:
    from api.frontend_stubs import router as stubs_router
    app.include_router(stubs_router)
    print("[API] S2 Frontend Stubs: ACTIVE")
except ImportError as e:
    print(f"[API] S2 FAILED: {e}")

# === S4: Agent Health ===
try:
    from api.agent_health import router as agent_health_router
    app.include_router(agent_health_router)
    print("[API] S4 Agent Health: ACTIVE")
except ImportError as e:
    print(f"[API] S4 FAILED: {e}")
`;
if (m.includes("if __name__")) {
  m = m.replace("if __name__", inject + "\nif __name__");
} else {
  m += inject;
}
fs.writeFileSync("api/main.py", m);
console.log("OK: 3 modules injected");
