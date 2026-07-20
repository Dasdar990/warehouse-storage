<template>
  <section class="card">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <button v-if="showBack" class="btn btn--ghost btn--small mb-2" type="button" @click="emit('back')">
          ← Back to rack
        </button>
        <h2>Level {{ shelfPosition }}</h2>
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
        <button class="rounded-lg bg-transparent px-2.5 py-1 text-base text-muted" title="Close" @click="emit('close')">✕</button>
      </div>
    </div>

    <p v-if="loading" class="py-5 text-muted">Loading shelf contents…</p>
    <DashboardItemTable v-else :items="items" :show-shelf="false" />
  </section>
</template>

<script setup lang="ts">
import type { Item } from '~/composables/useWarehouseApi'

const props = defineProps<{
  shelfPosition: string
  items: Item[]
  loading: boolean
  showBack?: boolean
}>()

const emit = defineEmits<{ close: []; back: [] }>()

const totalQuantity = computed(() => props.items.reduce((sum, i) => sum + i.quantity, 0))
</script>
