<template>
  <div class="flex flex-col gap-3">
    <section
      class="card flex flex-wrap items-center justify-between gap-3 py-3"
    >
      <div>
        <h2 class="text-[1.05rem] font-semibold">Inventory Dashboard</h2>
        <p class="mt-1 text-sm text-muted">
          Keep stock operations simple and fast.
        </p>
      </div>
      <div class="flex items-center gap-2.5">
        <button
          type="button"
          class="flex items-center btn btn--small text-[0.9rem]"
          :class="
            labelSelectMode ? 'btn--confirm text-[#06280f]' : 'btn--ghost'
          "
          title="Select one or more serials to move, print labels for, or delete together"
          @click="toggleLabelSelectMode"
        >
          <img src="~/assets/icons/list.svg" class="w-6 mr-2 h-auto" />
          {{ labelSelectMode ? "Cancel selection" : "Select items" }}
        </button>
        <button
          type="button"
          class="flex items-center btn btn--ghost btn--small text-[0.9rem]"
          title="Create, rename, move or inspect storage boxes"
          @click="showBoxManagerModal = true"
        >
          <img
            src="~/assets/icons/package.svg"
            class="w-5 h-auto inline-block mr-1"
          />
          Manage boxes
        </button>
        <button
          type="button"
          class="flex items-center btn btn--ghost btn--small text-[0.9rem]"
          :disabled="!isAdmin"
          :title="
            isAdmin
              ? 'Move everything on a shelf, or a whole rack, at once'
              : 'Admins only'
          "
          @click="showSpecialMoveModal = true"
        >
          <img
            src="~/assets/icons/special_move.svg"
            class="w-7 h-auto i mr-1"
          />
          Special move
        </button>
        <button
          type="button"
          class="group relative flex items-center gap-3 overflow-hidden rounded-lg border border-accent/35 bg-accent/9 px-3.5 py-3 text-left transition-all duration-200 ease-out hover:-translate-y-0.5 hover:border-accent/60 hover:bg-accent/16 hover:shadow-[0_8px_20px_rgba(0,0,0,0.28)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60 active:translate-y-0 active:shadow-none"
          @click="showAddForm = !showAddForm"
        >
          <span
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-accent/22 transition-colors duration-200 group-hover:bg-accent/32"
          >
            <img src="~/assets/icons/add.svg" class="h-6 w-6" />
          </span>
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="text-[1.05rem] font-semibold text-ink">{{
              showAddForm ? "Close" : "New Item"
            }}</span>
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
      </div>
    </section>

    <transition
      enter-active-class="transition duration-200 ease-out"
      leave-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-1.5"
      leave-to-class="opacity-0 -translate-y-1.5"
    >
      <section v-if="showAddForm" class="card border border-accent/25">
        <DashboardAddItemForm @created="onItemCreated" />
      </section>
    </transition>

    <section class="card">
      <DashboardFilterBar
        v-model="filters"
        :categories="categories"
        :programs="programs"
        :shelves="shelves"
        :zones="zones"
        :tags="tags"
      />
    </section>

    <transition
      enter-active-class="transition duration-200 ease-out"
      leave-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-1.5"
      leave-to-class="opacity-0 -translate-y-1.5"
    >
      <section
        v-if="labelSelectMode"
        class="card flex flex-wrap items-center justify-between gap-3 border border-accent/25 py-2.5"
      >
        <p class="m-0 text-sm text-muted">
          {{
            selectedLabelIds.length
              ? `${selectedLabelIds.length} serial${selectedLabelIds.length === 1 ? "" : "s"} selected`
              : "Tick one or more serials in the table to select them"
          }}
        </p>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="btn btn--ghost btn--small text-[0.85rem]"
            :disabled="!selectedLabelIds.length"
            @click="selectedLabelIds = []"
          >
            Clear
          </button>
          <button
            type="button"
            class="btn btn--small text-[0.85rem]"
            :disabled="!selectedLabelIds.length"
            @click="showBulkMoveModal = true"
          >
            📍 Move {{ selectedLabelIds.length || "" }} selected
          </button>
          <button
            v-if="isAdmin"
            type="button"
            class="btn btn--small text-[0.85rem] border border-red-400/40 text-red-300 hover:bg-red-400/10"
            :disabled="!selectedLabelIds.length || deletingSelected"
            :title="!isAdmin ? 'Admins only' : undefined"
            @click="deleteSelectedItems"
          >
            🗑
            {{
              deletingSelected
                ? "Deleting…"
                : `Delete ${selectedLabelIds.length || ""}`
            }}
          </button>
          <a
            :href="
              selectedLabelIds.length
                ? labelBatchUrl(selectedLabelIds)
                : undefined
            "
            target="_blank"
            rel="noopener"
            class="btn btn--confirm btn--small text-[0.85rem] text-[#06280f]"
            :class="{
              'pointer-events-none opacity-50': !selectedLabelIds.length,
            }"
            @click="handleLabelsPrinted"
          >
            🖨 Print {{ selectedLabelIds.length || "" }} label{{
              selectedLabelIds.length === 1 ? "" : "s"
            }}
          </a>
        </div>
      </section>
    </transition>

    <section class="card">
      <p v-if="loading" class="text-muted">Loading…</p>
      <DashboardItemTable
        v-else
        :items="items"
        :selectable="!labelSelectMode"
        :label-select-mode="labelSelectMode"
        :selected-ids="selectedLabelIds"
        @update:selected-ids="selectedLabelIds = $event"
        @select="openViewModal"
        @move="openMoveModal"
        @relocate="openRelocateModal"
        @locate="handleLocate"
        @info="openInfoModal"
        @add-serial="openAddSerialModal"
      />
    </section>

    <BaseModal
      v-model="showMoveModal"
      :title="
        moveAction === 'deposit'
          ? 'Deposit item'
          : moveAction === 'withdraw'
            ? 'Withdraw item'
            : 'Move item'
      "
      size="md"
    >
      <ItemDetailCard
        v-if="moveItem"
        :key="`${moveItem.id}-${moveAction}-${moveNonce}`"
        :item="moveItem"
        :auto-start-action="moveAction"
        default-source="manual"
        @close="showMoveModal = false"
        @updated="onQuickActionUpdated"
        @deleted="handleItemDeleted"
      />
    </BaseModal>

    <BaseModal v-model="showViewModal" title="Item details" size="md">
      <ItemDetailCard
        v-if="viewItem"
        :key="viewItem.id"
        :item="viewItem"
        default-source="manual"
        @close="showViewModal = false"
        @updated="onViewModalUpdated"
        @deleted="handleItemDeleted"
      />
    </BaseModal>

    <BaseModal v-model="showInfoModal" title="Activity log" size="md">
      <div v-if="infoItem">
        <p class="m-0 mb-3 text-[0.9rem] font-semibold text-ink">
          {{ infoItem.name }}
        </p>
        <ItemActivityLog :item-id="infoItem.id" />
      </div>
    </BaseModal>

    <BaseModal v-model="showLocateModal" title="Choose a location" size="md">
      <DashboardLocateModal
        v-if="locateItem"
        :name="locateItem.name"
        :pn="locateItem.pn"
        :locations="locateCandidates"
        @locate="goToMap"
      />
    </BaseModal>

    <BaseModal v-model="showSpecialMoveModal" title="Special move" size="md">
      <DashboardSpecialMoveModal @done="handleSpecialMoveDone" />
    </BaseModal>

    <BaseModal v-model="showBoxManagerModal" title="Manage boxes" size="lg">
      <AdminBoxManager />
    </BaseModal>

    <BaseModal
      v-model="showBulkMoveModal"
      :title="`Move ${selectedLabelIds.length} item${selectedLabelIds.length === 1 ? '' : 's'}`"
      size="md"
    >
      <DashboardBulkMoveModal
        v-if="showBulkMoveModal"
        :items="selectedItemsForMove"
        @done="handleBulkMoveDone"
      />
    </BaseModal>

    <BaseModal v-model="showAddSerialModal" title="Add a new serial" size="md">
      <DashboardAddSerialModal
        v-if="addSerialBaseItem"
        :key="addSerialBaseItem.id"
        :base-item="addSerialBaseItem"
        @close="showAddSerialModal = false"
        @created="onSerialsAdded"
      />
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import type { Item, ItemFilters, Zone } from "~/composables/useWarehouseApi";

