<template>
  <div class="flex flex-col gap-4">
    <!-- SEARCH BAR -->
    <div class="flex flex-wrap items-stretch gap-3">
      <UnifiedSearchBar
        ref="searchBarRef"
        class="min-w-0 flex-1"
        @scan-item="handleScanItem"
        @scan-not-found="handleScanNotFound"
        @locate-item="handleLocateItem"
      />
    </div>
    <section class="card">
      <div
        class="mb-2.5 text-sm font-semibold uppercase tracking-[0.22em] text-muted"
      >
        Quick actions
      </div>
      <div class="flex flex-wrap gap-2.5 max-[640px]:flex-col">
        <button
          type="button"
          class="group relative flex flex-1 items-center gap-3 overflow-hidden rounded-lg border border-accent/35 bg-accent/[0.09] px-3.5 py-3 text-left shadow-[0_1px_0_rgba(255,255,255,0.02)] transition-all duration-200 ease-out hover:-translate-y-0.5 hover:border-accent/60 hover:bg-accent/[0.16] hover:shadow-[0_8px_20px_rgba(0,0,0,0.28)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60 active:translate-y-0 active:shadow-none"
          @click="showAddItemModal = true"
        >
          <span
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-accent/22 transition-colors duration-200 group-hover:bg-accent/32"
          >
            <img src="~/assets/icons/add.svg" class="h-6 w-6" />
          </span>
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="text-[1.05rem] font-semibold text-ink">New Item</span>
            <span class="text-[0.8rem] text-muted"
              >Create a new item in the system</span
            >
          </span>
          <svg
            viewBox="0 0 24 24"
            class="h-4 w-4 shrink-0 -translate-x-1.5 text-muted opacity-0 transition-all duration-200 ease-out group-hover:translate-x-0 group-hover:text-accent group-hover:opacity-100"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M9 5l7 7-7 7" />
          </svg>
        </button>
        <button
          type="button"
          class="group relative flex flex-1 items-center gap-3 overflow-hidden rounded-lg border border-good/35 bg-good/[0.09] px-3.5 py-3 text-left shadow-[0_1px_0_rgba(255,255,255,0.02)] transition-all duration-200 ease-out hover:-translate-y-0.5 hover:border-good/60 hover:bg-good/[0.16] hover:shadow-[0_8px_20px_rgba(0,0,0,0.28)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-good/60 active:translate-y-0 active:shadow-none"
          @click="quickAction = 'deposit'"
        >
          <span
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-good/22 transition-colors duration-200 group-hover:bg-good/32"
          >
            <img src="~/assets/icons/inbox.svg" class="h-6 w-6" />
          </span>
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="text-[1.05rem] font-semibold text-ink"
              >Deposit Item</span
            >
            <span class="text-[0.8rem] text-muted"
              >Deposit an item to the warehouse</span
            >
          </span>
          <svg
            viewBox="0 0 24 24"
            class="h-4 w-4 shrink-0 -translate-x-1.5 text-muted opacity-0 transition-all duration-200 ease-out group-hover:translate-x-0 group-hover:text-green-300 group-hover:opacity-100"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M9 5l7 7-7 7" />
          </svg>
        </button>
        <button
          type="button"
          class="group relative flex flex-1 items-center gap-3 overflow-hidden rounded-lg border border-bad/35 bg-bad/[0.09] px-3.5 py-3 text-left shadow-[0_1px_0_rgba(255,255,255,0.02)] transition-all duration-200 ease-out hover:-translate-y-0.5 hover:border-bad/60 hover:bg-bad/[0.16] hover:shadow-[0_8px_20px_rgba(0,0,0,0.28)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bad/60 active:translate-y-0 active:shadow-none"
          @click="quickAction = 'withdraw'"
        >
          <span
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-bad/22 transition-colors duration-200 group-hover:bg-bad/32"
          >
            <img src="~/assets/icons/outbox.svg" class="h-6 w-6" />
          </span>
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="text-[1.05rem] font-semibold text-ink"
              >Withdraw Item</span
            >
            <span class="text-[0.8rem] text-muted"
              >Remove an item from the warehouse</span
            >
          </span>
          <svg
            viewBox="0 0 24 24"
            class="h-4 w-4 shrink-0 -translate-x-1.5 text-muted opacity-0 transition-all duration-200 ease-out group-hover:translate-x-0 group-hover:text-red-300 group-hover:opacity-100"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M9 5l7 7-7 7" />
          </svg>
        </button>
        <button
          type="button"
          class="group relative flex flex-1 items-center gap-3 overflow-hidden rounded-lg border border-edge bg-surface-2/60 px-3.5 py-3 text-left shadow-[0_1px_0_rgba(255,255,255,0.02)] transition-all duration-200 ease-out hover:-translate-y-0.5 hover:border-ink/30 hover:bg-surface-2 hover:shadow-[0_8px_20px_rgba(0,0,0,0.28)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink/30 active:translate-y-0 active:shadow-none"
          @click="showCatalogModal = true"
        >
          <span
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-ink/10 transition-colors duration-200 group-hover:bg-ink/16"
          >
            <svg
              viewBox="0 0 24 24"
              class="h-5 w-5 text-muted"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M20.59 13.41 11 3.83A2 2 0 0 0 9.59 3.24L3 3v6.59a2 2 0 0 0 .59 1.41l9.58 9.59a2 2 0 0 0 2.83 0l4.59-4.59a2 2 0 0 0 0-2.83Z"
              />
              <circle cx="7.5" cy="7.5" r="1.5" fill="currentColor" stroke="none" />
            </svg>
          </span>
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="text-[1.05rem] font-semibold text-ink"
              >Categories &amp; Programs</span
            >
            <span class="text-[0.8rem] text-muted"
              >Manage the catalog used when creating items</span
            >
          </span>
          <svg
            viewBox="0 0 24 24"
            class="h-4 w-4 shrink-0 -translate-x-1.5 text-muted opacity-0 transition-all duration-200 ease-out group-hover:translate-x-0 group-hover:text-ink group-hover:opacity-100"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </section>

    <!-- Interactive map: full width, so there's real room to work with -->
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

    <ActivityLog ref="activityLogRef" collapsible default-collapsed />

    <!-- The searched/scanned item, or the rack/level drill-down from a direct map
         click, now opens as a modal instead of pushing content below the map. -->
    <BaseModal
      :model-value="showDetailModal"
      :title="detailModalTitle"
      size="lg"
      @update:model-value="closeDetailModal"
    >
      <transition name="panel-fade" mode="out-in">
        <ItemDetailCard
          v-if="selectedItem"
          :key="`${selectedItem.id}-${autoStartAction ?? 'none'}-${selectionNonce}`"
          :item="selectedItem"
          :low-stock-threshold="layout?.low_stock_threshold"
          :zone-label="selectedItemZoneLabel"
          :default-source="lastSelectionSource"
          :auto-start-action="autoStartAction"
          @close="clearSelection"
          @updated="handleItemUpdated"
        />

        <div v-else class="flex flex-col gap-4">
          <MapRackLevelsPanel
            v-if="layout?.has_custom_layout && selectedRack && rackLevels"
            :rack="rackLevels"
            :selected-level="selectedLevel"
            :loading="loadingRack"
            :show-header="false"
            @select-level="selectLevel"
            @close="closeDrilldown"
          />

          <MapShelfDetailPanel
            v-if="selectedLevel"
            :shelf-position="selectedLevel"
            :items="levelItems"
            :loading="loadingLevelItems"
            :show-back="!!(layout?.has_custom_layout && selectedRack)"
            :show-header="false"
            @close="closeDrilldown"
            @back="backToRack"
            @select-item="handleSelectItemFromShelf"
            @info="openInfoModal"
          />
        </div>
      </transition>
    </BaseModal>

    <BaseModal v-model="showInfoModal" title="Activity log" size="md">
      <div v-if="infoItem">
        <p class="m-0 mb-3 text-[0.9rem] font-semibold text-ink">
          {{ infoItem.name }}
        </p>
        <ItemActivityLog :item-id="infoItem.id" />
      </div>
    </BaseModal>

    <BaseModal v-model="showCatalogModal" title="Categories & Programs" size="lg">
      <div class="flex flex-col gap-5">
        <section>
          <h2 class="mb-1 text-[1.05rem]">Categories</h2>
          <p class="m-0 mb-3 text-sm text-muted">
            Manage the categories available when creating a new item.
          </p>
          <AdminCategoryManager />
        </section>

        <section>
          <h2 class="mb-1 text-[1.05rem]">Programs</h2>
          <p class="m-0 mb-3 text-sm text-muted">
            Manage the (optional) programs available when creating a new item.
          </p>
          <AdminProgramManager />
        </section>
      </div>
    </BaseModal>

    <BaseModal v-model="showAddItemModal" title="New Item" size="lg">
      <DashboardAddItemForm @created="handleItemCreated" />
    </BaseModal>

    <BaseModal
      :model-value="!!quickAction"
      :title="quickAction === 'deposit' ? 'Deposit item' : 'Withdraw item'"
      size="md"
      @update:model-value="quickAction = null"
    >
      <QuickStockModal
        v-if="quickAction"
        :action="quickAction"
        @updated="handleQuickActionUpdated"
      />
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import type {
  Item,
  RackLevelsResponse,
  WarehouseLayout,
} from "~/composables/useWarehouseApi";

