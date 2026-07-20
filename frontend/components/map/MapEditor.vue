<template>
  <div class="flex flex-col gap-3">
    <div class="flex flex-wrap items-center gap-3.5">
      <button class="btn btn--confirm text-[#06280f]" type="button" @click="addZone">
        + Add zone
      </button>
      <label class="flex items-center gap-1.5 text-[0.85rem] text-muted">
        <input v-model="snapToGrid" type="checkbox" />
        Snap to grid
      </label>
      <button
        class="btn btn--ghost disabled:cursor-not-allowed disabled:opacity-50"
        type="button"
        :disabled="!hasAnything"
        @click="clearAll"
      >
        Clear canvas
      </button>
      <span class="ml-auto text-[0.8rem] text-muted">
        {{ zones.length }} zone(s) · {{ walls.length }} wall(s) · {{ doors.length }} door(s) ·
        {{ racks.length }} rack(s)
      </span>
    </div>

    <div
      class="flex flex-wrap items-center gap-2.5 rounded-card border border-edge bg-surface-2 px-3.5 py-2.5"
    >
      <span class="mr-1 text-[0.8rem] text-muted">Drag onto the map to place it:</span>
      <div
        v-for="preset in PALETTE_ITEMS"
        :key="preset.kind"
        class="flex cursor-grab select-none items-center gap-2 rounded-lg border border-edge bg-surface px-3 py-2 text-[0.82rem] active:cursor-grabbing"
        draggable="true"
        @dragstart="onPaletteDragStart($event, preset)"
      >
        <span
          v-if="preset.kind === 'rack'"
          class="inline-block shrink-0 rounded-sm border-[1.5px] border-accent/80 bg-accent/45"
          :style="{ width: preset.width / 5 + 'px', height: preset.height / 5 + 'px' }"
        ></span>
        <span
          v-else-if="preset.kind === 'wall'"
          class="inline-block h-1.5 w-8 shrink-0 rounded-sm bg-[#94a3b8]"
        ></span>
        <span
          v-else
          class="inline-block h-5 w-5 shrink-0 rounded-tr-full border-t-2 border-r-2 border-[#facc15]"
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
              <!-- Zones: background/organizational rectangles -->
              <v-group
                v-for="zone in zones"
                :key="zone._key"
                :config="{
                  id: zone._key,
                  x: zone.x,
                  y: zone.y,
                  width: zone.width,
                  height: zone.height,
                  draggable: true,
                }"
                @dragend="handleTransformEnd($event, zone, 'zone')"
                @transformend="handleTransformEnd($event, zone, 'zone')"
                @click="select('zone', zone._key)"
                @tap="select('zone', zone._key)"
              >
                <v-rect
                  :config="{
                    width: zone.width,
                    height: zone.height,
                    fill: zone.color + '18',
                    stroke: isSelected('zone', zone._key) ? '#60a5fa' : zone.color + '88',
                    strokeWidth: isSelected('zone', zone._key) ? 2.5 : 1.5,
                    dash: [6, 4],
                    cornerRadius: 6,
                  }"
                />
                <v-text
                  :config="{
                    x: 8,
                    y: 6,
                    text: zone.name || '(unnamed zone)',
                    fontSize: 12,
                    fontStyle: 'bold',
                    fill: zone.color,
                    listening: false,
                  }"
                />
              </v-group>

              <!-- Walls: solid partitions with end-caps, same drag/rotate model as racks
                   but resized via dedicated length/thickness handles (see transformerConfig)
                   since corner-only anchors are unusable on a shape this thin. -->
              <v-group
                v-for="wall in walls"
                :key="wall._key"
                :config="{
                  id: wall._key,
                  x: wall.x,
                  y: wall.y,
                  width: wall.width,
                  height: wall.height,
                  rotation: wall.rotation,
                  draggable: true,
                }"
                @dragend="handleTransformEnd($event, wall, 'wall')"
                @transformend="handleTransformEnd($event, wall, 'wall')"
                @click="select('wall', wall._key)"
                @tap="select('wall', wall._key)"
              >
                <!-- End-caps: small perpendicular nubs hinting at a joint/corner -->
                <v-rect
                  :config="{
                    x: -wall.height * 0.35,
                    y: -wall.height * 0.35,
                    width: wall.height * 0.7,
                    height: wall.height * 1.7,
                    fill: isSelected('wall', wall._key) ? '#60a5fa' : '#64748b',
                    cornerRadius: 1,
                  }"
                />
                <v-rect
                  :config="{
                    x: wall.width - wall.height * 0.35,
                    y: -wall.height * 0.35,
                    width: wall.height * 0.7,
                    height: wall.height * 1.7,
                    fill: isSelected('wall', wall._key) ? '#60a5fa' : '#64748b',
                    cornerRadius: 1,
                  }"
                />
                <!-- Main body: beveled fill (light top edge, darker body) for a solid, wall-like read -->
                <v-rect
                  :config="{
                    width: wall.width,
                    height: wall.height,
                    fillLinearGradientStartPoint: { x: 0, y: 0 },
                    fillLinearGradientEndPoint: { x: 0, y: wall.height },
                    fillLinearGradientColorStops: isSelected('wall', wall._key)
                      ? [0, '#bfdbfe', 1, '#60a5fa']
                      : [0, '#e2e8f0', 1, '#94a3b8'],
                    stroke: isSelected('wall', wall._key) ? '#3b82f6' : '#475569',
                    strokeWidth: 1,
                    cornerRadius: 1,
                  }"
                />
                <!-- Center hairline: classic architectural double-line wall symbol -->
                <v-line
                  :config="{
                    points: [0, wall.height / 2, wall.width, wall.height / 2],
                    stroke: isSelected('wall', wall._key) ? '#2563eb' : '#334155',
                    strokeWidth: 1,
                    opacity: 0.5,
                    listening: false,
                  }"
                />
              </v-group>

              <!-- Doors: hinge + swing-arc symbol -->
              <v-group
                v-for="door in doors"
                :key="door._key"
                :config="{
                  id: door._key,
                  x: door.x,
                  y: door.y,
                  width: door.width,
                  height: door.width,
                  rotation: door.rotation,
                  draggable: true,
                }"
                @dragend="handleTransformEnd($event, door, 'door')"
                @transformend="handleTransformEnd($event, door, 'door')"
                @click="select('door', door._key)"
                @tap="select('door', door._key)"
              >
                <v-arc
                  :config="{
                    innerRadius: 0,
                    outerRadius: door.width,
                    angle: 90,
                    stroke: isSelected('door', door._key) ? '#60a5fa' : '#facc15',
                    strokeWidth: 2,
                    dash: [5, 4],
                  }"
                />
                <v-circle
                  :config="{
                    x: 0,
                    y: 0,
                    radius: 4,
                    fill: isSelected('door', door._key) ? '#60a5fa' : '#facc15',
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
                @dragend="handleTransformEnd($event, rack, 'rack')"
                @transformend="handleTransformEnd($event, rack, 'rack')"
                @click="select('rack', rack._key)"
                @tap="select('rack', rack._key)"
              >
                <v-rect
                  :config="{
                    width: rack.width,
                    height: rack.height,
                    fill: isSelected('rack', rack._key)
                      ? 'rgba(59,130,246,0.65)'
                      : 'rgba(75,85,99,0.75)',
                    stroke:
                      zoneColor(rack.zone_id) ||
                      (isSelected('rack', rack._key) ? '#60a5fa' : '#9ca3af'),
                    strokeWidth: isSelected('rack', rack._key) ? 3 : 2,
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

              <v-transformer ref="transformerRef" :config="transformerConfig" />
            </v-layer>
          </v-stage>
        </ClientOnly>
      </div>

      <aside
        class="flex w-[280px] shrink-0 flex-col gap-3 rounded-card border border-edge bg-surface-2 p-4"
      >
        <template v-if="selectedZone">
          <h3 class="m-0 border-b border-edge pb-2 text-[0.95rem]">Zone</h3>
          <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
            <span>Name</span>
            <input
              v-model="selectedZone.name"
              type="text"
              placeholder="e.g. Spare parts zone"
              class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
              @change="commit('zone')"
            />
          </label>
          <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
            <span>Color</span>
            <input
              v-model="selectedZone.color"
              type="color"
              class="h-9 w-full cursor-pointer rounded-lg border border-edge bg-surface p-1"
              @change="commit('zone')"
            />
          </label>
          <button class="btn btn--danger" type="button" @click="deleteSelected">
            Delete zone
          </button>
        </template>

        <template v-else-if="selectedWall">
          <h3 class="m-0 border-b border-edge pb-2 text-[0.95rem]">Wall</h3>
          <p class="m-0 text-[0.82rem] leading-relaxed text-muted">
            Drag to move. On the canvas, use the side handles to stretch its
            length or thickness, or type exact values below.
          </p>

          <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
            <span>Length (px)</span>
            <input
              v-model.number="selectedWall.width"
              type="number"
              min="10"
              step="10"
              class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
              @change="commitWall"
            />
          </label>

          <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
            <span>Thickness (px)</span>
            <input
              v-model.number="selectedWall.height"
              type="number"
              min="4"
              step="2"
              class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
              @change="commitWall"
            />
          </label>

          <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
            <span>Rotation (°)</span>
            <input
              v-model.number="selectedWall.rotation"
              type="number"
              min="0"
              max="359"
              step="15"
              class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
              @change="commitWall"
            />
          </label>

          <div class="flex gap-2">
            <button class="btn btn--ghost btn--small flex-1" type="button" @click="rotateWallBy(-90)">
              ⟲ -90°
            </button>
            <button class="btn btn--ghost btn--small flex-1" type="button" @click="rotateWallBy(90)">
              ⟳ +90°
            </button>
          </div>

          <button class="btn btn--danger" type="button" @click="deleteSelected">
            Delete wall
          </button>
        </template>

        <template v-else-if="selectedDoor">
          <h3 class="m-0 border-b border-edge pb-2 text-[0.95rem]">Door</h3>

          <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
            <span>Width (px)</span>
            <input
              v-model.number="selectedDoor.width"
              type="number"
              min="10"
              class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
              @change="commit('door')"
            />
          </label>

          <div class="flex gap-2">
            <button class="btn btn--ghost btn--small flex-1" type="button" @click="rotateDoorBy(-90)">
              ⟲ -90°
            </button>
            <button class="btn btn--ghost btn--small flex-1" type="button" @click="rotateDoorBy(90)">
              ⟳ +90°
            </button>
          </div>

          <button class="btn btn--danger" type="button" @click="deleteSelected">
            Delete door
          </button>
        </template>

        <template v-else-if="selectedRack">
          <h3 class="m-0 border-b border-edge pb-2 text-[0.95rem]">Rack properties</h3>

          <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
            <span>Code (numeric, e.g. 12)</span>
            <input
              v-model="selectedRack.rack_code"
              type="text"
              class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
              @change="commit('rack')"
            />
          </label>

          <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
            <span>Label (optional)</span>
            <input
              v-model="selectedRack.label"
              type="text"
              placeholder="e.g. Parts rack"
              class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
              @change="commit('rack')"
            />
          </label>

          <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
            <span>Levels (comma-separated letters)</span>
            <input
              v-model="levelsText"
              type="text"
              placeholder="A,B,C"
              class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
              @change="commit('rack')"
            />
          </label>

          <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
            <span>Zone</span>
            <select
              v-model="selectedRack.zone_id"
              class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
              @change="commit('rack')"
            >
              <option :value="null">No zone</option>
              <option v-for="z in zoneRefs" :key="z.id" :value="z.id">
                {{ z.name || "(unnamed)" }}
              </option>
            </select>
          </label>

          <div class="flex gap-2">
            <button class="btn btn--ghost btn--small flex-1" type="button" @click="rotateRackBy(-90)">
              ⟲ -90°
            </button>
            <button class="btn btn--ghost btn--small flex-1" type="button" @click="rotateRackBy(90)">
              ⟳ +90°
            </button>
          </div>

          <button class="btn btn--danger" type="button" @click="deleteSelected">
            Delete rack
          </button>
        </template>

        <p v-else class="m-0 text-[0.82rem] leading-relaxed text-muted">
          Sketch the room first — walls and the door are purely for
          orientation — then delimit zones and place racks inside them.
          Select anything on the map to edit or delete it; drag the corner
          handles to resize, or the top handle to rotate.
        </p>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DoorInput, ShelfNode, WallInput, ZoneInput } from "~/composables/useWarehouseApi";

