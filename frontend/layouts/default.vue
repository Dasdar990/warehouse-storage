<template>
  <div class="mx-auto min-h-full max-w-[1600px] px-5 pb-10 pt-5">
    <header class="mb-5 flex flex-wrap items-center justify-between gap-4">
      <NuxtLink to="/" class="flex items-center gap-3.5 text-inherit no-underline">
        <span class="text-[2rem]">📦</span>
        <div>
          <h1 class="m-0 text-[1.3rem] font-bold">Warehouse Storage</h1>
          <p class="mt-0.5 mb-0 text-[0.8rem] text-muted">Scan → Verify → Withdraw</p>
        </div>
      </NuxtLink>

      <nav class="flex gap-1.5 rounded-full border border-edge bg-surface p-1 max-[640px]:w-full max-[640px]:justify-between">
        <NuxtLink
          to="/"
          class="rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          Map
        </NuxtLink>
        <NuxtLink
          to="/scan"
          class="rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          Scan
        </NuxtLink>
        <NuxtLink
          to="/dashboard"
          class="rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          Dashboard
        </NuxtLink>
        <NuxtLink
          to="/categories"
          class="rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          Categories
        </NuxtLink>
        <NuxtLink
          to="/map-config"
          class="rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          Configure Map
        </NuxtLink>
        <NuxtLink
          v-if="isAdmin"
          to="/admin/users"
          class="rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          Users
        </NuxtLink>
      </nav>

      <div v-if="user" class="flex items-center gap-2.5 max-[640px]:w-full max-[640px]:justify-between">
        <span class="text-sm text-muted">
          👤 <span class="font-semibold text-ink">{{ user.full_name }}</span>
          <span v-if="isAdmin" class="ml-1.5 rounded-full bg-accent/15 px-2 py-0.5 text-[0.7rem] font-bold text-blue-300">ADMIN</span>
        </span>
        <button type="button" class="btn btn--ghost btn--small" @click="handleLogout">Log out</button>
      </div>
    </header>

    <transition
      enter-active-class="transition duration-200 ease-out"
      leave-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-1.5"
      leave-to-class="opacity-0 -translate-y-1.5"
    >
      <div
        v-if="toast"
        class="fixed left-1/2 top-[18px] z-50 max-w-[90vw] -translate-x-1/2 rounded-card px-[22px] py-3.5 text-center font-semibold shadow-card"
        :class="
          toast.type === 'success'
            ? 'border border-good bg-good-dim text-green-200'
            : 'border border-bad bg-bad-dim text-red-200'
        "
      >
        {{ toast.message }}
      </div>
    </transition>

    <main class="flex flex-col gap-4">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
const { toast } = useToast()
const { user, isAdmin, logout } = useAuth()

async function handleLogout() {
  logout()
  await navigateTo('/login')
}
</script>
