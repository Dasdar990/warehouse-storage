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
        <template v-for="row in displayRows" :key="row.key">
          <!-- Group header: same P/N (or name), several serials -->
          <tr
            v-if="row.kind === 'group'"
            class="cursor-pointer bg-surface-2/30 transition-colors hover:bg-surface-2/60"
            @click="toggleGroup(row.key)"
          >
            <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
              <span class="inline-flex items-center gap-1.5">
                <span
                  class="inline-block w-3 text-center text-muted transition-transform"
                  :style="{
                    transform: expandedGroups.has(row.key)
                      ? 'rotate(90deg)'
                      : 'none',
                  }"
                  >▶</span
                >
                {{ row.items[0].name }}
              </span>
            </td>
            <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
              <span v-if="row.pn" class="inline-flex items-center gap-1.5">
                <span class="badge badge--pn">{{ row.pn }}</span>
              </span>
              <span v-else class="text-[0.82rem] text-muted">—</span>
              <span
                class="ml-1.5 rounded-full bg-accent/15 px-1.5 py-0.5 text-[0.68rem] font-bold text-accent"
                >×{{ row.items.length }} serials</span
              >
            </td>
            <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
              <span class="badge badge--category">{{
                row.items[0].category
              }}</span>
            </td>
            <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
              <span v-if="row.items[0].program" class="badge badge--program">{{
                row.items[0].program
              }}</span>
              <span v-else class="text-[0.82rem] text-muted">—</span>
            </td>
            <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
              <span
                class="badge badge--size"
                :class="`badge--size-${row.items[0].size}`"
                >{{ sizeLabel(row.items[0].size) }}</span
              >
            </td>
            <td
              v-if="showShelf"
              class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5"
            >
              <span class="text-[0.82rem] text-muted">{{
                row.locationsLabel
              }}</span>
            </td>
            <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
              {{ row.totalQuantity }}
            </td>
            <td
              class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5"
            ></td>
            <td
              class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5"
            ></td>
          </tr>

          <!-- Expanded serials for that group -->
          <template v-if="row.kind === 'group' && expandedGroups.has(row.key)">
            <tr
              v-for="item in row.items"
              :key="item.id"
              class="bg-surface/40"
              :class="{
                'cursor-pointer transition-colors hover:bg-surface-2/60':
                  selectable,
              }"
              @click="onRowClick(item, $event)"
            >
              <td
                class="whitespace-nowrap border-b border-[#1c222c] py-2 pl-8 pr-2 text-[0.85rem] text-muted"
              >
                ↳ S/N {{ item.serial || "—" }}
              </td>
              <td
                class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2"
              ></td>
              <td
                class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2"
              ></td>
              <td
                class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2"
              ></td>
              <td
                class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2"
              ></td>
              <td
                v-if="showShelf"
                class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2"
              >
                <span v-if="item.shelf_position" class="badge badge--shelf">{{
                  item.shelf_position
                }}</span>
                <span
                  v-else-if="item.zone_id"
                  class="badge badge--shelf"
                  title="Placed at zone-level, no specific shelf"
                  >📍 {{ zoneName(item.zone_id) }}</span
                >
                <span v-else class="text-[0.82rem] text-muted">—</span>
              </td>
              <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2">
                {{ item.quantity }}
              </td>
              <td
                class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2 font-mono text-muted"
              >
                {{ item.barcode }}
              </td>
              <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2">
                <DashboardItemRowActions
                  :item="item"
                  :show-locate="showLocate"
                  @info="emit('info', $event)"
                  @locate="emit('locate', $event)"
                  @move="(i, a) => emit('move', i, a)"
                  @relocate="emit('relocate', $event)"
                />
              </td>
            </tr>
          </template>

          <!-- Standalone item, no grouping -->
          <tr
            v-if="row.kind === 'single'"
            :class="{
              'cursor-pointer transition-colors hover:bg-surface-2/60':
                selectable,
            }"
            @click="onRowClick(row.item, $event)"
          >
            <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
              {{ row.item.name }}
              <div
                v-if="row.item.tags?.length"
                class="mt-1 flex flex-wrap gap-1"
              >
                <span
                  v-for="tag in row.item.tags"
                  :key="tag"
                  class="rounded-full bg-surface-2 px-1.5 py-0.5 text-[0.68rem] font-semibold text-muted"
                  >#{{ tag }}</span
                >
              </div>
              <div
                v-if="row.item.notes"
                class="mt-1 max-w-50 truncate text-[0.75rem] italic text-muted"
                :title="row.item.notes"
              >
                📝 {{ row.item.notes }}
              </div>
            </td>
            <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
              <span v-if="row.item.pn" class="inline-flex items-center gap-1.5">
                <span class="badge badge--pn">{{ row.item.pn }}</span>
              </span>
              <span v-else class="text-[0.82rem] text-muted">—</span>
              <div
                v-if="row.item.serial"
                class="mt-1 font-mono text-[0.7rem] text-muted"
              >
                S/N {{ row.item.serial }}
              </div>
            </td>
            <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
              <span class="badge badge--category">{{ row.item.category }}</span>
            </td>
            <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
              <span v-if="row.item.program" class="badge badge--program">{{
                row.item.program
              }}</span>
              <span v-else class="text-[0.82rem] text-muted">—</span>
            </td>
            <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
              <span
                class="badge badge--size"
                :class="`badge--size-${row.item.size}`"
                >{{ sizeLabel(row.item.size) }}</span
              >
            </td>
            <td
              v-if="showShelf"
              class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5"
            >
              <span v-if="row.item.shelf_position" class="badge badge--shelf">{{
                row.item.shelf_position
              }}</span>
              <span
                v-else-if="row.item.zone_id"
                class="badge badge--shelf"
                title="Placed at zone-level, no specific shelf"
                >📍 {{ zoneName(row.item.zone_id) }}</span
              >
              <span
                v-else
                class="text-[0.82rem] text-muted"
                title="Fully withdrawn -- no shelf assigned"
                >—</span
              >
            </td>
            <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
              {{ row.item.quantity }}
            </td>
            <td
              class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5 font-mono text-muted"
            >
              {{ row.item.barcode }}
            </td>
            <td class="whitespace-nowrap border-b border-[#1c222c] px-2 py-2.5">
              <DashboardItemRowActions
                :item="row.item"
                :show-locate="showLocate"
                @info="emit('info', $event)"
                @locate="emit('locate', $event)"
                @move="(i, a) => emit('move', i, a)"
                @relocate="emit('relocate', $event)"
              />
            </td>
          </tr>
        </template>
      </tbody>
    </table>
    <p v-else class="py-7.5 text-center text-muted">
      No items match the current filters.
    </p>
  </div>
