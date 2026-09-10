<template>
  <div class="flex flex-col gap-3">
    <div class="flex items-center justify-between">
      <p class="m-0 text-[0.8rem] text-muted">
        Drag to orbit, scroll to zoom, right-click drag to pan. Click a rack to
        highlight it and see details.
      </p>
      <button v-if="isOrbiting" type="button" class="btn btn--ghost btn--small" @click="resetView">
        ↺ Reset view
      </button>
    </div>

    <div ref="wrapperRef"
      class="scrollbar-slim relative h-[78vh] min-h-140 overflow-hidden rounded-card border border-edge bg-input">
      <ClientOnly fallback="Loading 3D map…">
        <div ref="canvasHost" class="absolute inset-0 cursor-grab active:cursor-grabbing"></div>
        <p v-if="webglUnavailable"
          class="absolute inset-0 flex items-center justify-center px-6 text-center text-[0.85rem] text-muted">
          WebGL isn't available in this browser, so the 3D warehouse view can't
          render here.
        </p>
      </ClientOnly>
    </div>

    <div class="flex flex-wrap gap-4.5">
      <span class="flex items-center gap-1.5 text-[0.8rem] text-muted"><i
          class="inline-block h-2.5 w-2.5 rounded-[3px] border border-edge bg-surface-2"></i>
        Empty</span>
      <span class="flex items-center gap-1.5 text-[0.8rem] text-muted"><i
          class="inline-block h-2.5 w-2.5 rounded-[3px] bg-accent/60"></i>
        Active</span>
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
  /** Highlights a direct-storage zone the same way selectedRack highlights a
   *  rack -- needed for items placed straight into a zone, with no shelf. */
  selectedZoneId?: number | null;
}>();

const emit = defineEmits<{ select: [string]; "select-zone": [number] }>();

const wrapperRef = ref<HTMLElement | null>(null);
const canvasHost = ref<HTMLElement | null>(null);
const webglUnavailable = ref(false);
const isOrbiting = ref(false);

// ---------------------------------------------------------------------------
// Everything below only ever runs in the browser (guarded by onMounted /
// ClientOnly), since Three.js needs window/document/WebGL. Nuxt auto-imports
// ref/computed/onMounted/watch etc., matching the rest of this codebase.
//
// PERF NOTE (why this file differs from the original):
// The original built one THREE.Mesh per post/plate/package PLUS one live
// THREE.PointLight per rack (even at intensity 0). Three.js compiles a
// distinct shader permutation per light *count* present in the scene, so
// N racks meant N point lights meant a heavier fragment shader for the
// entire scene, on top of hundreds/thousands of individual draw calls for
// posts+plates+boxes. On integrated/weak GPUs that's the actual lag source
// -- no browser flag fixes a CPU/GPU-bound draw-call and shader problem.
// Fix: posts, plates and packages are now each a single THREE.InstancedMesh
// (1 draw call per category, however many racks/boxes exist), and the
// per-rack PointLight is gone entirely (selection now reads purely from the
// pulsing outline, no lighting cost). Materials are also MeshLambertMaterial
// instead of MeshStandardMaterial (no PBR roughness/metalness workload).
// ---------------------------------------------------------------------------

const WORLD_SCALE = 1 / 45;
const WALL_HEIGHT = 2.6;
const LEVEL_HEIGHT = 0.22;
const MIN_RACK_HEIGHT = 0.55;
const POST_THICKNESS = 0.045;
const PLATE_THICKNESS = 0.035;
const FLY_MS = 800;
const RESET_MS = 600;

type RackEntry = {
  group: any; // THREE.Group (shadow + outline + label only now)
  node: ShelfMapNode;
  outline: any; // THREE.LineSegments
  labelEl: HTMLDivElement;
  center: any; // THREE.Vector3 (world center, for camera fly-to)
  radius: number;
  width: number;
  depth: number;
  height: number;
};

