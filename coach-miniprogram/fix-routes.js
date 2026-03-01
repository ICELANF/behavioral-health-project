const fs = require("fs");
let pj = JSON.parse(fs.readFileSync("src/pages.json", "utf8"));

// 找到coach子包
const coach = pj.subPackages.find(s => s.root === "pages/coach");
if (coach) {
  // 重建pages数组，修复路径
  coach.pages = [
    { path: "dashboard/index", style: { navigationBarTitleText: "教练工作台", enablePullDownRefresh: true } },
    { path: "students/index", style: { navigationBarTitleText: "我的学员", enablePullDownRefresh: true } },
    { path: "students/detail", style: { navigationBarTitleText: "学员详情" } },
    { path: "push-queue/index", style: { navigationBarTitleText: "推送审批" } },
    { path: "assessment/index", style: { navigationBarTitleText: "评估管理" } },
    { path: "assessment/review", style: { navigationBarTitleText: "审核评估" } },
    { path: "analytics/index", style: { navigationBarTitleText: "数据分析" } },
    { path: "live/index", style: { navigationBarTitleText: "直播管理" } },
    { path: "flywheel/index", style: { navigationBarTitleText: "AI飞轮" } },
    { path: "messages/index", style: { navigationBarTitleText: "消息" } },
    { path: "risk/index", style: { navigationBarTitleText: "风险管理" } }
  ];
  console.log("Coach routes: " + coach.pages.length + " pages");
}

// 修复condition中的dashboard路径
if (pj.condition && pj.condition.list) {
  pj.condition.list.forEach(c => {
    if (c.path === "pages/coach/dashboard") {
      c.path = "pages/coach/dashboard/index";
    }
  });
}

fs.writeFileSync("src/pages.json", JSON.stringify(pj, null, 2) + "\n");
console.log("OK - src/pages.json updated");