const { isAdmin } = useAuth();
const { show } = useToast();
const route = useRoute();
const {
  listItems,
  listCategories,
  listItemPrograms,
  listItemShelves,
  listItemTags,
  getZones,
  labelBatchUrl,
  deleteItemsBulk,
} = useWarehouseApi();

const filters = ref<ItemFilters>({
  shelf_position:
    typeof route.query.shelf_position === "string"
      ? route.query.shelf_position
      : undefined,
  zone_id:
    typeof route.query.zone_id === "string"
      ? Number(route.query.zone_id)
      : undefined,
});
const items = ref<Item[]>([]);
const categories = ref<string[]>([]);
const programs = ref<string[]>([]);
const shelves = ref<string[]>([]);
const zones = ref<Zone[]>([]);
const tags = ref<string[]>([]);
const loading = ref(false);
const showAddForm = ref(false);

// --- Quick withdraw/deposit/move straight from the table row, no page change ---
const showMoveModal = ref(false);
const moveItem = ref<Item | null>(null);
const moveAction = ref<"deposit" | "withdraw" | "move">("deposit");
const moveNonce = ref(0);

function openMoveModal(item: Item, action: "deposit" | "withdraw" | "move") {
  moveItem.value = item;
  moveAction.value = action;
  moveNonce.value += 1;
  showMoveModal.value = true;
}

