/**
 * Batch transform miniprogram .vue files for H5 compatibility.
 * Run: node transform.js
 */
const fs = require('fs')
const path = require('path')

const viewsDir = path.join(__dirname, 'src/views')
let totalFiles = 0
let totalReplacements = 0

function walkDir(dir) {
  const files = fs.readdirSync(dir)
  for (const f of files) {
    const full = path.join(dir, f)
    if (fs.statSync(full).isDirectory()) {
      walkDir(full)
    } else if (f.endsWith('.vue')) {
      transformFile(full)
    }
  }
}

function transformFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf-8')
  const original = content
  let replacements = 0

  // 1. Replace `import { onLoad } from '@dcloudio/uni-app'` → from compat
  //    and `import { onShow } from '@dcloudio/uni-app'`
  content = content.replace(
    /import\s*\{([^}]*)\}\s*from\s*['"]@dcloudio\/uni-app['"]/g,
    (match, imports) => {
      replacements++
      return `import {${imports}} from '@/compat/uni'`
    }
  )

  // 2. Replace `import { API_BASE, API_HOST } from '@/config/env'` → remove (handled in request.ts)
  content = content.replace(
    /import\s*\{[^}]*\}\s*from\s*['"]@\/config\/env['"]\s*;?\n?/g,
    () => { replacements++; return '' }
  )

  // 3. Replace `uni.navigateTo({ url: '/pages/xxx' })` → `uni.navigateTo({ url: '/xxx' })`
  //    The uni compat layer already strips /pages, but fix literal URLs in code
  content = content.replace(
    /url:\s*['"]\/pages\//g,
    () => { replacements++; return "url: '/" }
  )

  // 4. Fix navigateTo with template literals: url: `/pages/xxx` → url: `/xxx`
  content = content.replace(
    /url:\s*`\/pages\//g,
    () => { replacements++; return 'url: `/' }
  )

  // 5. Replace `uni.switchTab({ url: '/pages/home/index' })` paths
  content = content.replace(
    /switchTab\(\{\s*url:\s*['"]\/pages\//g,
    () => { replacements++; return "switchTab({ url: '/" }
  )

  // 6. Replace reLaunch paths
  content = content.replace(
    /reLaunch\(\{\s*url:\s*['"]\/pages\//g,
    () => { replacements++; return "reLaunch({ url: '/" }
  )

  // 7. getCurrentPages() is shimmed globally, no change needed

  // 8. Remove `enablePullDownRefresh` related onPullDownRefresh if it's a no-op
  // (already handled by compat shim)

  // 9. Fix scroll-view attributes: refresher-enabled, refresher-triggered, @refresherrefresh
  // These are mini-program specific. Convert to standard scroll with pull-to-refresh handled differently.
  // For now, keep them — they'll be treated as custom attributes on a custom element.

  if (content !== original) {
    fs.writeFileSync(filePath, content, 'utf-8')
    totalReplacements += replacements
    totalFiles++
    const rel = path.relative(viewsDir, filePath)
    console.log(`  [${replacements}] ${rel}`)
  }
}

console.log('Transforming .vue files...\n')
walkDir(viewsDir)
console.log(`\nDone: ${totalFiles} files modified, ${totalReplacements} replacements total.`)

// Also transform api/*.ts files (remove @/config/env imports)
const apiDir = path.join(__dirname, 'src/api')
const apiFiles = fs.readdirSync(apiDir).filter(f => f.endsWith('.ts') && f !== 'request.ts')
let apiChanges = 0
for (const f of apiFiles) {
  const fp = path.join(apiDir, f)
  let c = fs.readFileSync(fp, 'utf-8')
  const orig = c

  // Replace `import { httpReq as http } from '@/api/request'` - keep as-is, it's compatible
  // Replace `import http from '@/api/request'` - keep as-is

  // Remove @/config/env imports
  c = c.replace(/import\s*\{[^}]*\}\s*from\s*['"]@\/config\/env['"]\s*;?\n?/g, '')

  // Replace BASE_URL references if they use API_BASE
  c = c.replace(/\bAPI_BASE\b/g, "''")
  c = c.replace(/\bAPI_HOST\b/g, "''")

  if (c !== orig) {
    fs.writeFileSync(fp, c, 'utf-8')
    apiChanges++
    console.log(`  API: ${f}`)
  }
}
if (apiChanges) console.log(`\n${apiChanges} API files updated.`)

// Transform stores
const storesDir = path.join(__dirname, 'src/stores')
if (fs.existsSync(storesDir)) {
  const storeFiles = fs.readdirSync(storesDir).filter(f => f.endsWith('.ts'))
  for (const f of storeFiles) {
    const fp = path.join(storesDir, f)
    let c = fs.readFileSync(fp, 'utf-8')
    const orig = c
    c = c.replace(/import\s*\{[^}]*\}\s*from\s*['"]@\/config\/env['"]\s*;?\n?/g, '')
    if (c !== orig) {
      fs.writeFileSync(fp, c, 'utf-8')
      console.log(`  Store: ${f}`)
    }
  }
}

// Transform utils
const utilsDir = path.join(__dirname, 'src/utils')
if (fs.existsSync(utilsDir)) {
  const utilFiles = fs.readdirSync(utilsDir).filter(f => f.endsWith('.ts'))
  for (const f of utilFiles) {
    const fp = path.join(utilsDir, f)
    let c = fs.readFileSync(fp, 'utf-8')
    const orig = c
    c = c.replace(/import\s*\{[^}]*\}\s*from\s*['"]@\/config\/env['"]\s*;?\n?/g, '')
    if (c !== orig) {
      fs.writeFileSync(fp, c, 'utf-8')
      console.log(`  Utils: ${f}`)
    }
  }
}
