<template>
  <div class="flex flex-col gap-3">
    <div class="flex items-center justify-between">
      <p class="m-0 text-[0.8rem] text-muted">
        Drag to pan, scroll to zoom. Click a rack for details.
      </p>
      <button
        v-if="isZoomed"
        type="button"
        class="btn btn--ghost btn--small"
        @click="resetView"
      >
        ↺ Reset view
      </button>
    </div>

    <div
      ref="wrapperRef"
      class="scrollbar-slim min-h-0 max-h-[65vh] overflow-hidden rounded-card border border-edge bg-input bg-[radial-gradient(#2a313c_1px,transparent_1px)] bg-[length:20px_20px]"
    >
      <ClientOnly fallback="Loading map…">
        <v-stage
          :config="stageConfig"
          class="block"
          @wheel="onWheel"
          @dragmove="onStageDragMove"
          @dragend="onStageDragMove"
        >
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
            <v-group
              v-for="zone in layout.zones"
              :key="`zone-${zone.id}`"
              :config="{ listening: false }"
            >
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
              <!-- Glow halo behind the selected rack -->
              <v-rect
                v-if="node.rack_code === selectedRack"
                :config="{
                  x: -6,
                  y: -6,
                  width: node.width + 12,
                  height: node.height + 12,
                  cornerRadius: 8,
                  fill: 'transparent',
                  stroke: '#22c55e',
                  strokeWidth: 3,
                  shadowColor: '#22c55e',
                  shadowBlur: glowBlur,
                  shadowOpacity: 0.9,
                  listening: false,
                }"
              />
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
                  text:
                    (node.label || node.rack_code) +
                    '\n' +
                    node.item_count +
                    ' item(s)',
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
      <span class="flex items-center gap-1.5 text-[0.8rem] text-muted"
        ><i
          class="inline-block h-2.5 w-2.5 rounded-[3px] border border-edge bg-surface-2"
        ></i>
        Empty</span
      >
      <span class="flex items-center gap-1.5 text-[0.8rem] text-muted"
        ><i class="inline-block h-2.5 w-2.5 rounded-[3px] bg-accent/60"></i>
        Active</span
      >
    </div>
  </div>
</template>

<script setup lang="ts">
import type { WarehouseLayout } from "~/composables/useWarehouseApi";

const props = defineProps<{
  layout: WarehouseLayout;
  selectedRack: string | null;
}>();

const emit = defineEmits<{ select: [string] }>();

// Logical coordinate space the layout (walls/zones/racks) is authored in.
const CANVAS_WIDTH = 1400;
const CANVAS_HEIGHT = 760;
const FOCUS_SCALE = 1.7;
const ANIM_MS = 450;

const wrapperRef = ref<HTMLElement | null>(null);
// Actual pixel width the map has to work with -- starts at the logical
// width and gets corrected as soon as we can measure the real container,
// so there's no flash of the oversized canvas before the observer fires.
const containerWidth = ref(CANVAS_WIDTH);
let resizeObserver: ResizeObserver | null = null;

// "Fit" scale: how much the 1400x760 layout must be shrunk (or grown) so it
// exactly fills the current container width. This is what the stage renders
// at by default -- previously the stage was always rendered at a fixed
// 1400px regardless of the container, so on any narrower screen most of it
// was simply clipped by `overflow-hidden`, which looked like the map was
// permanently zoomed in too far.
const fitScale = computed(() => {
  if (!containerWidth.value) return 1;
  return Math.min(1.4, Math.max(0.25, containerWidth.value / CANVAS_WIDTH));
});
const displayHeight = computed(() => CANVAS_HEIGHT * fitScale.value);

const stageX = ref(0);
const stageY = ref(0);
// Zoom relative to the fit scale: 1 = fitted view (the "reset" baseline).
const userZoom = ref(1);
const effectiveScale = computed(() => fitScale.value * userZoom.value);
const isZoomed = computed(() => userZoom.value > 1.02);

