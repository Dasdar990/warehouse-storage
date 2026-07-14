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

function sizeLabel(size: string) {
  return { small: 'S', big: 'B', xl: 'XL' }[size] || size
}
</script>

<template>
  <div class="table-wrap scrollbar-slim">
    <table v-if="items.length">
      <thead>
        <tr>
          <th>Name</th>
          <th>P/N</th>
          <th>Category</th>
          <th>Size</th>
          <th v-if="showShelf">Shelf</th>
          <th>Qty</th>
          <th>Barcode</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td>{{ item.name }}</td>
          <td><span class="badge badge--pn">{{ item.pn }}</span></td>
          <td><span class="badge badge--category">{{ item.category }}</span></td>
          <td><span class="badge badge--size" :class="`badge--size-${item.size}`">{{ sizeLabel(item.size) }}</span></td>
          <td v-if="showShelf"><span class="badge badge--shelf">{{ item.shelf_position }}</span></td>
          <td :class="{ 'qty-low': item.quantity <= props.lowStockThreshold }">{{ item.quantity }}</td>
          <td class="mono">{{ item.barcode }}</td>
          <td>
            <a class="btn btn--small btn--ghost" :href="labelUrl(item.id)" target="_blank" rel="noopener">Label</a>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else class="empty-state">No items match the current filters.</p>
  </div>
</template>

<style scoped>
.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.92rem;
}

th {
  text-align: left;
  color: var(--text-dim);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 8px 10px;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}

td {
  padding: 10px;
  border-bottom: 1px solid #1c222c;
  white-space: nowrap;
}

.mono {
  font-family: 'SFMono-Regular', Consolas, monospace;
  color: var(--text-dim);
}

.qty-low {
  color: var(--red);
  font-weight: 700;
}

.empty-state {
  color: var(--text-dim);
  text-align: center;
  padding: 30px 0;
}

.btn {
  cursor: pointer;
  border: none;
  border-radius: 8px;
  padding: 6px 12px;
  font-weight: 600;
  font-size: 0.8rem;
  text-decoration: none;
  display: inline-block;
}

.btn--ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
}
</style>