type ZoneEntry = {
  group: any; // THREE.Group
  outline: any; // THREE.LineSegments
  glowLight: any; // THREE.PointLight
  labelEl: HTMLDivElement;
  center: any; // THREE.Vector3 (world center, for camera fly-to)
  width: number;
  height: number;
};

type InstanceAccumulator = {
  posts: { matrix: any; rackCode: string }[];
  plates: { matrix: any; color: number; rackCode: string }[];
  boxes: { matrix: any; color: number }[];
};

let shadowTexture: any = null;

let THREE: typeof import("three");
let CSS2DObjectCtor: any = null;
let renderer: any = null;
let labelRenderer: any = null;
let scene: any = null;
let camera: any = null;
let controls: any = null;
let contentGroup: any = null;
let resizeObserver: ResizeObserver | null = null;
let raf = 0;
let raycaster: any = null;
let pointerVec: any = null;

// Instanced meshes rebuilt on every layout change (see buildInstancedParts).
let postsMesh: any = null;
let platesMesh: any = null;
let postInstanceCodes: string[] = [];
let plateInstanceCodes: string[] = [];

const rackMeshes: any[] = []; // raycast targets: [postsMesh, platesMesh]
const zoneMeshes: any[] = []; // raycast targets: direct-storage zone planes
const rackByCode = new Map<string, RackEntry>();
const zoneById = new Map<number, ZoneEntry>();

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

function levelCount(node: ShelfMapNode) {
  return Math.max(1, node.levels?.length || 3);
}

function rackHeight(node: ShelfMapNode) {
  return Math.max(MIN_RACK_HEIGHT, levelCount(node) * LEVEL_HEIGHT + 0.15);
}

function rackColor(node: ShelfMapNode): number {
  if (node.item_count > 0) return 0x2f9d63;
  return 0x4b5563;
}

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
  // Lambert instead of Standard: no roughness/metalness PBR workload, and
  // this plane already covers the whole viewport so it's the single most
  // expensive fragment-shader surface in the scene.
  const floorMat = new THREE.MeshLambertMaterial({ color: 0x161b22 });
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(cx, 0, cz);
  contentGroup.add(floor);

  // Half the line density of the original (divisor 1 instead of 0.5) --
  // visually still reads as a fine grid, at a quarter of the segment count.
  const divisions = Math.max(4, Math.round(Math.max(w, d) / 1));
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
  const mat = new THREE.MeshLambertMaterial({ color: 0x64748b });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(length / 2, WALL_HEIGHT / 2, thickness / 2);
  group.add(mesh);
  contentGroup.add(group);
}

