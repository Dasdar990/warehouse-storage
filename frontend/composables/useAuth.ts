import type { UserRole } from './useWarehouseApi'

export interface AuthUser {
  id: number
  username: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
}

const TOKEN_STORAGE_KEY = 'warehouse_auth_token'

/**
 * Shared login/session state for the whole app. Token lives in
 * localStorage (client only) so a reload keeps you logged in; the actual
 * user record is re-validated against /auth/me on boot rather than
 * trusted from storage, so a revoked/expired session gets caught early.
 */
export function useAuth() {
  const token = useState<string | null>('auth-token', () => null)
  const user = useState<AuthUser | null>('auth-user', () => null)
  const ready = useState<boolean>('auth-ready', () => false)

  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase as string

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(username: string, password: string) {
    const res = await $fetch<{ access_token: string; user: AuthUser }>(`${apiBase}/auth/login`, {
      method: 'POST',
      body: { username, password },
    })
    token.value = res.access_token
    user.value = res.user
    if (import.meta.client) {
      localStorage.setItem(TOKEN_STORAGE_KEY, res.access_token)
    }
    return res.user
  }

  function logout() {
    token.value = null
    user.value = null
    if (import.meta.client) {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
    }
  }

  /** Validates the current token against the backend and refreshes `user`; logs out if it's no longer valid. */
  async function fetchMe() {
    if (!token.value) return
    try {
      user.value = await $fetch<AuthUser>(`${apiBase}/auth/me`, {
        headers: { Authorization: `Bearer ${token.value}` },
      })
    } catch {
      logout()
    } finally {
      ready.value = true
    }
  }

  /** Called once by the client boot plugin; reads the persisted token, if any. */
  function hydrateFromStorage() {
    if (!import.meta.client) return
    const stored = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (stored) {
      token.value = stored
    } else {
      ready.value = true
    }
  }

  return { token, user, ready, isAuthenticated, isAdmin, login, logout, fetchMe, hydrateFromStorage }
}