interface EditorZone extends ZoneInput {
  _key: string;
}
interface EditorWall extends WallInput {
  _key: string;
}
interface EditorDoor extends DoorInput {
  _key: string;
}
interface EditorRack extends ShelfNode {
  _key: string;
}

type Kind = "zone" | "wall" | "door" | "rack";

const props = withDefaults(
  defineProps<{
    zones: ZoneInput[];
    nodes: ShelfNode[];
    walls: WallInput[];
    doors: DoorInput[];
    /** Real (or last-saved) zone ids, positional — used only for the rack's zone dropdown/coloring. */
    zoneIds?: number[];
  }>(),
  { zoneIds: () => [] },
);

const emit = defineEmits<{
  "update:zones": [ZoneInput[]];
  "update:nodes": [ShelfNode[]];
  "update:walls": [WallInput[]];
  "update:doors": [DoorInput[]];
}>();

const CANVAS_WIDTH = 1400;
const CANVAS_HEIGHT = 760;
const GRID_STEP = 10;
const PALETTE = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#a855f7", "#06b6d4", "#ec4899", "#84cc16"];

let keySeed = 0;
function nextKey(prefix: string) {
  keySeed += 1;
  return `${prefix}${Date.now()}-${keySeed}`;
}

const zones = ref<EditorZone[]>(props.zones.map((z) => ({ ...z, _key: nextKey("zone-") })));
const walls = ref<EditorWall[]>(props.walls.map((w) => ({ ...w, _key: nextKey("wall-") })));
const doors = ref<EditorDoor[]>(props.doors.map((d) => ({ ...d, _key: nextKey("door-") })));
const racks = ref<EditorRack[]>(props.nodes.map((n) => ({ ...n, _key: nextKey("rack-") })));

