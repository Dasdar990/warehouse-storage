<template>
  <div class="flex flex-col gap-4">
    <section>
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="mb-1.5 text-[1.15rem]">Warehouse Storage</h2>
          <p class="m-0 text-sm text-muted">
            Scan a barcode to withdraw/deposit instantly, or search for an item to locate it on the map.
          </p>
        </div>
        <div class="flex items-center gap-2.5">
          <button
            type="button"
            class="btn btn--primary whitespace-nowrap text-[0.85rem]"
            @click="showAddItemModal = true"
          >+ New Item</button>
          <NuxtLink
            to="/map-config"
            class="whitespace-nowrap rounded-lg border border-edge bg-transparent px-4 py-2.5 text-[0.85rem] font-semibold text-ink no-underline"
          >Configure Map</NuxtLink>
        </div>
      </div>
    </section>

    <UnifiedSearchBar
      ref="searchBarRef"
      @scan-item="handleScanItem"
      @scan-not-found="handleScanNotFound"
      @locate-item="handleLocateItem"
    />

    <div class="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_400px]">
      <!-- Interactive map -->
      <section class="card">
        <p v-if="loadingLayout" class="text-muted">Loading warehouse map…</p>
        <MapFreeformMap
          v-else-if="layout?.has_custom_layout"
          :layout="layout"
          :selected-rack="highlightRackCode"
          @select="selectRack"
        />
        <MapWarehouseMap
          v-else-if="layout"
          :layout="layout"
          :selected-shelf="highlightShelfPosition"
          @select="selectFlatShelf"
        />
      </section>

      <!-- Right column: either the searched/scanned item, or the rack/level drill-down from a direct map click -->
      <div class="flex flex-col gap-4">
        <ItemDetailCard
          v-if="selectedItem"
          :key="selectedItem.id"
          :item="selectedItem"
          :low-stock-threshold="layout?.low_stock_threshold"
          :zone-label="selectedItemZoneLabel"
          :default-source="lastSelectionSource"
          @close="clearSelection"
          @updated="handleItemUpdated"
        />

        <MapRackLevelsPanel
          v-else-if="layout?.has_custom_layout && selectedRack && rackLevels"
          :rack="rackLevels"
          :selected-level="selectedLevel"
          :loading="loadingRack"
          @select-level="selectLevel"
          @close="closeDrilldown"
        />

        <MapShelfDetailPanel
          v-if="!selectedItem && selectedLevel"
          :shelf-position="selectedLevel"
          :items="levelItems"
          :loading="loadingLevelItems"
          :show-back="!!(layout?.has_custom_layout && selectedRack)"
          @close="closeDrilldown"
          @back="backToRack"
        />

        <p v-if="!selectedItem && !selectedLevel && !(layout?.has_custom_layout && selectedRack)" class="card text-sm text-muted">
          Scan a code, search for an item, or click a shelf on the map to get started.
        </p>
      </div>
    </div>

    <ActivityLog ref="activityLogRef" />

    <BaseModal v-model="showAddItemModal" title="New Item" size="md">
      <DashboardAddItemForm @created="handleItemCreated" />
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import type {
  Item,
  RackLevelsResponse,
  WarehouseLayout,
} from "~/composables/useWarehouseApi";

const { getWarehouseLayout, getRackLevels, getShelfItems, getZones, withdrawItem, depositItem } = useWarehouseApi();
const { mode } = useOperationMode();
const { show } = useToast();

const searchBarRef = ref<{ focus: () => void } | null>(null);
const activityLogRef = ref<{ refresh: () => void } | null>(null);

const layout = ref<WarehouseLayout | null>(null);
const loadingLayout = ref(false);

// --- Quick action: New Item modal ---
const showAddItemModal = ref(false);

async function handleItemCreated(item: Item) {
  showAddItemModal.value = false;
  show('success', `"${item.name}" created — here's where it landed`);
  closeDrilldown();
  lastSelectionSource.value = 'manual';
  selectedItem.value = item;
  // Shelf item counts on the map just changed, so refresh the layout in the background.
  loadLayout(true);
}

// --- Search/scan-driven selection (UnifiedSearchBar -> ItemDetailCard) ---
const selectedItem = ref<Item | null>(null);
const lastSelectionSource = ref<'barcode' | 'manual'>('manual');
const zoneNameById = ref<Map<number, string>>(new Map());

const selectedItemZoneLabel = computed(() => {
  if (!selectedItem.value || !layout.value?.has_custom_layout) return undefined;
  const node = layout.value.nodes.find((n) => n.rack_code === parseRackCode(selectedItem.value!.shelf_position));
  if (!node || node.zone_id == null) return undefined;
  return zoneNameById.value.get(node.zone_id);
});

// --- Direct map-click drill-down (rack -> level -> items), unchanged from before ---
const selectedRack = ref<string | null>(null);
const rackLevels = ref<RackLevelsResponse | null>(null);
const loadingRack = ref(false);

const selectedLevel = ref<string | null>(null);
const levelItems = ref<Item[]>([]);
const loadingLevelItems = ref(false);

// Whichever flow set it, this is what the maps highlight/pan to.
const highlightShelfPosition = computed(() => selectedItem.value?.shelf_position ?? selectedLevel.value);
const highlightRackCode = computed(() =>
  selectedItem.value ? parseRackCode(selectedItem.value.shelf_position) : selectedRack.value
);

function parseRackCode(shelfPosition: string): string | null {
  const match = shelfPosition.match(/^(\d+)/);
  return match ? match[1] : null;
}

async function loadLayout(silent = false) {
  if (!silent) loadingLayout.value = true;
  try {
    layout.value = await getWarehouseLayout();
    if (layout.value.has_custom_layout) {
      const zones = await getZones();
      zoneNameById.value = new Map(zones.map((z) => [z.id, z.name]));
    }
  } finally {
    if (!silent) loadingLayout.value = false;
  }
}

// --- UnifiedSearchBar handlers ---

async function handleScanItem(item: Item) {
  lastSelectionSource.value = 'barcode';
  closeDrilldown();

  // Scan & Confirm: barcode reads execute the toggled action immediately with qty 1.
  try {
    const payload = { barcode: item.barcode, quantity: 1, source: 'barcode' as const };
    const res = mode.value === 'deposit' ? await depositItem(payload) : await withdrawItem(payload);
    selectedItem.value = res.item;
    show('success', res.message);
    activityLogRef.value?.refresh();
  } catch (err: any) {
    // Still show the item card even if the auto-action failed (e.g. insufficient stock),
    // so the operator can see what's there and act manually.
    selectedItem.value = item;
    show('error', err?.data?.detail || "Automatic operation failed");
  }
}

function handleScanNotFound(code: string) {
  show('error', `No item found for code "${code}"`);
}

function handleLocateItem(item: Item) {
  lastSelectionSource.value = 'manual';
  closeDrilldown();
  selectedItem.value = item;
}

function handleItemUpdated(item: Item) {
  selectedItem.value = item;
  activityLogRef.value?.refresh();
}

function clearSelection() {
  selectedItem.value = null;
  searchBarRef.value?.focus();
}

// --- Direct map click flow (kept for browsing without search) ---

async function selectRack(rackCode: string) {
  selectedItem.value = null;
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
  selectedItem.value = null;
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

function closeDrilldown() {
  selectedRack.value = null;
  rackLevels.value = null;
  selectedLevel.value = null;
  levelItems.value = [];
}

onMounted(loadLayout);
</script>
