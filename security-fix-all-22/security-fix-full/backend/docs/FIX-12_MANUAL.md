# FIX-12: rxApi Token Key 对齐 (CRITICAL)

## 问题
`modules/rx/api/rxApi.ts` 第51行使用 `localStorage.getItem('access_token')`
而全局 `api/http.ts` 使用 `const TOKEN_KEY = 'bos_access_token'`

## 最小修复 (已自动应用)
```diff
- const token = localStorage.getItem('access_token')
+ const token = localStorage.getItem('bos_access_token')
```

## 推荐修复 (手动)
将 rxApi 的独立 axios 实例替换为导入共享 http:
```typescript
// rxApi.ts 顶部
import { getToken } from '@/api/http'

// 拦截器中
http.interceptors.request.use((config) => {
  const token = getToken()  // 统一来源
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
```

## 验证
1. 登录后访问行为处方页面
2. 检查 Network → rx/strategies 请求的 Authorization header
3. 应显示 `Bearer <token>`, 不应为空
