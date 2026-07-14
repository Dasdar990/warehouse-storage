<script setup lang="ts">
import type { ZoneInput } from '~/composables/useWarehouseApi'

/**
 * Freeform drag-and-drop canvas for delimiting warehouse zones. Each zone
 * is an absolutely-positioned, named, colored rectangle the user can drag,
 * resize, and delete — same interaction pattern as the rack editor, but
 * zones are purely visual/organizational (no code has to match anything).
 */

interface EditorZone extends ZoneInput {
  _key: string
}

const props = defineProps<{
  modelValue: ZoneInput[]
}>()

const emit = defineEmits<{ 'update:modelValue': [ZoneInput[]] }>()

const CANVAS_WIDTH = 1400
const CANVAS_HEIGHT = 760
const MIN_SIZE = 60
const GRID_STEP = 20

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

<template>
  <div class="editor">
    <div class="editor__toolbar">
      <button class="btn btn--confirm" type="button" @click="addZone">+ Add zone</button>
      <label class="snap-toggle">
        <input v-model="snapToGrid" type="checkbox" />
        Snap to grid
      </label>
      <button class="btn btn--ghost" type="button" :disabled="!zones.length" @click="clearAll">
        Clear canvas
      </button>
      <span class="editor__count">{{ zones.length }} zone(s)</span>
    </div>

    <div class="canvas-scroll scrollbar-slim">
      <div
        class="canvas"
        :class="{ 'canvas--snap': snapToGrid }"
        :style="{ width: `${CANVAS_WIDTH}px`, height: `${CANVAS_HEIGHT}px` }"
        @pointerdown="selectedKey = null"
      >
        <div
          v-for="zone in zones"
          :key="zone._key"
          class="zone-box"
          :class="{ 'zone-box--selected': selectedKey === zone._key, 'zone-box--invalid': !zone.name }"
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
          <button class="zone-box__delete" type="button" title="Remove zone" @pointerdown.stop @click="removeZone(zone._key)">
            ×
          </button>
          <div class="zone-box__header">
            <input
              :id="`zone-name-${zone._key}`"
              v-model="zone.name"
              class="zone-box__input"
              type="text"
              placeholder="e.g. Zona ricambi"
              maxlength="60"
              @pointerdown.stop
              @change="commit"
            />
            <input
              v-model="zone.color"
              class="zone-box__swatch"
              type="color"
              title="Zone color"
              @pointerdown.stop
              @change="commit"
            />
          </div>
          <div class="zone-box__handle" @pointerdown.stop="startResize($event, zone)"></div>
        </div>
      </div>
    </div>

    <p class="editor__hint">
      Drag a zone to move it, drag its bottom-right corner to resize, and give it a name — this is purely
      visual and helps you group racks (e.g. "Zona ricambi motore"). Click "Save layout" above when done.
    </p>
  </div>
</template>

<style scoped>
.editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.editor__toolbar {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.snap-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-dim);
  font-size: 0.85rem;
}

.editor__count {
  margin-left: auto;
  color: var(--text-dim);
  font-size: 0.8rem;
}

.btn {
  cursor: pointer;
  border: none;
  border-radius: 8px;
  padding: 9px 16px;
  font-weight: 600;
  font-size: 0.85rem;
}

.btn--confirm {
  background: var(--green);
  color: #06280f;
}

.btn--ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.canvas-scroll {
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: #0a0e14;
  max-height: 65vh;
}

.canvas {
  position: relative;
  background-image: radial-gradient(var(--border) 1px, transparent 1px);
  background-size: 20px 20px;
}

.zone-box {
  position: absolute;
  border: 2px dashed;
  border-radius: 10px;
  cursor: grab;
  touch-action: none;
  user-select: none;
  padding: 8px;
}

.zone-box:active {
  cursor: grabbing;
}

.zone-box--selected {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  z-index: 2;
}

.zone-box--invalid {
  border-color: rgba(239, 68, 68, 0.6) !important;
}

.zone-box__header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.zone-box__input {
  flex: 1;
  min-width: 0;
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  font-weight: 700;
  font-size: 0.78rem;
  padding: 4px 6px;
  pointer-events: auto;
}

.zone-box__swatch {
  width: 24px;
  height: 24px;
  padding: 0;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  pointer-events: auto;
  flex-shrink: 0;
}

.zone-box__delete {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  color: var(--text-dim);
  cursor: pointer;
  line-height: 1;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.zone-box__delete:hover {
  color: #fca5a5;
  border-color: rgba(239, 68, 68, 0.6);
}

.zone-box__handle {
  position: absolute;
  right: 2px;
  bottom: 2px;
  width: 12px;
  height: 12px;
  cursor: se-resize;
  border-right: 2px solid var(--text-dim);
  border-bottom: 2px solid var(--text-dim);
  opacity: 0.6;
}

.editor__hint {
  margin: 0;
  color: var(--text-dim);
  font-size: 0.8rem;
}
</style>
