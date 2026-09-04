<template>
  <div class="flex flex-col gap-3">
    <div class="flex items-center justify-between">
      <p class="m-0 text-[0.8rem] text-muted">
        Drag to orbit, scroll to zoom, right-click drag to pan. Click a rack to
        highlight it and see details.
      </p>
      <button
        v-if="isOrbiting"
        type="button"
        class="btn btn--ghost btn--small"
        @click="resetView"
      >
        ↺ Reset view
      </button>
    </div>

    <div
      ref="wrapperRef"
      class="scrollbar-slim relative h-[78vh] min-h-140 overflow-hidden rounded-card border border-edge bg-input"
    >
      <ClientOnly fallback="Loading 3D map…">
        <div
          ref="canvasHost"
          class="absolute inset-0 cursor-grab active:cursor-grabbing"
        ></div>
        <p
          v-if="webglUnavailable"
          class="absolute inset-0 flex items-center justify-center px-6 text-center text-[0.85rem] text-muted"
        >
          WebGL isn't available in this browser, so the 3D warehouse view can't
          render here.
        </p>
      </ClientOnly>
    </div>

    <div class="flex flex-wrap gap-4.5">
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
import type {
  WarehouseLayout,
  Wall,
  Door,
  Zone,
  ShelfMapNode,
} from "~/composables/useWarehouseApi";

const props = defineProps<{
  layout: WarehouseLayout;
  selectedRack: string | null;
}>();

const emit = defineEmits<{ select: [string] }>();

const wrapperRef = ref<HTMLElement | null>(null);
const canvasHost = ref<HTMLElement | null>(null);
const webglUnavailable = ref(false);
const isOrbiting = ref(false);

// ---------------------------------------------------------------------------
// Everything below only ever runs in the browser (guarded by onMounted /
// ClientOnly), since Three.js needs window/document/WebGL. Nuxt auto-imports
// ref/computed/onMounted/watch etc., matching the rest of this codebase.
// ---------------------------------------------------------------------------

// The layout (walls/zones/racks) is authored in a flat px-ish coordinate
// space (see useWallGeometry.ts). This scales that space down into
// reasonable Three.js world units ("meters").
const WORLD_SCALE = 1 / 45;
const WALL_HEIGHT = 2.6;
const LEVEL_HEIGHT = 0.22;
const MIN_RACK_HEIGHT = 0.55;
const POST_THICKNESS = 0.045;
const PLATE_THICKNESS = 0.035;
const FLY_MS = 800;
const RESET_MS = 600;

type RackEntry = {
  group: any; // THREE.Group
  node: ShelfMapNode;
  outline: any; // THREE.LineSegments
  glowLight: any; // THREE.PointLight
  labelEl: HTMLDivElement;
  center: any; // THREE.Vector3 (world center, for camera fly-to)
  radius: number;
  width: number; // world-space footprint width (local X)
  depth: number; // world-space footprint depth (local Z)
  height: number; // world-space physical height
};

let shadowTexture: any = null; // shared soft contact-shadow blob, cached lazily

let THREE: typeof import("three");
let CSS2DObjectCtor: any = null;
let renderer: any = null;
let labelRenderer: any = null;
let scene: any = null;
let camera: any = null;
let controls: any = null;
let contentGroup: any = null; // everything that gets rebuilt on layout change
let resizeObserver: ResizeObserver | null = null;
let raf = 0;
let raycaster: any = null;
let pointerVec: any = null;

const rackMeshes: any[] = []; // flat list of meshes -> raycast targets
const rackByCode = new Map<string, RackEntry>();

let defaultCamPos: any = null;
let defaultTarget: any = null;
let flyAnim: {
  start: number;
  from: any;
  fromT: any;
  to: any;
  toT: any;
  ms: number;
} | null = null;

let pointerDown = { x: 0, y: 0, isDown: false };

function toX(px: number) {
  return px * WORLD_SCALE;
}
function toZ(py: number) {
  return py * WORLD_SCALE;
}

/** Real level count from the editor's `levels` array (e.g. ["A","B","C","D"])
 *  -- falls back to 3 only for legacy racks saved before that field existed,
 *  matching the previous 2D renderer's behaviour exactly. */