const {
  getWarehouseLayout,
  getRackLevels,
  getShelfItems,
  getZones,
  scanItem,
} = useWarehouseApi();
const { show } = useToast();
const route = useRoute();
const router = useRouter();

const searchBarRef = ref<{ focus: () => void } | null>(null);
const activityLogRef = ref<{ refresh: () => void } | null>(null);

const layout = ref<WarehouseLayout | null>(null);
const loadingLayout = ref(false);

// --- Quick action: New Item modal ---
const showAddItemModal = ref(false);

// --- Quick action: Deposit / Withdraw popup ---
const quickAction = ref<"deposit" | "withdraw" | null>(null);

// --- Quick action: Categories & Programs modal ---
const showCatalogModal = ref(false);

function handleQuickActionUpdated(item: Item) {
  closeDrilldown();
  lastSelectionSource.value = "manual";
  selectedItem.value = item;
  autoStartAction.value = undefined;
  selectionNonce.value += 1;
  activityLogRef.value?.refresh();
}

async function handleItemCreated(item: Item) {
  showAddItemModal.value = false;
  show("success", `"${item.name}" created — here's where it landed`);
  closeDrilldown();
  lastSelectionSource.value = "manual";
  selectedItem.value = item;
  autoStartAction.value = undefined;
  selectionNonce.value += 1;
  // Shelf item counts on the map just changed, so refresh the layout in the background.
  loadLayout(true);
}

