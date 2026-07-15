<script setup lang="ts">
import type { ShelfNode, ZoneInput } from '~/composables/useWarehouseApi'

/**
 * Konva-based freeform canvas for placing racks ("scaffali") exactly as
 * they physically sit in the room: drag to position, use the transformer
 * handles to resize and -- unlike the plain zone editor -- rotate. Same
 * coordinate space (1400x760) as ZoneMapEditor so zones drawn there line
 * up visually as background context here.
 */

interface EditorRack extends ShelfNode {
  _key: string
}

const props = defineProps<{
  modelValue: ShelfNode[]
  zones: (ZoneInput & { id: number })[]
}>()

const emit = defineEmits<{ 'update:modelValue': [ShelfNode[]] }>()

const CANVAS_WIDTH = 1400
const CANVAS_HEIGHT = 760
const GRID_STEP = 10

let keySeed = 0
function nextKey() {
  keySeed += 1
  return `r${Date.now()}-${keySeed}`
}

function toEditorRack(node: ShelfNode): EditorRack {
  return { ...node, _key: nextKey() }
}

const racks = ref<EditorRack[]>(props.modelValue.map(toEditorRack))
const selectedKey = ref<string | null>(null)
const snapToGrid = ref(true)
const stageRef = ref<any>(null)
const transformerRef = ref<any>(null)

let lastEmitted: ShelfNode[] | null = null
watch(
  () => props.modelValue,
  (value) => {
    if (value !== lastEmitted) {
      racks.value = value.map(toEditorRack)
      selectedKey.value = null
    }
  }
)

function commit() {
  const plain = racks.value.map(({ _key, ...rest }) => rest)
  lastEmitted = plain
  emit('update:modelValue', plain)
}

const selectedRack = computed(() => racks.value.find((r) => r._key === selectedKey.value) || null)

const zoneById = computed(() => {
  const map = new Map<number, (typeof props.zones)[number]>()
  for (const z of props.zones) map.set(z.id, z)
  return map
})

function zoneColor(zoneId: number | null) {
  if (zoneId == null) return null
  return zoneById.value.get(zoneId)?.color || null
}

function snap(value: number) {
  return snapToGrid.value ? Math.round(value / GRID_STEP) * GRID_STEP : Math.round(value)
}

function nextRackCode(): string {
  const used = new Set(racks.value.map((r) => r.rack_code))
  let n = 1
  while (used.has(String(n))) n += 1
  return String(n)
}

const RACK_PRESETS = [
  { key: 'standard', label: 'Scaffale standard', width: 90, height: 140 },
  { key: 'wide', label: 'Scaffale largo', width: 160, height: 70 },
  { key: 'tall', label: 'Scaffale alto', width: 70, height: 180 },
] as const

function createRack(x: number, y: number, width: number, height: number): EditorRack {
  return {
    _key: nextKey(),
    rack_code: nextRackCode(),
    label: null,
    x,
    y,
    width,
    height,
    levels: ['A'],
    zone_id: null,
    rotation: 0,
  }
}

function addRack() {
  const cascade = (racks.value.length % 8) * 24
  const rack = createRack(40 + cascade, 40 + cascade, 90, 140)
  racks.value.push(rack)
  selectedKey.value = rack._key
  commit()
}

// --- Drag-and-drop from the palette onto the canvas ---
function onPaletteDragStart(e: DragEvent, preset: (typeof RACK_PRESETS)[number]) {
  e.dataTransfer?.setData('application/json', JSON.stringify(preset))
  if (e.dataTransfer) e.dataTransfer.effectAllowed = 'copy'
}

function onCanvasDragOver(e: DragEvent) {
  e.preventDefault()
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy'
}

function onCanvasDrop(e: DragEvent) {
  e.preventDefault()
  const raw = e.dataTransfer?.getData('application/json')
  if (!raw) return
  let preset: (typeof RACK_PRESETS)[number]
  try {
    preset = JSON.parse(raw)
  } catch {
    return
  }
  const stage = stageRef.value?.getStage?.()
  const containerEl: HTMLElement | undefined = stage?.container()
  const rect = containerEl?.getBoundingClientRect()
  const dropX = rect ? e.clientX - rect.left : CANVAS_WIDTH / 2
  const dropY = rect ? e.clientY - rect.top : CANVAS_HEIGHT / 2

  const rack = createRack(
    Math.max(0, snap(dropX - preset.width / 2)),
    Math.max(0, snap(dropY - preset.height / 2)),
    preset.width,
    preset.height
  )
  racks.value.push(rack)
  selectedKey.value = rack._key
  commit()
}

function selectRack(key: string) {
  selectedKey.value = key
}

function deleteSelected() {
  if (!selectedKey.value) return
  racks.value = racks.value.filter((r) => r._key !== selectedKey.value)
  selectedKey.value = null
  commit()
}

