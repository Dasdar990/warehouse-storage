<template>
  <div class="scrollbar-slim overflow-x-auto">
    <table v-if="items.length" class="w-full border-collapse text-[0.92rem]">
      <thead>
        <tr>
          <th class="whitespace-nowrap border-b border-edge px-2.5 py-2 text-left text-[0.75rem] uppercase tracking-wider text-muted">Name</th>
          <th class="whitespace-nowrap border-b border-edge px-2.5 py-2 text-left text-[0.75rem] uppercase tracking-wider text-muted">P/N</th>
          <th class="whitespace-nowrap border-b border-edge px-2.5 py-2 text-left text-[0.75rem] uppercase tracking-wider text-muted">Category</th>
          <th class="whitespace-nowrap border-b border-edge px-2.5 py-2 text-left text-[0.75rem] uppercase tracking-wider text-muted">Size</th>
          <th v-if="showShelf" class="whitespace-nowrap border-b border-edge px-2.5 py-2 text-left text-[0.75rem] uppercase tracking-wider text-muted">Shelf</th>
          <th class="whitespace-nowrap border-b border-edge px-2.5 py-2 text-left text-[0.75rem] uppercase tracking-wider text-muted">Qty</th>
          <th class="whitespace-nowrap border-b border-edge px-2.5 py-2 text-left text-[0.75rem] uppercase tracking-wider text-muted">Barcode</th>
          <th class="whitespace-nowrap border-b border-edge px-2.5 py-2 text-left text-[0.75rem] uppercase tracking-wider text-muted"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td class="whitespace-nowrap border-b border-[#1c222c] px-2.5 py-2.5">{{ item.name }}</td>
          <td class="whitespace-nowrap border-b border-[#1c222c] px-2.5 py-2.5"><span class="badge badge--pn">{{ item.pn }}</span></td>
          <td class="whitespace-nowrap border-b border-[#1c222c] px-2.5 py-2.5"><span class="badge badge--category">{{ item.category }}</span></td>
          <td class="whitespace-nowrap border-b border-[#1c222c] px-2.5 py-2.5"><span class="badge badge--size" :class="`badge--size-${item.size}`">{{ sizeLabel(item.size) }}</span></td>
          <td v-if="showShelf" class="whitespace-nowrap border-b border-[#1c222c] px-2.5 py-2.5"><span class="badge badge--shelf">{{ item.shelf_position }}</span></td>
          <td
            class="whitespace-nowrap border-b border-[#1c222c] px-2.5 py-2.5"
            :class="item.quantity <= props.lowStockThreshold ? 'font-bold text-bad' : ''"
          >
            {{ item.quantity }}
          </td>
          <td class="whitespace-nowrap border-b border-[#1c222c] px-2.5 py-2.5 font-mono text-muted">{{ item.barcode }}</td>
          <td class="whitespace-nowrap border-b border-[#1c222c] px-2.5 py-2.5">
            <div class="flex gap-1.5">
              <button
                type="button"
                class="inline-block rounded-lg border border-accent/40 bg-accent/10 px-3 py-1.5 text-[0.8rem] font-semibold text-blue-300"
                @click="emit('move', item)"
              >
                Move
              </button>
              <a
                class="inline-block rounded-lg border border-edge px-3 py-1.5 text-[0.8rem] font-semibold text-ink no-underline"
                :href="labelUrl(item.id)"
                target="_blank"
                rel="noopener"
              >
                Label
              </a>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else class="py-[30px] text-center text-muted">No items match the current filters.</p>
  </div>
</template>

<script setup lang="ts">
import type { Item } from '~/composables/useWarehouseApi'

const props = withDefaults(
  defineProps<{
    items: Item[]
    showShelf?: boolean
    lowStockThreshold?: number
  }>(),
  { showShelf: true, lowStockThreshold: 3 }
)

const { labelUrl } = useWarehouseApi()

const emit = defineEmits<{ move: [item: Item] }>()

function sizeLabel(size: string) {
  return { small: 'S', big: 'B', xl: 'XL' }[size] || size
}
</script>