function levelCount(node: ShelfMapNode) {
  return Math.max(1, node.levels?.length || 3);
}

function rackHeight(node: ShelfMapNode) {
  return Math.max(MIN_RACK_HEIGHT, levelCount(node) * LEVEL_HEIGHT + 0.15);
}

/** Colour a rack by its (rack-level) occupancy: stocked vs empty. */
function rackColor(node: ShelfMapNode): number {
  if (node.item_count > 0) return 0x2f9d63; // accent green
  return 0x4b5563; // empty / neutral
}

/** Soft circular contact-shadow blob rendered flat on the floor under each
 *  rack -- a cheap grounding cue (no real shadow maps needed) that reads a
 *  lot more like a real room. Cached and reused across every rack. */
function getShadowTexture() {
  if (shadowTexture) return shadowTexture;
  const size = 128;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d")!;
  const grad = ctx.createRadialGradient(
    size / 2,
    size / 2,
    0,
    size / 2,
    size / 2,
    size / 2,
  );
  grad.addColorStop(0, "rgba(0,0,0,0.42)");
  grad.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, size, size);
  shadowTexture = new THREE.CanvasTexture(canvas);
  return shadowTexture;
}

/** Deterministic per-rack RNG (seeded from rack_code) so the "packages"
 *  scattered on the shelves stay put across re-renders instead of jumping
 *  around every time the layout prop updates. */