function clearAll() {
  if (racks.value.length && !confirm('Remove every rack from the canvas?')) return
  racks.value = []
  selectedKey.value = null
  commit()
}

function handleStageMouseDown(e: any) {
  if (e.target === e.target.getStage()) {
    selectedKey.value = null
  }
}

// Fired after a drag (position only) or a transform (resize/rotate) ends.
// Konva expresses resizing as a scale change rather than new width/height,
// so we bake the scale back into width/height and reset it to 1 to keep
// subsequent drags/rotations clean.
function handleTransformEnd(e: any, rack: EditorRack) {
  const node = e.target
  rack.x = snap(node.x())
  rack.y = snap(node.y())
  rack.rotation = Math.round(((node.rotation() % 360) + 360) % 360)
  rack.width = Math.max(20, Math.round(node.width() * node.scaleX()))
  rack.height = Math.max(20, Math.round(node.height() * node.scaleY()))
  node.scaleX(1)
  node.scaleY(1)
  commit()
}

function rotateBy(delta: number) {
  if (!selectedRack.value) return
  selectedRack.value.rotation = Math.round(((selectedRack.value.rotation + delta) % 360 + 360) % 360)
  commit()
}

// --- Side-panel field helpers ---
const levelsText = computed({
  get: () => selectedRack.value?.levels.join(',') || '',
  set: (value: string) => {
    if (!selectedRack.value) return
    const parsed = Array.from(
      new Set(
        value
          .split(',')
          .map((s) => s.trim().toUpperCase())
          .filter((s) => s.length > 0)
      )
    )
    selectedRack.value.levels = parsed
  },
})

function onFieldChange() {
  commit()
}

watch(selectedKey, async () => {
  await nextTick()
  const transformer = transformerRef.value?.getNode()
  if (!transformer) return
  if (selectedKey.value) {
    const stage = transformer.getStage()
    const node = stage.findOne('#' + selectedKey.value)
    if (node) {
      transformer.nodes([node])
      transformer.getLayer().batchDraw()
      return
    }
  }
  transformer.nodes([])
  transformer.getLayer().batchDraw()
})

defineExpose({ addRack, clearAll })
</script>

