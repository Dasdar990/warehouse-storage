<template>
  <div class="mx-auto min-h-full max-w-400 px-5 pb-10 pt-5">
    <header class="mb-5 flex flex-wrap items-center justify-between gap-4">
      <NuxtLink
        to="/"
        class="flex items-center gap-3.5 text-inherit no-underline"
      >
        <span
          class="flex h-10 w-10 items-center justify-center rounded-full border border-edge/80 bg-surface-2 text-[0.95rem] font-semibold text-accent"
        >
          WS
        </span>
        <div>
          <h1 class="m-0 text-[1.3rem] font-bold">Warehouse Storage</h1>
          <p class="mt-0.5 mb-0 text-[0.8rem] text-muted">
            Scan, search, update stock
          </p>
        </div>
      </NuxtLink>

      <nav
        class="flex gap-1.5 rounded-full border border-edge/80 bg-surface p-1 max-[640px]:w-full max-[640px]:justify-between"
      >
        <NuxtLink
          to="/"
          class="rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          Map
        </NuxtLink>
        <NuxtLink
          to="/dashboard"
          class="rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          Dashboard
        </NuxtLink>
        <NuxtLink
          v-if="isAdmin"
          to="/map-config"
          class="rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          Map Config
        </NuxtLink>
      </nav>

      <div
        v-if="user"
        class="flex items-center gap-2.5 max-[640px]:w-full max-[640px]:justify-between"
      >
        <span
          class="inline-flex items-center gap-2 rounded-full border border-edge/80 bg-surface-2 px-3 py-1.5 text-sm text-muted"
        >
          <span class="h-2.5 w-2.5 rounded-full bg-accent"></span>
          <span class="font-semibold text-ink">{{ user.full_name }}</span>
          <span
            v-if="isAdmin"
            class="rounded-full bg-accent/12 px-2 py-0.5 text-[0.7rem] font-semibold text-accent"
            >ADMIN</span
          >
        </span>
        <button
          type="button"
          class="btn btn--ghost btn--small cursor-pointer"
          @click="handleLogout"
        >
          Log out
        </button>
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
        class="fixed left-1/2 top-4.5 z-50 max-w-[90vw] -translate-x-1/2 rounded-card px-5.5 py-3.5 text-center font-semibold shadow-card"
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
const { toast } = useToast();
const { user, isAdmin, logout } = useAuth();

async function handleLogout() {
  logout();
  await navigateTo("/login");
}
</script>