function buildDoor(door: Door) {
  const group = new THREE.Group();
  group.position.set(toX(door.x), 0, toZ(door.y));
  group.rotation.y = (-door.rotation * Math.PI) / 180;

  const width = Math.max(0.3, toX(door.width));
  const jambThickness = 0.06;
  const openingHeight = Math.min(WALL_HEIGHT - 0.3, 2.05);

  const frameMat = new THREE.MeshLambertMaterial({ color: 0x8b96a5 });

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

  const threshold = new THREE.Mesh(
    new THREE.BoxGeometry(width, 0.015, 0.05),
    frameMat,
  );
  threshold.position.set(width / 2, 0.008, 0);
  group.add(threshold);

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

  const isDirectStorage = zone.kind === "direct_storage";
  const w = toX(zone.width);
  const d = toZ(zone.height);
  const geo = new THREE.PlaneGeometry(w, d);
  const color = new THREE.Color(zone.color || "#2f9d63");
  const mat = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    // Direct-storage zones hold items directly, so they read a bit more
    // "solid"/clickable than a shelf_group zone, which is just a grouping.
    opacity: isDirectStorage ? 0.16 : 0.08,
    side: THREE.DoubleSide,
  });
  const plane = new THREE.Mesh(geo, mat);
  plane.rotation.x = -Math.PI / 2;
  plane.position.set(w / 2, 0, d / 2);
  if (isDirectStorage) {
    plane.userData.zoneId = zone.id;
    zoneMeshes.push(plane);
  }
  group.add(plane);

  const edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(geo),
    isDirectStorage
      ? new THREE.LineBasicMaterial({ color })
      : new THREE.LineDashedMaterial({ color, dashSize: 0.15, gapSize: 0.1 }),
  );
  edges.rotation.x = -Math.PI / 2;
  edges.position.set(w / 2, 0, d / 2);
  edges.computeLineDistances();
  group.add(edges);

  const label = document.createElement("div");
  label.style.cssText =
    "pointer-events:none;border-radius:5px;padding:2px 6px;font-size:10px;font-weight:600;font-family:inherit;white-space:nowrap;transition:background .15s ease, border-color .15s ease;border-width:1px;border-style:solid;border-color:transparent;";
  label.style.background = "rgba(15,18,24,0.6)";
  label.style.color = zone.color || "#2f9d63";
  label.textContent = (isDirectStorage ? "📦 " : "") + zone.name;
  const labelObj = new CSS2DObjectCtor(label);
  labelObj.position.set(w / 2, 0.02, d / 2);
  group.add(labelObj);

  // Selection outline + glow, same idea as a rack -- only direct-storage
  // zones are selectable/locatable (a shelf_group zone is just a visual
  // grouping, items never live directly on it).
  let outline: any = null;
  let glowLight: any = null;
  if (isDirectStorage) {
    const outlineGeo = new THREE.PlaneGeometry(w + 0.08, d + 0.08);
    const outlineMat = new THREE.LineBasicMaterial({
      color: 0x22c55e,
      transparent: true,
      opacity: 0.9,
    });
    outline = new THREE.LineSegments(
      new THREE.EdgesGeometry(outlineGeo),
      outlineMat,
    );
    outline.rotation.x = -Math.PI / 2;
    outline.position.set(w / 2, 0.015, d / 2);
    outline.visible = false;
    group.add(outline);

    glowLight = new THREE.PointLight(0x22c55e, 0, 2.2);
    glowLight.position.set(w / 2, 0.4, d / 2);
    group.add(glowLight);

    zoneById.set(zone.id, {
      group,
      outline,
      glowLight,
      labelEl: label,
      center: group.position.clone().add(new THREE.Vector3(w / 2, 0.4, d / 2)),
      width: w,
      height: d,
    });
  }

  contentGroup.add(group);
}

/** Builds shadow + outline + label for a rack, and PUSHES the rack's post /
 *  plate / package transforms into `acc` instead of creating individual
 *  meshes. The actual geometry is created once, globally, by
 *  buildInstancedParts() after every rack has been visited. */
