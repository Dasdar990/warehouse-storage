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
        class="btn btn--primary text-[0.85rem]"
        @click="showAddForm = !showAddForm"
      >
        {{ showAddForm ? "Close" : "+ New Item" }}
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
      <DashboardFilterBar v-model="filters" :categories="categories" :programs="programs" />
    </section>

    <section class="card">
      <p v-if="loading" class="text-muted">Loading…</p>
      <DashboardItemTable v-else :items="items" @move="openMoveModal" />
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
  </div>
</template>

<script setup lang="ts">
import type { Item, ItemFilters } from "~/composables/useWarehouseApi";

const route = useRoute();
const { listItems, listCategories, listItemPrograms } = useWarehouseApi();

const filters = ref<ItemFilters>({
  shelf_position:
    typeof route.query.shelf_position === "string"
      ? route.query.shelf_position
      : undefined,
});
const items = ref<Item[]>([]);
const categories = ref<string[]>([]);
const programs = ref<string[]>([]);
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

function onItemMoved(item: Item) {
  moveItem.value = item;
  const idx = items.value.findIndex((i) => i.id === item.id);
  if (idx !== -1) items.value[idx] = item;
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
  await Promise.all([fetchItems(), fetchCategories(), fetchPrograms()]);
}

onMounted(() => {
  fetchItems();
  fetchCategories();
  fetchPrograms();
});
</script>