const snapToGrid = ref(true);
const stageRef = ref<any>(null);
const transformerRef = ref<any>(null);
const selected = ref<{ kind: Kind; key: string } | null>(null);

const hasAnything = computed(
  () => zones.value.length > 0 || walls.value.length > 0 || doors.value.length > 0 || racks.value.length > 0,
);

// Each array is watched independently so editing one kind never touches the
// in-progress local state (and unsaved _key identifiers) of the others.
let lastEmittedZones: ZoneInput[] | null = null;
watch(
  () => props.zones,
  (value) => {
    if (value !== lastEmittedZones) {
      zones.value = value.map((z) => ({ ...z, _key: nextKey("zone-") }));
    }
  },
);
let lastEmittedWalls: WallInput[] | null = null;
watch(
  () => props.walls,
  (value) => {
    if (value !== lastEmittedWalls) {
      walls.value = value.map((w) => ({ ...w, _key: nextKey("wall-") }));
    }
  },
);
let lastEmittedDoors: DoorInput[] | null = null;
watch(
  () => props.doors,
  (value) => {
    if (value !== lastEmittedDoors) {
      doors.value = value.map((d) => ({ ...d, _key: nextKey("door-") }));
    }
  },
);
let lastEmittedNodes: ShelfNode[] | null = null;
watch(
  () => props.nodes,
  (value) => {
    if (value !== lastEmittedNodes) {
      racks.value = value.map((n) => ({ ...n, _key: nextKey("rack-") }));
    }
  },
);