// Pulsing glow radius for the selected rack's halo.
const glowBlur = ref(14);
let glowRaf: number | null = null;
function animateGlow(timestamp: number) {
  glowBlur.value = 14 + Math.sin(timestamp / 250) * 8;
  glowRaf = requestAnimationFrame(animateGlow);
}

const stageConfig = computed(() => ({
  width: containerWidth.value,
  height: displayHeight.value,
  x: stageX.value,
  y: stageY.value,
  scaleX: effectiveScale.value,
  scaleY: effectiveScale.value,
  draggable: true,
}));

function rackFill(node: WarehouseLayout["nodes"][number]) {
  if (node.item_count === 0) return "rgba(148, 163, 184, 0.12)";
  return "rgba(47, 157, 99, 0.22)";
}

function rackStroke(node: WarehouseLayout["nodes"][number]) {
  if (node.rack_code === props.selectedRack) return "#22c55e";
  if (node.item_count === 0) return "#2a313c";
  return "rgba(47, 157, 99, 0.8)";
}

/** Smoothly tween the stage transform from its current values to a target.
 *  `targetZoom` is relative to the fit scale (1 = the fitted "reset" view). */
let animFrame: number | null = null;
function animateTo(targetX: number, targetY: number, targetZoom: number) {
  if (animFrame) cancelAnimationFrame(animFrame);
  const startX = stageX.value;
  const startY = stageY.value;
  const startZoom = userZoom.value;
  const startTime = performance.now();

  function step(now: number) {
    const t = Math.min(1, (now - startTime) / ANIM_MS);
    const eased = 1 - Math.pow(1 - t, 3); // ease-out cubic
    stageX.value = startX + (targetX - startX) * eased;
    stageY.value = startY + (targetY - startY) * eased;
    userZoom.value = startZoom + (targetZoom - startZoom) * eased;
    if (t < 1) {
      animFrame = requestAnimationFrame(step);
    } else {
      animFrame = null;
    }
  }
  animFrame = requestAnimationFrame(step);
}

function focusOnRack(rackCode: string) {
  const node = props.layout.nodes.find((n) => n.rack_code === rackCode);
  if (!node) return;
  const cx = node.x + node.width / 2;
  const cy = node.y + node.height / 2;
  const targetScale = fitScale.value * FOCUS_SCALE;
  animateTo(
    containerWidth.value / 2 - cx * targetScale,
    displayHeight.value / 2 - cy * targetScale,
    FOCUS_SCALE,
  );
}

function resetView() {
  animateTo(0, 0, 1);
}

function onWheel(e: any) {
  e.evt.preventDefault();
  const scaleBy = 1.08;
  const newZoom =
    e.evt.deltaY < 0 ? userZoom.value * scaleBy : userZoom.value / scaleBy;
  userZoom.value = Math.min(3, Math.max(0.6, newZoom));
}

// Konva moves the stage itself while dragging, independently of the reactive
// x/y refs. Without this, stageX/stageY go stale the moment someone pans the
// map by hand -- the *next* focus-on-rack animation then starts from that
// stale point instead of where the view actually is, producing a visible
// snap/glitch. Keeping the refs in sync on every drag frame fixes it.
function onStageDragMove(e: any) {
  const stage = e.target?.getStage?.() ?? e.target;
  if (!stage || typeof stage.x !== "function") return;
  stageX.value = stage.x();
  stageY.value = stage.y();
}

watch(
  () => props.selectedRack,
  (val) => {
    if (val) focusOnRack(val);
  },
);

onMounted(() => {
  glowRaf = requestAnimationFrame(animateGlow);

  if (wrapperRef.value) {
    containerWidth.value = wrapperRef.value.clientWidth || CANVAS_WIDTH;
    resizeObserver = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width;
      if (width) containerWidth.value = width;
    });
    resizeObserver.observe(wrapperRef.value);
  }

  if (props.selectedRack) focusOnRack(props.selectedRack);
});

onUnmounted(() => {
  if (animFrame) cancelAnimationFrame(animFrame);
  if (glowRaf) cancelAnimationFrame(glowRaf);
  resizeObserver?.disconnect();
});
</script>
