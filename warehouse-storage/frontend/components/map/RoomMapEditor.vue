<template>
  <div class="flex flex-col gap-3">
    <div class="flex flex-wrap items-center gap-3.5">
      <button class="btn btn--confirm text-[#06280f]" type="button" @click="addWall">
        + Add wall
      </button>
      <button class="btn btn--confirm text-[#06280f]" type="button" @click="addDoor">
        + Add door
      </button>
      <label class="flex items-center gap-1.5 text-[0.85rem] text-muted">
        <input v-model="snapToGrid" type="checkbox" />
        Snap to grid
      </label>
      <button
        class="btn btn--ghost disabled:cursor-not-allowed disabled:opacity-50"
        type="button"
        :disabled="!walls.length && !doors.length"
        @click="clearAll"
      >
        Clear canvas
      </button>
      <span class="ml-auto text-[0.8rem] text-muted"
        >{{ walls.length }} wall(s), {{ doors.length }} door(s)</span
      >
    </div>

    <div class="flex items-start gap-4">
      <div
        class="scrollbar-slim max-h-[65vh] flex-1 overflow-auto rounded-card border border-edge bg-input bg-[radial-gradient(#2a313c_1px,transparent_1px)] bg-[length:20px_20px]"
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
              <!-- Walls: the room perimeter, purely visual/orientation context -->
              <v-group v-for="wall in walls" :key="`wall-${wall._key}`">
                <v-line
                  :config="{
                    points: [wall.x1, wall.y1, wall.x2, wall.y2],
                    stroke: selectedKey === wall._key ? '#60a5fa' : '#cbd5e1',
                    strokeWidth: 8,
                    lineCap: 'round',
                    draggable: true,
                    hitStrokeWidth: 16,
                  }"
                  @dragstart="selectWall(wall._key)"
                  @dragmove="handleWallBodyDrag($event, wall)"
                  @dragend="handleWallBodyDrag($event, wall)"
                  @click="selectWall(wall._key)"
                  @tap="selectWall(wall._key)"
                />
                <!-- Endpoint handles: drag either end to reshape the wall -->
                <v-circle
                  :config="{
                    x: wall.x1,
                    y: wall.y1,
                    radius: 7,
                    fill: '#0f172a',
                    stroke: '#60a5fa',
                    strokeWidth: 2,
                    draggable: true,
                  }"
                  @dragstart="selectWall(wall._key)"
                  @dragmove="handleEndpointDrag($event, wall, 'x1', 'y1')"
                  @dragend="handleEndpointDrag($event, wall, 'x1', 'y1')"
                />
                <v-circle
                  :config="{
                    x: wall.x2,
                    y: wall.y2,
                    radius: 7,
                    fill: '#0f172a',
                    stroke: '#60a5fa',
                    strokeWidth: 2,
                    draggable: true,
                  }"
                  @dragstart="selectWall(wall._key)"
                  @dragmove="handleEndpointDrag($event, wall, 'x2', 'y2')"
                  @dragend="handleEndpointDrag($event, wall, 'x2', 'y2')"
                />
              </v-group>

              <!-- Doors: hinge + swing-arc symbol, dropped onto a wall gap -->
              <v-group
                v-for="door in doors"
                :key="`door-${door._key}`"
                :config="{
                  x: door.x,
                  y: door.y,
                  rotation: door.rotation,
                  draggable: true,
                }"
                @dragstart="selectDoor(door._key)"
                @dragend="handleDoorDragEnd($event, door)"
                @click="selectDoor(door._key)"
                @tap="selectDoor(door._key)"
              >
                <v-arc
                  :config="{
                    innerRadius: 0,
                    outerRadius: door.width,
                    angle: 90,
                    stroke: selectedKey === door._key ? '#60a5fa' : '#facc15',
                    strokeWidth: 2,
                    dash: [5, 4],
                  }"
                />
                <v-circle
                  :config="{
                    x: 0,
                    y: 0,
                    radius: 4,
                    fill: selectedKey === door._key ? '#60a5fa' : '#facc15',
                  }"
                />
              </v-group>
            </v-layer>
          </v-stage>
        </ClientOnly>
      </div>

      <aside
        class="flex w-[280px] shrink-0 flex-col gap-3 rounded-card border border-edge bg-surface-2 p-4"
      >
        <template v-if="selectedWall">
          <h3 class="m-0 border-b border-edge pb-2 text-[0.95rem]">Wall</h3>
          <p class="m-0 text-[0.82rem] leading-relaxed text-muted">
            Drag the wall to move it, or drag either endpoint to reshape it.
          </p>
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
              @change="commit"
            />
          </label>

          <label class="flex flex-col gap-1 text-[0.8rem] text-muted">
            <span>Rotation (degrees °)</span>
            <input
              v-model.number="selectedDoor.rotation"
              type="number"
              class="rounded-lg border border-edge bg-surface px-2.5 py-1.5 font-sans text-[0.85rem] text-ink"
              @change="commit"
            />
          </label>

          <div class="flex gap-2">
            <button class="btn btn--ghost btn--small flex-1" type="button" @click="rotateBy(-90)">
              ⟲ -90°
            </button>
            <button class="btn btn--ghost btn--small flex-1" type="button" @click="rotateBy(90)">
              ⟳ +90°
            </button>
          </div>

          <button class="btn btn--danger" type="button" @click="deleteSelected">
            Delete door
          </button>
        </template>

        <p v-else class="m-0 text-[0.82rem] leading-relaxed text-muted">
          Draw the room's walls and drop the door where it sits, purely so the
          rack map below is easier to orient yourself in — this has no effect
          on inventory. Select a wall or door to edit or delete it.
        </p>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DoorInput, RoomLayoutInput, WallInput } from "~/composables/useWarehouseApi";