function commit(kind: Kind) {
  if (kind === "zone") {
    const plain = zones.value.map(({ _key, ...rest }) => rest);
    lastEmittedZones = plain;
    emit("update:zones", plain);
  } else if (kind === "wall") {
    const plain = walls.value.map(({ _key, ...rest }) => rest);
    lastEmittedWalls = plain;
    emit("update:walls", plain);
  } else if (kind === "door") {
    const plain = doors.value.map(({ _key, ...rest }) => rest);
    lastEmittedDoors = plain;
    emit("update:doors", plain);
  } else {
    const plain = racks.value.map(({ _key, ...rest }) => rest);
    lastEmittedNodes = plain;
    emit("update:nodes", plain);
  }
}

function select(kind: Kind, key: string) {
  selected.value = { kind, key };
}
function isSelected(kind: Kind, key: string) {
  return selected.value?.kind === kind && selected.value?.key === key;
}

const selectedZone = computed(() =>
  selected.value?.kind === "zone" ? zones.value.find((z) => z._key === selected.value!.key) || null : null,
);
const selectedWall = computed(() =>
  selected.value?.kind === "wall" ? walls.value.find((w) => w._key === selected.value!.key) || null : null,
);
const selectedDoor = computed(() =>
  selected.value?.kind === "door" ? doors.value.find((d) => d._key === selected.value!.key) || null : null,
);
const selectedRack = computed(() =>
  selected.value?.kind === "rack" ? racks.value.find((r) => r._key === selected.value!.key) || null : null,
);

