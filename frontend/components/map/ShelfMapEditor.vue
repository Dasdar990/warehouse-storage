<script setup lang="ts">
import type { ShelfNode, Zone } from '~/composables/useWarehouseApi'

/**
 * Freeform drag-and-drop canvas for placing racks ("scaffali") on the
 * warehouse map. Each rack is an absolutely-positioned box the user can
 * drag, resize, rename, assign to a zone, and give one or more levels
 * ("mensole", e.g. "A,B,C"). The parent page owns the `nodes` array and
 * persists it to the backend; this component only edits it in place.
 * Saved zones are rendered underneath as a non-interactive backdrop so
 * racks can be positioned inside the right zone.
 */

interface EditorNode extends ShelfNode {
  _key: string
}

const props = defineProps<{
  modelValue: ShelfNode[]
  zones: Zone[]
}>()

const emit = defineEmits<{ 'update:modelValue': [ShelfNode[]] }>()

const CANVAS_WIDTH = 1400
const CANVAS_HEIGHT = 760
const MIN_SIZE = 40
const GRID_STEP = 20

let keySeed = 0
function nextKey() {
  keySeed += 1
  return `n${Date.now()}-${keySeed}`
}

const nodes = ref<EditorNode[]>(props.modelValue.map((n) => ({ ...n, _key: nextKey() })))
const snapToGrid = ref(true)
const selectedKey = ref<string | null>(null)

// Keep local editor state in sync if the parent swaps the whole array
// (e.g. after loading from the API or after "Generate from stock").
watch(
  () => props.modelValue,
  (value) => {
    if (value.length !== nodes.value.length || value !== lastEmitted) {
      nodes.value = value.map((n) => ({ ...n, _key: nextKey() }))
    }
  }
)

let lastEmitted: ShelfNode[] | null = null
function commit() {
  const plain = nodes.value.map(({ _key, ...rest }) => rest)
  lastEmitted = plain
  emit('update:modelValue', plain)
}

