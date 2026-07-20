<template>
  <div class="flex flex-col gap-3">
    <div class="flex flex-wrap items-center gap-3.5">
      <button
        class="btn btn--confirm text-[#06280f]"
        type="button"
        @click="addRack"
      >
        + Add rack
      </button>
      <label class="flex items-center gap-1.5 text-[0.85rem] text-muted">
        <input v-model="snapToGrid" type="checkbox" />
        Snap to grid
      </label>
      <button
        class="btn btn--ghost disabled:cursor-not-allowed disabled:opacity-50"
        type="button"
        :disabled="!racks.length"
        @click="clearAll"
      >
        Clear canvas
      </button>
      <span class="ml-auto text-[0.8rem] text-muted"
        >{{ racks.length }} rack(s)</span
      >
    </div>

    <div
      class="flex flex-wrap items-center gap-2.5 rounded-card border border-edge bg-surface-2 px-3.5 py-2.5"
    >
      <span class="mr-1 text-[0.8rem] text-muted"
        >Drag a rack onto the map to place it:</span
      >
      <div
        v-for="preset in RACK_PRESETS"
        :key="preset.key"
        class="flex cursor-grab select-none items-center gap-2 rounded-lg border border-edge bg-surface px-3 py-2 text-[0.82rem] active:cursor-grabbing"
        draggable="true"
        @dragstart="onPaletteDragStart($event, preset)"
      >
        <span
          class="inline-block shrink-0 rounded-sm border-[1.5px] border-accent/80 bg-accent/45"
          :style="{
            width: preset.width / 5 + 'px',
            height: preset.height / 5 + 'px',
          }"
        ></span>
        {{ preset.label }}
      </div>
    </div>

    <div class="flex items-start gap-4">
      <div
        class="scrollbar-slim max-h-[65vh] flex-1 overflow-auto rounded-card border border-edge bg-input bg-[radial-gradient(#2a313c_1px,transparent_1px)] bg-[length:20px_20px]"
        @dragover="onCanvasDragOver"
        @drop="onCanvasDrop"
      >
        <ClientOnly fallback="Loading map…">
          <v-stage
            ref="stageRef"
            :config="{ width: CANVAS_WIDTH, height: CANVAS_HEIGHT }"
            class="block"
            @mousedown="handleStageMouseDown"
            @touchstart="handleStageMouseDown"
          >
            <v-layer>
              <!-- Room outline (walls + door): background context only, for orientation -->
              <v-group :config="{ listening: false }">
                <v-line
                  v-for="(wall, idx) in walls"
                  :key="`bg-wall-${wall.id ?? idx}`"
                  :config="{
                    points: [wall.x1, wall.y1, wall.x2, wall.y2],
                    stroke: '#cbd5e1',
                    strokeWidth: 8,
                    lineCap: 'round',
                  }"
                />
                <v-group
                  v-for="(door, idx) in doors"
                  :key="`bg-door-${door.id ?? idx}`"
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

              <!-- Zone rectangles drawn first, purely as background context -->
              <v-group
                v-for="zone in zones"
                :key="`zone-${zone.id}`"
                :config="{ listening: false }"
              >
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
                    fill:
                      selectedKey === rack._key
                        ? 'rgba(59,130,246,0.65)'
                        : 'rgba(75,85,99,0.75)',
                    stroke:
                      zoneColor(rack.zone_id) ||
                      (selectedKey === rack._key ? '#60a5fa' : '#9ca3af'),
                    strokeWidth: selectedKey === rack._key ? 3 : 2,
                    cornerRadius: 4,
                  }"
                />
                <v-text
                  :config="{
                    text:
                      (rack.label || rack.rack_code) +
                      '\n' +
                      rack.levels.join(','),
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
                  enabledAnchors: [
                    'top-left',
                    'top-right',
                    'bottom-left',
                    'bottom-right',
                  ],
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

      <aside
        class="flex w-[280px] shrink-0 flex-col gap-3 rounded-card border border-edge bg-surface-2 p-4"
      >
        <template v-if="selectedRack">
          <h3 class="m-0 border-b border-edge pb-2 text-[0.95rem]">
            Rack properties
          </h3>

          <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
            <span>Code (numeric, e.g. 12)</span>
            <input
              v-model="selectedRack.rack_code"
              type="text"
              class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
              @change="onFieldChange"
            />
          </label>

          <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
            <span>Label (optional)</span>
            <input
              v-model="selectedRack.label"
              type="text"
              placeholder="e.g. Parts rack"
              class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
              @change="onFieldChange"
            />
          </label>

          <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
            <span>Levels (comma-separated letters)</span>
            <input
              v-model="levelsText"
              type="text"
              placeholder="A,B,C"
              class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
              @change="onFieldChange"
            />
          </label>

          <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
            <span>Zone</span>
            <select
              v-model="selectedRack.zone_id"
              class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
              @change="onFieldChange"
            >
              <option :value="null">No zone</option>
              <option v-for="z in zones" :key="z.id" :value="z.id">
                {{ z.name || "(unnamed)" }}
              </option>
            </select>
          </label>

          <div class="grid grid-cols-2 gap-2.5">
            <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
              <span>Width (px)</span>
              <input
                v-model.number="selectedRack.width"
                type="number"
                min="20"
                class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
                @change="onFieldChange"
              />
            </label>
            <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
              <span>Height (px)</span>
              <input
                v-model.number="selectedRack.height"
                type="number"
                min="20"
                class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
                @change="onFieldChange"
              />
            </label>
          </div>

          <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
            <span>Rotation (degrees °)</span>
            <input
              v-model.number="selectedRack.rotation"
              type="number"
              class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
              @change="onFieldChange"
            />
          </label>

          <div class="flex gap-2">
            <button
              class="btn btn--ghost btn--small flex-1"
              type="button"
              @click="rotateBy(-90)"
            >
              -90°
            </button>
            <button
              class="btn btn--ghost btn--small flex-1"
              type="button"
              @click="rotateBy(90)"
            >
              +90°
            </button>
            <button
              class="btn btn--ghost btn--small flex-1"
              type="button"
              @click="rotateBy(-selectedRack.rotation)"
            >
              Reset
            </button>
          </div>

          <button class="btn btn--danger" type="button" @click="deleteSelected">
            Delete rack
          </button>
        </template>

        <p v-else class="m-0 text-[0.82rem] leading-relaxed text-muted">
          Select a rack on the map to edit its properties, or drag it and use
          the corner handles to resize or rotate it — exactly as it's physically
          placed in the room.
        </p>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DoorInput, ShelfNode, WallInput, ZoneInput } from "~/composables/useWarehouseApi";

