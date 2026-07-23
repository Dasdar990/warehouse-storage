<template>
  <div class="scrollbar-slim overflow-x-auto">
    <table v-if="items.length" class="w-full border-collapse text-[0.92rem]">
      <thead>
        <tr>
          <th
            class="whitespace-nowrap border-b border-edge px-2 py-2 text-left text-[0.72rem] uppercase tracking-wider text-muted"
          >
            Name
          </th>
          <th
            class="whitespace-nowrap border-b border-edge px-2 py-2 text-left text-[0.72rem] uppercase tracking-wider text-muted"
          >
            P/N
          </th>
          <th
            class="whitespace-nowrap border-b border-edge px-2 py-2 text-left text-[0.72rem] uppercase tracking-wider text-muted"
          >
            Category
          </th>
          <th
            class="whitespace-nowrap border-b border-edge px-2 py-2 text-left text-[0.72rem] uppercase tracking-wider text-muted"
          >
            Size
          </th>
          <th
            v-if="showShelf"
            class="whitespace-nowrap border-b border-edge px-2 py-2 text-left text-[0.72rem] uppercase tracking-wider text-muted"
          >
            Shelf
          </th>
          <th
            class="whitespace-nowrap border-b border-edge px-2 py-2 text-left text-[0.72rem] uppercase tracking-wider text-muted"
          >
            Qty
          </th>
          <th
            class="whitespace-nowrap border-b border-edge px-2 py-2 text-left text-[0.72rem] uppercase tracking-wider text-muted"
          >
            Barcode
          </th>
          <th
            class="whitespace-nowrap border-b border-edge px-2 py-2 text-left text-[0.72rem] uppercase tracking-wider text-muted"
          ></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
            {{ item.name }}
          </td>
          <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
            <span v-if="item.pn" class="badge badge--pn">{{ item.pn }}</span>
            <span v-else class="text-[0.82rem] text-muted">—</span>
          </td>
          <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
            <span class="badge badge--category">{{ item.category }}</span>
          </td>
          <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
            <span
              class="badge badge--size"
              :class="`badge--size-${item.size}`"
              >{{ sizeLabel(item.size) }}</span
            >
          </td>
          <td
            v-if="showShelf"
            class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5"
          >
            <span class="badge badge--shelf">{{ item.shelf_position }}</span>
          </td>
          <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
            {{ item.quantity }}
          </td>
          <td
            class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5 font-mono text-muted"
          >
            {{ item.barcode }}
          </td>
          <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
            <div class="flex gap-1.5">
              <button
                type="button"
                class="inline-flex items-center gap-1.5 rounded-lg border border-accent/40 bg-accent/10 px-2.5 py-1.5 text-[0.78rem] font-semibold text-emerald-200 cursor-pointer"
                title="Add or remove stock"
                @click="emit('move', item)"
              >
                <svg
                  viewBox="0 0 24 24"
                  class="h-3.5 w-3.5"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M7 4v16M7 4 3 8M7 4l4 4" />
                  <path d="M17 20V4M17 20l-4-4M17 20l4-4" />
                </svg>
                Adjust
              </button>
              <a
                class="inline-flex items-center gap-1.5 rounded-lg border border-edge px-2.5 py-1.5 text-[0.78rem] font-semibold text-ink no-underline"
                :href="labelUrl(item.id)"
                target="_blank"
                rel="noopener"
              >
                <svg
                  viewBox="0 0 24 24"
                  class="h-3.5 w-3.5"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M8 3h8" />
                  <path
                    d="M8 3v3H6a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-2V3"
                  />
                  <rect x="8" y="12" width="8" height="8" rx="1" />
                </svg>
                Label
              </a>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else class="py-7.5 text-center text-muted">
      No items match the current filters.
    </p>
  </div>
</template>

<script setup lang="ts">
import type { Item } from "~/composables/useWarehouseApi";

const props = withDefaults(
  defineProps<{
    items: Item[];
    showShelf?: boolean;
  }>(),
  { showShelf: true },
);

const { labelUrl } = useWarehouseApi();

const emit = defineEmits<{ move: [item: Item] }>();

function sizeLabel(size: string) {
  return { small: "S", big: "B", xl: "XL" }[size] || size;
}
</script>
