<template>
  <section class="card py-3.5">
    <div class="flex flex-wrap items-stretch gap-2.5 max-[640px]:flex-col">
      <!-- Unified input: barcode reader burst OR manual typing, same field -->
      <div class="relative flex-1">
        <input
          ref="inputEl"
          v-model="query"
          type="text"
          autocomplete="off"
          autofocus
          placeholder="Search or scan an item…"
          class="w-full rounded-[10px] border border-edge bg-input px-4 py-3 text-[0.95rem] font-medium text-ink outline-none focus:border-accent/70 focus:shadow-[0_0_0_2px_rgba(76,123,97,0.16)]"
          @keydown="onKeydown"
          @keyup.enter="handleEnter"
          @input="handleInput"
        />
        <span
          v-if="loading"
          class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-sm text-muted"
          >…</span
        >

        <!-- Autocomplete dropdown for manual typing -->
        <ul
          v-if="showDropdown"
          class="scrollbar-slim absolute z-20 mt-1.5 max-h-80 w-full overflow-y-auto rounded-[10px] border border-edge bg-surface-2 shadow-card"
        >
          <li
            v-if="suggestions.length === 0"
            class="px-4 py-3 text-sm text-muted"
          >
            No results for "{{ query }}"
          </li>
          <li
            v-for="item in suggestions"
            :key="item.id"
            class="cursor-pointer border-b border-edge/60 px-4 py-3 last:border-b-0 hover:bg-accent/10"
            @mousedown.prevent="selectSuggestion(item)"
          >
            <div class="flex items-center justify-between gap-3">
              <div>
                <div class="font-semibold text-ink">{{ item.name }}</div>
                <div class="mt-0.5 text-[0.8rem] text-muted">
                  P/N {{ item.pn }} · {{ item.category }} · Shelf
                  {{ item.shelf_position }}
                </div>
              </div>
              <span
                class="whitespace-nowrap rounded-full px-2.5 py-1 text-[0.75rem] font-bold"
                :class="
                  item.quantity === 0
                    ? 'bg-bad/20 text-red-300'
                    : 'bg-good/15 text-green-300'
                "
                >{{ item.quantity }} pcs</span
              >
            </div>
          </li>
        </ul>
      </div>
    </div>

    <p class="mt-2 mb-0 text-[0.76rem] text-muted">
      Scan applies the selected action directly; typing opens the item card.
    </p>
  </section>
</template>

<script setup lang="ts">
import type { Item } from "~/composables/useWarehouseApi";

const emit = defineEmits<{
  /** Fast barcode-reader burst + Enter, resolved to a known item. */
  "scan-item": [item: Item];
  /** Fast barcode-reader burst + Enter, but no item matched that code. */
  "scan-not-found": [code: string];
  /** Manual typing, user picked (or confirmed) an item -- locate only, no stock change. */
  "locate-item": [item: Item];
}>();

const { listItems, scanItem } = useWarehouseApi();
const { mode, setMode } = useOperationMode();
const { onKeydown, onEnter, resetTiming } = useBarcodeScanner({
  onScan: handleScan,
  onManualSubmit: handleManualSubmit,
});

const inputEl = ref<HTMLInputElement | null>(null);
const query = ref("");
const suggestions = ref<Item[]>([]);
const loading = ref(false);
const dropdownOpen = ref(false);

const showDropdown = computed(
  () => dropdownOpen.value && query.value.trim().length >= 2,
);

let debounceTimer: ReturnType<typeof setTimeout> | null = null;

function handleInput() {
  dropdownOpen.value = true;
  if (debounceTimer) clearTimeout(debounceTimer);
  const term = query.value.trim();
  if (term.length < 2) {
    suggestions.value = [];
    return;
  }
  debounceTimer = setTimeout(async () => {
    loading.value = true;
    try {
      suggestions.value = (await listItems({ search: term })).slice(0, 8);
    } finally {
      loading.value = false;
    }
  }, 200);
}

function handleEnter(event: KeyboardEvent) {
  onEnter(event, query.value);
}

/** Fast burst + Enter: treat the value as a scanned barcode. */
async function handleScan(value: string) {
  loading.value = true;
  try {
    const item = await scanItem(value);
    emit("scan-item", item);
  } catch {
    emit("scan-not-found", value);
  } finally {
    loading.value = false;
    clearAndRefocus();
  }
}

/** Slow typing + Enter with no dropdown pick: use the top suggestion if there is one. */
async function handleManualSubmit(value: string) {
  if (suggestions.value.length > 0) {
    selectSuggestion(suggestions.value[0]);
    return;
  }
  // Fall back to an exact barcode lookup in case it was typed rather than scanned.
  loading.value = true;
  try {
    const item = await scanItem(value);
    emit("locate-item", item);
  } catch {
    emit("scan-not-found", value);
  } finally {
    loading.value = false;
    clearAndRefocus();
  }
}

function selectSuggestion(item: Item) {
  emit("locate-item", item);
  clearAndRefocus();
}

function clearAndRefocus() {
  query.value = "";
  suggestions.value = [];
  dropdownOpen.value = false;
  resetTiming();
  focus();
}

function focus() {
  nextTick(() => inputEl.value?.focus());
}

onMounted(focus);

defineExpose({ focus });
</script>
