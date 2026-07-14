<script setup lang="ts">
const { toast } = useToast()
</script>

<template>
  <div class="shell">
    <header class="topbar">
      <NuxtLink to="/" class="brand">
        <span class="brand__icon">📦</span>
        <div>
          <h1>Warehouse Storage</h1>
          <p class="brand__subtitle">Scan → Verify → Withdraw</p>
        </div>
      </NuxtLink>

      <nav class="nav">
        <NuxtLink to="/" class="nav__link">Map</NuxtLink>
        <NuxtLink to="/scan" class="nav__link">Scan</NuxtLink>
        <NuxtLink to="/dashboard" class="nav__link">Dashboard</NuxtLink>
        <NuxtLink to="/map-config" class="nav__link">Configure Map</NuxtLink>
      </nav>
    </header>

    <transition name="fade">
      <div v-if="toast" class="toast" :class="`toast--${toast.type}`">
        {{ toast.message }}
      </div>
    </transition>

    <main class="shell__content">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 20px 60px;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  text-decoration: none;
  color: inherit;
}

.brand__icon {
  font-size: 2rem;
}

.brand h1 {
  font-size: 1.3rem;
  font-weight: 700;
  margin: 0;
}

.brand__subtitle {
  margin: 2px 0 0;
  color: var(--text-dim);
  font-size: 0.8rem;
}

.nav {
  display: flex;
  gap: 6px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 4px;
}

.nav__link {
  padding: 8px 18px;
  border-radius: 999px;
  color: var(--text-dim);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
  transition: background 0.15s ease, color 0.15s ease;
}

.nav__link:hover {
  color: var(--text);
}

.nav__link.router-link-exact-active {
  background: var(--accent);
  color: #fff;
}

.toast {
  position: fixed;
  top: 18px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 50;
  padding: 14px 22px;
  border-radius: var(--radius);
  font-weight: 600;
  box-shadow: var(--shadow);
  max-width: 90vw;
  text-align: center;
}

.toast--success {
  background: var(--green-dim);
  color: #bbf7d0;
  border: 1px solid var(--green);
}

.toast--error {
  background: var(--red-dim);
  color: #fecaca;
  border: 1px solid var(--red);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.shell__content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

@media (max-width: 640px) {
  .topbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .nav {
    width: 100%;
    justify-content: space-between;
  }

  .nav__link {
    flex: 1;
    text-align: center;
    padding: 8px 10px;
  }
}
</style>
