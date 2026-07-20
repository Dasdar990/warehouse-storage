<template>
  <div class="flex flex-col gap-3">
    <div class="flex flex-wrap items-center gap-3.5">
      <button class="btn btn--confirm text-[#06280f] disabled:cursor-not-allowed disabled:opacity-50" type="button" @click="addZone">+ Add zone</button>
      <label class="flex items-center gap-1.5 text-[0.85rem] text-muted">
        <input v-model="snapToGrid" type="checkbox" />
        Snap to grid
      </label>
      <button class="btn btn--ghost disabled:cursor-not-allowed disabled:opacity-50" type="button" :disabled="!zones.length" @click="clearAll">
        Clear canvas
      </button>
      <span class="ml-auto text-[0.8rem] text-muted">{{ zones.length }} zone(s)</span>
    </div>

    <div class="scrollbar-slim min-h-0 max-h-[65vh] overflow-auto rounded-card border border-edge bg-input">
      <div
        class="relative bg-[radial-gradient(#2a313c_1px,transparent_1px)] bg-[length:20px_20px]"
        :style="{ width: `${CANVAS_WIDTH}px`, height: `${CANVAS_HEIGHT}px` }"
        @pointerdown="selectedKey = null"
      >
        <svg
          class="pointer-events-none absolute inset-0"
          :width="CANVAS_WIDTH"
          :height="CANVAS_HEIGHT"
        >
          <line
            v-for="(wall, idx) in walls"
            :key="`bg-wall-${wall.id ?? idx}`"
            :x1="wall.x1"
            :y1="wall.y1"
            :x2="wall.x2"
            :y2="wall.y2"
            stroke="#cbd5e1"
            stroke-width="8"
            stroke-linecap="round"
          />
          <path
            v-for="(door, idx) in doors"
            :key="`bg-door-${door.id ?? idx}`"
            :d="doorArcPath(door)"
            fill="none"
            stroke="#facc15"
            stroke-width="2"
            stroke-dasharray="5 4"
          />
        </svg>
        <div
          v-for="zone in zones"
          :key="zone._key"
          class="absolute select-none rounded-[10px] border-2 border-dashed p-2 [touch-action:none]"
          :class="[
            selectedKey === zone._key ? 'z-[2] outline outline-2 outline-offset-2 outline-accent cursor-grabbing' : 'cursor-grab',
            !zone.name ? 'border-bad/60!' : '',
          ]"
          :style="{
            left: `${zone.x}px`,
            top: `${zone.y}px`,
            width: `${zone.width}px`,
            height: `${zone.height}px`,
            background: `${zone.color}22`,
            borderColor: `${zone.color}88`,
          }"
          @pointerdown.stop="startDrag($event, zone)"
        >
          <button
            class="zone-box__delete absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full border border-edge bg-surface text-[0.9rem] leading-none text-muted hover:text-red-300 hover:border-bad/60"
            type="button"
            title="Remove zone"
            @pointerdown.stop
            @click="removeZone(zone._key)"
          >
            ×
          </button>
          <div class="flex items-center gap-1.5">
            <input
              :id="`zone-name-${zone._key}`"
              v-model="zone.name"
              class="zone-box__input min-w-0 flex-1 rounded-md border border-edge bg-black/35 px-1.5 py-1 text-[0.78rem] font-bold text-ink [pointer-events:auto]"
              type="text"
              placeholder="e.g. Spare parts zone"
              maxlength="60"
              @pointerdown.stop
              @change="commit"
            />
            <input
              v-model="zone.color"
              class="zone-box__swatch h-6 w-6 shrink-0 cursor-pointer rounded-md border border-edge bg-transparent p-0 [pointer-events:auto]"
              type="color"
              title="Zone color"
              @pointerdown.stop
              @change="commit"
            />
          </div>
          <div
            class="zone-box__handle absolute bottom-0.5 right-0.5 h-3 w-3 cursor-se-resize border-b-2 border-r-2 border-muted opacity-60"
            @pointerdown.stop="startResize($event, zone)"
          ></div>
        </div>
      </div>
    </div>

    <p class="m-0 text-[0.8rem] text-muted">
      Drag a zone to move it, drag its bottom-right corner to resize, and give it a name — this is purely
      visual and helps you group racks (e.g. "Engine parts zone"). Click "Save layout" above when done.
    </p>
  </div>
</template>

<script setup lang="ts">
import type { DoorInput, WallInput, ZoneInput } from '~/composables/useWarehouseApi'

/**
 * Freeform drag-and-drop canvas for delimiting warehouse zones. Each zone
 * is an absolutely-positioned, named, colored rectangle the user can drag,
 * resize, and delete — same interaction pattern as the rack editor, but
 * zones are purely visual/organizational (no code has to match anything).
 */

interface EditorZone extends ZoneInput {
  _key: string
}

const props = withDefaults(
  defineProps<{
    modelValue: ZoneInput[]
    walls?: (WallInput & { id?: number })[]
    doors?: (DoorInput & { id?: number })[]
  }>(),
  { walls: () => [], doors: () => [] },
)

const emit = defineEmits<{ 'update:modelValue': [ZoneInput[]] }>()

const CANVAS_WIDTH = 1400
const CANVAS_HEIGHT = 760
const MIN_SIZE = 60
const GRID_STEP = 20

