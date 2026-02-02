/**
 * 本地存储封装
 */

const PREFIX = 'behavioral_health_'

export const storage = {
  /**
   * 设置存储
   */
  set(key: string, value: any): void {
    try {
      const data = JSON.stringify(value)
      localStorage.setItem(PREFIX + key, data)
    } catch (error) {
      console.error('Storage set error:', error)
    }
  },

  /**
   * 获取存储
   */
  get<T = any>(key: string, defaultValue?: T): T | null {
    try {
      const data = localStorage.getItem(PREFIX + key)
      if (data) {
        return JSON.parse(data) as T
      }
      return defaultValue ?? null
    } catch (error) {
      console.error('Storage get error:', error)
      return defaultValue ?? null
    }
  },

  /**
   * 移除存储
   */
  remove(key: string): void {
    try {
      localStorage.removeItem(PREFIX + key)
    } catch (error) {
      console.error('Storage remove error:', error)
    }
  },

  /**
   * 清空存储
   */
  clear(): void {
    try {
      const keys = Object.keys(localStorage)
      keys.forEach((key) => {
        if (key.startsWith(PREFIX)) {
          localStorage.removeItem(key)
        }
      })
    } catch (error) {
      console.error('Storage clear error:', error)
    }
  },

  /**
   * Token相关
   */
  token: {
    set(token: string): void {
      storage.set('access_token', token)
    },
    get(): string | null {
      return storage.get<string>('access_token')
    },
    remove(): void {
      storage.remove('access_token')
    }
  },

  /**
   * 用户信息相关
   */
  user: {
    set(user: any): void {
      storage.set('user_info', user)
    },
    get(): any {
      return storage.get('user_info')
    },
    remove(): void {
      storage.remove('user_info')
    }
  }
}