<template>
  <div class="editor">
    <div class="editor__toolbar">
      <button class="btn btn--confirm" type="button" @click="addRack">+ Aggiungi scaffale</button>
      <label class="snap-toggle">
        <input v-model="snapToGrid" type="checkbox" />
        Snap to grid
      </label>
      <button class="btn btn--ghost" type="button" :disabled="!racks.length" @click="clearAll">
        Clear canvas
      </button>
      <span class="editor__count">{{ racks.length }} scaffale/i</span>
    </div>

    <div class="palette">
      <span class="palette__hint">Trascina uno scaffale sulla mappa per posizionarlo:</span>
      <div
        v-for="preset in RACK_PRESETS"
        :key="preset.key"
        class="palette__item"
        draggable="true"
        @dragstart="onPaletteDragStart($event, preset)"
      >
        <span class="palette__swatch" :style="{ width: preset.width / 5 + 'px', height: preset.height / 5 + 'px' }"></span>
        {{ preset.label }}
      </div>
    </div>

    <div class="editor__body">
      <div class="canvas-scroll scrollbar-slim" @dragover="onCanvasDragOver" @drop="onCanvasDrop">
        <ClientOnly fallback="Caricamento mappa in corso...">
          <v-stage
            ref="stageRef"
            :config="{ width: CANVAS_WIDTH, height: CANVAS_HEIGHT }"
            class="stage"
            @mousedown="handleStageMouseDown"
            @touchstart="handleStageMouseDown"
          >
            <v-layer>
              <!-- Zone rectangles drawn first, purely as background context -->
              <v-group v-for="zone in zones" :key="`zone-${zone.id}`" :config="{ listening: false }">
                <v-rect
                  :config="{
                    x: zone.x,
                    y: zone.y,
                    width: zone.width,
                    height: zone.height,
                    fill: zone.color + '18',
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

              <!-- Racks -->
              <v-group
                v-for="rack in racks"
                :key="rack._key"
                :config="{
                  id: rack._key,
                  x: rack.x,
                  y: rack.y,
                  width: rack.width,
                  height: rack.height,
                  rotation: rack.rotation,
                  draggable: true,
                }"
                @dragend="handleTransformEnd($event, rack)"
                @transformend="handleTransformEnd($event, rack)"
                @click="selectRack(rack._key)"
                @tap="selectRack(rack._key)"
              >
                <v-rect
                  :config="{
                    width: rack.width,
                    height: rack.height,
                    fill: selectedKey === rack._key ? 'rgba(59,130,246,0.65)' : 'rgba(75,85,99,0.75)',
                    stroke: zoneColor(rack.zone_id) || (selectedKey === rack._key ? '#60a5fa' : '#9ca3af'),
                    strokeWidth: selectedKey === rack._key ? 3 : 2,
                    cornerRadius: 4,
                  }"
                />
                <v-text
                  :config="{
                    text: (rack.label || rack.rack_code) + '\n' + rack.levels.join(','),
                    fontSize: 12,
                    fontFamily: 'Segoe UI, Arial',
                    fill: '#ffffff',
                    width: rack.width,
                    height: rack.height,
                    align: 'center',
                    verticalAlign: 'middle',
                    listening: false,
                  }"
                />
              </v-group>

              <v-transformer
                ref="transformerRef"
                :config="{
                  enabledAnchors: ['top-left', 'top-right', 'bottom-left', 'bottom-right'],
                  rotateEnabled: true,
                  keepRatio: false,
                  anchorStroke: '#60a5fa',
                  anchorFill: '#ffffff',
                  borderStroke: '#3b82f6',
                }"
              />
            </v-layer>
          </v-stage>
        </ClientOnly>
      </div>

      <aside class="panel">
        <template v-if="selectedRack">
          <h3 class="panel__title">Proprietà scaffale</h3>

          <label class="field">
            <span>Codice (numerico, es. 12)</span>
            <input v-model="selectedRack.rack_code" type="text" @change="onFieldChange" />
          </label>

          <label class="field">
            <span>Etichetta (opzionale)</span>
            <input v-model="selectedRack.label" type="text" placeholder="es. Scaffale ricambi" @change="onFieldChange" />
          </label>

          <label class="field">
            <span>Mensole (lettere separate da virgola)</span>
            <input v-model="levelsText" type="text" placeholder="A,B,C" @change="onFieldChange" />
          </label>

          <label class="field">
            <span>Zona</span>
            <select v-model="selectedRack.zone_id" @change="onFieldChange">
              <option :value="null">Nessuna zona</option>
              <option v-for="z in zones" :key="z.id" :value="z.id">{{ z.name || '(senza nome)' }}</option>
            </select>
          </label>

          <div class="field-row">
            <label class="field">
              <span>Larghezza (px)</span>
              <input v-model.number="selectedRack.width" type="number" min="20" @change="onFieldChange" />
            </label>
            <label class="field">
              <span>Altezza (px)</span>
              <input v-model.number="selectedRack.height" type="number" min="20" @change="onFieldChange" />
            </label>
          </div>

          <label class="field">
            <span>Rotazione (gradi °)</span>
            <input v-model.number="selectedRack.rotation" type="number" @change="onFieldChange" />
          </label>

          <div class="rotate-quick">
            <button class="btn btn--ghost btn--small" type="button" @click="rotateBy(-90)">-90°</button>
            <button class="btn btn--ghost btn--small" type="button" @click="rotateBy(90)">+90°</button>
            <button class="btn btn--ghost btn--small" type="button" @click="rotateBy(-selectedRack.rotation)">
              Reset
            </button>
          </div>

          <button class="btn btn--danger" type="button" @click="deleteSelected">Elimina scaffale</button>
        </template>
        <p v-else class="panel__hint">
          Seleziona uno scaffale sulla mappa per modificarne le proprietà, oppure trascinalo e usa le maniglie
          agli angoli per ridimensionarlo o ruotarlo — esattamente come è posizionato fisicamente nella stanza.
        </p>
      </aside>
    </div>
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

.palette {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  background: var(--bg-elevated-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px 14px;
}

.palette__hint {
  color: var(--text-dim);
  font-size: 0.8rem;
  margin-right: 4px;
}

.palette__item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: grab;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 0.82rem;
  user-select: none;
}

.palette__item:active {
  cursor: grabbing;
}

.palette__swatch {
  display: inline-block;
  background: rgba(59, 130, 246, 0.45);
  border: 1.5px solid rgba(59, 130, 246, 0.8);
  border-radius: 2px;
  flex-shrink: 0;
}

.editor__body {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.canvas-scroll {
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background-color: #0a0e14;
  background-image: radial-gradient(var(--border) 1px, transparent 1px);
  background-size: 20px 20px;
  max-height: 65vh;
  flex: 1;
}

.stage {
  display: block;
}

.panel {
  width: 280px;
  flex-shrink: 0;
  background: var(--bg-elevated-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.panel__title {
  font-size: 0.95rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 8px;
  margin: 0;
}

.panel__hint {
  margin: 0;
  color: var(--text-dim);
  font-size: 0.82rem;
  line-height: 1.5;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.8rem;
  color: var(--text-dim);
}

.field input,
.field select {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 7px 9px;
  color: var(--text);
  font-size: 0.85rem;
  font-family: inherit;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.rotate-quick {
  display: flex;
  gap: 8px;
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

.btn--small {
  padding: 6px 10px;
  font-size: 0.78rem;
  flex: 1;
}

.btn--danger {
  background: var(--red-dim);
  color: #fca5a5;
  border: 1px solid rgba(239, 68, 68, 0.5);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
