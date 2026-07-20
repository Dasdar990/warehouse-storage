<template>
  <div class="flex flex-col gap-3">
    <div
      class="scrollbar-slim min-h-0 max-h-[65vh] overflow-auto rounded-card border border-edge bg-input bg-[radial-gradient(#2a313c_1px,transparent_1px)] bg-[length:20px_20px]"
    >
      <ClientOnly fallback="Loading map…">
        <v-stage :config="{ width: CANVAS_WIDTH, height: CANVAS_HEIGHT }" class="block">
          <v-layer>
            <!-- Room outline (walls + door): background context only, for orientation -->
            <v-group :config="{ listening: false }">
              <v-group
                v-for="wall in layout.walls"
                :key="`wall-${wall.id}`"
                :config="{ x: wall.x, y: wall.y, rotation: wall.rotation }"
              >
                <v-rect
                  :config="{
                    x: -wall.height * 0.35,
                    y: -wall.height * 0.35,
                    width: wall.height * 0.7,
                    height: wall.height * 1.7,
                    fill: '#64748b',
                    cornerRadius: 1,
                  }"
                />
                <v-rect
                  :config="{
                    x: wall.width - wall.height * 0.35,
                    y: -wall.height * 0.35,
                    width: wall.height * 0.7,
                    height: wall.height * 1.7,
                    fill: '#64748b',
                    cornerRadius: 1,
                  }"
                />
                <v-rect
                  :config="{
                    width: wall.width,
                    height: wall.height,
                    fillLinearGradientStartPoint: { x: 0, y: 0 },
                    fillLinearGradientEndPoint: { x: 0, y: wall.height },
                    fillLinearGradientColorStops: [0, '#e2e8f0', 1, '#94a3b8'],
                    stroke: '#475569',
                    strokeWidth: 1,
                    cornerRadius: 1,
                  }"
                />
                <v-line
                  :config="{
                    points: [0, wall.height / 2, wall.width, wall.height / 2],
                    stroke: '#334155',
                    strokeWidth: 1,
                    opacity: 0.5,
                  }"
                />
              </v-group>
              <v-group
                v-for="door in layout.doors"
                :key="`door-${door.id}`"
                :config="{ x: door.x, y: door.y, rotation: door.rotation }"
              >
                <v-arc
                  :config="{
                    innerRadius: 0,
                    outerRadius: door.width,
                    angle: 90,
                    stroke: '#facc15',
                    strokeWidth: 2,
                    dash: [5, 4],
                  }"
                />
              </v-group>
            </v-group>

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

    <div class="flex flex-wrap gap-[18px]">
      <span class="flex items-center gap-1.5 text-[0.8rem] text-muted"><i class="inline-block h-2.5 w-2.5 rounded-[3px] border border-edge bg-surface-2"></i> Empty</span>
      <span class="flex items-center gap-1.5 text-[0.8rem] text-muted"><i class="inline-block h-2.5 w-2.5 rounded-[3px] bg-accent/60"></i> Stocked</span>
      <span class="flex items-center gap-1.5 text-[0.8rem] text-muted"><i class="inline-block h-2.5 w-2.5 rounded-[3px] bg-bad/60"></i> Low stock (≤ {{ layout.low_stock_threshold }})</span>
    </div>
  </div>
</template>

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
  if (node.item_count === 0) return '#2a313c'
  if (node.has_low_stock) return 'rgba(239, 68, 68, 0.7)'
  return 'rgba(59, 130, 246, 0.7)'
}
</script>