function buildRack(node: ShelfMapNode, acc: InstanceAccumulator) {
  const gx = toX(node.x);
  const gz = toZ(node.y);
  const rotY = (-node.rotation * Math.PI) / 180;

  const width = toX(node.width);
  const depth = toZ(node.height);
  const height = rackHeight(node);
  const levels = levelCount(node);
  const inset = Math.min(POST_THICKNESS * 1.5, width / 4, depth / 4);
  const color = rackColor(node);

  const worldQuat = new THREE.Quaternion().setFromAxisAngle(
    new THREE.Vector3(0, 1, 0),
    rotY,
  );
  const worldMat = new THREE.Matrix4().compose(
    new THREE.Vector3(gx, 0, gz),
    worldQuat,
    new THREE.Vector3(1, 1, 1),
  );
  const identityQuat = new THREE.Quaternion();
  const tmpMat = new THREE.Matrix4();

  // Posts (4 corner uprights) -- unit cube, scaled per-instance.
  const postPositions = [
    [inset, inset],
    [width - inset, inset],
    [inset, depth - inset],
    [width - inset, depth - inset],
  ];
  for (const [px, pz] of postPositions) {
    tmpMat.compose(
      new THREE.Vector3(px, height / 2, pz),
      identityQuat,
      new THREE.Vector3(POST_THICKNESS, height, POST_THICKNESS),
    );
    acc.posts.push({
      matrix: worldMat.clone().multiply(tmpMat),
      rackCode: node.rack_code,
    });
  }

  // Shelf plates -- unit cube, scaled per-instance.
  const plateW = Math.max(0.05, width - inset * 1.4);
  const plateD = Math.max(0.05, depth - inset * 1.4);
  const spacing = height / levels;
  for (let i = 0; i <= levels; i++) {
    tmpMat.compose(
      new THREE.Vector3(width / 2, i * spacing, depth / 2),
      identityQuat,
      new THREE.Vector3(plateW, PLATE_THICKNESS, plateD),
    );
    acc.plates.push({
      matrix: worldMat.clone().multiply(tmpMat),
      color,
      rackCode: node.rack_code,
    });
  }

  // "Packages" on the shelves -- same visual logic as before, but pushed as
  // instance transforms instead of individual meshes.
  if (node.item_count > 0) {
    const rng = mulberry32(seedFromString(node.rack_code));
    const boxColors = [0xb2854e, 0xc79a63, 0x9c7038, 0xae8a52];
    const boxFootprint = 0.22;
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
          if (rng() < 0.25) continue;
          const bw = boxFootprint * (0.82 + rng() * 0.3);
          const bd = boxFootprint * (0.82 + rng() * 0.3);
          const jitterX = (rng() - 0.5) * cellW * 0.25;
          const jitterZ = (rng() - 0.5) * cellD * 0.25;
          const boxRotY =
            (Math.floor(rng() * 4) * Math.PI) / 2 + (rng() - 0.5) * 0.08;
          const boxQuat = new THREE.Quaternion().setFromAxisAngle(
            new THREE.Vector3(0, 1, 0),
            boxRotY,
          );
          tmpMat.compose(
            new THREE.Vector3(
              marginX + cellW * (c + 0.5) + jitterX,
              shelfTopY + bh / 2,
              marginZ + cellD * (r + 0.5) + jitterZ,
            ),
            boxQuat,
            new THREE.Vector3(bw, bh, bd),
          );
          acc.boxes.push({
            matrix: worldMat.clone().multiply(tmpMat),
            color: boxColors[Math.floor(rng() * boxColors.length)],
          });
        }
      }
    }
  }

  const group = new THREE.Group();

  // Soft contact shadow -- kept as a lightweight per-rack mesh (cheap: a
  // single transparent textured plane).
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

  // Selection outline (no more PointLight -- the pulsing wireframe alone is
  // the selection cue now, at zero per-rack lighting cost).
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

  group.position.set(gx, 0, gz);
  group.rotation.y = rotY;
  contentGroup.add(group);

  const center = new THREE.Vector3(gx, height / 2, gz).add(
    new THREE.Vector3(
      (width / 2) * Math.cos(rotY) - (depth / 2) * Math.sin(rotY),
      0,
      (width / 2) * Math.sin(rotY) + (depth / 2) * Math.cos(rotY),
    ),
  );

  rackByCode.set(node.rack_code, {
    group,
    node,
    outline,
    labelEl: label,
    center,
    radius: Math.max(width, depth, height),
    width,
    depth,
    height,
  });
}

/** Creates (at most) three InstancedMesh objects for the whole scene --
 *  one for posts, one for plates, one for packages -- replacing what used
 *  to be up to thousands of individual THREE.Mesh draw calls. */
