<script setup lang="ts">
import type { WarehouseLayout } from '~/composables/useWarehouseApi'

const props = defineProps<{
  layout: WarehouseLayout
  selectedRack: string | null
}>()

const emit = defineEmits<{ select: [string] }>()

function cellClass(rackCode: string, hasLowStock: boolean, hasItems: boolean) {
  return {
    'shelf--empty': !hasItems,
    'shelf--stocked': hasItems && !hasLowStock,
    'shelf--low': hasItems && hasLowStock,
    'shelf--selected': props.selectedRack === rackCode,
  }
}

const canvasBounds = computed(() => {
  const boxes = [...props.layout.nodes, ...props.layout.zones]
  const width = Math.max(...boxes.map((n) => n.x + n.width), 400)
  const height = Math.max(...boxes.map((n) => n.y + n.height), 300)
  return { width: width + 24, height: height + 24 }
})
</script>

<template>
  <div class="map-wrap scrollbar-slim">
    <div class="canvas" :style="{ width: `${canvasBounds.width}px`, height: `${canvasBounds.height}px` }">
      <!-- Zones: background layer, purely visual grouping -->
      <div
        v-for="zone in layout.zones"
        :key="`zone-${zone.id}`"
        class="zone"
        :style="{
          left: `${zone.x}px`,
          top: `${zone.y}px`,
          width: `${zone.width}px`,
          height: `${zone.height}px`,
          background: `${zone.color}14`,
          borderColor: `${zone.color}55`,
        }"
      >
        <span class="zone__label" :style="{ color: zone.color }">{{ zone.name }}</span>
      </div>

      <!-- Racks: clickable, colored by aggregated stock across all their levels -->
      <button
        v-for="node in layout.nodes"
        :key="node.rack_code"
        class="shelf"
        :class="cellClass(node.rack_code, node.has_low_stock, node.item_count > 0)"
        :style="{ left: `${node.x}px`, top: `${node.y}px`, width: `${node.width}px`, height: `${node.height}px` }"
        :title="`${node.label || node.rack_code} — ${node.levels.length} mensola/e — ${node.item_count} item(s)`"
        @click="emit('select', node.rack_code)"
      >
        <span class="shelf__label">{{ node.label || node.rack_code }}</span>
        <span class="shelf__levels">{{ node.levels.length }} mensola/e</span>
        <span v-if="node.item_count" class="shelf__count">{{ node.item_count }}</span>
      </button>
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
  overflow: auto;
  padding-bottom: 6px;
  max-height: 65vh;
}

.canvas {
  position: relative;
}

.zone {
  position: absolute;
  border: 2px dashed;
  border-radius: 10px;
  pointer-events: none;
  padding: 6px 8px;
}

.zone__label {
  font-size: 0.75rem;
  font-weight: 700;
  opacity: 0.85;
}

.shelf {
  position: absolute;
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
  padding: 4px;
  z-index: 1;
}

.shelf:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
  z-index: 2;
}

.shelf--empty {
  background: var(--bg-elevated);
}

.shelf--stocked {
  background: rgba(59, 130, 246, 0.18);
  border-color: rgba(59, 130, 246, 0.5);
}

.shelf--low {
  background: rgba(239, 68, 68, 0.18);
  border-color: rgba(239, 68, 68, 0.55);
}

.shelf--selected {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  z-index: 3;
}

.shelf__label {
  font-size: 0.72rem;
  font-weight: 700;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.shelf__levels {
  font-size: 0.6rem;
  color: var(--text-dim);
}

.shelf__count {
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
