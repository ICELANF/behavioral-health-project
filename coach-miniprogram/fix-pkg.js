const fs = require("fs");
const pkg = {
  name: "coach-miniprogram",
  version: "1.0.0",
  description: "BehaviorOS Coach Miniprogram",
  scripts: {
    "dev:mp-weixin": "uni -p mp-weixin",
    "build:mp-weixin": "uni build -p mp-weixin",
    "dev:h5": "uni --platform h5",
    "build:h5": "uni build -p h5",
    "type-check": "vue-tsc --noEmit"
  },
  dependencies: {
    "@dcloudio/uni-app": "3.0.0-alpha-5000120260211001",
    "@dcloudio/uni-components": "3.0.0-alpha-5000120260211001",
    "@dcloudio/uni-mp-weixin": "3.0.0-alpha-5000120260211001",
    "@dcloudio/uni-ui": "^1.5.6",
    "pinia": "^2.2.6",
    "vue": "^3.4.21"
  },
  devDependencies: {
    "@dcloudio/types": "*",
    "@dcloudio/uni-cli-shared": "3.0.0-alpha-5000120260211001",
    "@dcloudio/vite-plugin-uni": "3.0.0-alpha-5000120260211001",
    "@types/node": "^20.0.0",
    "typescript": "^5.4.0",
    "vue-tsc": "^2.0.0"
  }
};
fs.writeFileSync("package.json", JSON.stringify(pkg, null, 2) + "\n");
console.log("OK - package.json rebuilt");
console.log("Scripts:", JSON.stringify(pkg.scripts));
