import { ref, watch, onMounted } from 'vue';

/**
 * 存储类型
 */
export type StorageType = 'local' | 'session';

/**
 * 持久化配置
 */
export interface PersistenceOptions<T> {
  key: string;
  defaultValue: T;
  storage?: StorageType;
  serialize?: (value: T) => string;
  deserialize?: (value: string) => T;
  debounceMs?: number;
  onError?: (error: Error) => void;
}

/**
 * 通用状态持久化 Hook
 * 自动同步状态到 localStorage/sessionStorage
 */
export function useStatePersistence<T>(options: PersistenceOptions<T>) {
  const {
    key,
    defaultValue,
    storage = 'local',
    serialize = JSON.stringify,
    deserialize = JSON.parse,
    debounceMs = 0,
    onError = console.error,
  } = options;

  const storageApi = storage === 'local' ? localStorage : sessionStorage;
  const state = ref<T>(defaultValue) as { value: T };
  const isLoaded = ref(false);

  let debounceTimer: number | null = null;

  /**
   * 从存储中加载状态
   */
  const load = (): T | null => {
    try {
      const stored = storageApi.getItem(key);
      if (stored !== null) {
        const value = deserialize(stored);
        state.value = value;
        isLoaded.value = true;
        return value;
      }
    } catch (error) {
      onError(error as Error);
    }
    isLoaded.value = true;
    return null;
  };

  /**
   * 保存状态到存储
   */
  const save = (value?: T) => {
    try {
      const toSave = value !== undefined ? value : state.value;
      storageApi.setItem(key, serialize(toSave));
    } catch (error) {
      onError(error as Error);
    }
  };

  /**
   * 防抖保存
   */
  const debouncedSave = (value: T) => {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    if (debounceMs > 0) {
      debounceTimer = window.setTimeout(() => {
        save(value);
      }, debounceMs);
    } else {
      save(value);
    }
  };

  /**
   * 清除存储
   */
  const clear = () => {
    try {
      storageApi.removeItem(key);
      state.value = defaultValue;
    } catch (error) {
      onError(error as Error);
    }
  };

  /**
   * 重置为默认值
   */
  const reset = () => {
    state.value = defaultValue;
    save(defaultValue);
  };

  // 监听状态变化自动保存
  watch(
    () => state.value,
    (newValue) => {
      if (isLoaded.value) {
        debouncedSave(newValue);
      }
    },
    { deep: true }
  );

  // 组件挂载时加载
  onMounted(() => {
    load();
  });

  return {
    state,
    isLoaded,
    load,
    save,
    clear,
    reset,
  };
}

/**
 * 创建持久化 Store
 * 用于跨组件共享持久化状态
 */
export function createPersistentStore<T extends Record<string, any>>(
  name: string,
  initialState: T,
  options: Partial<Omit<PersistenceOptions<T>, 'key' | 'defaultValue'>> = {}
) {
  const key = `store_${name}`;
  const storage = options.storage === 'session' ? sessionStorage : localStorage;

  // 从存储加载初始状态
  let currentState: T;
  try {
    const stored = storage.getItem(key);
    currentState = stored ? JSON.parse(stored) : { ...initialState };
  } catch {
    currentState = { ...initialState };
  }

  const state = ref(currentState) as { value: T };

  // 保存到存储
  const persist = () => {
    try {
      storage.setItem(key, JSON.stringify(state.value));
    } catch (error) {
      console.error(`[PersistentStore:${name}] Save error:`, error);
    }
  };

  // 监听变化自动保存
  watch(state, persist, { deep: true });

  // 获取值
  const get = <K extends keyof T>(key: K): T[K] => state.value[key];

  // 设置值
  const set = <K extends keyof T>(key: K, value: T[K]) => {
    state.value[key] = value;
  };

  // 批量更新
  const patch = (updates: Partial<T>) => {
    state.value = { ...state.value, ...updates };
  };

  // 重置
  const reset = () => {
    state.value = { ...initialState };
    persist();
  };

  // 清除
  const clear = () => {
    storage.removeItem(key);
    state.value = { ...initialState };
  };

  return {
    state,
    get,
    set,
    patch,
    reset,
    clear,
    persist,
  };
}

/**
 * 用户偏好设置持久化
 */
export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: 'zh-CN' | 'en-US';
  sidebarCollapsed: boolean;
  tablePageSize: number;
  notifications: boolean;
}

const defaultPreferences: UserPreferences = {
  theme: 'light',
  language: 'zh-CN',
  sidebarCollapsed: false,
  tablePageSize: 10,
  notifications: true,
};

/**
 * 用户偏好设置 Hook
 */
export function useUserPreferences() {
  return createPersistentStore('user_preferences', defaultPreferences);
}

/**
 * 表单草稿持久化
 */
export function useFormDraft<T extends Record<string, any>>(formId: string, initialData: T) {
  const key = `form_draft_${formId}`;

  return useStatePersistence<T>({
    key,
    defaultValue: initialData,
    storage: 'session', // 表单草稿用 sessionStorage
    debounceMs: 500, // 500ms 防抖
  });
}

/**
 * 最近访问记录
 */
export interface RecentItem {
  id: string;
  type: string;
  title: string;
  path: string;
  timestamp: number;
}

export function useRecentItems(maxItems: number = 10) {
  const { state, save, clear } = useStatePersistence<RecentItem[]>({
    key: 'recent_items',
    defaultValue: [],
  });

  const addItem = (item: Omit<RecentItem, 'timestamp'>) => {
    const newItem: RecentItem = {
      ...item,
      timestamp: Date.now(),
    };

    // 移除重复项
    const filtered = state.value.filter((i) => i.id !== item.id);

    // 添加到开头并限制数量
    state.value = [newItem, ...filtered].slice(0, maxItems);
    save();
  };

  const removeItem = (id: string) => {
    state.value = state.value.filter((i) => i.id !== id);
    save();
  };

  return {
    items: state,
    addItem,
    removeItem,
    clear,
  };
}

/**
 * 搜索历史
 */
export function useSearchHistory(key: string, maxItems: number = 20) {
  const { state, save, clear } = useStatePersistence<string[]>({
    key: `search_history_${key}`,
    defaultValue: [],
  });

  const addSearch = (query: string) => {
    if (!query.trim()) return;

    const filtered = state.value.filter((q) => q !== query);
    state.value = [query, ...filtered].slice(0, maxItems);
    save();
  };

  const removeSearch = (query: string) => {
    state.value = state.value.filter((q) => q !== query);
    save();
  };

  return {
    history: state,
    addSearch,
    removeSearch,
    clear,
  };
}
