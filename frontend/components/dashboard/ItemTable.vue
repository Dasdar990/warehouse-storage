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
            Program
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
        <tr
          v-for="item in items"
          :key="item.id"
          :class="{
            'cursor-pointer transition-colors hover:bg-surface-2/60':
              selectable,
          }"
          @click="onRowClick(item, $event)"
        >
          <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
            {{ item.name }}
            <div v-if="item.tags?.length" class="mt-1 flex flex-wrap gap-1">
              <span
                v-for="tag in item.tags"
                :key="tag"
                class="rounded-full bg-surface-2 px-1.5 py-0.5 text-[0.68rem] font-semibold text-muted"
                >#{{ tag }}</span
              >
            </div>
            <div
              v-if="item.notes"
              class="mt-1 max-w-50 truncate text-[0.75rem] italic text-muted"
              :title="item.notes"
            >
              📝 {{ item.notes }}
            </div>
          </td>
          <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
            <span v-if="item.pn" class="inline-flex items-center gap-1.5">
              <span class="badge badge--pn">{{ item.pn }}</span>
              <span
                v-if="shelfCountByPn.get(item.pn.toLowerCase())! > 1"
                class="rounded-full bg-accent/15 px-1.5 py-0.5 text-[0.68rem] font-bold text-accent"
                :title="`Also on: ${otherShelvesForPn(item).join(', ')}`"
              >
                ×{{ shelfCountByPn.get(item.pn.toLowerCase()) }} shelves
              </span>
            </span>
            <span v-else class="text-[0.82rem] text-muted">—</span>
            <div
              v-if="item.serial"
              class="mt-1 font-mono text-[0.7rem] text-muted"
            >
              S/N {{ item.serial }}
            </div>
          </td>
          <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
            <span class="badge badge--category">{{ item.category }}</span>
          </td>
          <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
            <span v-if="item.program" class="badge badge--program">{{
              item.program
            }}</span>
            <span v-else class="text-[0.82rem] text-muted">—</span>
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
            <span v-if="item.shelf_position" class="badge badge--shelf">{{
              item.shelf_position
            }}</span>
            <span
              v-else
              class="text-[0.82rem] text-muted"
              title="Fully withdrawn -- no shelf assigned"
              >—</span
            >
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
                class="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-lg border border-edge bg-transparent text-muted transition-colors hover:border-accent/40 hover:text-accent"
                title="Activity log for this item"
                @click="emit('info', item)"
              >
                <img src="~/assets/icons/activity.svg" class="w-5 h-auto" />
              </button>
              <button
                :disabled="!item.shelf_position"
                type="button"
                class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-accent/40 bg-accent/10 text-accent transition-colors hover:bg-accent/20 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-accent/10"
                title="Locate on the map"
                @click="emit('locate', item)"
              >
                <img src="~/assets/icons/locate.svg" class="w-5 h-auto" />
              </button>
              <button
                type="button"
                class="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-lg border border-good/40 bg-good/10 text-green-300 transition-colors hover:bg-good/20"
                title="Deposit stock"
                @click="emit('move', item, 'deposit')"
              >
                <svg
                  viewBox="0 0 24 24"
                  class="h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.25"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M12 5v14M5 12h14" />
                </svg>
              </button>
              <button
                type="button"
                class="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-lg border border-bad/40 bg-bad/10 text-red-300 transition-colors hover:bg-bad/20 disabled:cursor-not-allowed disabled:opacity-40"
                title="Withdraw stock"
                :disabled="item.quantity <= 0"
                @click="emit('move', item, 'withdraw')"
              >
                <svg
                  viewBox="0 0 24 24"
                  class="h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.25"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M5 12h14" />
                </svg>
              </button>
              <button
                type="button"
                class="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-lg border border-edge bg-transparent text-ink transition-colors hover:border-accent/40 hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-40"
                title="Move to another shelf"
                :disabled="item.quantity <= 0"
                @click="emit('relocate', item)"
              >
                <img src="~/assets/icons/move.svg" class="w-4 h-auto" />
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
    /** Makes whole rows clickable to open the item's details (used in the map drill-down). */
    selectable?: boolean;
    /** Hide the "Locate on the map" pin -- doesn't make sense when this table
     *  is already being shown as part of the map drill-down (you're looking
     *  right at the shelf). */
    showLocate?: boolean;
  }>(),
  { showShelf: true, selectable: false, showLocate: true },
);

const { labelUrl } = useWarehouseApi();

const emit = defineEmits<{
  move: [item: Item, action: "deposit" | "withdraw"];
  select: [item: Item];
  locate: [item: Item];
  info: [item: Item];
  relocate: [item: Item];
}>();

function onRowClick(item: Item, event: MouseEvent) {
  if (!props.selectable) return;
  // Don't hijack clicks on the row's own buttons/links (Deposit, Withdraw, Label).
  if ((event.target as HTMLElement)?.closest("button, a")) return;
  emit("select", item);
}

// Same part (same P/N) can legitimately live on more than one shelf --
// count occurrences (within the currently displayed/filtered list) so the
// table can flag it instead of looking like unrelated duplicate rows.
const shelfCountByPn = computed(() => {
  const counts = new Map<string, number>();
  for (const it of props.items) {
    if (!it.pn) continue;
    const key = it.pn.toLowerCase();
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return counts;
});

function otherShelvesForPn(item: Item) {
  if (!item.pn) return [];
  const key = item.pn.toLowerCase();
  return props.items
    .filter((it) => it.pn && it.pn.toLowerCase() === key && it.id !== item.id)
    .map((it) => it.shelf_position);
}

function sizeLabel(size: string) {
  return { small: "S", big: "B", xl: "XL" }[size] || size;
}
</script>