function seedFromString(str: string) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}
function mulberry32(seed: number) {
  let s = seed;
  return function () {
    s |= 0;
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function disposeObject3D(obj: any) {
  if (!obj) return;
  obj.traverse((child: any) => {
    if (child.isCSS2DObject) {
      child.element?.remove();
    }
    if (child.geometry) child.geometry.dispose();
    if (child.material) {
      const mats = Array.isArray(child.material)
        ? child.material
        : [child.material];
      mats.forEach((m: any) => m.dispose?.());
    }
  });
  obj.parent?.remove(obj);
}

/** Corners (in raw layout px space) of a rotated rect whose *pivot* is its
 *  own top-left corner (x, y) -- matching how walls/racks are authored by
 *  the editor and previously drawn by the Konva groups. */
function rectCorners(
  x: number,
  y: number,
  width: number,
  height: number,
  rotationDeg: number,
) {
  const rad = (rotationDeg * Math.PI) / 180;
  const cos = Math.cos(rad);
  const sin = Math.sin(rad);
  const pts = [
    [0, 0],
    [width, 0],
    [width, height],
    [0, height],
  ];
  return pts.map(([lx, ly]) => ({
    x: x + lx * cos - ly * sin,
    y: y + lx * sin + ly * cos,
  }));
}

function layoutBounds() {
  let minX = Infinity,
    maxX = -Infinity,
    minY = Infinity,
    maxY = -Infinity;
  const consider = (x: number, y: number) => {
    minX = Math.min(minX, x);
    maxX = Math.max(maxX, x);
    minY = Math.min(minY, y);
    maxY = Math.max(maxY, y);
  };
  for (const w of props.layout.walls || []) {
    rectCorners(w.x, w.y, w.width, w.height, w.rotation).forEach((c) =>
      consider(c.x, c.y),
    );
  }
  for (const z of props.layout.zones || []) {
    rectCorners(z.x, z.y, z.width, z.height, 0).forEach((c) =>
      consider(c.x, c.y),
    );
  }
  for (const n of props.layout.nodes || []) {
    rectCorners(n.x, n.y, n.width, n.height, n.rotation).forEach((c) =>
      consider(c.x, c.y),
    );
  }
  if (!isFinite(minX)) {
    minX = 0;
    maxX = 1400;
    minY = 0;
    maxY = 760;
  }
  return { minX, maxX, minY, maxY };
}

// --- builders --------------------------------------------------------------

function buildFloorAndGrid(bounds: ReturnType<typeof layoutBounds>) {
  const margin = 2;
  const w = toX(bounds.maxX - bounds.minX) + margin * 2;
  const d = toZ(bounds.maxY - bounds.minY) + margin * 2;
  const cx = toX((bounds.minX + bounds.maxX) / 2);
  const cz = toZ((bounds.minY + bounds.maxY) / 2);

  const floorGeo = new THREE.PlaneGeometry(w, d);
  const floorMat = new THREE.MeshStandardMaterial({
    color: 0x161b22,
    roughness: 0.95,
    metalness: 0,
  });
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(cx, 0, cz);
  contentGroup.add(floor);

  const divisions = Math.max(4, Math.round(Math.max(w, d) / 0.5));
  const grid = new THREE.GridHelper(
    Math.max(w, d),
    divisions,
    0x2a313c,
    0x232833,
  );
  grid.position.set(cx, 0.005, cz);
  (grid.material as any).transparent = true;
  (grid.material as any).opacity = 0.6;
  contentGroup.add(grid);
}

function buildWall(wall: Wall) {
  const group = new THREE.Group();
  group.position.set(toX(wall.x), 0, toZ(wall.y));
  group.rotation.y = (-wall.rotation * Math.PI) / 180;

  const length = toX(wall.width);
  const thickness = toZ(wall.height);

  const geo = new THREE.BoxGeometry(length, WALL_HEIGHT, thickness);
  const mat = new THREE.MeshStandardMaterial({
    color: 0x64748b,
    roughness: 0.85,
    metalness: 0.05,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(length / 2, WALL_HEIGHT / 2, thickness / 2);
  group.add(mesh);
  contentGroup.add(group);
}

function buildDoor(door: Door) {
  const group = new THREE.Group();
  group.position.set(toX(door.x), 0, toZ(door.y));
  group.rotation.y = (-door.rotation * Math.PI) / 180;

  // Full opening width, matching the gap left in the wall in map-config --
  // no more scaling this down, since that's what made the 3D doorway look
  // disconnected from the 2D layout.
  const width = Math.max(0.3, toX(door.width));
  const jambThickness = 0.06;
  const openingHeight = Math.min(WALL_HEIGHT - 0.3, 2.05);

  const frameMat = new THREE.MeshStandardMaterial({
    color: 0x8b96a5,
    roughness: 0.5,
    metalness: 0.25,
  });

  // Two slim jambs marking the opening, plus a lintel across the top --
  // no swinging leaf, just a clearly framed gap in the wall.
  const jambGeo = new THREE.BoxGeometry(
    jambThickness,
    openingHeight,
    jambThickness,
  );
  const leftJamb = new THREE.Mesh(jambGeo, frameMat);
  leftJamb.position.set(0, openingHeight / 2, 0);
  group.add(leftJamb);
  const rightJamb = new THREE.Mesh(jambGeo, frameMat);
  rightJamb.position.set(width, openingHeight / 2, 0);
  group.add(rightJamb);

  const lintel = new THREE.Mesh(
    new THREE.BoxGeometry(width + jambThickness, 0.05, jambThickness),
    frameMat,
  );
  lintel.position.set(width / 2, openingHeight + 0.025, 0);
  group.add(lintel);

  // A subtle threshold strip on the floor so the gap doesn't read as an
  // accidental hole in the wall.
  const threshold = new THREE.Mesh(
    new THREE.BoxGeometry(width, 0.015, 0.05),
    frameMat,
  );
  threshold.position.set(width / 2, 0.008, 0);
  group.add(threshold);

  // "DOOR" label floating in the opening -- clear at any zoom level,
  // unlike a tiny swinging leaf.
  const label = document.createElement("div");
  label.style.cssText =
    "pointer-events:none;white-space:nowrap;border-radius:5px;padding:2px 7px;font-size:11px;font-weight:800;letter-spacing:0.08em;font-family:inherit;box-shadow:0 1px 3px rgba(0,0,0,0.35);border-width:1px;border-style:solid;";
  label.style.background = "rgba(15, 18, 24, 0.85)";
  label.style.borderColor = "rgba(148, 163, 184, 0.4)";
  label.style.color = "#cbd5e1";
  label.textContent = "DOOR";
  const labelObj = new CSS2DObjectCtor(label);
  labelObj.position.set(width / 2, openingHeight * 0.55, 0);
  group.add(labelObj);

  contentGroup.add(group);
}

function buildZone(zone: Zone) {
  const group = new THREE.Group();
  group.position.set(toX(zone.x), 0.01, toZ(zone.y));

  const w = toX(zone.width);
  const d = toZ(zone.height);
  const geo = new THREE.PlaneGeometry(w, d);
  const color = new THREE.Color(zone.color || "#2f9d63");
  const mat = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: 0.08,
    side: THREE.DoubleSide,
  });
  const plane = new THREE.Mesh(geo, mat);
  plane.rotation.x = -Math.PI / 2;
  plane.position.set(w / 2, 0, d / 2);
  group.add(plane);

  const edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(geo),
    new THREE.LineDashedMaterial({ color, dashSize: 0.15, gapSize: 0.1 }),
  );
  edges.rotation.x = -Math.PI / 2;
  edges.position.set(w / 2, 0, d / 2);
  edges.computeLineDistances();
  group.add(edges);

  const label = document.createElement("div");
  label.style.cssText =
    "pointer-events:none;border-radius:5px;padding:2px 6px;font-size:10px;font-weight:600;font-family:inherit;white-space:nowrap;background:rgba(15,18,24,0.6);";
  label.style.color = zone.color || "#2f9d63";
  label.textContent = zone.name;
  const labelObj = new CSS2DObjectCtor(label);
  labelObj.position.set(w / 2, 0.02, d / 2);
  group.add(labelObj);

  contentGroup.add(group);
}

function buildRack(node: ShelfMapNode) {
  const group = new THREE.Group();
  const gx = toX(node.x);
  const gz = toZ(node.y);
  group.position.set(gx, 0, gz);
  group.rotation.y = (-node.rotation * Math.PI) / 180;

  const width = toX(node.width);
  const depth = toZ(node.height);
  const height = rackHeight(node);
  const levels = levelCount(node);
  const inset = Math.min(POST_THICKNESS * 1.5, width / 4, depth / 4);

  const color = rackColor(node);
  const postMat = new THREE.MeshStandardMaterial({
    color: 0x4b5563,
    metalness: 0.5,
    roughness: 0.45,
  });
  const plateMat = new THREE.MeshStandardMaterial({
    color,
    metalness: 0.15,
    roughness: 0.55,
    transparent: true,
    opacity: 0.92,
  });

  const postGeo = new THREE.BoxGeometry(POST_THICKNESS, height, POST_THICKNESS);
  const postPositions = [
    [inset, inset],
    [width - inset, inset],
    [inset, depth - inset],
    [width - inset, depth - inset],
  ];
  for (const [px, pz] of postPositions) {
    const post = new THREE.Mesh(postGeo, postMat);
    post.position.set(px, height / 2, pz);
    post.userData.rackCode = node.rack_code;
    group.add(post);
    rackMeshes.push(post);
  }

  const plateGeo = new THREE.BoxGeometry(
    Math.max(0.05, width - inset * 1.4),
    PLATE_THICKNESS,
    Math.max(0.05, depth - inset * 1.4),
  );
  const spacing = height / levels;
  for (let i = 0; i <= levels; i++) {
    const plate = new THREE.Mesh(plateGeo, plateMat);
    plate.position.set(width / 2, i * spacing, depth / 2);
    plate.userData.rackCode = node.rack_code;
    group.add(plate);
    rackMeshes.push(plate);
  }

  // "Packages" sitting on the shelves -- there's no per-level breakdown in
  // the map payload (see rackColor() above), but a rack with stock should
  // still *look* stocked instead of showing bare empty shelves. Placed on a
  // loose grid with near-axis-aligned rotation so they read as stacked
  // cartons rather than tumbled debris. Positions are seeded from rack_code
  // so a given rack looks the same on every re-render.
  if (node.item_count > 0) {
    const rng = mulberry32(seedFromString(node.rack_code));
    const boxPalette = [0xb2854e, 0xc79a63, 0x9c7038, 0xae8a52].map(
      (c) =>
        new THREE.MeshStandardMaterial({
          color: c,
          roughness: 0.9,
          metalness: 0.02,
        }),
    );
    const boxFootprint = 0.22; // roughly uniform carton footprint
    for (let lvl = 0; lvl < levels; lvl++) {
      const shelfTopY = lvl * spacing + PLATE_THICKNESS / 2;
      const clearance = spacing - PLATE_THICKNESS - 0.03;
      if (clearance < 0.08) continue;
      const bh = Math.min(clearance, 0.16 + rng() * 0.08);

      const marginX = inset + 0.03;
      const marginZ = inset + 0.03;
      const usableW = Math.max(0.01, width - marginX * 2);
      const usableD = Math.max(0.01, depth - marginZ * 2);
      const cols = Math.max(1, Math.floor(usableW / (boxFootprint + 0.03)));
      const rows = Math.max(1, Math.floor(usableD / (boxFootprint + 0.03)));
      const cellW = usableW / cols;
      const cellD = usableD / rows;

      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          if (rng() < 0.25) continue; // leave gaps so shelves don't look packed solid
          const bw = boxFootprint * (0.82 + rng() * 0.3);
          const bd = boxFootprint * (0.82 + rng() * 0.3);
          const jitterX = (rng() - 0.5) * cellW * 0.25;
          const jitterZ = (rng() - 0.5) * cellD * 0.25;
          const box = new THREE.Mesh(
            new THREE.BoxGeometry(bw, bh, bd),
            boxPalette[Math.floor(rng() * boxPalette.length)],
          );
          box.position.set(
            marginX + cellW * (c + 0.5) + jitterX,
            shelfTopY + bh / 2,
            marginZ + cellD * (r + 0.5) + jitterZ,
          );
          // Snap to near-axis-aligned so boxes look set down on the shelf,
          // not spun at a random angle.
          box.rotation.y =
            (Math.floor(rng() * 4) * Math.PI) / 2 + (rng() - 0.5) * 0.08;
          group.add(box);
        }
      }
    }
  }

  // Soft contact shadow on the floor beneath the unit, for grounding.
  const shadow = new THREE.Mesh(
    new THREE.PlaneGeometry(width * 1.5, depth * 1.5),
    new THREE.MeshBasicMaterial({
      map: getShadowTexture(),
      transparent: true,
      depthWrite: false,
    }),
  );
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.set(width / 2, 0.004, depth / 2);
  group.add(shadow);

  // Selection outline: a slightly larger wireframe box around the whole
  // unit, hidden by default and toggled/pulsed when this rack is selected.
  const outlineGeo = new THREE.BoxGeometry(
    width + 0.1,
    height + 0.1,
    depth + 0.1,
  );
  const outlineMat = new THREE.LineBasicMaterial({
    color: 0x22c55e,
    transparent: true,
    opacity: 0.9,
  });
  const outline = new THREE.LineSegments(
    new THREE.EdgesGeometry(outlineGeo),
    outlineMat,
  );
  outline.position.set(width / 2, height / 2, depth / 2);
  outline.visible = false;
  group.add(outline);

  const glowLight = new THREE.PointLight(0x22c55e, 0, 2.2);
  glowLight.position.set(width / 2, height * 0.6, depth / 2);
  group.add(glowLight);

  // Always-visible label, floating above the unit. The name is the whole
  // point of the label, so it gets its own bold line; the item count is
  // secondary, smaller and muted underneath.
  const label = document.createElement("div");
  label.style.cssText =
    "pointer-events:none;white-space:nowrap;border-radius:6px;padding:4px 8px;font-family:inherit;box-shadow:0 1px 3px rgba(0,0,0,0.4);border-width:1px;border-style:solid;transition:background .15s ease, border-color .15s ease;text-align:center;line-height:1.25;";
  label.style.background = "rgba(15, 18, 24, 0.92)";
  label.style.borderColor = "rgba(148, 163, 184, 0.35)";

  const nameEl = document.createElement("div");
  nameEl.style.cssText = "font-size:13.5px;font-weight:800;color:#f1f5f9;";
  nameEl.textContent = node.label || node.rack_code;
  label.appendChild(nameEl);

  const countEl = document.createElement("div");
  countEl.style.cssText = "font-size:10px;font-weight:500;color:#94a3b8;";
  countEl.textContent = `${node.item_count} item(s)`;
  label.appendChild(countEl);

  const labelObj = new CSS2DObjectCtor(label);
  labelObj.position.set(width / 2, height + 0.22, depth / 2);
  group.add(labelObj);

  contentGroup.add(group);

  const center = new THREE.Vector3(gx, height / 2, gz).add(
    new THREE.Vector3(
      (width / 2) * Math.cos(group.rotation.y) -
        (depth / 2) * Math.sin(group.rotation.y),
      0,
      (width / 2) * Math.sin(group.rotation.y) +
        (depth / 2) * Math.cos(group.rotation.y),
    ),
  );

  rackByCode.set(node.rack_code, {
    group,
    node,
    outline,
    glowLight,
    labelEl: label,
    center,
    radius: Math.max(width, depth, height),
    width,
    depth,
    height,
  });
}

