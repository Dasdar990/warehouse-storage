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
          v-if="isAdmin"
          type="button"
          class="flex items-center btn btn--ghost btn--small text-[0.9rem]"
          title="Move everything on a shelf, or a whole rack, at once"
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
      />
    </section>

    <section class="card">
      <p v-if="loading" class="text-muted">Loading…</p>
      <DashboardItemTable
        v-else
        :items="items"
        selectable
        @select="openViewModal"
        @move="openMoveModal"
        @relocate="openRelocateModal"
        @locate="handleLocate"
        @info="openInfoModal"
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
  </div>
</template>

<script setup lang="ts">
import type { Item, ItemFilters } from "~/composables/useWarehouseApi";

type MoveActionType = "deposit" | "withdraw" | "move";

interface MoveModalState {
  showModal: boolean;
  item: Item | null;
  action: MoveActionType;
  nonce: number;
}

interface ViewModalState {
  showModal: boolean;
  item: Item | null;
}

interface InfoModalState {
  showModal: boolean;
  item: Item | null;
}

interface LocateModalState {
  showModal: boolean;
  item: Item | null;
  candidates: Item[];
}

const { isAdmin } = useAuth();
const route = useRoute();
const { listItems, listCategories, listItemPrograms, listItemShelves } =
  useWarehouseApi();

const filters = ref<ItemFilters>({
  shelf_position:
    typeof route.query.shelf_position === "string"
      ? route.query.shelf_position
      : undefined,
});
const items = ref<Item[]>([]);
const categories = ref<string[]>([]);
const programs = ref<string[]>([]);
const shelves = ref<string[]>([]);
const loading = ref<boolean>(false);
const showAddForm = ref<boolean>(false);

// --- Quick withdraw/deposit/move straight from the table row, no page change ---
const showMoveModal = ref<boolean>(false);
const moveItem = ref<Item | null>(null);
const moveAction = ref<MoveActionType>("deposit");
const moveNonce = ref<number>(0);

function openMoveModal(item: Item, action: MoveActionType): void {
  moveItem.value = item;
  moveAction.value = action;
  moveNonce.value += 1;
  showMoveModal.value = true;
}

function openRelocateModal(item: Item): void {
  openMoveModal(item, "move");
}

// --- Click a row: open the full item card (view details, no forced action) ---
const showViewModal = ref<boolean>(false);
const viewItem = ref<Item | null>(null);

function openViewModal(item: Item): void {
  viewItem.value = item;
  showViewModal.value = true;
}

// --- Info icon: quick glance at this item's activity log only ---
const showInfoModal = ref<boolean>(false);
const infoItem = ref<Item | null>(null);

function openInfoModal(item: Item): void {
  infoItem.value = item;
  showInfoModal.value = true;
}

// --- Locate on the map: same P/N can live on several shelves, so if there's
// more than one location, let the operator pick which one to jump to. ---
const showLocateModal = ref<boolean>(false);
const locateItem = ref<Item | null>(null);
const locateCandidates = ref<Item[]>([]);

async function handleLocate(item: Item): Promise<void> {
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

async function goToMap(item: Item): Promise<void> {
  showLocateModal.value = false;
  await navigateTo({ path: "/", query: { locate: item.barcode } });
}

// --- Special move: admin-only bulk relocation of a whole shelf/rack ---
const showSpecialMoveModal = ref<boolean>(false);

async function handleSpecialMoveDone(): Promise<void> {
  showSpecialMoveModal.value = false;
  await fetchItems();
  await fetchShelves();
}

function syncItemInList(item: Item): void {
  const idx = items.value.findIndex((i) => i.id === item.id);
  if (idx !== -1) items.value[idx] = item;
  fetchShelves();
}

function onQuickActionUpdated(item: Item): void {
  moveItem.value = item;
  syncItemInList(item);
}

function onViewModalUpdated(item: Item): void {
  viewItem.value = item;
  syncItemInList(item);
}

let debounceTimer: ReturnType<typeof setTimeout> | null = null;

async function fetchItems(): Promise<void> {
  loading.value = true;
  try {
    items.value = await listItems(filters.value);
  } finally {
    loading.value = false;
  }
}

async function fetchCategories(): Promise<void> {
  categories.value = await listCategories();
}

async function fetchPrograms(): Promise<void> {
  programs.value = await listItemPrograms();
}

/** Occupied shelves only -- a fully withdrawn item's shelf is cleared, so
 *  this naturally drops out of the list once nothing's on it anymore. */
async function fetchShelves(): Promise<void> {
  shelves.value = await listItemShelves();
}

watch(
  filters,
  () => {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(fetchItems, 250);
  },
  { deep: true },
);

async function onItemCreated(): Promise<void> {
  showAddForm.value = false;
  await Promise.all([
    fetchItems(),
    fetchCategories(),
    fetchPrograms(),
    fetchShelves(),
  ]);
}

onMounted(() => {
  fetchItems();
  fetchCategories();
  fetchPrograms();
  fetchShelves();
});
</script>
