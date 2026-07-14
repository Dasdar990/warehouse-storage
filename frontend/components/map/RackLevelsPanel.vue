<script setup lang="ts">
import type { RackLevelsResponse } from '~/composables/useWarehouseApi'

const props = defineProps<{
  rack: RackLevelsResponse
  selectedLevel: string | null
  loading: boolean
}>()

const emit = defineEmits<{ 'select-level': [string]; close: [] }>()

function levelClass(shelfPosition: string, hasLowStock: boolean, hasItems: boolean) {
  return {
    'level--empty': !hasItems,
    'level--stocked': hasItems && !hasLowStock,
    'level--low': hasItems && hasLowStock,
    'level--selected': props.selectedLevel === shelfPosition,
  }
}
</script>

<template>
  <section class="panel">
    <div class="panel__header">
      <div>
        <h2>Scaffale {{ rack.label || rack.rack_code }}</h2>
        <p class="panel__subtitle">{{ rack.levels.length }} mensola/e — clicca una mensola per vedere gli articoli</p>
      </div>
      <button class="btn btn--icon" title="Close" @click="emit('close')">✕</button>
    </div>

    <p v-if="loading" class="panel__loading">Loading…</p>
    <div v-else class="levels">
      <button
        v-for="lvl in rack.levels"
        :key="lvl.shelf_position"
        class="level"
        :class="levelClass(lvl.shelf_position, lvl.has_low_stock, lvl.item_count > 0)"
        @click="emit('select-level', lvl.shelf_position)"
      >
        <span class="level__code">Mensola {{ lvl.level }}</span>
        <span class="level__meta">{{ lvl.shelf_position }}</span>
        <span v-if="lvl.item_count" class="level__count">{{ lvl.item_count }} art. · {{ lvl.total_quantity }} pz</span>
        <span v-else class="level__count level__count--empty">Vuota</span>
      </button>
    </div>
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
  margin-bottom: 14px;
}

.panel__subtitle {
  margin: 4px 0 0;
  color: var(--text-dim);
  font-size: 0.85rem;
}

.panel__loading {
  color: var(--text-dim);
  padding: 20px 0;
}

.levels {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
}

.level {
  cursor: pointer;
  border-radius: 10px;
  border: 1px solid var(--border);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
  color: var(--text);
  transition: transform 0.08s ease, box-shadow 0.15s ease;
}

.level:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
}

.level--empty {
  background: var(--bg-elevated-2);
}

.level--stocked {
  background: rgba(59, 130, 246, 0.14);
  border-color: rgba(59, 130, 246, 0.45);
}

.level--low {
  background: rgba(239, 68, 68, 0.14);
  border-color: rgba(239, 68, 68, 0.5);
}

.level--selected {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.level__code {
  font-weight: 700;
  font-size: 0.85rem;
}

.level__meta {
  color: var(--text-dim);
  font-size: 0.72rem;
}

.level__count {
  margin-top: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.level__count--empty {
  color: var(--text-dim);
  font-weight: 400;
}

.btn {
  cursor: pointer;
  border: none;
  border-radius: 8px;
  padding: 8px 14px;
  font-weight: 600;
  font-size: 0.8rem;
}

.btn--icon {
  background: transparent;
  color: var(--text-dim);
  padding: 4px 10px;
  font-size: 1rem;
}
</style>
