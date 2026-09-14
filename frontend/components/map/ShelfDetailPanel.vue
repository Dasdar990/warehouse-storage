<template>
  <section :class="showHeader ? 'card' : ''">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <button
          v-if="showBack"
          class="btn btn--ghost btn--small mb-2"
          type="button"
          @click="emit('back')"
        >
          ← Back to rack
        </button>
        <h2 v-if="showHeader">{{ title || `Level ${shelfPosition}` }}</h2>
        <p class="mt-1 mb-0 text-[0.85rem] text-muted">
          {{ items.length }} item type(s) · {{ totalQuantity }} unit(s) total
        </p>
      </div>
      <div class="flex items-center gap-2">
        <NuxtLink
          class="inline-block rounded-lg border border-edge px-3.5 py-2 text-[0.8rem] font-semibold text-ink no-underline"
          :to="{
            path: '/dashboard',
            query: dashboardQuery || { shelf_position: shelfPosition },
          }"
        >
          Open in Dashboard
        </NuxtLink>
        <button
          v-if="showHeader"
          class="rounded-lg bg-transparent px-2.5 py-1 text-base text-muted transition-colors hover:text-ink"
          title="Close"
          @click="emit('close')"
        >
          ✕
        </button>
      </div>
    </div>

    <p v-if="loading" class="py-5 text-muted">Loading shelf contents…</p>
    <template v-else>
      <!-- Boxes: containers for generic items with no room for their own
           label (e.g. loose cables). Always shown for a real shelf level
           (even an otherwise-empty one) so a box is never invisible. -->
      <div v-if="shelfPosition && !disableBoxes" class="mt-3.5">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <p class="m-0 text-[0.78rem] font-semibold uppercase tracking-wide text-muted">
            📦 Boxes on this shelf
          </p>
          <button
            v-if="!creatingBox"
            type="button"
            class="btn btn--ghost btn--small"
            @click="startCreateBox"
          >
            + New box
          </button>
        </div>

        <div v-if="creatingBox" class="mt-2 flex items-center gap-1.5">
          <input
            v-model="newBoxName"
            type="text"
            placeholder="Box name (optional)"
            class="field-input h-9 flex-1 text-[0.82rem]"
            @keyup.enter="confirmCreateBox"
          />
          <button
            type="button"
            class="btn btn--confirm btn--small shrink-0"
            :disabled="boxBusy"
            @click="confirmCreateBox"
          >
            Create
          </button>
          <button
            type="button"
            class="btn btn--ghost btn--small shrink-0"
            @click="creatingBox = false"
          >
            Cancel
          </button>
        </div>

        <p v-if="loadingBoxes" class="mt-2 text-[0.82rem] text-muted">
          Loading boxes…
        </p>
        <p v-else-if="!boxes.length && !creatingBox" class="mt-2 text-[0.82rem] text-muted">
          No box on this shelf yet.
        </p>

        <div v-else class="mt-2 flex flex-col gap-1.5">
          <div
            v-for="box in boxes"
            :key="box.id"
            class="rounded-lg border border-edge bg-surface-2 px-3 py-2"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <button
                type="button"
                class="flex min-w-0 flex-1 items-center gap-2 text-left"
                @click="toggleBox(box.id)"
              >
                <span class="font-semibold text-ink">{{ box.code }}</span>
                <span v-if="box.name" class="truncate text-[0.85rem] text-muted"
                  >· {{ box.name }}</span
                >
                <span class="shrink-0 text-[0.78rem] text-muted"
                  >{{ box.item_count }} item(s) · {{ box.total_quantity }} pcs</span
                >
              </button>
              <div class="flex shrink-0 items-center gap-1.5">
                <a
                  :href="boxLabelUrl(box.id)"
                  target="_blank"
                  rel="noopener"
                  class="btn btn--ghost btn--small"
                  title="Print box label"
                >
                  🖨
                </a>
                <button
                  v-if="box.item_count === 0"
                  type="button"
                  class="btn btn--ghost btn--small"
                  title="Delete empty box"
                  @click="deleteEmptyBox(box)"
                >
                  🗑
                </button>
              </div>
            </div>

            <div v-if="expandedBoxId === box.id" class="mt-2 border-t border-edge pt-2">
              <p v-if="loadingBoxItems" class="m-0 text-[0.8rem] text-muted">
                Loading…
              </p>
              <p v-else-if="!boxItems.length" class="m-0 text-[0.8rem] text-muted">
                Empty box.
              </p>
              <div
                v-for="bi in boxItems"
                :key="bi.id"
                class="flex items-center justify-between gap-2 py-1 text-[0.82rem]"
              >
                <span class="min-w-0 flex-1 truncate">{{ bi.name }} ({{ bi.quantity }})</span>
                <button
                  type="button"
                  class="shrink-0 text-[0.78rem] text-muted underline"
                  :disabled="boxBusy"
                  @click="unassignItem(bi)"
                >
                  Take out
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

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
      <p
        v-if="query && !filteredItems.length"
        class="py-5 text-center text-muted"
      >
        No item on this shelf matches "{{ query }}".
      </p>
      <div
        v-else-if="!items.length"
        class="mt-3.5 flex flex-col items-center gap-1 rounded-[10px] border border-dashed border-sky-400/40 bg-sky-500/[0.07] px-4 py-6 text-center"
      >
        <span class="text-[1.5rem]">＋</span>
        <span class="text-[0.95rem] font-bold text-sky-300">{{
          emptyLabel || "This shelf is empty"
        }}</span>
        <span class="text-[0.8rem] text-muted">{{
          emptyHint || "Plenty of room here for new stock."
        }}</span>
      </div>
      <DashboardItemTable
        v-else
        :items="filteredItems"
        :show-shelf="false"
        :show-locate="false"
        selectable
        @select="emit('select-item', $event)"
        @move="(item, action) => emit('select-item', item, action)"
        @relocate="(item) => emit('select-item', item, 'move')"
        @info="(item) => emit('info', item)"
      />
    </template>
  </section>
