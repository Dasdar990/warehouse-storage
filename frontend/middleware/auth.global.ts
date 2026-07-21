/**
 * Runs on every navigation. Skipped entirely on the server: the token only
 * exists in localStorage, which the server can't read, so the real check
 * happens client-side once the boot plugin has hydrated the session
 * (this can cause a brief flash of a protected page's shell before the
 * redirect on first load -- an acceptable tradeoff for small internal
 * tooling, not a public-facing app).
 */
export default defineNuxtRouteMiddleware((to) => {
  if (import.meta.server) return

  const { token } = useAuth()
  const isLoginPage = to.path === '/login'

  if (!token.value && !isLoginPage) {
    return navigateTo('/login')
  }
  if (token.value && isLoginPage) {
    return navigateTo('/')
  }
})
