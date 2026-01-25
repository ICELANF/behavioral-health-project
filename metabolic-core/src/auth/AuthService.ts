/**
 * Auth Service - 认证服务
 * JWT认证、登录、用户身份管理
 */

import { v4 as uuidv4 } from 'uuid';
import * as crypto from 'crypto';
import { UserIdentity, SystemRole, UserStatus } from '../permission/PermissionSchema';
import { permissionService } from '../permission/PermissionService';

/**
 * 用户账户
 */
export interface UserAccount {
  user_id: string;
  username: string;
  email: string;
  phone?: string;
  password_hash: string;
  salt: string;
  role: SystemRole;
  level: number;
  certifications: string[];
  status: UserStatus;
  specialty_tags?: string[];
  coach_id?: string;
  team_id?: string;
  profile?: {
    name?: string;
    avatar?: string;
    bio?: string;
  };
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}

/**
 * 登录请求
 */
export interface LoginRequest {
  username: string;
  password: string;
}

/**
 * 登录响应
 */
export interface LoginResponse {
  success: boolean;
  token?: string;
  refresh_token?: string;
  user?: UserIdentity;
  expires_in?: number;
  error?: string;
}

/**
 * Token载荷
 */
export interface TokenPayload {
  user_id: string;
  role: SystemRole;
  level: number;
  iat: number;
  exp: number;
}

/**
 * 注册请求
 */
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  phone?: string;
  name?: string;
  role?: SystemRole;
}

/**
 * 认证服务
 */
export class AuthService {
  private users: Map<string, UserAccount> = new Map();
  private tokens: Map<string, TokenPayload> = new Map();
  private refreshTokens: Map<string, string> = new Map(); // refresh_token -> user_id
  private readonly JWT_SECRET = process.env.JWT_SECRET || 'behavioral-health-secret-key-2024';
  private readonly TOKEN_EXPIRY = 24 * 60 * 60 * 1000; // 24小时
  private readonly REFRESH_TOKEN_EXPIRY = 7 * 24 * 60 * 60 * 1000; // 7天

  constructor() {
    this.initializeDefaultUsers();
  }

  /**
   * 初始化默认用户
   */
  private initializeDefaultUsers(): void {
    // 管理员
    this.createAccount({
      username: 'admin',
      email: 'admin@behavioral-health.com',
      password: 'admin123',
      name: '系统管理员',
      role: 'ADMIN'
    });

    // 专家
    this.createAccount({
      username: 'expert',
      email: 'expert@behavioral-health.com',
      password: 'expert123',
      name: '李专家',
      role: 'EXPERT'
    });

    // 高级教练
    this.createAccount({
      username: 'coach_senior',
      email: 'senior@behavioral-health.com',
      password: 'coach123',
      name: '王教练',
      role: 'COACH_SENIOR'
    });

    // 中级教练
    this.createAccount({
      username: 'coach',
      email: 'coach@behavioral-health.com',
      password: 'coach123',
      name: '张教练',
      role: 'COACH_INTERMEDIATE'
    });

    // 初级教练
    this.createAccount({
      username: 'coach_junior',
      email: 'junior@behavioral-health.com',
      password: 'coach123',
      name: '刘教练',
      role: 'COACH_JUNIOR'
    });

    // 普通用户
    this.createAccount({
      username: 'user',
      email: 'user@example.com',
      password: 'user123',
      name: '测试用户',
      role: 'USER'
    });

    // 学员
    this.createAccount({
      username: 'student',
      email: 'student@example.com',
      password: 'student123',
      name: '学习者',
      role: 'STUDENT'
    });
  }