</template>

<script setup lang="ts">
import type { Box, Item } from "~/composables/useWarehouseApi";

const props = withDefaults(
  defineProps<{
    shelfPosition: string;
    items: Item[];
    loading: boolean;
    showBack?: boolean;
    showHeader?: boolean;
    /** Overrides for reuse outside the "shelf" context (e.g. a direct-storage zone). */
    title?: string;
    emptyLabel?: string;
    emptyHint?: string;
    dashboardQuery?: Record<string, string>;
    /** Set for a direct-storage zone drilldown, where `shelfPosition` is
     * actually the zone's name, not a real shelf level -- boxes always
     * live on an actual shelf, so the boxes section makes no sense there. */
    disableBoxes?: boolean;
  }>(),
  { showHeader: true },
);

const emit = defineEmits<{
  close: [];
  back: [];
  "select-item": [item: Item, action?: "deposit" | "withdraw" | "move"];
  info: [item: Item];
}>();

const query = ref("");

// Reset the local search whenever a different shelf is opened, so a stale
// filter from the previous shelf doesn't silently hide everything here.
watch(
  () => props.shelfPosition,
  () => {
    query.value = "";
  },
);

const filteredItems = computed(() => {
  const q = query.value.trim().toLowerCase();
  if (!q) return props.items;
  return props.items.filter((item) =>
    [item.name, item.pn, item.serial, item.barcode]
      .filter(Boolean)
      .some((field) => field!.toLowerCase().includes(q)),
  );
});

const totalQuantity = computed(() =>
  props.items.reduce((sum, i) => sum + i.quantity, 0),
);

// -- Boxes on this shelf -----------------------------------------------
const {
  listBoxes,
  createBox,
  deleteBox,
  listBoxItems,
  removeItemFromBox,
  boxLabelUrl,
} = useWarehouseApi();
const { show } = useToast();

const boxes = ref<Box[]>([]);
const loadingBoxes = ref(false);
const creatingBox = ref(false);
const newBoxName = ref("");
const boxBusy = ref(false);
const expandedBoxId = ref<number | null>(null);
const boxItems = ref<Item[]>([]);
const loadingBoxItems = ref(false);

async function loadBoxes() {
  if (!props.shelfPosition || props.disableBoxes) {
    boxes.value = [];
    return;
  }
  loadingBoxes.value = true;
  try {
    boxes.value = await listBoxes(props.shelfPosition);
  } catch {
    boxes.value = [];
  } finally {
    loadingBoxes.value = false;
  }
}

watch(() => props.shelfPosition, loadBoxes, { immediate: true });

function startCreateBox() {
  creatingBox.value = true;
  newBoxName.value = "";
}

async function confirmCreateBox() {
  boxBusy.value = true;
  try {
    await createBox({
      name: newBoxName.value.trim() || null,
      shelf_position: props.shelfPosition,
    });
    creatingBox.value = false;
    await loadBoxes();
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to create the box");
  } finally {
    boxBusy.value = false;
  }
}

async function deleteEmptyBox(box: Box) {
  boxBusy.value = true;
  try {
    await deleteBox(box.id);
    if (expandedBoxId.value === box.id) expandedBoxId.value = null;
    await loadBoxes();
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to delete the box");
  } finally {
    boxBusy.value = false;
  }
}

async function toggleBox(boxId: number) {
  if (expandedBoxId.value === boxId) {
    expandedBoxId.value = null;
    return;
  }
  expandedBoxId.value = boxId;
  loadingBoxItems.value = true;
  try {
    boxItems.value = await listBoxItems(boxId);
  } catch {
    boxItems.value = [];
  } finally {
    loadingBoxItems.value = false;
  }
}

async function unassignItem(item: Item) {
  boxBusy.value = true;
  try {
    await removeItemFromBox(item.id);
    show("success", `"${item.name}" taken out of its box`);
    if (expandedBoxId.value) {
      boxItems.value = await listBoxItems(expandedBoxId.value);
    }
    await loadBoxes();
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to take this item out of the box");
  } finally {
    boxBusy.value = false;
  }
}
</script>
