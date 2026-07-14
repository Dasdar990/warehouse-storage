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

<template>
  <div class="dashboard-page">
    <section class="header-row">
      <h2>Dashboard</h2>
      <button class="btn btn--ghost" @click="showAddForm = !showAddForm">
        {{ showAddForm ? 'Close' : '+ New Item' }}
      </button>
    </section>

    <transition name="fade">
      <section v-if="showAddForm" class="add-card">
        <h3>New Item</h3>
        <DashboardAddItemForm @created="onItemCreated" />
      </section>
    </transition>

    <section class="filter-card">
      <DashboardFilterBar v-model="filters" :categories="categories" />
    </section>

    <section class="table-card">
      <p v-if="loading" class="loading">Loading…</p>
      <DashboardItemTable v-else :items="items" />
    </section>
  </div>
</template>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-row h2 {
  font-size: 1.15rem;
}

.add-card,
.filter-card,
.table-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow);
}

.add-card h3 {
  margin-bottom: 14px;
  font-size: 1rem;
}

.loading {
  color: var(--text-dim);
}

.btn {
  cursor: pointer;
  border: none;
  border-radius: 8px;
  padding: 10px 18px;
  font-weight: 600;
  font-size: 0.95rem;
}

.btn--ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