function buildInstancedParts(acc: InstanceAccumulator) {
  postsMesh = null;
  platesMesh = null;
  postInstanceCodes = [];
  plateInstanceCodes = [];

  if (acc.posts.length) {
    const postGeo = new THREE.BoxGeometry(1, 1, 1);
    const postMat = new THREE.MeshLambertMaterial({ color: 0x4b5563 });
    postsMesh = new THREE.InstancedMesh(postGeo, postMat, acc.posts.length);
    acc.posts.forEach((p, i) => {
      postsMesh.setMatrixAt(i, p.matrix);
      postInstanceCodes.push(p.rackCode);
    });
    postsMesh.instanceMatrix.needsUpdate = true;
    contentGroup.add(postsMesh);
    rackMeshes.push(postsMesh);
  }

  if (acc.plates.length) {
    const plateGeo = new THREE.BoxGeometry(1, 1, 1);
    const plateMat = new THREE.MeshLambertMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.92,
    });
    platesMesh = new THREE.InstancedMesh(plateGeo, plateMat, acc.plates.length);
    const c = new THREE.Color();
    acc.plates.forEach((p, i) => {
      platesMesh.setMatrixAt(i, p.matrix);
      platesMesh.setColorAt(i, c.setHex(p.color));
      plateInstanceCodes.push(p.rackCode);
    });
    platesMesh.instanceMatrix.needsUpdate = true;
    if (platesMesh.instanceColor) platesMesh.instanceColor.needsUpdate = true;
    contentGroup.add(platesMesh);
    rackMeshes.push(platesMesh);
  }

  if (acc.boxes.length) {
    const boxGeo = new THREE.BoxGeometry(1, 1, 1);
    const boxMat = new THREE.MeshLambertMaterial({ color: 0xffffff });
    const boxesMesh = new THREE.InstancedMesh(boxGeo, boxMat, acc.boxes.length);
    const c = new THREE.Color();
    acc.boxes.forEach((p, i) => {
      boxesMesh.setMatrixAt(i, p.matrix);
      boxesMesh.setColorAt(i, c.setHex(p.color));
    });
    boxesMesh.instanceMatrix.needsUpdate = true;
    if (boxesMesh.instanceColor) boxesMesh.instanceColor.needsUpdate = true;
    contentGroup.add(boxesMesh);
    // Packages were never clickable in the original either -- not pushed
    // into rackMeshes, so no raycast cost for them.
  }
}

function buildContent() {
  if (contentGroup) {
    disposeObject3D(contentGroup);
  }
  contentGroup = new THREE.Group();
  scene.add(contentGroup);
  rackMeshes.length = 0;
  zoneMeshes.length = 0;
  rackByCode.clear();
  zoneById.clear();

  const bounds = layoutBounds();
  buildFloorAndGrid(bounds);

  for (const wall of props.layout.walls || []) buildWall(wall);
  for (const door of props.layout.doors || []) buildDoor(door);
  for (const zone of props.layout.zones || []) buildZone(zone);

  const acc: InstanceAccumulator = { posts: [], plates: [], boxes: [] };
  for (const node of props.layout.nodes || []) buildRack(node, acc);
  buildInstancedParts(acc);

  applySelectionVisuals();
  return bounds;
}

function frameCameraToBounds(bounds: ReturnType<typeof layoutBounds>) {
  const w = toX(bounds.maxX - bounds.minX);
  const d = toZ(bounds.maxY - bounds.minY);
  const cx = toX((bounds.minX + bounds.maxX) / 2);
  const cz = toZ((bounds.minY + bounds.maxY) / 2);
  const size = Math.max(w, d, 4);

  defaultTarget = new THREE.Vector3(cx, 0.4, cz);
  defaultCamPos = new THREE.Vector3(cx, size * 1.3, cz + size * 0.7);

  camera.position.copy(defaultCamPos);
  controls.target.copy(defaultTarget);
  controls.update();

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
  }
  for (const [id, entry] of zoneById) {
    const isSelected = id === props.selectedZoneId;
    entry.outline.visible = isSelected;
    if (entry.glowLight) entry.glowLight.intensity = isSelected ? 1.4 : 0;
  }
}

