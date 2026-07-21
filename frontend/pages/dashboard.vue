<template>
  <div class="flex flex-col gap-4">
    <section class="flex items-center justify-between">
      <h2 class="text-[1.15rem]">Dashboard</h2>
      <button class="btn btn--ghost" @click="showAddForm = !showAddForm">
        {{ showAddForm ? 'Close' : '+ New Item' }}
      </button>
    </section>

    <transition
      enter-active-class="transition duration-200 ease-out"
      leave-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-1.5"
      leave-to-class="opacity-0 -translate-y-1.5"
    >
      <section v-if="showAddForm" class="card">
        <h3 class="mb-3.5 text-base">New Item</h3>
        <DashboardAddItemForm @created="onItemCreated" />
      </section>
    </transition>

    <section class="card">
      <DashboardFilterBar v-model="filters" :categories="categories" />
    </section>

    <section class="card">
      <p v-if="loading" class="text-muted">Loading…</p>
      <DashboardItemTable v-else :items="items" @move="openMoveModal" />
    </section>

    <BaseModal v-model="showMoveModal" title="Withdraw / Deposit" size="md">
      <ItemDetailCard
        v-if="moveItem"
        :key="moveItem.id"
        :item="moveItem"
        @close="showMoveModal = false"
        @updated="onItemMoved"
      />
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import type { Item, ItemFilters } from '~/composables/useWarehouseApi'

const route = useRoute()
const { listItems, listCategories } = useWarehouseApi()

const filters = ref<ItemFilters>({
  shelf_position: typeof route.query.shelf_position === 'string' ? route.query.shelf_position : undefined,
})
const items = ref<Item[]>([])
const categories = ref<string[]>([])
const loading = ref(false)
const showAddForm = ref(false)

// --- Quick withdraw/deposit straight from the table row, no page change ---
const showMoveModal = ref(false)
const moveItem = ref<Item | null>(null)

function openMoveModal(item: Item) {
  moveItem.value = item
  showMoveModal.value = true
}

function onItemMoved(item: Item) {
  moveItem.value = item
  const idx = items.value.findIndex((i) => i.id === item.id)
  if (idx !== -1) items.value[idx] = item
}

let debounceTimer: ReturnType<typeof setTimeout> | null = null

async function fetchItems() {
  loading.value = true
  try {
    items.value = await listItems(filters.value)
  } finally {
    loading.value = false
  }
}

async function fetchCategories() {
  categories.value = await listCategories()
}

watch(
  filters,
  () => {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(fetchItems, 250)
  },
  { deep: true }
)

async function onItemCreated() {
  showAddForm.value = false
  await Promise.all([fetchItems(), fetchCategories()])
}

onMounted(() => {
  fetchItems()
  fetchCategories()
})
</script>
