<template>
  <div>
    <!-- Step 1: find the item, by scan or by search -->
    <div v-if="!foundItem" class="flex flex-col gap-3">
      <p class="m-0 text-[0.85rem] text-muted">
        Scan a barcode, or type to search by name / P/N.
      </p>

      <div class="relative">
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
                  P/N {{ item.pn }} · {{ item.category }}<template
                    v-if="item.program"
                  >
                    · {{ item.program }}</template
                  >
                  · Shelf {{ item.shelf_position }}
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

    <!-- Step 2: item found -- reuse ItemDetailCard, jumping straight to this action -->
    <div v-else class="flex flex-col gap-2.5">
      <button
        type="button"
        class="self-start text-[0.8rem] text-muted underline-offset-2 hover:underline"
        @click="backToSearch"
      >
        ← Search a different item
      </button>
      <ItemDetailCard
        :key="foundItem.id"
        :item="foundItem"
        :auto-start-action="action"
        default-source="manual"
        @updated="handleUpdated"
        @close="backToSearch"
        @deleted="backToSearch"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Item } from "~/composables/useWarehouseApi";

const props = defineProps<{
  action: "deposit" | "withdraw";
}>();

const emit = defineEmits<{
  updated: [item: Item];
}>();

const { listItems, scanItem } = useWarehouseApi();
const { show } = useToast();
const { onKeydown, onEnter, resetTiming } = useBarcodeScanner({
  onScan: handleScan,
  onManualSubmit: handleManualSubmit,
});

const inputEl = ref<HTMLInputElement | null>(null);
const query = ref("");
const suggestions = ref<Item[]>([]);
const loading = ref(false);
const dropdownOpen = ref(false);
const foundItem = ref<Item | null>(null);

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

async function handleScan(value: string) {
  loading.value = true;
  try {
    foundItem.value = await scanItem(value);
  } catch {
    show("error", `No item found for code "${value}"`);
  } finally {
    loading.value = false;
    clearSearch();
  }
}

async function handleManualSubmit(value: string) {
  if (suggestions.value.length > 0) {
    selectSuggestion(suggestions.value[0]);
    return;
  }
  loading.value = true;
  try {
    foundItem.value = await scanItem(value);
    clearSearch();
  } catch {
    show("error", `No item found for code "${value}"`);
  } finally {
    loading.value = false;
  }
}

function selectSuggestion(item: Item) {
  foundItem.value = item;
  clearSearch();
}

function clearSearch() {
  query.value = "";
  suggestions.value = [];
  dropdownOpen.value = false;
  resetTiming();
}

function backToSearch() {
  foundItem.value = null;
  nextTick(() => inputEl.value?.focus());
}

function handleUpdated(item: Item) {
  emit("updated", item);
  // Ready for the next item right away -- handy for working through a batch.
  backToSearch();
}

onMounted(() => nextTick(() => inputEl.value?.focus()));
</script>