// --- Search/scan-driven selection (UnifiedSearchBar -> ItemDetailCard) ---
const selectedItem = ref<Item | null>(null);
const lastSelectionSource = ref<"barcode" | "manual">("manual");
const autoStartAction = ref<"deposit" | "withdraw" | "move" | undefined>(undefined);
// Bumped on every selection so the card remounts (and autoStartAction jumps
// straight to the right step) even when re-selecting the same item.
const selectionNonce = ref(0);
const zoneNameById = ref<Map<number, string>>(new Map());

// --- Info icon on a shelf's item row: quick glance at its activity log ---
const showInfoModal = ref(false);
const infoItem = ref<Item | null>(null);

function openInfoModal(item: Item) {
  infoItem.value = item;
  showInfoModal.value = true;
}

const selectedItemZoneLabel = computed(() => {
  if (!selectedItem.value || !layout.value?.has_custom_layout) return undefined;
  const node = layout.value.nodes.find(
    (n) => n.rack_code === parseRackCode(selectedItem.value!.shelf_position),
  );
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

// "Locate" from the dashboard: highlights the item's shelf/rack on the map
// only -- no modal. Kept separate from `selectedItem` (which opens the
// detail modal) so the two behaviors don't get tangled.
const locatedItem = ref<Item | null>(null);

// Whichever flow set it, this is what the maps highlight.
const highlightShelfPosition = computed(
  () =>
    selectedItem.value?.shelf_position ??
    selectedLevel.value ??
    locatedItem.value?.shelf_position ??
    null,
);
const highlightRackCode = computed(() => {
  if (selectedItem.value) return parseRackCode(selectedItem.value.shelf_position);
  if (selectedRack.value) return selectedRack.value;
  if (locatedItem.value) return parseRackCode(locatedItem.value.shelf_position);
  return null;
});

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

function handleScanItem(item: Item) {
  lastSelectionSource.value = "barcode";
  closeDrilldown();
  selectedItem.value = item;
  autoStartAction.value = undefined;
  selectionNonce.value += 1;
}

function handleScanNotFound(code: string) {
  show("error", `No item found for code "${code}"`);
}

function handleLocateItem(item: Item) {
  lastSelectionSource.value = "manual";
  closeDrilldown();
  selectedItem.value = item;
  autoStartAction.value = undefined;
  selectionNonce.value += 1;
}

function handleItemUpdated(item: Item) {
  selectedItem.value = item;
  activityLogRef.value?.refresh();
}

/** Row click (or a Deposit/Withdraw button) on the shelf's item list -- jump
 *  straight into the full item card, optionally already on the right step. */
function handleSelectItemFromShelf(
  item: Item,
  action?: "deposit" | "withdraw" | "move",
) {
  lastSelectionSource.value = "manual";
  selectedItem.value = item;
  autoStartAction.value = action;
  selectionNonce.value += 1;
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
  locatedItem.value = null;
}

// --- Results modal: shows the searched/scanned item or the map drill-down ---
const showDetailModal = computed(
  () => !!selectedItem.value || !!selectedRack.value || !!selectedLevel.value,
);

const detailModalTitle = computed(() => {
  if (selectedItem.value) return selectedItem.value.name;
  if (selectedLevel.value) return `Shelf ${selectedLevel.value}`;
  if (selectedRack.value) {
    return `Rack ${rackLevels.value?.label || selectedRack.value}`;
  }
  return "";
});

function closeDetailModal() {
  clearSelection();
  closeDrilldown();
}

/** Coming from the dashboard's "Locate" button: `?locate=<barcode>` highlights
 *  that item's shelf/rack on the map -- it doesn't open the item modal, since
 *  the point is just to see where it is. */
async function handleLocateFromQuery() {
  const barcode = route.query.locate;
  if (typeof barcode !== "string" || !barcode) return;
  try {
    const item = await scanItem(barcode);
    selectedItem.value = null;
    quickAction.value = null;
    closeDrilldown();
    locatedItem.value = item;
    show("success", `Highlighted on shelf ${item.shelf_position}.`);
  } catch {
    show("error", "Couldn't find that item anymore -- it may have been removed.");
  } finally {
    // Strip the query param so a refresh/back-nav doesn't re-trigger this.
    router.replace({ path: "/", query: {} });
  }
}

// Same-route navigations (e.g. clicking "Locate" in the item modal while
// already on this page) don't remount the page, so onMounted alone would
// miss them -- watch the query too.
watch(
  () => route.query.locate,
  (val) => {
    if (val) handleLocateFromQuery();
  },
);

onMounted(() => {
  loadLayout();
  handleLocateFromQuery();
});
</script>

<style scoped>
.panel-fade-enter-active,
.panel-fade-leave-active {
  transition: all 0.18s ease-out;
}
.panel-fade-enter-from,
.panel-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