  /**
   * 创建账户
   */
  createAccount(request: RegisterRequest): UserAccount {
    const salt = crypto.randomBytes(16).toString('hex');
    const password_hash = this.hashPassword(request.password, salt);

    const role = request.role || 'USER';
    const level = permissionService.getRoleBaseLevel(role);

    const account: UserAccount = {
      user_id: uuidv4(),
      username: request.username,
      email: request.email,
      phone: request.phone,
      password_hash,
      salt,
      role,
      level,
      certifications: this.getDefaultCertifications(role, level),
      status: 'active',
      profile: {
        name: request.name
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    this.users.set(account.user_id, account);
    return account;
  }

  /**
   * 获取默认认证
   */
  private getDefaultCertifications(role: SystemRole, level: number): string[] {
    const certs: string[] = [];
    if (level >= 1) certs.push('L1_CERTIFIED');
    if (level >= 2) certs.push('L2_CERTIFIED');
    if (level >= 3) certs.push('L3_CERTIFIED');
    if (level >= 4) certs.push('L4_CERTIFIED');
    return certs;
  }

  /**
   * 密码哈希
   */
  private hashPassword(password: string, salt: string): string {
    return crypto.pbkdf2Sync(password, salt, 10000, 64, 'sha512').toString('hex');
  }

  /**
   * 验证密码
   */
  private verifyPassword(password: string, hash: string, salt: string): boolean {
    const computedHash = this.hashPassword(password, salt);
    return computedHash === hash;
  }

  /**
   * 生成Token
   */
  private generateToken(user: UserAccount): string {
    const payload: TokenPayload = {
      user_id: user.user_id,
      role: user.role,
      level: user.level,
      iat: Date.now(),
      exp: Date.now() + this.TOKEN_EXPIRY
    };

    // 简化的token生成（生产环境应使用真正的JWT库）
    const tokenData = JSON.stringify(payload);
    const signature = crypto
      .createHmac('sha256', this.JWT_SECRET)
      .update(tokenData)
      .digest('hex');

    const token = Buffer.from(tokenData).toString('base64') + '.' + signature;
    this.tokens.set(token, payload);

    return token;
  }

  /**
   * 生成刷新Token
   */
  private generateRefreshToken(userId: string): string {
    const refreshToken = uuidv4() + '-' + uuidv4();
    this.refreshTokens.set(refreshToken, userId);
    return refreshToken;
  }

  /**
   * 登录
   */
  login(request: LoginRequest): LoginResponse {
    // 查找用户
    const user = Array.from(this.users.values()).find(
      u => u.username === request.username || u.email === request.username
    );

    if (!user) {
      return {
        success: false,
        error: '用户不存在'
      };
    }

    // 验证密码
    if (!this.verifyPassword(request.password, user.password_hash, user.salt)) {
      return {
        success: false,
        error: '密码错误'
      };
    }

    // 检查状态
    if (user.status === 'suspended') {
      return {
        success: false,
        error: '账户已暂停'
      };
    }

    if (user.status === 'inactive') {
      return {
        success: false,
        error: '账户未激活'
      };
    }

    // 更新最后登录时间
    user.last_login_at = new Date().toISOString();

    // 生成token
    const token = this.generateToken(user);
    const refreshToken = this.generateRefreshToken(user.user_id);

    // 获取权限
    const identity = this.getUserIdentity(user);

    return {
      success: true,
      token,
      refresh_token: refreshToken,
      user: identity,
      expires_in: this.TOKEN_EXPIRY / 1000
    };
  }

  /**
   * 验证Token
   */
  verifyToken(token: string): TokenPayload | null {
    const payload = this.tokens.get(token);
    if (!payload) {
      // 尝试解析token
      try {
        const [dataBase64, signature] = token.split('.');
        const tokenData = Buffer.from(dataBase64, 'base64').toString();
        const expectedSignature = crypto
          .createHmac('sha256', this.JWT_SECRET)
          .update(tokenData)
          .digest('hex');

        if (signature !== expectedSignature) {
          return null;
        }

        const parsed = JSON.parse(tokenData) as TokenPayload;
        if (parsed.exp < Date.now()) {
          return null;
        }

        return parsed;
      } catch {
        return null;
      }
    }

    if (payload.exp < Date.now()) {
      this.tokens.delete(token);
      return null;
    }

    return payload;
  }

  /**
   * 刷新Token
   */
  refreshToken(refreshToken: string): LoginResponse {
    const userId = this.refreshTokens.get(refreshToken);
    if (!userId) {
      return {
        success: false,
        error: '无效的刷新令牌'
      };
    }

    const user = this.users.get(userId);
    if (!user) {
      return {
        success: false,
        error: '用户不存在'
      };
    }

    // 删除旧的刷新令牌
    this.refreshTokens.delete(refreshToken);

    // 生成新token
    const newToken = this.generateToken(user);
    const newRefreshToken = this.generateRefreshToken(user.user_id);

    return {
      success: true,
      token: newToken,
      refresh_token: newRefreshToken,
      user: this.getUserIdentity(user),
      expires_in: this.TOKEN_EXPIRY / 1000
    };
  }

  /**
   * 登出
   */
  logout(token: string): void {
    this.tokens.delete(token);
  }

  /**
   * 获取用户身份
   */
  getUserIdentity(user: UserAccount): UserIdentity & { username: string; name: string } {
    const identity: UserIdentity & { username: string; name: string } = {
      user_id: user.user_id,
      username: user.username,
      name: user.profile?.name || user.username,
      role: user.role,
      level: user.level,
      certifications: user.certifications,
      status: user.status,
      permissions: [],
      specialty_tags: user.specialty_tags,
      coach_id: user.coach_id,
      team_id: user.team_id
    };

    // 计算权限
    identity.permissions = permissionService.getUserPermissions(identity);

    return identity;
  }

  /**
   * 根据Token获取用户
   */
  getUserByToken(token: string): UserIdentity | null {
    const payload = this.verifyToken(token);
    if (!payload) {
      return null;
    }

    const user = this.users.get(payload.user_id);
    if (!user) {
      return null;
    }

    return this.getUserIdentity(user);
  }

  /**
   * 获取用户账户
   */
  getAccount(userId: string): UserAccount | undefined {
    return this.users.get(userId);
  }

  /**
   * 更新用户角色
   */
  updateRole(userId: string, role: SystemRole): boolean {
    const user = this.users.get(userId);
    if (!user) return false;

    user.role = role;
    user.level = permissionService.getRoleBaseLevel(role);
    user.updated_at = new Date().toISOString();

    return true;
  }

  /**
   * 更新用户等级
   */
  updateLevel(userId: string, level: number): boolean {
    const user = this.users.get(userId);
    if (!user) return false;

    user.level = level;
    user.certifications = this.getDefaultCertifications(user.role, level);
    user.updated_at = new Date().toISOString();

    return true;
  }

  /**
   * 添加认证
   */
  addCertification(userId: string, certification: string): boolean {
    const user = this.users.get(userId);
    if (!user) return false;

    if (!user.certifications.includes(certification)) {
      user.certifications.push(certification);
      user.updated_at = new Date().toISOString();
    }

    return true;
  }

  /**
   * 更新用户状态
   */
  updateStatus(userId: string, status: UserStatus): boolean {
    const user = this.users.get(userId);
    if (!user) return false;

    user.status = status;
    user.updated_at = new Date().toISOString();

    return true;
  }

  /**
   * 获取所有用户
   */
  getAllUsers(): UserIdentity[] {
    return Array.from(this.users.values()).map(u => this.getUserIdentity(u));
  }

  /**
   * 按角色获取用户
   */
  getUsersByRole(role: SystemRole): UserIdentity[] {
    return Array.from(this.users.values())
      .filter(u => u.role === role)
      .map(u => this.getUserIdentity(u));
  }
}

// 导出单例
export const authService = new AuthService();
