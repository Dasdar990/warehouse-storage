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
      <button
        type="button"
        class="group relative flex items-center gap-3 overflow-hidden rounded-lg border border-accent/35 bg-accent/[0.09] px-3.5 py-3 text-left transition-all duration-200 ease-out hover:-translate-y-0.5 hover:border-accent/60 hover:bg-accent/[0.16] hover:shadow-[0_8px_20px_rgba(0,0,0,0.28)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60 active:translate-y-0 active:shadow-none"
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
          <span class="text-[0.8rem] text-muted">Create a new item in the system</span>
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
        @move="openMoveModal"
        @locate="handleLocate"
      />
    </section>

    <BaseModal
      v-model="showMoveModal"
      :title="moveAction === 'deposit' ? 'Deposit item' : 'Withdraw item'"
      size="md"
    >
      <ItemDetailCard
        v-if="moveItem"
        :key="`${moveItem.id}-${moveAction}-${moveNonce}`"
        :item="moveItem"
        :auto-start-action="moveAction"
        default-source="manual"
        @close="showMoveModal = false"
        @updated="onItemMoved"
      />
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
  </div>
</template>

<script setup lang="ts">
import type { Item, ItemFilters } from "~/composables/useWarehouseApi";

const route = useRoute();
const { listItems, listCategories, listItemPrograms, listItemShelves } = useWarehouseApi();

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
const loading = ref(false);
const showAddForm = ref(false);

// --- Quick withdraw/deposit straight from the table row, no page change ---
const showMoveModal = ref(false);
const moveItem = ref<Item | null>(null);
const moveAction = ref<"deposit" | "withdraw">("deposit");
const moveNonce = ref(0);

function openMoveModal(item: Item, action: "deposit" | "withdraw") {
  moveItem.value = item;
  moveAction.value = action;
  moveNonce.value += 1;
  showMoveModal.value = true;
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

function onItemMoved(item: Item) {
  moveItem.value = item;
  const idx = items.value.findIndex((i) => i.id === item.id);
  if (idx !== -1) items.value[idx] = item;
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
  await Promise.all([fetchItems(), fetchCategories(), fetchPrograms(), fetchShelves()]);
}

onMounted(() => {
  fetchItems();
  fetchCategories();
  fetchPrograms();
  fetchShelves();
});
</script>
