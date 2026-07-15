<script setup lang="ts">
import type { WarehouseLayout } from '~/composables/useWarehouseApi'

const props = defineProps<{
  layout: WarehouseLayout
  selectedRack: string | null
}>()

const emit = defineEmits<{ select: [string] }>()

const CANVAS_WIDTH = 1400
const CANVAS_HEIGHT = 760

function rackFill(node: WarehouseLayout['nodes'][number]) {
  if (node.item_count === 0) return 'rgba(148, 163, 184, 0.12)'
  if (node.has_low_stock) return 'rgba(239, 68, 68, 0.22)'
  return 'rgba(59, 130, 246, 0.22)'
}

function rackStroke(node: WarehouseLayout['nodes'][number]) {
  if (node.rack_code === props.selectedRack) return '#22c55e'
  if (node.item_count === 0) return 'var(--border, #374151)'
  if (node.has_low_stock) return 'rgba(239, 68, 68, 0.7)'
  return 'rgba(59, 130, 246, 0.7)'
}
</script>

<template>
  <div class="map-wrap">
    <div class="canvas-scroll scrollbar-slim">
      <ClientOnly fallback="Caricamento mappa in corso...">
        <v-stage :config="{ width: CANVAS_WIDTH, height: CANVAS_HEIGHT }" class="stage">
          <v-layer>
            <!-- Zones as background context -->
            <v-group v-for="zone in layout.zones" :key="`zone-${zone.id}`" :config="{ listening: false }">
              <v-rect
                :config="{
                  x: zone.x,
                  y: zone.y,
                  width: zone.width,
                  height: zone.height,
                  fill: zone.color + '14',
                  stroke: zone.color + '55',
                  strokeWidth: 1.5,
                  dash: [6, 4],
                  cornerRadius: 6,
                }"
              />
              <v-text
                :config="{
                  x: zone.x + 8,
                  y: zone.y + 6,
                  text: zone.name,
                  fontSize: 12,
                  fontStyle: 'bold',
                  fill: zone.color,
                }"
              />
            </v-group>

            <!-- Racks, rotated exactly as saved in the editor -->
            <v-group
              v-for="node in layout.nodes"
              :key="node.rack_code"
              :config="{
                x: node.x,
                y: node.y,
                width: node.width,
                height: node.height,
                rotation: node.rotation,
              }"
              @click="emit('select', node.rack_code)"
              @tap="emit('select', node.rack_code)"
            >
              <v-rect
                :config="{
                  width: node.width,
                  height: node.height,
                  fill: rackFill(node),
                  stroke: rackStroke(node),
                  strokeWidth: node.rack_code === selectedRack ? 3 : 2,
                  cornerRadius: 4,
                }"
              />
              <v-text
                :config="{
                  text: (node.label || node.rack_code) + '\n' + node.item_count + ' item(s)',
                  fontSize: 12,
                  fontFamily: 'Segoe UI, Arial',
                  fill: '#e5e7eb',
                  width: node.width,
                  height: node.height,
                  align: 'center',
                  verticalAlign: 'middle',
                  listening: false,
                }"
              />
            </v-group>
          </v-layer>
        </v-stage>
      </ClientOnly>
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
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.canvas-scroll {
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background-color: #0a0e14;
  background-image: radial-gradient(var(--border) 1px, transparent 1px);
  background-size: 20px 20px;
  max-height: 65vh;
}

.stage {
  display: block;
}

.legend {
  display: flex;
  gap: 18px;
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
