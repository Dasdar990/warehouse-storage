<template>
  <div class="mx-auto min-h-full max-w-400 px-5 pb-10 pt-5">
    <header class="mb-5 flex flex-wrap items-center justify-between gap-4">
      <NuxtLink
        to="/"
        class="flex items-center gap-3.5 text-inherit no-underline"
      >
        <img src="~/assets/images/logo_reduced.svg" class="w-8 h-auto" />
        <div>
          <h1 class="m-0 text-[1.3rem] font-bold">
            Industrial Engineering Warehouse
          </h1>
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
          Home
        </NuxtLink>
        <NuxtLink
          to="/dashboard"
          class="rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          Dashboard
        </NuxtLink>
        <NuxtLink
          to="/activity-log"
          class="rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          Activity Log
        </NuxtLink>
        <NuxtLink
          v-if="isAdmin"
          to="/map-config"
          class="rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          Map Config
        </NuxtLink>
        <NuxtLink
          v-if="isAdmin"
          to="/admin/users"
          class="rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          Users
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
      leave-active-class="transition duration-150 ease-in"
      enter-from-class="opacity-0 translate-y-2"
      leave-to-class="opacity-0 translate-y-1"
    >
      <div
        v-if="toast"
        class="pointer-events-none fixed top-4.5 right-4.5 z-100 max-w-80 max-[640px]:left-4.5 max-[640px]:right-4.5 max-[640px]:max-w-none"
      >
        <div
          class="pointer-events-auto flex items-start gap-2.5 rounded-lg border px-3.5 py-2.5 text-[0.85rem] font-medium shadow-card backdrop-blur-sm"
          :class="
            toast.type === 'success'
              ? 'border-good/50 bg-good-dim/95 text-green-200'
              : 'border-bad/50 bg-bad-dim/95 text-red-200'
          "
        >
          <span class="mt-0.5 shrink-0 text-4xl">{{
            toast.type === "success" ? "✓" : "!"
          }}</span>
          <span class="text-lg min-w-0 flex-1">{{ toast.message }}</span>
          <button
            type="button"
            class="text-lg shrink-0 cursor-pointer bg-transparent text-current opacity-60 hover:opacity-100"
            title="Dismiss"
            @click="dismiss"
          >
            ✕
          </button>
        </div>
      </div>
    </transition>

    <main class="flex flex-col gap-4">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
const { toast, dismiss } = useToast();
const { user, isAdmin, logout } = useAuth();

async function handleLogout() {
  logout();
  await navigateTo("/login");
}
</script>
