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
          class="flex items-center rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          <img
            src="~/assets/icons/home.svg"
            class="w-5 h-auto inline-block mr-1"
          />
          Home
        </NuxtLink>
        <NuxtLink
          to="/dashboard"
          class="flex items-center rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          <img
            src="~/assets/icons/dashboard.svg"
            class="w-5 h-auto inline-block mr-1"
          />
          Dashboard
        </NuxtLink>
        <NuxtLink
          to="/activity-log"
          class="flex items-center rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          <img
            src="~/assets/icons/activity.svg"
            class="w-5 h-auto inline-block mr-1"
          />
          Activity Log
        </NuxtLink>
        <NuxtLink
          v-if="isAdmin"
          to="/map-config"
          class="flex items-center rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          <img
            src="~/assets/icons/map.svg"
            class="w-5 h-auto inline-block mr-1"
          />
          Map Config
        </NuxtLink>
        <NuxtLink
          v-if="isAdmin"
          to="/admin/users"
          class="flex items-center rounded-full px-4.5 py-2 text-sm font-semibold text-muted no-underline transition-colors duration-150 hover:text-ink [&.router-link-exact-active]:bg-accent [&.router-link-exact-active]:text-white max-[640px]:flex-1 max-[640px]:px-2.5 max-[640px]:text-center"
        >
          <img
            src="~/assets/icons/users.svg"
            class="w-5 h-auto inline-block mr-1"
          />
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

    <div
      class="pointer-events-none fixed top-4.5 right-4.5 z-100 flex max-w-80 flex-col gap-2 max-[640px]:left-4.5 max-[640px]:right-4.5 max-[640px]:max-w-none"
    >
      <TransitionGroup
        enter-active-class="transition duration-200 ease-out"
        leave-active-class="transition duration-150 ease-in absolute w-full"
        enter-from-class="opacity-0 translate-y-2 scale-95"
        leave-to-class="opacity-0 translate-x-3"
        move-class="transition-transform duration-200 ease-out"
      >
        <div
          v-for="t in toasts"
          :key="t.id"
          class="toast pointer-events-auto relative overflow-hidden rounded-lg border py-2.5 pl-3 pr-8 shadow-card backdrop-blur-sm"
          :class="
            t.type === 'success'
              ? 'border-good/50 bg-good-dim/95'
              : t.type === 'error'
                ? 'border-bad/50 bg-bad-dim/95'
                : 'border-accent/50 bg-accent-dim/95'
          "
          @mouseenter="pause(t.id)"
          @mouseleave="resume(t.id)"
        >
          <div class="flex items-start gap-2.5">
            <span
              class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[0.7rem] font-bold"
              :class="
                t.type === 'success'
                  ? 'bg-good/25 text-green-200'
                  : t.type === 'error'
                    ? 'bg-bad/25 text-red-200'
                    : 'bg-accent/25 text-accent'
              "
            >
              {{ t.type === "success" ? "✓" : t.type === "error" ? "!" : "i" }}
            </span>
            <span
              class="min-w-0 flex-1 text-[0.85rem] font-medium leading-snug"
              :class="
                t.type === 'success'
                  ? 'text-green-200'
                  : t.type === 'error'
                    ? 'text-red-200'
                    : 'text-ink'
              "
              >{{ t.message }}</span
            >
          </div>
          <button
            type="button"
            class="absolute right-2 top-2 cursor-pointer bg-transparent text-current opacity-50 hover:opacity-100"
            title="Dismiss"
            @click="dismiss(t.id)"
          >
            ✕
          </button>
          <div
            class="toast__bar absolute inset-x-0 bottom-0 h-0.5 origin-left"
            :class="
              t.type === 'success'
                ? 'bg-good'
                : t.type === 'error'
                  ? 'bg-bad'
                  : 'bg-accent'
            "
            :style="{ animationDuration: `${t.duration}ms` }"
          />
        </div>
      </TransitionGroup>
    </div>

    <main class="flex flex-col gap-4">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
const { toasts, dismiss, pause, resume } = useToast();
const { user, isAdmin, logout } = useAuth();

async function handleLogout() {
  logout();
  await navigateTo("/login");
}
</script>