function openRelocateModal(item: Item) {
  openMoveModal(item, "move");
}

// --- Click a row: open the full item card (view details, no forced action) ---
const showViewModal = ref(false);
const viewItem = ref<Item | null>(null);

function openViewModal(item: Item) {
  viewItem.value = item;
  showViewModal.value = true;
}

// --- Info icon: quick glance at this item's activity log only ---
const showInfoModal = ref(false);
const infoItem = ref<Item | null>(null);

function openInfoModal(item: Item) {
  infoItem.value = item;
  showInfoModal.value = true;
}

// --- Locate on the map: same P/N can live on several shelves, so if there's
// more than one location, let the operator pick which one to jump to. ---
const showLocateModal = ref(false);
const locateItem = ref<Item | null>(null);
const locateCandidates = ref<Item[]>([]);

async function handleLocate(item: Item) {
  if (!item.pn) {
    await goToMap(item);
    return;
  }
  try {
    const matches = await listItems({ pn: item.pn });
    if (matches.length <= 1) {
      await goToMap(item);
      return;
    }
    locateItem.value = item;
    locateCandidates.value = matches;
    showLocateModal.value = true;
  } catch {
    // If the lookup fails, still let the operator locate this one item.
    await goToMap(item);
  }
}

async function goToMap(item: Item) {
  showLocateModal.value = false;
  await navigateTo({ path: "/", query: { locate: item.barcode } });
}

// --- Label select mode: tick one or more serials (across groups, across
// the whole filtered list) and reprint their labels together in one
// batch instead of one popup per item. ---
const labelSelectMode = ref(false);
const selectedLabelIds = ref<number[]>([]);

function toggleLabelSelectMode() {
  labelSelectMode.value = !labelSelectMode.value;
  selectedLabelIds.value = [];
}

function handleLabelsPrinted() {
  // Leave the tab to print in the background; reset selection here so a
  // second batch starts clean instead of re-adding already-printed ids.
  labelSelectMode.value = false;
  selectedLabelIds.value = [];
}

const deletingSelected = ref(false);

