<script setup lang="ts">
import type { ItemFilters } from '~/composables/useWarehouseApi'

const props = defineProps<{
  modelValue: ItemFilters
  categories: string[]
}>()

const emit = defineEmits<{
  'update:modelValue': [ItemFilters]
}>()

function update<K extends keyof ItemFilters>(key: K, value: ItemFilters[K]) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}

function reset() {
  emit('update:modelValue', {})
}
</script>

<template>
  <div class="filter-bar">
    <input
      class="filter-search"
      type="text"
      placeholder="Search name, P/N, or barcode…"
      :value="modelValue.search"
      @input="update('search', ($event.target as HTMLInputElement).value)"
    />

    <select
      class="filter-select"
      :value="modelValue.category || ''"
      @change="update('category', ($event.target as HTMLSelectElement).value)"
    >
      <option value="">All categories</option>
      <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
    </select>

    <select
      class="filter-select"
      :value="modelValue.size || ''"
      @change="update('size', ($event.target as HTMLSelectElement).value as any)"
    >
      <option value="">All sizes</option>
      <option value="small">Small</option>
      <option value="big">Big</option>
      <option value="xl">XL</option>
    </select>

    <input
      class="filter-select filter-shelf"
      type="text"
      placeholder="Shelf (e.g. 12B)"
      :value="modelValue.shelf_position"
      @input="update('shelf_position', ($event.target as HTMLInputElement).value)"
    />

    <label class="filter-checkbox">
      <input
        type="checkbox"
        :checked="modelValue.low_stock"
        @change="update('low_stock', ($event.target as HTMLInputElement).checked)"
      />
      Low stock only
    </label>

    <button class="btn btn--ghost btn--small" @click="reset">Clear</button>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.filter-search {
  flex: 1 1 220px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #0a0e14;
  color: var(--text);
}

.filter-select {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #0a0e14;
  color: var(--text);
}

.filter-shelf {
  width: 140px;
}

.filter-checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-dim);
  font-size: 0.9rem;
  white-space: nowrap;
}

.btn {
  cursor: pointer;
  border: none;
  border-radius: 8px;
  padding: 10px 16px;
  font-weight: 600;
  font-size: 0.85rem;
}

.btn--ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
}

@media (max-width: 640px) {
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-shelf {
    width: 100%;
  }
}
</style>
