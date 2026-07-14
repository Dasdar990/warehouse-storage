<script setup lang="ts">
import type { Item, RackLevelsResponse, WarehouseLayout } from '~/composables/useWarehouseApi'

const { getWarehouseLayout, getRackLevels, getShelfItems } = useWarehouseApi()

const layout = ref<WarehouseLayout | null>(null)
const loadingLayout = ref(false)

// Drill-down state: rack ("scaffale") selected first, then a mensola
// (level) within it, then that mensola's items.
const selectedRack = ref<string | null>(null)
const rackLevels = ref<RackLevelsResponse | null>(null)
const loadingRack = ref(false)

const selectedLevel = ref<string | null>(null)
const levelItems = ref<Item[]>([])
const loadingLevelItems = ref(false)

async function loadLayout() {
  loadingLayout.value = true
  try {
    layout.value = await getWarehouseLayout()
  } finally {
    loadingLayout.value = false
  }
}

async function selectRack(rackCode: string) {
  selectedRack.value = rackCode
  selectedLevel.value = null
  levelItems.value = []
  loadingRack.value = true
  try {
    rackLevels.value = await getRackLevels(rackCode)
  } finally {
    loadingRack.value = false
  }
}

async function selectLevel(shelfPosition: string) {
  selectedLevel.value = shelfPosition
  loadingLevelItems.value = true
  try {
    const res = await getShelfItems(shelfPosition)
    levelItems.value = res.items
  } finally {
    loadingLevelItems.value = false
  }
}

// Legacy fallback grid (no custom layout saved yet) has no rack/mensola
// split -- clicking a cell goes straight to its items.
async function selectFlatShelf(shelfPosition: string) {
  await selectLevel(shelfPosition)
}

function backToRack() {
  selectedLevel.value = null
  levelItems.value = []
}

function closeAll() {
  selectedRack.value = null
  rackLevels.value = null
  selectedLevel.value = null
  levelItems.value = []
}

onMounted(loadLayout)
</script>

<template>
  <div class="map-page">
    <section class="intro">
      <div class="intro__row">
        <div>
          <h2>Warehouse Map</h2>
          <p v-if="layout?.has_custom_layout">Click a rack to see its mensole, then a mensola to see what's stored there.</p>
          <p v-else>Click a shelf to see what's stored there. Columns are shelf numbers, rows are levels.</p>
        </div>
        <NuxtLink to="/map-config" class="btn btn--ghost">Configure map</NuxtLink>
      </div>
    </section>

    <section class="map-panel">
      <p v-if="loadingLayout" class="loading">Loading warehouse layout…</p>
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

<style scoped>
.map-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.intro__row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.intro h2 {
  font-size: 1.15rem;
  margin-bottom: 6px;
}

.intro p {
  color: var(--text-dim);
  margin: 0;
  font-size: 0.9rem;
}

.btn {
  cursor: pointer;
  border: none;
  border-radius: 8px;
  padding: 9px 16px;
  font-weight: 600;
  font-size: 0.85rem;
  text-decoration: none;
  white-space: nowrap;
}

.btn--ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
}

.map-panel {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow);
}

.loading {
  color: var(--text-dim);
}
</style>
