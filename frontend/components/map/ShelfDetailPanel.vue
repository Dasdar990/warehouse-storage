<template>
  <section :class="showHeader ? 'card' : ''">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <button v-if="showBack" class="btn btn--ghost btn--small mb-2" type="button" @click="emit('back')">
          ← Back to rack
        </button>
        <h2 v-if="showHeader">Level {{ shelfPosition }}</h2>
        <p class="mt-1 mb-0 text-[0.85rem] text-muted">
          {{ items.length }} item type(s) · {{ totalQuantity }} unit(s) total
        </p>
      </div>
      <div class="flex items-center gap-2">
        <NuxtLink
          class="inline-block rounded-lg border border-edge px-3.5 py-2 text-[0.8rem] font-semibold text-ink no-underline"
          :to="{ path: '/dashboard', query: { shelf_position: shelfPosition } }"
        >
          Open in Dashboard
        </NuxtLink>
        <button v-if="showHeader" class="rounded-lg bg-transparent px-2.5 py-1 text-base text-muted transition-colors hover:text-ink" title="Close" @click="emit('close')">✕</button>
      </div>
    </div>

    <p v-if="loading" class="py-5 text-muted">Loading shelf contents…</p>
    <template v-else>
      <div v-if="items.length > 4" class="relative mt-3.5 mb-1">
        <svg
          viewBox="0 0 24 24"
          class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="m21 21-4.3-4.3" />
        </svg>
        <input
          v-model="query"
          type="text"
          placeholder="Find an item on this shelf — name, P/N, S/N, or barcode…"
          class="field-input h-9.5 w-full py-2 pl-9 text-[0.85rem]"
        />
      </div>
      <p v-if="query && !filteredItems.length" class="py-5 text-center text-muted">
        No item on this shelf matches "{{ query }}".
      </p>
      <DashboardItemTable
        v-else
        :items="filteredItems"
        :show-shelf="false"
        :show-locate="false"
        selectable
        @select="emit('select-item', $event)"
        @move="(item, action) => emit('select-item', item, action)"
      />
    </template>
  </section>
</template>

<script setup lang="ts">
import type { Item } from '~/composables/useWarehouseApi'

const props = withDefaults(
  defineProps<{
    shelfPosition: string
    items: Item[]
    loading: boolean
    showBack?: boolean
    showHeader?: boolean
  }>(),
  { showHeader: true },
)

const emit = defineEmits<{
  close: []
  back: []
  'select-item': [item: Item, action?: 'deposit' | 'withdraw']
}>()

const query = ref('')

// Reset the local search whenever a different shelf is opened, so a stale
// filter from the previous shelf doesn't silently hide everything here.
watch(
  () => props.shelfPosition,
  () => {
    query.value = ''
  },
)

const filteredItems = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return props.items
  return props.items.filter((item) =>
    [item.name, item.pn, item.serial, item.barcode]
      .filter(Boolean)
      .some((field) => field!.toLowerCase().includes(q)),
  )
})

const totalQuantity = computed(() => props.items.reduce((sum, i) => sum + i.quantity, 0))
</script>
