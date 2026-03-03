// postbuild-miniapp.js — 编译后自动复制配置文件
const fs = require("fs");
const path = require("path");

const configs = ["project.miniapp.json", "project.config.json"];
const dists = [
  "dist/dev/mp-weixin",
  "dist/build/mp-weixin",
  "unpackage/dist/dev/mp-weixin",
  "unpackage/dist/build/mp-weixin",
];

for (const cfg of configs) {
  if (!fs.existsSync(cfg)) continue;
  for (const dist of dists) {
    if (!fs.existsSync(dist)) continue;
    const target = path.join(dist, cfg);
    fs.copyFileSync(cfg, target);
    console.log("COPY:", cfg, "->", target);
  }
}