interface EditorWall {
  _key: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  /** Wall thickness in px -- preserved across edits, not exposed in the UI. */
  thickness: number;
}
interface EditorDoor extends DoorInput {
  _key: string;
}

const props = defineProps<{
  modelValue: RoomLayoutInput;
}>();

const emit = defineEmits<{ "update:modelValue": [RoomLayoutInput] }>();

const CANVAS_WIDTH = 1400;
const CANVAS_HEIGHT = 760;
const GRID_STEP = 10;

let keySeed = 0;
function nextKey(prefix: string) {
  keySeed += 1;
  return `${prefix}${Date.now()}-${keySeed}`;
}

function toEditorWall(wall: WallInput): EditorWall {
  const { x1, y1, x2, y2 } = wallToEndpoints(wall);
  return { _key: nextKey("w"), x1, y1, x2, y2, thickness: wall.height };
}
function toApiWall(wall: EditorWall): WallInput {
  return endpointsToWall(wall.x1, wall.y1, wall.x2, wall.y2, wall.thickness);
}
function toEditorDoor(door: DoorInput): EditorDoor {
  return { ...door, _key: nextKey("d") };
}

const walls = ref<EditorWall[]>(props.modelValue.walls.map(toEditorWall));
const doors = ref<EditorDoor[]>(props.modelValue.doors.map(toEditorDoor));
const selectedKey = ref<string | null>(null);
const snapToGrid = ref(true);
const stageRef = ref<any>(null);

let lastEmitted: RoomLayoutInput | null = null;
watch(
  () => props.modelValue,
  (value) => {
    if (value !== lastEmitted) {
      walls.value = value.walls.map(toEditorWall);
      doors.value = value.doors.map(toEditorDoor);
      selectedKey.value = null;
    }
  },
);

function commit() {
  const plain: RoomLayoutInput = {
    walls: walls.value.map(toApiWall),
    doors: doors.value.map(({ _key, ...rest }) => rest),
  };
  lastEmitted = plain;
  emit("update:modelValue", plain);
}

const selectedWall = computed(
  () => walls.value.find((w) => w._key === selectedKey.value) || null,
);
const selectedDoor = computed(
  () => doors.value.find((d) => d._key === selectedKey.value) || null,
);

function snap(value: number) {
  return snapToGrid.value ? Math.round(value / GRID_STEP) * GRID_STEP : Math.round(value);
}

function selectWall(key: string) {
  selectedKey.value = key;
}
function selectDoor(key: string) {
  selectedKey.value = key;
}

function addWall() {
  const cascade = (walls.value.length % 8) * 24;
  const wall: EditorWall = {
    _key: nextKey("w"),
    x1: 40 + cascade,
    y1: 40 + cascade,
    x2: 340 + cascade,
    y2: 40 + cascade,
    thickness: DEFAULT_WALL_THICKNESS,
  };
  walls.value.push(wall);
  selectedKey.value = wall._key;
  commit();
}

function addDoor() {
  const cascade = (doors.value.length % 8) * 24;
  const door: EditorDoor = {
    _key: nextKey("d"),
    x: 80 + cascade,
    y: 80 + cascade,
    width: 40,
    rotation: 0,
  };
  doors.value.push(door);
  selectedKey.value = door._key;
  commit();
}

function deleteSelected() {
  if (!selectedKey.value) return;
  walls.value = walls.value.filter((w) => w._key !== selectedKey.value);
  doors.value = doors.value.filter((d) => d._key !== selectedKey.value);
  selectedKey.value = null;
  commit();
}

function clearAll() {
  if ((walls.value.length || doors.value.length) && !confirm("Remove every wall and door from the canvas?"))
    return;
  walls.value = [];
  doors.value = [];
  selectedKey.value = null;
  commit();
}

function handleStageMouseDown(e: any) {
  if (e.target === e.target.getStage()) {
    selectedKey.value = null;
  }
}

// Dragging the wall's body moves both endpoints together by the same delta.
function handleWallBodyDrag(e: any, wall: EditorWall) {
  const node = e.target;
  const dx = snap(node.x());
  const dy = snap(node.y());
  if (dx === 0 && dy === 0) return;
  wall.x1 += dx;
  wall.y1 += dy;
  wall.x2 += dx;
  wall.y2 += dy;
  node.x(0);
  node.y(0);
  if (e.type === "dragend") commit();
}

// Dragging an endpoint handle reshapes the wall by moving just that end.
function handleEndpointDrag(
  e: any,
  wall: EditorWall,
  xKey: "x1" | "x2",
  yKey: "y1" | "y2",
) {
  const node = e.target;
  wall[xKey] = snap(node.x());
  wall[yKey] = snap(node.y());
  if (e.type === "dragend") commit();
}

function handleDoorDragEnd(e: any, door: EditorDoor) {
  const node = e.target;
  door.x = snap(node.x());
  door.y = snap(node.y());
  commit();
}

function rotateBy(delta: number) {
  if (!selectedDoor.value) return;
  selectedDoor.value.rotation = Math.round(
    (((selectedDoor.value.rotation + delta) % 360) + 360) % 360,
  );
  commit();
}

defineExpose({ addWall, addDoor, clearAll });
</script>