</template>

<script setup lang="ts">
import type { Item, Zone } from "~/composables/useWarehouseApi";

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

const { getZones } = useWarehouseApi();

// Fetched lazily (only if the table actually has to render a zone-only
// item) so pages that never deal with zones don't pay for the request.
const zoneCache = ref<Zone[]>([]);
watch(
  () => props.items,
  (items) => {
    if (!zoneCache.value.length && items.some((i) => i.zone_id)) {
      getZones()
        .then((z) => (zoneCache.value = z))
        .catch(() => {});
    }
  },
  { immediate: true },
);
function zoneName(zoneId: number): string {
  return (
    zoneCache.value.find((z) => z.id === zoneId)?.name ?? `Zone #${zoneId}`
  );
}

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

// --- Group same P/N (or, lacking one, same name) items into one collapsible
// row -- this is what a bulk multi-serial creation looks like in the table,
// so instead of N near-identical rows you get one row you expand to see
// each serial. A lone item never gets a group wrapper. ---
type Row =
  | { kind: "single"; key: string; item: Item }
  | {
      kind: "group";
      key: string;
      pn: string;
      items: Item[];
      totalQuantity: number;
      locationsLabel: string;
    };

function groupKey(item: Item): string {
  return (item.pn || item.name).trim().toLowerCase();
}

function locationLabel(item: Item): string {
  if (item.shelf_position) return item.shelf_position;
  if (item.zone_id) return `zone:${item.zone_id}`;
  return "—";
}

const expandedGroups = ref<Set<string>>(new Set());
function toggleGroup(key: string) {
  const next = new Set(expandedGroups.value);
  if (next.has(key)) next.delete(key);
  else next.add(key);
  expandedGroups.value = next;
}

const displayRows = computed<Row[]>(() => {
  const buckets = new Map<string, Item[]>();
  for (const item of props.items) {
    const key = groupKey(item);
    const list = buckets.get(key);
    if (list) list.push(item);
    else buckets.set(key, [item]);
  }

  const rows: Row[] = [];
  for (const item of props.items) {
    const key = groupKey(item);
    const bucket = buckets.get(key)!;
    if (bucket.length <= 1) {
      rows.push({ kind: "single", key: `i${item.id}`, item });
      continue;
    }
    // Only emit the group header once, at the position of its first item.
    if (bucket[0].id !== item.id) continue;
    const locations = new Set(bucket.map(locationLabel));
    rows.push({
      kind: "group",
      key: `g${key}`,
      pn: bucket[0].pn,
      items: bucket,
      totalQuantity: bucket.reduce((sum, i) => sum + i.quantity, 0),
      locationsLabel:
        locations.size === 1
          ? [...locations][0] === "—"
            ? "—"
            : bucket[0].shelf_position
              ? bucket[0].shelf_position
              : `📍 ${zoneName(bucket[0].zone_id!)}`
          : `${locations.size} locations`,
    });
  }
  return rows;
});

function sizeLabel(size: string) {
  return { small: "S", big: "B", xl: "XL" }[size] || size;
}
</script>