function buildContent() {
  if (contentGroup) {
    disposeObject3D(contentGroup);
  }
  contentGroup = new THREE.Group();
  scene.add(contentGroup);
  rackMeshes.length = 0;
  rackByCode.clear();

  const bounds = layoutBounds();
  buildFloorAndGrid(bounds);

  // Soft ambient context: pareti/porte/zone are background orientation only,
  // same intent as the previous 2D renderer's `listening: false` groups.
  for (const wall of props.layout.walls || []) buildWall(wall);
  for (const door of props.layout.doors || []) buildDoor(door);
  for (const zone of props.layout.zones || []) buildZone(zone);
  for (const node of props.layout.nodes || []) buildRack(node);

  applySelectionVisuals();
  return bounds;
}

function frameCameraToBounds(bounds: ReturnType<typeof layoutBounds>) {
  const w = toX(bounds.maxX - bounds.minX);
  const d = toZ(bounds.maxY - bounds.minY);
  const cx = toX((bounds.minX + bounds.maxX) / 2);
  const cz = toZ((bounds.minY + bounds.maxY) / 2);
  const size = Math.max(w, d, 4);

  // A steeper, more top-down default (previously 0.62/0.78, ~38° above the
  // floor) so the layout reads like a plan view first and foremost -- users
  // can still orbit to a lower angle manually, but they land on a "fixed
  // from above" shot instead of a low oblique one.
  defaultTarget = new THREE.Vector3(cx, 0.4, cz);
  defaultCamPos = new THREE.Vector3(cx, size * 0.98, cz + size * 0.52);

  camera.position.copy(defaultCamPos);
  controls.target.copy(defaultTarget);
  controls.update();

  // Fog range must scale with the scene's own size, not a fixed constant --
  // a fixed near/far (e.g. 12-40) fogs everything to the background colour
  // on any layout whose camera distance sits close to or beyond that fixed
  // far plane, which looks exactly like "nothing rendered" even though the
  // scene is fine. Base it on the actual camera-to-target distance instead.
  const dist = defaultCamPos.distanceTo(defaultTarget);
  scene.fog = new THREE.Fog(0x0b0e13, dist * 2.2, dist * 6);
}