// Background-only door swing symbol (hinge -> gap edge -> arc -> leaf edge -> hinge),
// same shape drawn natively by the rack editor's Konva v-arc.
function doorArcPath(door: DoorInput) {
  const rad = (door.rotation * Math.PI) / 180
  const rad90 = ((door.rotation + 90) * Math.PI) / 180
  const gapX = door.x + door.width * Math.cos(rad)
  const gapY = door.y + door.width * Math.sin(rad)
  const leafX = door.x + door.width * Math.cos(rad90)
  const leafY = door.y + door.width * Math.sin(rad90)
  return `M ${door.x} ${door.y} L ${gapX} ${gapY} A ${door.width} ${door.width} 0 0 1 ${leafX} ${leafY} Z`
}

const PALETTE = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#a855f7', '#06b6d4', '#ec4899', '#84cc16']

let keySeed = 0
function nextKey() {
  keySeed += 1
  return `z${Date.now()}-${keySeed}`
}

const zones = ref<EditorZone[]>(props.modelValue.map((z) => ({ ...z, _key: nextKey() })))
const snapToGrid = ref(true)
const selectedKey = ref<string | null>(null)

watch(
  () => props.modelValue,
  (value) => {
    if (value.length !== zones.value.length || value !== lastEmitted) {
      zones.value = value.map((z) => ({ ...z, _key: nextKey() }))
    }
  }
)

let lastEmitted: ZoneInput[] | null = null
function commit() {
  const plain = zones.value.map(({ _key, ...rest }) => rest)
  lastEmitted = plain
  emit('update:modelValue', plain)
}

function snap(value: number) {
  return snapToGrid.value ? Math.round(value / GRID_STEP) * GRID_STEP : Math.round(value)
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

function addZone() {
  const cascade = (zones.value.length % 8) * 24
  const color = PALETTE[zones.value.length % PALETTE.length]
  const zone: EditorZone = {
    _key: nextKey(),
    name: '',
    color,
    x: 24 + cascade,
    y: 24 + cascade,
    width: 280,
    height: 180,
  }
  zones.value.push(zone)
  selectedKey.value = zone._key
  commit()
  nextTick(() => {
    const input = document.getElementById(`zone-name-${zone._key}`) as HTMLInputElement | null
    input?.focus()
  })
}

function removeZone(key: string) {
  zones.value = zones.value.filter((z) => z._key !== key)
  commit()
}

function clearAll() {
  if (zones.value.length && !confirm('Remove every zone from the canvas?')) return
  zones.value = []
  commit()
}

// --- Drag to move ---
let dragState: { key: string; startX: number; startY: number; zoneX: number; zoneY: number } | null = null

function startDrag(event: PointerEvent, zone: EditorZone) {
  if ((event.target as HTMLElement).closest('.zone-box__handle, .zone-box__delete, .zone-box__input, .zone-box__swatch')) return
  selectedKey.value = zone._key
  dragState = { key: zone._key, startX: event.clientX, startY: event.clientY, zoneX: zone.x, zoneY: zone.y }
  ;(event.target as HTMLElement).setPointerCapture(event.pointerId)
  window.addEventListener('pointermove', onDragMove)
  window.addEventListener('pointerup', onDragEnd)
}

function onDragMove(event: PointerEvent) {
  if (!dragState) return
  const zone = zones.value.find((z) => z._key === dragState!.key)
  if (!zone) return
  const dx = event.clientX - dragState.startX
  const dy = event.clientY - dragState.startY
  zone.x = clamp(snap(dragState.zoneX + dx), 0, CANVAS_WIDTH - zone.width)
  zone.y = clamp(snap(dragState.zoneY + dy), 0, CANVAS_HEIGHT - zone.height)
}

function onDragEnd() {
  dragState = null
  window.removeEventListener('pointermove', onDragMove)
  window.removeEventListener('pointerup', onDragEnd)
  commit()
}

// --- Resize handle ---
let resizeState: { key: string; startX: number; startY: number; w: number; h: number } | null = null

function startResize(event: PointerEvent, zone: EditorZone) {
  event.stopPropagation()
  selectedKey.value = zone._key
  resizeState = { key: zone._key, startX: event.clientX, startY: event.clientY, w: zone.width, h: zone.height }
  ;(event.target as HTMLElement).setPointerCapture(event.pointerId)
  window.addEventListener('pointermove', onResizeMove)
  window.addEventListener('pointerup', onResizeEnd)
}

function onResizeMove(event: PointerEvent) {
  if (!resizeState) return
  const zone = zones.value.find((z) => z._key === resizeState!.key)
  if (!zone) return
  const dx = event.clientX - resizeState.startX
  const dy = event.clientY - resizeState.startY
  zone.width = clamp(snap(resizeState.w + dx), MIN_SIZE, CANVAS_WIDTH - zone.x)
  zone.height = clamp(snap(resizeState.h + dy), MIN_SIZE, CANVAS_HEIGHT - zone.y)
}

function onResizeEnd() {
  resizeState = null
  window.removeEventListener('pointermove', onResizeMove)
  window.removeEventListener('pointerup', onResizeEnd)
  commit()
}

onBeforeUnmount(() => {
  window.removeEventListener('pointermove', onDragMove)
  window.removeEventListener('pointerup', onDragEnd)
  window.removeEventListener('pointermove', onResizeMove)
  window.removeEventListener('pointerup', onResizeEnd)
})

defineExpose({ addZone, clearAll })
</script>