function snap(value: number) {
  return snapToGrid.value ? Math.round(value / GRID_STEP) * GRID_STEP : Math.round(value)
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

function addShelf() {
  const cascade = (nodes.value.length % 8) * 24
  const node: EditorNode = {
    _key: nextKey(),
    rack_code: '',
    label: null,
    x: 24 + cascade,
    y: 24 + cascade,
    width: 90,
    height: 140,
    levels: ['A'],
    zone_id: null,
    // editor-only helper field kept in sync with `levels`, see levelsText()
  } as EditorNode
  nodes.value.push(node)
  selectedKey.value = node._key
  commit()
  nextTick(() => {
    const input = document.getElementById(`shelf-name-${node._key}`) as HTMLInputElement | null
    input?.focus()
  })
}

function removeShelf(key: string) {
  nodes.value = nodes.value.filter((n) => n._key !== key)
  commit()
}

function clearAll() {
  if (nodes.value.length && !confirm('Remove every rack from the canvas?')) return
  nodes.value = []
  commit()
}

// --- Levels text input helpers ("A,B,C" <-> string[]) ---
function levelsText(node: EditorNode) {
  return node.levels.join(',')
}

function onLevelsChange(node: EditorNode, raw: string) {
  const parsed = raw
    .split(',')
    .map((s) => s.trim().toUpperCase())
    .filter(Boolean)
  node.levels = parsed.length ? Array.from(new Set(parsed)) : ['A']
  commit()
}

function zoneName(zoneId: number | null) {
  if (zoneId == null) return null
  return props.zones.find((z) => z.id === zoneId)?.name ?? null
}

// --- Drag to move ---
let dragState: { key: string; startX: number; startY: number; nodeX: number; nodeY: number } | null = null

function startDrag(event: PointerEvent, node: EditorNode) {
  if ((event.target as HTMLElement).closest('.shelf-box__handle, .shelf-box__delete, .shelf-box__field')) return
  selectedKey.value = node._key
  dragState = { key: node._key, startX: event.clientX, startY: event.clientY, nodeX: node.x, nodeY: node.y }
  ;(event.target as HTMLElement).setPointerCapture(event.pointerId)
  window.addEventListener('pointermove', onDragMove)
  window.addEventListener('pointerup', onDragEnd)
}

function onDragMove(event: PointerEvent) {
  if (!dragState) return
  const node = nodes.value.find((n) => n._key === dragState!.key)
  if (!node) return
  const dx = event.clientX - dragState.startX
  const dy = event.clientY - dragState.startY
  node.x = clamp(snap(dragState.nodeX + dx), 0, CANVAS_WIDTH - node.width)
  node.y = clamp(snap(dragState.nodeY + dy), 0, CANVAS_HEIGHT - node.height)
}

function onDragEnd() {
  dragState = null
  window.removeEventListener('pointermove', onDragMove)
  window.removeEventListener('pointerup', onDragEnd)
  commit()
}

// --- Resize handle ---
let resizeState: { key: string; startX: number; startY: number; w: number; h: number } | null = null

function startResize(event: PointerEvent, node: EditorNode) {
  event.stopPropagation()
  selectedKey.value = node._key
  resizeState = { key: node._key, startX: event.clientX, startY: event.clientY, w: node.width, h: node.height }
  ;(event.target as HTMLElement).setPointerCapture(event.pointerId)
  window.addEventListener('pointermove', onResizeMove)
  window.addEventListener('pointerup', onResizeEnd)
}

function onResizeMove(event: PointerEvent) {
  if (!resizeState) return
  const node = nodes.value.find((n) => n._key === resizeState!.key)
  if (!node) return
  const dx = event.clientX - resizeState.startX
  const dy = event.clientY - resizeState.startY
  node.width = clamp(snap(resizeState.w + dx), MIN_SIZE, CANVAS_WIDTH - node.x)
  node.height = clamp(snap(resizeState.h + dy), MIN_SIZE, CANVAS_HEIGHT - node.y)
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

defineExpose({ addShelf, clearAll })
</script>

<template>
  <div class="editor">
    <div class="editor__toolbar">
      <button class="btn btn--confirm" type="button" @click="addShelf">+ Add rack</button>
      <label class="snap-toggle">
        <input v-model="snapToGrid" type="checkbox" />
        Snap to grid
      </label>
      <button class="btn btn--ghost" type="button" :disabled="!nodes.length" @click="clearAll">
        Clear canvas
      </button>
      <span class="editor__count">{{ nodes.length }} rack(s)</span>
    </div>

    <div class="canvas-scroll scrollbar-slim">
      <div
        class="canvas"
        :class="{ 'canvas--snap': snapToGrid }"
        :style="{ width: `${CANVAS_WIDTH}px`, height: `${CANVAS_HEIGHT}px` }"
        @pointerdown="selectedKey = null"
      >
        <!-- Read-only zone backdrop, for visual reference only -->
        <div
          v-for="zone in zones"
          :key="`zone-bg-${zone.id}`"
          class="zone-backdrop"
          :style="{
            left: `${zone.x}px`,
            top: `${zone.y}px`,
            width: `${zone.width}px`,
            height: `${zone.height}px`,
            background: `${zone.color}14`,
            borderColor: `${zone.color}55`,
          }"
        >
          <span class="zone-backdrop__label" :style="{ color: zone.color }">{{ zone.name }}</span>
        </div>

        <div
          v-for="node in nodes"
          :key="node._key"
          class="shelf-box"
          :class="{ 'shelf-box--selected': selectedKey === node._key, 'shelf-box--invalid': !node.rack_code }"
          :style="{ left: `${node.x}px`, top: `${node.y}px`, width: `${node.width}px`, height: `${node.height}px` }"
          @pointerdown.stop="startDrag($event, node)"
        >
          <button class="shelf-box__delete" type="button" title="Remove rack" @pointerdown.stop @click="removeShelf(node._key)">
            ×
          </button>
          <input
            :id="`shelf-name-${node._key}`"
            v-model="node.rack_code"
            class="shelf-box__field shelf-box__input"
            type="text"
            placeholder="e.g. 12"
            maxlength="8"
            @pointerdown.stop
            @change="commit"
          />
          <input
            :value="levelsText(node)"
            class="shelf-box__field shelf-box__levels"
            type="text"
            title="Levels / mensole, comma separated"
            placeholder="A,B,C"
            @pointerdown.stop
            @change="onLevelsChange(node, ($event.target as HTMLInputElement).value)"
          />
          <select
            v-model.number="node.zone_id"
            class="shelf-box__field shelf-box__zone"
            @pointerdown.stop
            @change="commit"
          >
            <option :value="null">No zone</option>
            <option v-for="zone in zones" :key="zone.id" :value="zone.id">{{ zone.name }}</option>
          </select>
          <div class="shelf-box__handle" @pointerdown.stop="startResize($event, node)"></div>
        </div>
      </div>
    </div>

    <p class="editor__hint">
      Drag a rack to move it, drag its bottom-right corner to resize. Give it a numeric code (must match the
      shelf codes used on items, e.g. "12"), the levels/mensole it has (e.g. "A,B,C,D"), and optionally a
      zone. Click "Save layout" above when done.
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

.zone-backdrop {
  position: absolute;
  border: 2px dashed;
  border-radius: 10px;
  pointer-events: none;
  padding: 6px 8px;
}

.zone-backdrop__label {
  font-size: 0.72rem;
  font-weight: 700;
  opacity: 0.85;
}

.shelf-box {
  position: absolute;
  background: rgba(59, 130, 246, 0.16);
  border: 1px solid rgba(59, 130, 246, 0.55);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: grab;
  touch-action: none;
  user-select: none;
  padding: 4px;
  z-index: 1;
}

.shelf-box:active {
  cursor: grabbing;
}

.shelf-box--selected {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  z-index: 2;
}

.shelf-box--invalid {
  border-color: rgba(239, 68, 68, 0.6);
  background: rgba(239, 68, 68, 0.12);
}

.shelf-box__field {
  width: 90%;
  text-align: center;
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  font-size: 0.72rem;
  padding: 2px 4px;
  pointer-events: auto;
}

.shelf-box__input {
  font-weight: 700;
  font-size: 0.75rem;
}

.shelf-box__levels {
  font-size: 0.68rem;
  letter-spacing: 0.03em;
}

.shelf-box__zone {
  font-size: 0.65rem;
  max-width: 90%;
}

.shelf-box__delete {
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

.shelf-box__delete:hover {
  color: #fca5a5;
  border-color: rgba(239, 68, 68, 0.6);
}

.shelf-box__handle {
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