// --- selection / highlight ---------------------------------------------------

function applySelectionVisuals() {
  for (const [code, entry] of rackByCode) {
    const isSelected = code === props.selectedRack;
    entry.outline.visible = isSelected;
    entry.labelEl.style.borderColor = isSelected
      ? "#22c55e"
      : "rgba(148, 163, 184, 0.35)";
    entry.labelEl.style.background = isSelected
      ? "rgba(15, 40, 28, 0.9)"
      : "rgba(15, 18, 24, 0.82)";
    if (!isSelected) entry.glowLight.intensity = 0;
  }
}

function pulseSelection(now: number) {
  const entry = props.selectedRack ? rackByCode.get(props.selectedRack) : null;
  if (!entry) return;
  const t = now / 300;
  const wave = 0.55 + Math.sin(t) * 0.35;
  (entry.outline.material as any).opacity = wave;
  entry.glowLight.intensity = 0.6 + Math.sin(t) * 0.4;
}

// --- camera fly-to (selection + "locate" search both drive this via the
// selectedRack prop, giving the exact "vola lì" behaviour requirement 5
// asks for without any separate API) ------------------------------------

function animateCamera(toPos: any, toTarget: any, ms: number) {
  flyAnim = {
    start: performance.now(),
    from: camera.position.clone(),
    fromT: controls.target.clone(),
    to: toPos,
    toT: toTarget,
    ms,
  };
}

