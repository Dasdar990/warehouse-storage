<script setup lang="ts">
import type { Item } from '~/composables/useWarehouseApi'

const props = defineProps<{
  shelfPosition: string
  items: Item[]
  loading: boolean
  showBack?: boolean
}>()

const emit = defineEmits<{ close: []; back: [] }>()

const totalQuantity = computed(() => props.items.reduce((sum, i) => sum + i.quantity, 0))
</script>

<template>
  <section class="panel">
    <div class="panel__header">
      <div>
        <button v-if="showBack" class="btn btn--ghost btn--small back" type="button" @click="emit('back')">
          ← Torna allo scaffale
        </button>
        <h2>Mensola {{ shelfPosition }}</h2>
        <p class="panel__subtitle">
          {{ items.length }} item type(s) · {{ totalQuantity }} unit(s) total
        </p>
      </div>
      <div class="panel__actions">
        <NuxtLink
          class="btn btn--ghost btn--small"
          :to="{ path: '/dashboard', query: { shelf_position: shelfPosition } }"
        >
          Open in Dashboard
        </NuxtLink>
        <button class="btn btn--icon" title="Close" @click="emit('close')">✕</button>
      </div>
    </div>

    <p v-if="loading" class="panel__loading">Loading shelf contents…</p>
    <DashboardItemTable v-else :items="items" :show-shelf="false" />
  </section>
</template>

<style scoped>
.panel {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow);
}

.panel__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.back {
  margin-bottom: 8px;
}

.panel__subtitle {
  margin: 4px 0 0;
  color: var(--text-dim);
  font-size: 0.85rem;
}

.panel__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel__loading {
  color: var(--text-dim);
  padding: 20px 0;
}

.btn {
  cursor: pointer;
  border: none;
  border-radius: 8px;
  padding: 8px 14px;
  font-weight: 600;
  font-size: 0.8rem;
  text-decoration: none;
  display: inline-block;
}

.btn--ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
}

.btn--small {
  padding: 6px 10px;
  font-size: 0.75rem;
}

.btn--icon {
  background: transparent;
  color: var(--text-dim);
  padding: 4px 10px;
  font-size: 1rem;
}
</style>
