/**
 * Runs once on app boot (client only). Restores the JWT from localStorage
 * synchronously so route middleware sees it immediately, then validates it
 * against the backend -- an expired/revoked token gets cleared before the
 * user can act on stale session data.
 */
export default defineNuxtPlugin(async () => {
  const { hydrateFromStorage, fetchMe } = useAuth()
  hydrateFromStorage()
  await fetchMe()
})