function stepFlyAnim(now: number) {
  if (!flyAnim) return;
  const t = Math.min(1, (now - flyAnim.start) / flyAnim.ms);
  const eased = 1 - Math.pow(1 - t, 3);
  camera.position.lerpVectors(flyAnim.from, flyAnim.to, eased);
  controls.target.lerpVectors(flyAnim.fromT, flyAnim.toT, eased);
  if (t >= 1) flyAnim = null;
}

function flyToRack(code: string) {
  const entry = rackByCode.get(code);
  if (!entry || !camera || !controls) return;
  // Elevated angle, matching the default overview camera, instead of a low
  // eye-level shot -- a low frontal approach had no wall-awareness and
  // could end up positioned outside the room, peeking back in through a
  // wall. Coming in from above (well over WALL_HEIGHT) always clears them.
  const front = new THREE.Vector3(0, 0, -1).applyQuaternion(
    entry.group.quaternion,
  );
  if (!isFinite(front.x)) front.set(0, 0, -1);
  const footprint = Math.max(entry.width, entry.depth, 0.6);
  const viewDist = footprint * 1.5 + entry.height * 0.6 + 0.9;
  const camPos = entry.center.clone().add(front.multiplyScalar(viewDist * 0.4));
  camPos.y = entry.center.y + Math.max(WALL_HEIGHT * 0.85, viewDist * 0.95);
  animateCamera(camPos, entry.center.clone(), FLY_MS);
}