function pulseSelection(now: number) {
  const t = now / 300;
  const wave = 0.55 + Math.sin(t) * 0.35;

  const rackEntry = props.selectedRack ? rackByCode.get(props.selectedRack) : null;
  if (rackEntry?.outline) (rackEntry.outline.material as any).opacity = wave;

  const zoneEntry =
    props.selectedZoneId != null ? zoneById.get(props.selectedZoneId) : null;
  if (zoneEntry?.outline) (zoneEntry.outline.material as any).opacity = wave;
}

// --- camera fly-to -------------------------------------------------------

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

function flyToZone(id: number) {
  const entry = zoneById.get(id);
  if (!entry || !camera || !controls) return;
  const footprint = Math.max(entry.width, entry.height, 0.6);
  const viewDist = footprint * 0.9 + 1.2;
  const camPos = entry.center
    .clone()
    .add(new THREE.Vector3(0, viewDist, viewDist * 0.55));
  animateCamera(camPos, entry.center.clone(), FLY_MS);
}

function resetView() {
  if (!defaultCamPos || !defaultTarget) return;
  animateCamera(defaultCamPos.clone(), defaultTarget.clone(), RESET_MS);
}

// Rack selection and zone selection share one fly-in/reset behaviour, and
// neither should reset the view out from under the other -- e.g. clearing
// the rack while a zone is still highlighted (or vice versa) should just
// leave the camera where it is, not snap back to the overview.
watch(
  () => props.selectedRack,
  (code) => {
    applySelectionVisuals();
    if (code && rackByCode.has(code)) {
      flyToRack(code);
    } else if (!props.selectedZoneId) {
      resetView();
    }
  },
);

watch(
  () => props.selectedZoneId,
  (id) => {
    applySelectionVisuals();
    if (id != null && zoneById.has(id)) {
      flyToZone(id);
    } else if (!props.selectedRack) {
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
  if (moved > 6 || e.button !== 0) return;

  const host = canvasHost.value;
  if (!host) return;
  const rect = host.getBoundingClientRect();
  pointerVec.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  pointerVec.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointerVec, camera);

  const rackHits = raycaster.intersectObjects(rackMeshes, false);
  const zoneHits = raycaster.intersectObjects(zoneMeshes, false);

  const closestRack = rackHits[0];
  const closestZone = zoneHits[0];

  // Se entrambi colpiti, vince quello più vicino alla camera.
  if (closestRack && (!closestZone || closestRack.distance <= closestZone.distance)) {
    let code: string | undefined;
    if (closestRack.instanceId !== undefined) {
      if (closestRack.object === postsMesh) code = postInstanceCodes[closestRack.instanceId];
      else if (closestRack.object === platesMesh) code = plateInstanceCodes[closestRack.instanceId];
    } else if (closestRack.object.userData?.rackCode) {
      code = closestRack.object.userData.rackCode;
    }
    if (code) emit("select", code);
    return;
  }

  if (closestZone) {
    const zoneId = closestZone.object.userData?.zoneId;
    if (zoneId != null) emit("select-zone", zoneId);
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

    renderer = new THREE.WebGLRenderer({
      antialias: false, // AA was the single most expensive per-pixel flag
      // for a weak/integrated GPU on a scene this dense; MSAA cost scales
      // with fill rate, and this scene has a lot of overlapping transparent
      // geometry (fog, shadows, transparent plates). Off by default.
      alpha: true,
      powerPreference: "high-performance", // nudges laptops with a
      // discrete GPU to actually use it instead of the integrated one.
    });
    // Cap at 1.5x instead of 2x -- on a 2x-DPR weak-GPU laptop this alone
    // roughly halves the pixel-shading workload with a barely perceptible
    // sharpness loss.
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
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
    scene.background = new THREE.Color(0x0b0e13);

    camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 500);

    controls = new controlsMod.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.maxPolarAngle = Math.PI * 0.42;
    controls.minDistance = 1;
    controls.maxDistance = 300;
    controls.addEventListener("change", onControlsChange);

    // Down from 3 lights + N per-rack point lights to a fixed 3 lights,
    // full stop -- shader light-count no longer scales with rack count.
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