interface EditorRack extends ShelfNode {
  _key: string;
}

const props = withDefaults(
  defineProps<{
    modelValue: ShelfNode[];
    zones: (ZoneInput & { id: number })[];
    walls?: (WallInput & { id?: number })[];
    doors?: (DoorInput & { id?: number })[];
  }>(),
  { walls: () => [], doors: () => [] },
);

const emit = defineEmits<{ "update:modelValue": [ShelfNode[]] }>();

const CANVAS_WIDTH = 1400;
const CANVAS_HEIGHT = 760;
const GRID_STEP = 10;

let keySeed = 0;
function nextKey() {
  keySeed += 1;
  return `r${Date.now()}-${keySeed}`;
}

function toEditorRack(node: ShelfNode): EditorRack {
  return { ...node, _key: nextKey() };
}

const racks = ref<EditorRack[]>(props.modelValue.map(toEditorRack));
const selectedKey = ref<string | null>(null);
const snapToGrid = ref(true);
const stageRef = ref<any>(null);
const transformerRef = ref<any>(null);

let lastEmitted: ShelfNode[] | null = null;
watch(
  () => props.modelValue,
  (value) => {
    if (value !== lastEmitted) {
      racks.value = value.map(toEditorRack);
      selectedKey.value = null;
    }
  },
);

function commit() {
  const plain = racks.value.map(({ _key, ...rest }) => rest);
  lastEmitted = plain;
  emit("update:modelValue", plain);
}

const selectedRack = computed(
  () => racks.value.find((r) => r._key === selectedKey.value) || null,
);

const zoneById = computed(() => {
  const map = new Map<number, (typeof props.zones)[number]>();
  for (const z of props.zones) map.set(z.id, z);
  return map;
});

function zoneColor(zoneId: number | null) {
  if (zoneId == null) return null;
  return zoneById.value.get(zoneId)?.color || null;
}

function snap(value: number) {
  return snapToGrid.value
    ? Math.round(value / GRID_STEP) * GRID_STEP
    : Math.round(value);
}

function nextRackCode(): string {
  const used = new Set(racks.value.map((r) => r.rack_code));
  let n = 1;
  while (used.has(String(n))) n += 1;
  return String(n);
}

const RACK_PRESETS = [
  { key: "standard", label: "Standard rack", width: 90, height: 140 },
  { key: "wide", label: "Wide rack", width: 160, height: 70 },
  { key: "tall", label: "Tall rack", width: 70, height: 180 },
] as const;

