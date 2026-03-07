import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<{ id?: number; phone?: string } | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  function login(t: string, u?: { id?: number; phone?: string }) {
    token.value = t
    localStorage.setItem('token', t)
    if (u) user.value = u
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, isLoggedIn, login, logout }
})
