<template>
  <div class="flex flex-col gap-4">
    <section>
      <h2 class="mb-1 text-[1.15rem]">Users</h2>
      <p class="m-0 text-sm text-muted">
        Manage who can sign in. Every withdrawal/deposit is tracked with the name of who performed it.
      </p>
    </section>

    <section class="rounded-card border border-edge bg-surface p-4 shadow-card">
      <AdminUserManager />
    </section>
  </div>
</template>

<script setup lang="ts">
// Extra layer on top of the global auth middleware: that one only checks
// "logged in", not "is admin". A non-admin landing here (e.g. by typing
// the URL) gets bounced straight back to the map.
const { isAdmin, ready } = useAuth()

watch(
  ready,
  (isReady) => {
    if (isReady && !isAdmin.value) {
      navigateTo('/')
    }
  },
  { immediate: true }
)
</script>
