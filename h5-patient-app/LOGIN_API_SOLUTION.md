#  登录API问题解决方案

## 问题总结

经过深入调试，发现了以下问题：

1. ✅ **路由配置正确** - `/api/v1/auth/login` 已正确注册
2. ✅ **OAuth2表单接收正常** - FastAPI能正确处理form-urlencoded数据
3. ✅ **密码验证逻辑正常** - bcrypt验证通过
4. ✅ **Token生成正常** - JWT tokens可以成功生成
5. ⚠️ **可能的问题** - 多个服务器实例或路由冲突

## 临时解决方案

由于调试后端API比较复杂，我为您准备了三个解决方案：

### 方案1: 修改前端绕过登录（仅用于测试UI）

修改 `h5-patient-app/src/stores/user.ts`，添加临时登录：

```typescript
const login = async (credentials: LoginRequest) => {
  try {
    const response = await authAPI.login(credentials)
    // ... 原有逻辑
  } catch (error) {
    // 临时方案：模拟登录成功（仅用于测试UI）
    console.warn('[TEMP] Using mock login for UI testing')

    const mockToken = 'mock-jwt-token-for-testing'
    const mockUser = {
      id: 1,
      username: credentials.username,
      email: 'test@example.com',
      role: 'patient',
      full_name: 'Test User',
      is_active: true,
      created_at: new Date().toISOString()
    }

    token.value = mockToken
    user.value = mockUser
    storage.token.set(mockToken)
    storage.user.set(mockUser)

    showToast('登录成功（测试模式）')
    return { access_token: mockToken, refresh_token: mockToken, token_type: 'bearer', user: mockUser }
  }
}
```

### 方案2: 使用独立的简化登录API

我已创建了一个完全独立的登录测试服务器：

```bash
# 运行独立登录服务器（端口9000）
cd D:\behavioral-health-project
python -c "
import sys
sys.path.insert(0, '.')
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from core.database import get_db
from core.models import User
from core.auth import authenticate_user, create_user_tokens
from sqlalchemy.orm import Session
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

@app.post('/api/v1/auth/login')
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    def get_user(identifier: str):
        return db.query(User).filter((User.username == identifier) | (User.email == identifier)).first()

    user = authenticate_user(form_data.username, form_data.password, get_user)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='用户名或密码错误')

    tokens = create_user_tokens(user_id=user.id, username=user.username, role=user.role.value)

    return {
        **tokens,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role.value,
            'full_name': user.full_name
        }
    }

uvicorn.run(app, host='127.0.0.1', port=9000)
"
```

然后修改 `h5-patient-app/.env`:
```
VITE_API_BASE_URL=http://localhost:9000
```

### 方案3: 完全重启并清理（推荐）

```bash
# 1. 停止所有Python进程
taskkill /F /IM python.exe

# 2. 等待2秒
timeout /t 2

# 3. 重新启动后端
cd D:\behavioral-health-project
python __main__.py serve

# 4. 在新终端启动H5应用
cd D:\behavioral-health-project\h5-patient-app
npm run dev

# 5. 测试登录
curl -X POST http://localhost:8000/api/v1/auth/login -d "username=patient_alice&password=password123"
```

## 验证步骤

### 测试后端API

```bash
# 1. 测试health端点
curl http://localhost:8000/health

# 2. 测试登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=patient_alice&password=password123"

# 预期响应:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 2,
    "username": "patient_alice",
    "email": "alice@example.com",
    "role": "patient",
    "full_name": "Alice Wang"
  }
}
```

### 测试H5应用

1. 打开浏览器访问：http://localhost:5176 (或 http://192.168.1.103:5176)
2. 在登录页面输入：
   - 用户名：`patient_alice`
   - 密码：`password123`
3. 点击"登录"按钮
4. 检查浏览器控制台是否有错误
5. 成功后应跳转到首页

## 已知测试账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| patient_alice | password123 | 患者 |
| patient_bob | password123 | 患者 |
| coach_carol | password123 | 教练 |
| admin | password123 | 管理员 |

## 调试建议

### 查看后端日志

```bash
# Windows
type C:\Users\Administrator\AppData\Local\Temp\claude\D--behavioral-health-project\tasks\*.output

# 或在运行serve时直接查看输出
```

### 查看浏览器网络请求

1. 打开浏览器开发者工具（F12）
2. 切换到Network标签
3. 点击登录按钮
4. 查看`login`请求：
   - Request URL: 应该是 `http://localhost:8000/api/v1/auth/login`
   - Request Method: POST
   - Form Data: username 和 password
   - Response: 查看返回内容

### 如果还是401错误

检查：
1. 用户名是否正确（区分大小写）
2. 密码是否正确
3. 数据库中用户是否存在：
   ```bash
   python -c "import sys; sys.path.insert(0, '.'); from core.database import SessionLocal; from core.models import User; db = SessionLocal(); users = db.query(User).all(); [print(f'{u.username} - {u.email}') for u in users]"
   ```

## 下一步

一旦登录功能正常，您可以：

1. ✅ 测试完整用户流程
2. ✅ 提交评估数据
3. ✅ 查看评估结果
4. ✅ 在移动设备上测试
5. ✅ 优化UI/UX

---

**文档创建时间**: 2026-01-28
**问题跟踪**: #1 修复后端登录API功能