function createRack(
  x: number,
  y: number,
  width: number,
  height: number,
): EditorRack {
  return {
    _key: nextKey(),
    rack_code: nextRackCode(),
    label: null,
    x,
    y,
    width,
    height,
    levels: ["A"],
    zone_id: null,
    rotation: 0,
  };
}

function addRack() {
  const cascade = (racks.value.length % 8) * 24;
  const rack = createRack(40 + cascade, 40 + cascade, 90, 140);
  racks.value.push(rack);
  selectedKey.value = rack._key;
  commit();
}

// --- Drag-and-drop from the palette onto the canvas ---
function onPaletteDragStart(
  e: DragEvent,
  preset: (typeof RACK_PRESETS)[number],
) {
  e.dataTransfer?.setData("application/json", JSON.stringify(preset));
  if (e.dataTransfer) e.dataTransfer.effectAllowed = "copy";
}

function onCanvasDragOver(e: DragEvent) {
  e.preventDefault();
  if (e.dataTransfer) e.dataTransfer.dropEffect = "copy";
}

function onCanvasDrop(e: DragEvent) {
  e.preventDefault();
  const raw = e.dataTransfer?.getData("application/json");
  if (!raw) return;
  let preset: (typeof RACK_PRESETS)[number];
  try {
    preset = JSON.parse(raw);
  } catch {
    return;
  }
  const stage = stageRef.value?.getStage?.();
  const containerEl: HTMLElement | undefined = stage?.container();
  const rect = containerEl?.getBoundingClientRect();
  const dropX = rect ? e.clientX - rect.left : CANVAS_WIDTH / 2;
  const dropY = rect ? e.clientY - rect.top : CANVAS_HEIGHT / 2;

  const rack = createRack(
    Math.max(0, snap(dropX - preset.width / 2)),
    Math.max(0, snap(dropY - preset.height / 2)),
    preset.width,
    preset.height,
  );
  racks.value.push(rack);
  selectedKey.value = rack._key;
  commit();
}

function selectRack(key: string) {
  selectedKey.value = key;
}

function deleteSelected() {
  if (!selectedKey.value) return;
  racks.value = racks.value.filter((r) => r._key !== selectedKey.value);
  selectedKey.value = null;
  commit();
}

function clearAll() {
  if (racks.value.length && !confirm("Remove every rack from the canvas?"))
    return;
  racks.value = [];
  selectedKey.value = null;
  commit();
}

function handleStageMouseDown(e: any) {
  if (e.target === e.target.getStage()) {
    selectedKey.value = null;
  }
}

// Fired after a drag (position only) or a transform (resize/rotate) ends.
// Konva expresses resizing as a scale change rather than new width/height,
// so we bake the scale back into width/height and reset it to 1 to keep
// subsequent drags/rotations clean.
function handleTransformEnd(e: any, rack: EditorRack) {
  const node = e.target;
  rack.x = snap(node.x());
  rack.y = snap(node.y());
  rack.rotation = Math.round(((node.rotation() % 360) + 360) % 360);
  rack.width = Math.max(20, Math.round(node.width() * node.scaleX()));
  rack.height = Math.max(20, Math.round(node.height() * node.scaleY()));
  node.scaleX(1);
  node.scaleY(1);
  commit();
}

function rotateBy(delta: number) {
  if (!selectedRack.value) return;
  selectedRack.value.rotation = Math.round(
    (((selectedRack.value.rotation + delta) % 360) + 360) % 360,
  );
  commit();
}

// --- Side-panel field helpers ---
const levelsText = computed({
  get: () => selectedRack.value?.levels.join(",") || "",
  set: (value: string) => {
    if (!selectedRack.value) return;
    const parsed = Array.from(
      new Set(
        value
          .split(",")
          .map((s) => s.trim().toUpperCase())
          .filter((s) => s.length > 0),
      ),
    );
    selectedRack.value.levels = parsed;
  },
});

function onFieldChange() {
  commit();
}

watch(selectedKey, async () => {
  await nextTick();
  const transformer = transformerRef.value?.getNode();
  if (!transformer) return;
  if (selectedKey.value) {
    const stage = transformer.getStage();
    const node = stage.findOne("#" + selectedKey.value);
    if (node) {
      transformer.nodes([node]);
      transformer.getLayer().batchDraw();
      return;
    }
  }
  transformer.nodes([]);
  transformer.getLayer().batchDraw();
});

defineExpose({ addRack, clearAll });
</script>
