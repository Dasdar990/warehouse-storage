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
          class="group relative flex flex-1 items-center gap-3 overflow-hidden rounded-lg border border-edge/70 bg-edge/5 px-3.5 py-3 text-left transition-all duration-200 ease-out hover:-translate-y-0.5 hover:border-accent/50 hover:bg-accent/[0.08] hover:shadow-[0_8px_20px_rgba(0,0,0,0.28)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60 active:translate-y-0 active:shadow-none"
          @click="showAddItemModal = true"
        >
          <span
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-accent/12 transition-colors duration-200 group-hover:bg-accent/22"
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
          class="group relative flex flex-1 items-center gap-3 overflow-hidden rounded-lg border border-edge/70 bg-edge/5 px-3.5 py-3 text-left transition-all duration-200 ease-out hover:-translate-y-0.5 hover:border-good/50 hover:bg-good/[0.08] hover:shadow-[0_8px_20px_rgba(0,0,0,0.28)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-good/60 active:translate-y-0 active:shadow-none"
          @click="quickAction = 'deposit'"
        >
          <span
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-good/12 transition-colors duration-200 group-hover:bg-good/22"
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
          class="group relative flex flex-1 items-center gap-3 overflow-hidden rounded-lg border border-edge/70 bg-edge/5 px-3.5 py-3 text-left transition-all duration-200 ease-out hover:-translate-y-0.5 hover:border-bad/50 hover:bg-bad/[0.08] hover:shadow-[0_8px_20px_rgba(0,0,0,0.28)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bad/60 active:translate-y-0 active:shadow-none"
          @click="quickAction = 'withdraw'"
        >
          <span
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-bad/12 transition-colors duration-200 group-hover:bg-bad/22"
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

    <!-- Below the map: either the searched/scanned item, or the rack/level drill-down from a direct map click -->
    <div ref="resultsRef" class="flex flex-col gap-4">
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
        @select-level="selectLevel"
        @close="closeDrilldown"
      />

      <MapShelfDetailPanel
        v-if="selectedLevel"
        :shelf-position="selectedLevel"
        :items="levelItems"
        :loading="loadingLevelItems"
        :show-back="!!(layout?.has_custom_layout && selectedRack)"
        @close="closeDrilldown"
        @back="backToRack"
        @select-item="handleSelectItemFromShelf"
      />

      <p
        v-if="!selectedLevel && !(layout?.has_custom_layout && selectedRack)"
        class="card border border-dashed border-edge/70 text-sm text-muted"
      >
        Start with a search or scan, or click a shelf on the map, to open the item
        details.
      </p>
    </div>
    </transition>
    </div>

    <ActivityLog ref="activityLogRef" collapsible default-collapsed />

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
  withdrawItem,
  depositItem,
} = useWarehouseApi();
const { mode } = useOperationMode();
const { show } = useToast();

const searchBarRef = ref<{ focus: () => void } | null>(null);
const activityLogRef = ref<{ refresh: () => void } | null>(null);
const resultsRef = ref<HTMLElement | null>(null);

/** Smoothly bring the drill-down/results area into view -- keeps the flow
 *  fluid on smaller screens where the map pushes it below the fold. */
function scrollToResults() {
  nextTick(() => {
    resultsRef.value?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

const layout = ref<WarehouseLayout | null>(null);
const loadingLayout = ref(false);

// --- Quick action: New Item modal ---
const showAddItemModal = ref(false);

// --- Quick action: Deposit / Withdraw popup ---
const quickAction = ref<"deposit" | "withdraw" | null>(null);

function handleQuickActionUpdated(item: Item) {
  closeDrilldown();
  lastSelectionSource.value = "manual";
  selectedItem.value = item;
  autoStartAction.value = undefined;
  selectionNonce.value += 1;
  activityLogRef.value?.refresh();
  scrollToResults();
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
const autoStartAction = ref<"deposit" | "withdraw" | undefined>(undefined);
// Bumped on every selection so the card remounts (and autoStartAction jumps
// straight to the right step) even when re-selecting the same item.
const selectionNonce = ref(0);
const zoneNameById = ref<Map<number, string>>(new Map());

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

// Whichever flow set it, this is what the maps highlight/pan to.
const highlightShelfPosition = computed(
  () => selectedItem.value?.shelf_position ?? selectedLevel.value,
);
const highlightRackCode = computed(() =>
  selectedItem.value
    ? parseRackCode(selectedItem.value.shelf_position)
    : selectedRack.value,
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
  lastSelectionSource.value = "barcode";
  closeDrilldown();

  // Scan & Confirm: barcode reads execute the toggled action immediately with qty 1.
  try {
    const payload = {
      barcode: item.barcode,
      quantity: 1,
      source: "barcode" as const,
    };
    const res =
      mode.value === "deposit"
        ? await depositItem(payload)
        : await withdrawItem(payload);
    selectedItem.value = res.item;
    show("success", res.message);
    activityLogRef.value?.refresh();
  } catch (err: any) {
    // Still show the item card even if the auto-action failed (e.g. insufficient stock),
    // so the operator can see what's there and act manually.
    selectedItem.value = item;
    show("error", err?.data?.detail || "Automatic operation failed");
  }
  autoStartAction.value = undefined;
  selectionNonce.value += 1;
  scrollToResults();
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
  scrollToResults();
}

function handleItemUpdated(item: Item) {
  selectedItem.value = item;
  activityLogRef.value?.refresh();
}

/** Row click (or a Deposit/Withdraw button) on the shelf's item list -- jump
 *  straight into the full item card, optionally already on the right step. */
function handleSelectItemFromShelf(
  item: Item,
  action?: "deposit" | "withdraw",
) {
  lastSelectionSource.value = "manual";
  selectedItem.value = item;
  autoStartAction.value = action;
  selectionNonce.value += 1;
  scrollToResults();
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
  scrollToResults();
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
  scrollToResults();
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
