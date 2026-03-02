/**
 * fix-back.js — 批量把独立 van-nav-bar 页面的 $router.back() 替换为 useGoBack
 *
 * 处理两种情况：
 * 1. 模板里的 @click-left="$router.back()"
 * 2. script 里的 router.back() (非 PageShell 内的)
 */
const fs = require('fs')
const path = require('path')

// 需要处理的文件（独立 van-nav-bar，不走 PageShell）
const targets = [
  'src/views/AboutUs.vue',
  'src/views/ChallengeList.vue',
  'src/views/ChallengeDay.vue',
  'src/views/CoachDirectory.vue',
  'src/views/ContentDetail.vue',
  'src/views/Contribute.vue',
  'src/views/DataSync.vue',
  'src/views/ExpertRegister.vue',
  'src/views/HealthRecords.vue',
  'src/views/HistoryReports.vue',
  'src/views/MyCompanions.vue',
  'src/views/MyLearning.vue',
  'src/views/MyPlan.vue',
  'src/views/MyPrograms.vue',
  'src/views/MyStage.vue',
  'src/views/Notifications.vue',
  'src/views/PrivacyPolicy.vue',
  'src/views/ProgramProgress.vue',
  'src/views/ProgramTimeline.vue',
  'src/views/ProgramToday.vue',
  'src/views/PromotionProgress.vue',
  'src/views/RxPrescriptionDetail.vue',
  'src/views/WeeklyReport.vue',
  'src/views/journey/JourneyView.vue',
  'src/views/settings/NotificationSettings.vue',
  'src/views/v3/Assessment.vue',
  'src/views/v3/AssessmentBatch.vue',
  'src/views/v3/Coach.vue',
  'src/views/v3/Knowledge.vue',
  'src/views/v3/Register.vue',
  'src/views/vision/VisionDailyLog.vue',
  'src/views/vision/VisionExamRecord.vue',
  'src/views/vision/VisionGuardianView.vue',
  'src/views/vision/VisionProfile.vue',
]

const base = __dirname

let fixed = 0
let skipped = 0

for (const rel of targets) {
  const file = path.join(base, rel)
  if (!fs.existsSync(file)) { skipped++; console.log(`SKIP (not found): ${rel}`); continue }

  let src = fs.readFileSync(file, 'utf8')
  const original = src

  // ── Step 1: 模板里的 @click-left="$router.back()" → goBack()
  src = src.replace(/@click-left="\$router\.back\(\)"/g, '@click-left="goBack()"')

  // ── Step 2: 模板里的 @click-left="router.back()" → goBack()
  src = src.replace(/@click-left="router\.back\(\)"/g, '@click-left="goBack()"')

  // ── Step 3: script 里的 router.back() → goBack()（行内调用，不在 PageShell 里）
  // 替换 standalone `router.back()` 语句（行级）
  src = src.replace(/^\s*router\.back\(\)\s*$/gm, (m) => m.replace('router.back()', 'goBack()'))

  if (src === original) { skipped++; console.log(`NO CHANGE: ${rel}`); continue }

  // ── Step 4: 注入 useGoBack import + 在 setup 里解构 goBack
  // 判断 script setup 存在
  const hasScriptSetup = /<script\s[^>]*setup/.test(src)
  const hasScript = /<script/.test(src)

  if (!hasScriptSetup && !hasScript) {
    // 纯模板页（极少）→ 需要加 script setup
    src = src.replace(/<\/template>/, `</template>\n\n<script setup lang="ts">\nimport { useGoBack } from '@/composables/useGoBack'\nconst { goBack } = useGoBack()\n</script>`)
  } else {
    // 已有 script：注入 import（若未导入）
    if (!src.includes('useGoBack')) {
      // 在第一个 import 行后追加
      src = src.replace(/(import\s.+from\s+['"][^'"]+['"])/,
        `$1\nimport { useGoBack } from '@/composables/useGoBack'`)
      // 在 const router 或第一个 const/let/ref 前注入 destructure
      if (src.includes('const router = useRouter()')) {
        src = src.replace('const router = useRouter()',
          'const router = useRouter()\nconst { goBack } = useGoBack()')
      } else if (src.includes('const route = useRoute()')) {
        src = src.replace('const route = useRoute()',
          'const route = useRoute()\nconst { goBack } = useGoBack()')
      } else {
        // 在 script setup 开标签后插入
        src = src.replace(/(<script\b[^>]*>)/, `$1\nimport { useGoBack } from '@/composables/useGoBack'\nconst { goBack } = useGoBack()`)
        // 删掉重复的 import（因上面可能插了两次）
        const lines = src.split('\n')
        const seen = new Set()
        src = lines.filter(l => {
          if (l.includes('useGoBack')) {
            if (seen.has(l.trim())) return false
            seen.add(l.trim())
          }
          return true
        }).join('\n')
      }
    }
  }

  fs.writeFileSync(file, src, 'utf8')
  fixed++
  console.log(`FIXED: ${rel}`)
}

console.log(`\nDone: ${fixed} fixed, ${skipped} skipped`)