// Positional real/placeholder ids so the rack editor's zone dropdown and
// stroke coloring can reference a zone before it has been saved.
const zoneRefs = computed(() =>
  zones.value.map((z, i) => ({ id: props.zoneIds[i] ?? -(i + 1), name: z.name, color: z.color })),
);
function zoneColor(zoneId: number | null) {
  if (zoneId == null) return null;
  return zoneRefs.value.find((z) => z.id === zoneId)?.color || null;
}

function snap(value: number) {
  return snapToGrid.value ? Math.round(value / GRID_STEP) * GRID_STEP : Math.round(value);
}
function normalizeAngle(deg: number) {
  return Math.round(((deg % 360) + 360) % 360);
}

// --- Add ---
function addZone() {
  const cascade = (zones.value.length % 8) * 24;
  const color = PALETTE[zones.value.length % PALETTE.length];
  const zone: EditorZone = {
    _key: nextKey("zone-"),
    name: "",
    color,
    x: 24 + cascade,
    y: 24 + cascade,
    width: 280,
    height: 180,
  };
  zones.value.push(zone);
  select("zone", zone._key);
  commit("zone");
}

function nextRackCode(): string {
  const used = new Set(racks.value.map((r) => r.rack_code));
  let n = 1;
  while (used.has(String(n))) n += 1;
  return String(n);
}

function createRack(x: number, y: number, width: number, height: number): EditorRack {
  return {
    _key: nextKey("rack-"),
    rack_code: nextRackCode(),
    label: null,
    x,
    y,
    width,
    height,
    levels: ["A", "B", "C", "D"],
    zone_id: null,
    rotation: 0,
  };
}

function createWall(x: number, y: number, width: number, height: number): EditorWall {
  return { _key: nextKey("wall-"), x, y, width, height, rotation: 0 };
}

function createDoor(x: number, y: number, width: number): EditorDoor {
  return { _key: nextKey("door-"), x, y, width, rotation: 0 };
}

// Only one rack size is offered for now (4 levels by default); walls and
// doors are placed the same way, by dragging onto the canvas.
const PALETTE_ITEMS = [
  { kind: "rack", label: "Rack (4 levels)", width: 90, height: 140 },
  { kind: "wall", label: "Wall", width: 120, height: 10 },
  { kind: "door", label: "Door", width: 40, height: 40 },
] as const;

function onPaletteDragStart(e: DragEvent, preset: (typeof PALETTE_ITEMS)[number]) {
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
  let preset: (typeof PALETTE_ITEMS)[number];
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
  const x = Math.max(0, snap(dropX - preset.width / 2));
  const y = Math.max(0, snap(dropY - preset.height / 2));

  if (preset.kind === "rack") {
    const rack = createRack(x, y, preset.width, preset.height);
    racks.value.push(rack);
    select("rack", rack._key);
    commit("rack");
  } else if (preset.kind === "wall") {
    const wall = createWall(x, y, preset.width, preset.height);
    walls.value.push(wall);
    select("wall", wall._key);
    commit("wall");
  } else {
    const door = createDoor(x, y, preset.width);
    doors.value.push(door);
    select("door", door._key);
    commit("door");
  }
}

// --- Delete ---
function deleteSelected() {
  if (!selected.value) return;
  const { kind, key } = selected.value;
  if (kind === "zone") zones.value = zones.value.filter((z) => z._key !== key);
  else if (kind === "wall") walls.value = walls.value.filter((w) => w._key !== key);
  else if (kind === "door") doors.value = doors.value.filter((d) => d._key !== key);
  else racks.value = racks.value.filter((r) => r._key !== key);
  selected.value = null;
  commit(kind);
}

function clearAll() {
  if (hasAnything.value && !confirm("Remove every zone, wall, door, and rack from the canvas?")) return;
  zones.value = [];
  walls.value = [];
  doors.value = [];
  racks.value = [];
  selected.value = null;
  commit("zone");
  commit("wall");
  commit("door");
  commit("rack");
}

function handleStageMouseDown(e: any) {
  if (e.target === e.target.getStage()) {
    selected.value = null;
  }
}

