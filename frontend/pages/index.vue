<template>
  <div class="flex flex-col gap-5">
    <section>
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 class="mb-1.5 text-[1.15rem]">Warehouse Map</h2>
          <p v-if="layout?.has_custom_layout" class="m-0 text-sm text-muted">
            Click a rack to see its levels, then a level to see what's stored
            there.
          </p>
          <p v-else class="m-0 text-sm text-muted">
            Click a shelf to see what's stored there. Columns are shelf numbers,
            rows are levels.
          </p>
        </div>
        <NuxtLink
          to="/map-config"
          class="whitespace-nowrap rounded-lg border border-edge bg-transparent px-4 py-2.5 text-[0.85rem] font-semibold text-ink no-underline"
        >Configure map</NuxtLink>
      </div>
    </section>

    <section class="card">
      <p v-if="loadingLayout" class="text-muted">Loading warehouse layout…</p>
      <MapFreeformMap
        v-else-if="layout?.has_custom_layout"
        :layout="layout"
        :selected-rack="selectedRack"
        @select="selectRack"
      />
      <MapWarehouseMap
        v-else-if="layout"
        :layout="layout"
        :selected-shelf="selectedLevel"
        @select="selectFlatShelf"
      />
    </section>

    <MapRackLevelsPanel
      v-if="layout?.has_custom_layout && selectedRack && rackLevels"
      :rack="rackLevels"
      :selected-level="selectedLevel"
      :loading="loadingRack"
      @select-level="selectLevel"
      @close="closeAll"
    />

    <MapShelfDetailPanel
      v-if="selectedLevel"
      :shelf-position="selectedLevel"
      :items="levelItems"
      :loading="loadingLevelItems"
      :show-back="!!(layout?.has_custom_layout && selectedRack)"
      @close="closeAll"
      @back="backToRack"
    />
  </div>
</template>

<script setup lang="ts">
import type {
  Item,
  RackLevelsResponse,
  WarehouseLayout,
} from "~/composables/useWarehouseApi";

const { getWarehouseLayout, getRackLevels, getShelfItems } = useWarehouseApi();

const layout = ref<WarehouseLayout | null>(null);
const loadingLayout = ref(false);

// Drill-down state: rack selected first, then a level
// within it, then that level's items.
const selectedRack = ref<string | null>(null);
const rackLevels = ref<RackLevelsResponse | null>(null);
const loadingRack = ref(false);

const selectedLevel = ref<string | null>(null);
const levelItems = ref<Item[]>([]);
const loadingLevelItems = ref(false);

async function loadLayout() {
  loadingLayout.value = true;
  try {
    layout.value = await getWarehouseLayout();
  } finally {
    loadingLayout.value = false;
  }
}

async function selectRack(rackCode: string) {
  selectedRack.value = rackCode;
  selectedLevel.value = null;
  levelItems.value = [];
  loadingRack.value = true;
  try {
    rackLevels.value = await getRackLevels(rackCode);
  } finally {
    loadingRack.value = false;
  }
}

async function selectLevel(shelfPosition: string) {
  selectedLevel.value = shelfPosition;
  loadingLevelItems.value = true;
  try {
    const res = await getShelfItems(shelfPosition);
    levelItems.value = res.items;
  } finally {
    loadingLevelItems.value = false;
  }
}

// Legacy fallback grid (no custom layout saved yet) has no rack/level
// split -- clicking a cell goes straight to its items.
async function selectFlatShelf(shelfPosition: string) {
  await selectLevel(shelfPosition);
}

function backToRack() {
  selectedLevel.value = null;
  levelItems.value = [];
}

function closeAll() {
  selectedRack.value = null;
  rackLevels.value = null;
  selectedLevel.value = null;
  levelItems.value = [];
}

onMounted(loadLayout);
</script>