function resetView() {
  if (!defaultCamPos || !defaultTarget) return;
  animateCamera(defaultCamPos.clone(), defaultTarget.clone(), RESET_MS);
}

watch(
  () => props.selectedRack,
  (code) => {
    applySelectionVisuals();
    // Selecting (map click or search "locate") flies in for a clear look;
    // clearing the selection (closing the modal / search result) flies back
    // out to the fixed overview instead of leaving the camera stranded on
    // whatever rack was last inspected.
    if (code && rackByCode.has(code)) {
      flyToRack(code);
    } else {
      resetView();
    }
  },
);

watch(
  () => props.layout,
  () => {
    if (!scene) return;
    buildContent();
  },
);

// --- interaction -------------------------------------------------------

function onPointerDown(e: PointerEvent) {
  pointerDown = { x: e.clientX, y: e.clientY, isDown: true };
}

function onPointerUp(e: PointerEvent) {
  if (!pointerDown.isDown) return;
  pointerDown.isDown = false;
  const moved = Math.hypot(
    e.clientX - pointerDown.x,
    e.clientY - pointerDown.y,
  );
  if (moved > 6 || e.button !== 0) return; // treat as a drag/orbit, not a click

  const host = canvasHost.value;
  if (!host) return;
  const rect = host.getBoundingClientRect();
  pointerVec.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  pointerVec.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointerVec, camera);
  const hits = raycaster.intersectObjects(rackMeshes, false);
  if (hits.length && hits[0].object.userData.rackCode) {
    emit("select", hits[0].object.userData.rackCode);
  }
}

function onControlsChange() {
  if (!defaultCamPos || !defaultTarget || !camera || !controls) return;
  const moved =
    camera.position.distanceTo(defaultCamPos) > 0.05 ||
    controls.target.distanceTo(defaultTarget) > 0.05;
  isOrbiting.value = moved;
}

// --- lifecycle -----------------------------------------------------------

