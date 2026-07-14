<script setup lang="ts">
import type { WarehouseLayout } from '~/composables/useWarehouseApi'

const props = defineProps<{
  layout: WarehouseLayout
  selectedShelf: string | null
}>()

const emit = defineEmits<{ select: [string] }>()

const shelfByPosition = computed(() => {
  const map = new Map<string, WarehouseLayout['shelves'][number]>()
  for (const shelf of props.layout.shelves) {
    map.set(shelf.shelf_position, shelf)
  }
  return map
})

function shelfAt(shelfNumber: number, level: string) {
  return shelfByPosition.value.get(`${shelfNumber}${level}`)
}

function cellClass(shelfNumber: number, level: string) {
  const shelf = shelfAt(shelfNumber, level)
  const position = `${shelfNumber}${level}`
  return {
    'cell--empty': !shelf,
    'cell--stocked': !!shelf && !shelf.has_low_stock,
    'cell--low': !!shelf && shelf.has_low_stock,
    'cell--selected': props.selectedShelf === position,
  }
}
</script>

<template>
  <div class="map-wrap scrollbar-slim">
    <div
      class="map-grid"
      :style="{ gridTemplateColumns: `56px repeat(${layout.shelf_numbers.length}, 52px)` }"
    >
      <!-- Column header row -->
      <div class="corner"></div>
      <div v-for="n in layout.shelf_numbers" :key="`col-${n}`" class="col-header">{{ n }}</div>

      <!-- One row per level -->
      <template v-for="level in layout.levels" :key="`row-${level}`">
        <div class="row-header">{{ level }}</div>
        <button
          v-for="n in layout.shelf_numbers"
          :key="`${n}${level}`"
          class="cell"
          :class="cellClass(n, level)"
          :title="`Shelf ${n}${level}${shelfAt(n, level) ? ` — ${shelfAt(n, level)!.item_count} item(s)` : ' — empty'}`"
          @click="emit('select', `${n}${level}`)"
        >
          <span class="cell__label">{{ n }}{{ level }}</span>
          <span v-if="shelfAt(n, level)" class="cell__count">{{ shelfAt(n, level)!.item_count }}</span>
        </button>
      </template>
    </div>

    <div class="legend">
      <span class="legend__item"><i class="dot dot--empty"></i> Empty</span>
      <span class="legend__item"><i class="dot dot--stocked"></i> Stocked</span>
      <span class="legend__item"><i class="dot dot--low"></i> Low stock (≤ {{ layout.low_stock_threshold }})</span>
    </div>
  </div>
</template>

<style scoped>
.map-wrap {
  overflow-x: auto;
  padding-bottom: 6px;
}

.map-grid {
  display: grid;
  gap: 4px;
  width: max-content;
}

.corner {
  width: 56px;
  height: 32px;
}

.col-header,
.row-header {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-dim);
  font-size: 0.75rem;
  font-weight: 700;
  height: 32px;
}

.row-header {
  width: 56px;
}

.cell {
  position: relative;
  height: 52px;
  border-radius: 8px;
  border: 1px solid var(--border);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  color: var(--text);
  transition: transform 0.08s ease, box-shadow 0.15s ease;
}

.cell:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
}

.cell--empty {
  background: var(--bg-elevated);
}

.cell--stocked {
  background: rgba(59, 130, 246, 0.18);
  border-color: rgba(59, 130, 246, 0.5);
}

.cell--low {
  background: rgba(239, 68, 68, 0.18);
  border-color: rgba(239, 68, 68, 0.55);
}

.cell--selected {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.cell__label {
  font-size: 0.7rem;
  font-weight: 700;
}

.cell__count {
  font-size: 0.65rem;
  color: var(--text-dim);
}

.legend {
  display: flex;
  gap: 18px;
  margin-top: 14px;
  flex-wrap: wrap;
}

.legend__item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: var(--text-dim);
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  display: inline-block;
}

.dot--empty {
  background: var(--bg-elevated-2);
  border: 1px solid var(--border);
}

.dot--stocked {
  background: rgba(59, 130, 246, 0.6);
}

.dot--low {
  background: rgba(239, 68, 68, 0.6);
}
</style>