async function deleteSelectedItems() {
  const ids = selectedLabelIds.value;
  if (!ids.length) return;
  if (
    !confirm(
      `Delete ${ids.length} item${ids.length === 1 ? "" : "s"}? This can't be undone.`,
    )
  ) {
    return;
  }
  deletingSelected.value = true;
  try {
    await deleteItemsBulk(ids);
    show("success", `${ids.length} item${ids.length === 1 ? "" : "s"} deleted`);
    const deleted = new Set(ids);
    items.value = items.value.filter((i) => !deleted.has(i.id));
    labelSelectMode.value = false;
    selectedLabelIds.value = [];
    await Promise.all([fetchShelves(), fetchTags()]);
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to delete the selected items");
  } finally {
    deletingSelected.value = false;
  }
}

// --- Move selected: relocate every currently-selected item to the same
// destination (a shelf, a zone, or a box) in one go. Reuses the same
// selection as the label/delete batch above. ---
const showBulkMoveModal = ref(false);

const selectedItemsForMove = computed(() =>
  items.value.filter((i) => selectedLabelIds.value.includes(i.id)),
);

async function handleBulkMoveDone() {
  showBulkMoveModal.value = false;
  labelSelectMode.value = false;
  selectedLabelIds.value = [];
  await fetchItems();
  await fetchShelves();
}

// --- Special move: admin-only bulk relocation of a whole shelf/rack ---
const showSpecialMoveModal = ref(false);
const showBoxManagerModal = ref(false);

async function handleSpecialMoveDone() {
  showSpecialMoveModal.value = false;
  await fetchItems();
  await fetchShelves();
}

// --- Add serial: create one (or more) new items sharing an existing
// group's descriptive fields, for when a fresh unit of the same part
// comes in. Triggered from the "+ Add serial" action on a group/row. ---
const showAddSerialModal = ref(false);
const addSerialBaseItem = ref<Item | null>(null);

function openAddSerialModal(groupItems: Item[]) {
  addSerialBaseItem.value = groupItems[0] ?? null;
  showAddSerialModal.value = true;
}

async function onSerialsAdded(_newItems: Item[]) {
  showAddSerialModal.value = false;
  // Re-fetch (rather than just appending) so the new serials only show up
  // if they actually match whatever filters are currently applied.
  await Promise.all([fetchItems(), fetchShelves(), fetchTags()]);
}

function syncItemInList(item: Item) {
  const idx = items.value.findIndex((i) => i.id === item.id);
  if (idx !== -1) items.value[idx] = item;
  fetchShelves();
  fetchTags();
}

function onQuickActionUpdated(item: Item) {
  moveItem.value = item;
  syncItemInList(item);
}

function onViewModalUpdated(item: Item) {
  viewItem.value = item;
  syncItemInList(item);
}

function handleItemDeleted(itemId: number) {
  showMoveModal.value = false;
  showViewModal.value = false;
  items.value = items.value.filter((i) => i.id !== itemId);
  fetchShelves();
}

let debounceTimer: ReturnType<typeof setTimeout> | null = null;

async function fetchItems() {
  loading.value = true;
  try {
    items.value = await listItems(filters.value);
  } finally {
    loading.value = false;
  }
}

async function fetchCategories() {
  categories.value = await listCategories();
}

async function fetchPrograms() {
  programs.value = await listItemPrograms();
}

/** Occupied shelves only -- a fully withdrawn item's shelf is cleared, so
 *  this naturally drops out of the list once nothing's on it anymore. */
async function fetchShelves() {
  shelves.value = await listItemShelves();
}

async function fetchZones() {
  zones.value = await getZones();
}

async function fetchTags() {
  tags.value = await listItemTags();
}

watch(
  filters,
  () => {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(fetchItems, 250);
  },
  { deep: true },
);

async function onItemCreated() {
  showAddForm.value = false;
  await Promise.all([
    fetchItems(),
    fetchCategories(),
    fetchPrograms(),
    fetchShelves(),
    fetchZones(),
    fetchTags(),
  ]);
}

onMounted(() => {
  fetchItems();
  fetchCategories();
  fetchPrograms();
  fetchShelves();
  fetchZones();
  fetchTags();
});
</script>