function handleResize() {
  const host = canvasHost.value;
  if (!host || !renderer || !camera || !labelRenderer) return;
  const w = host.clientWidth || 1;
  const h = host.clientHeight || 1;
  renderer.setSize(w, h, false);
  labelRenderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

function animate(now: number) {
  raf = requestAnimationFrame(animate);
  stepFlyAnim(now);
  pulseSelection(now);
  controls?.update();
  renderer?.render(scene, camera);
  labelRenderer?.render(scene, camera);
}

// `<ClientOnly>` renders its fallback on the *first* client render and only
// swaps in the real slot (our canvasHost div) once its own onMounted flips
// an internal flag -- that DOM patch lands a tick after our onMounted has
// already run, so `onMounted(() => { if (!canvasHost.value) return; ... })`
// was finding a still-null ref and silently bailing out every time (no
// error, just nothing ever built). Watching the ref itself fires exactly
// when the element actually appears, regardless of ClientOnly's timing.
watch(
  canvasHost,
  async (host) => {
    if (!host || !wrapperRef.value || renderer) return;
    await initScene(host, wrapperRef.value);
  },
  { immediate: true },
);

async function initScene(host: HTMLElement, wrapper: HTMLElement) {
  try {
    const [threeMod, controlsMod, css2dMod] = await Promise.all([
      import("three"),
      import("three/addons/controls/OrbitControls.js"),
      import("three/addons/renderers/CSS2DRenderer.js"),
    ]);
    THREE = threeMod;
    CSS2DObjectCtor = css2dMod.CSS2DObject;

    const w = host.clientWidth || 800;
    const h = host.clientHeight || 480;

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(w, h);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    host.appendChild(renderer.domElement);

    labelRenderer = new css2dMod.CSS2DRenderer();
    labelRenderer.setSize(w, h);
    labelRenderer.domElement.style.position = "absolute";
    labelRenderer.domElement.style.top = "0";
    labelRenderer.domElement.style.left = "0";
    labelRenderer.domElement.style.pointerEvents = "none";
    wrapper.appendChild(labelRenderer.domElement);

    scene = new THREE.Scene();
    // Explicit background instead of relying on canvas alpha + the div's CSS
    // background matching underneath -- keeps the render correct regardless
    // of any surrounding style changes, and matches the fog colour set in
    // frameCameraToBounds().
    scene.background = new THREE.Color(0x0b0e13);

    camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 500);

    controls = new controlsMod.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.maxPolarAngle = Math.PI * 0.42;
    controls.minDistance = 1;
    controls.maxDistance = 300;
    controls.addEventListener("change", onControlsChange);

    const hemi = new THREE.HemisphereLight(0x3b4252, 0x0b0e13, 0.7);
    scene.add(hemi);
    const dir = new THREE.DirectionalLight(0xf8fafc, 0.9);
    dir.position.set(6, 10, 4);
    scene.add(dir);
    const fill = new THREE.AmbientLight(0x334155, 0.35);
    scene.add(fill);

    raycaster = new THREE.Raycaster();
    pointerVec = new THREE.Vector2();

    const bounds = buildContent();
    frameCameraToBounds(bounds);

    renderer.domElement.addEventListener("pointerdown", onPointerDown);
    renderer.domElement.addEventListener("pointerup", onPointerUp);

    resizeObserver = new ResizeObserver(() => handleResize());
    resizeObserver.observe(host);

    raf = requestAnimationFrame(animate);
  } catch (err) {
    // Surface real failures loudly (e.g. WebGL unavailable, module load
    // failure) instead of leaving an inexplicable blank canvas.
    console.error("[FreeformMap] 3D scene failed to initialise:", err);
    webglUnavailable.value = true;
  }
}

onUnmounted(() => {
  if (raf) cancelAnimationFrame(raf);
  resizeObserver?.disconnect();
  controls?.removeEventListener("change", onControlsChange);
  controls?.dispose?.();
  if (contentGroup) disposeObject3D(contentGroup);
  if (renderer) {
    renderer.domElement.removeEventListener("pointerdown", onPointerDown);
    renderer.domElement.removeEventListener("pointerup", onPointerUp);
    renderer.dispose();
    renderer.domElement.remove();
  }
  labelRenderer?.domElement.remove();
  shadowTexture?.dispose();
  shadowTexture = null;
});
</script>