// Fired after a drag (position only) or a transform (resize/rotate) ends.
// Konva expresses resizing as a scale change rather than new width/height,
// so we bake the scale back into width/height and reset it to 1 to keep
// subsequent drags/rotations clean. Doors never resize via the transformer
// (no corner anchors), so their `width` stays whatever the side panel set.
function handleTransformEnd(e: any, item: EditorZone | EditorWall | EditorDoor | EditorRack, kind: Kind) {
  const node = e.target;
  item.x = snap(node.x());
  item.y = snap(node.y());

  if (kind === "rack" || kind === "wall" || kind === "door") {
    item.rotation = normalizeAngle(node.rotation());
  }

  const minSize = kind === "zone" ? 60 : kind === "wall" ? 10 : 20;
  if (kind !== "door") {
    (item as EditorZone | EditorWall | EditorRack).width = Math.max(
      minSize,
      Math.round(node.width() * node.scaleX()),
    );
    (item as EditorZone | EditorWall | EditorRack).height = Math.max(
      kind === "wall" ? 4 : minSize,
      Math.round(node.height() * node.scaleY()),
    );
  }
  node.scaleX(1);
  node.scaleY(1);
  commit(kind);
}

// Typed inputs bypass the transformer entirely, so clamp defensively here
// too (the <input min> attribute alone doesn't stop a typed/pasted value).
function commitWall() {
  if (!selectedWall.value) return;
  selectedWall.value.width = Math.max(10, Math.round(selectedWall.value.width || 0));
  selectedWall.value.height = Math.max(4, Math.round(selectedWall.value.height || 0));
  selectedWall.value.rotation = normalizeAngle(selectedWall.value.rotation || 0);
  commit("wall");
}
function rotateWallBy(delta: number) {
  if (!selectedWall.value) return;
  selectedWall.value.rotation = normalizeAngle(selectedWall.value.rotation + delta);
  commit("wall");
}

function rotateRackBy(delta: number) {
  if (!selectedRack.value) return;
  selectedRack.value.rotation = normalizeAngle(selectedRack.value.rotation + delta);
  commit("rack");
}
function rotateDoorBy(delta: number) {
  if (!selectedDoor.value) return;
  selectedDoor.value.rotation = normalizeAngle(selectedDoor.value.rotation + delta);
  commit("door");
}

// --- Side-panel field helpers ---
const levelsText = computed({
  get: () => selectedRack.value?.levels.join(",") || "",
  set: (value: string) => {
    if (!selectedRack.value) return;
    selectedRack.value.levels = Array.from(
      new Set(
        value
          .split(",")
          .map((s) => s.trim().toUpperCase())
          .filter((s) => s.length > 0),
      ),
    );
  },
});

// A single shared Transformer, reconfigured per selected element's kind:
// zones resize only (no rotate); doors rotate only (no resize); racks get
// the full corner-resize + rotate treatment. Walls are long and thin, so
// corner anchors (like racks) sit only a few px apart vertically and are
// nearly impossible to grab precisely - Konva then silently rejects the
// drag and the wall snaps back to its old size, which looked like "resize
// doesn't stick". Walls instead get separate edge anchors: the sides
// stretch length, top/bottom adjust thickness, independently and reliably.
const transformerConfig = computed(() => {
  const base = {
    anchorStroke: "#60a5fa",
    anchorFill: "#ffffff",
    borderStroke: "#3b82f6",
    keepRatio: false,
  };
  const kind = selected.value?.kind;
  if (kind === "door") return { ...base, enabledAnchors: [], rotateEnabled: true };
  if (kind === "zone")
    return {
      ...base,
      enabledAnchors: ["top-left", "top-right", "bottom-left", "bottom-right"],
      rotateEnabled: false,
    };
  if (kind === "wall")
    return {
      ...base,
      anchorSize: 14,
      enabledAnchors: ["middle-left", "middle-right", "top-center", "bottom-center"],
      rotateEnabled: true,
    };
  return {
    ...base,
    enabledAnchors: ["top-left", "top-right", "bottom-left", "bottom-right"],
    rotateEnabled: true,
  };
});

watch(selected, async () => {
  await nextTick();
  const transformer = transformerRef.value?.getNode();
  if (!transformer) return;
  if (selected.value) {
    const stage = transformer.getStage();
    const node = stage.findOne("#" + selected.value.key);
    if (node) {
      transformer.setAttrs(transformerConfig.value);
      transformer.nodes([node]);
      transformer.getLayer().batchDraw();
      return;
    }
  }
  transformer.nodes([]);
  transformer.getLayer().batchDraw();
});

defineExpose({ addZone, clearAll });
</script>
