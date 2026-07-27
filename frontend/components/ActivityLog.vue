<template>
  <section class="card">
    <div class="flex flex-wrap items-center justify-between gap-2" :class="{ 'mb-3.5': expanded }">
      <button
        v-if="collapsible"
        type="button"
        class="flex min-w-0 flex-1 cursor-pointer items-center gap-2 bg-transparent text-left"
        @click="expanded = !expanded"
      >
        <svg
          viewBox="0 0 24 24"
          class="h-4 w-4 shrink-0 text-muted transition-transform duration-200 ease-out"
          :class="{ 'rotate-90': expanded }"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M9 5l7 7-7 7" />
        </svg>
        <h2 class="text-[1.05rem]">Activity Log</h2>
        <span
          v-if="!expanded && movements.length"
          class="rounded-full bg-surface-2 px-2 py-0.5 text-[0.7rem] font-semibold text-muted"
          >{{ movements.length }}</span
        >
      </button>
      <h2 v-else class="text-[1.05rem]">Activity Log</h2>
      <button
        v-if="expanded"
        type="button"
        class="btn btn--ghost btn--small"
        :disabled="loading"
        @click="refresh"
      >
        {{ loading ? "Refreshing…" : "Refresh" }}
      </button>
    </div>

    <div
      v-show="expanded"
      class="mb-3.5 flex flex-wrap items-center gap-2 max-[640px]:flex-col max-[640px]:items-stretch"
    >
      <input
        v-model="itemQuery"
        type="text"
        placeholder="Search item name or P/N…"
        class="field-input h-8.5 flex-1 basis-45 text-[0.82rem]"
      />
      <input
        v-model="operatorQuery"
        type="text"
        placeholder="Search by operator…"
        class="field-input h-8.5 flex-1 basis-40 text-[0.82rem]"
      />
      <select
        v-model="actionFilter"
        class="field-input h-8.5 w-40 shrink-0 text-[0.82rem] max-[640px]:w-full"
      >
        <option value="">All actions</option>
        <option value="deposit">Added</option>
        <option value="withdraw">Removed</option>
        <option value="move">Moved</option>
      </select>
      <select
        v-model="sourceFilter"
        class="field-input h-8.5 w-44 shrink-0 text-[0.82rem] max-[640px]:w-full"
      >
        <option value="">All sources</option>
        <option value="barcode">Barcode verified</option>
        <option value="manual">Manual entry</option>
      </select>
      <div class="flex items-center gap-1.5 max-[640px]:w-full">
        <input
          v-model="dateFrom"
          type="date"
          :max="dateTo || undefined"
          class="field-input h-8.5 max-[640px]:flex-1"
          title="From date"
        />
        <span class="text-[0.8rem] text-muted">–</span>
        <input
          v-model="dateTo"
          type="date"
          :min="dateFrom || undefined"
          class="field-input h-8.5 max-[640px]:flex-1"
          title="To date"
        />
      </div>
      <button
        v-if="hasActiveFilters"
        type="button"
        class="btn btn--ghost btn--small"
        @click="clearFilters"
      >
        Clear filters
      </button>
    </div>

    <template v-if="expanded">
    <p v-if="loading && movements.length === 0" class="py-4 text-muted">
      Loading log…
    </p>
    <p v-else-if="movements.length === 0 && hasActiveFilters" class="py-4 text-muted">
      No movements match these filters.
    </p>
    <p v-else-if="movements.length === 0" class="py-4 text-muted">
      No movements recorded yet.
    </p>

    <div
      v-else
      class="scrollbar-slim max-h-105 overflow-y-auto overflow-x-auto pr-1"
    >
      <table class="w-full min-w-160 border-collapse text-[0.85rem]">
        <thead>
          <tr
            class="border-b border-edge text-left text-[0.72rem] uppercase tracking-wide text-muted"
          >
            <th class="pb-2 pr-3 font-semibold">Time</th>
            <th class="pb-2 pr-3 font-semibold">Operator</th>
            <th class="pb-2 pr-3 font-semibold">Action</th>
            <th class="pb-2 pr-3 font-semibold text-right">Qty</th>
            <th class="pb-2 pr-3 font-semibold">Item / P/N</th>
            <th class="pb-2 pr-3 font-semibold">Source</th>
            <th v-if="isAdmin" class="pb-2 font-semibold">Rollback</th>
          </tr>
        </thead>
        <transition-group tag="tbody" name="log-row">
          <tr
            v-for="m in movements"
            :key="m.id"
            class="border-b border-edge/50 last:border-b-0"
            :class="{ 'opacity-45': m.voided }"
          >
            <td class="whitespace-nowrap py-2.5 pr-3 text-muted">
              {{ formatTime(m.timestamp) }}
            </td>
            <td class="whitespace-nowrap py-2.5 pr-3 font-medium text-ink">
              {{ m.operator }}
            </td>
            <td class="whitespace-nowrap py-2.5 pr-3">
              <span
                class="rounded-full px-2.5 py-1 text-[0.75rem] font-bold"
                :class="{
                  'bg-good/15 text-green-300': m.action === 'deposit',
                  'bg-bad/15 text-red-300': m.action === 'withdraw',
                  'bg-accent/15 text-accent': m.action === 'move',
                }"
              >
                {{
                  m.action === "deposit"
                    ? "Added"
                    : m.action === "withdraw"
                      ? "Removed"
                      : "Moved"
                }}
              </span>
              <span
                v-if="m.reversal_of_id"
                class="ml-1.5 rounded-full bg-surface-2 px-2 py-0.5 text-[0.68rem] font-semibold text-muted"
                title="This entry reverses a previous movement"
              >
                ↩ rollback of #{{ m.reversal_of_id }}
              </span>
            </td>
            <td
              class="whitespace-nowrap py-2.5 pr-3 text-right font-semibold text-ink"
            >
              {{ m.action === "move" ? "—" : m.quantity }}
            </td>
            <td class="py-2.5 pr-3">
              <div class="font-medium text-ink">{{ m.item_name }}</div>
              <div class="text-[0.75rem] text-muted">
                <template v-if="m.action === 'move'">
                  P/N {{ m.pn }} · {{ m.from_shelf_position }} → {{ m.shelf_position }}
                </template>
                <template v-else>
                  P/N {{ m.pn }} · Shelf {{ m.shelf_position }}
                </template>
              </div>
            </td>
            <td class="whitespace-nowrap py-2.5">
              <span
                v-if="m.source === 'barcode'"
                class="inline-flex items-center gap-1 rounded-full border border-good/40 bg-good/10 px-2.5 py-1 text-[0.72rem] font-bold text-green-300"
                title="Operation confirmed by barcode scan"
                >Barcode verified</span
              >
              <span
                v-else
                class="inline-flex items-center gap-1 rounded-full border border-warn/40 bg-warn/10 px-2.5 py-1 text-[0.72rem] font-bold text-amber-300"
                title="Operation entered manually from the interface"
                >Manual entry</span
              >
            </td>
            <td v-if="isAdmin" class="whitespace-nowrap py-2.5">
              <span v-if="m.voided" class="text-[0.75rem] text-muted"
                >Rolled back</span
              >
              <span v-else-if="m.reversal_of_id" class="text-[0.75rem] text-muted"
                >—</span
              >
              <button
                v-else
                type="button"
                class="btn btn--ghost btn--small whitespace-nowrap disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="rollingBack === m.id"
                @click="confirmRollback(m)"
              >
                {{ rollingBack === m.id ? "Rolling back…" : "Rollback" }}
              </button>
            </td>
          </tr>
        </transition-group>
      </table>
    </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import type {
  Movement,
  MovementAction,
  MovementSource,
} from "~/composables/useWarehouseApi";

const props = withDefaults(
  defineProps<{
    /** Show the collapse/expand arrow in the header. Set to false for a full, dedicated page. */
    collapsible?: boolean;
    /** Initial collapsed state when `collapsible` is true. */
    defaultCollapsed?: boolean;
  }>(),
  { collapsible: false, defaultCollapsed: false },
);

const { listMovements, rollbackMovement } = useWarehouseApi();
const { isAdmin } = useAuth();
const { show } = useToast();

const expanded = ref(!(props.collapsible && props.defaultCollapsed));

const movements = ref<Movement[]>([]);
const loading = ref(false);
const rollingBack = ref<number | null>(null);
const operatorQuery = ref("");
const itemQuery = ref("");
const actionFilter = ref<"" | MovementAction>("");
const sourceFilter = ref<"" | MovementSource>("");
const dateFrom = ref("");
const dateTo = ref("");
let pollTimer: ReturnType<typeof setInterval> | null = null;
let searchDebounce: ReturnType<typeof setTimeout> | undefined;

const hasActiveFilters = computed(
  () =>
    !!operatorQuery.value.trim() ||
    !!itemQuery.value.trim() ||
    !!actionFilter.value ||
    !!sourceFilter.value ||
    !!dateFrom.value ||
    !!dateTo.value,
);

async function refresh() {
  loading.value = true;
  try {
    movements.value = await listMovements(50, {
      operator: operatorQuery.value.trim() || undefined,
      item: itemQuery.value.trim() || undefined,
      action: actionFilter.value || undefined,
      source: sourceFilter.value || undefined,
      date_from: dateFrom.value || undefined,
      date_to: dateTo.value || undefined,
    });
  } finally {
    loading.value = false;
  }
}

watch([operatorQuery, itemQuery], () => {
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(refresh, 300);
});

watch([actionFilter, sourceFilter, dateFrom, dateTo], refresh);

function clearFilters() {
  operatorQuery.value = "";
  itemQuery.value = "";
  actionFilter.value = "";
  sourceFilter.value = "";
  dateFrom.value = "";
  dateTo.value = "";
}

async function confirmRollback(m: Movement) {
  const question =
    m.action === "move"
      ? `Roll back this move? This will send "${m.item_name}" back from shelf ${m.shelf_position} to shelf ${m.from_shelf_position}.`
      : `Roll back this movement? This will log a compensating entry ${
          m.action === "deposit" ? "removing" : "adding back"
        } ${m.quantity} unit(s) of "${m.item_name}".`;
  const ok = window.confirm(question);
  if (!ok) return;

  rollingBack.value = m.id;
  try {
    const res = await rollbackMovement(m.id);
    show("success", res.message);
    await refresh();
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to roll back this movement");
  } finally {
    rollingBack.value = null;
  }
}

function formatTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

/** Called by the parent right after a scan/quick-action so the feed updates without waiting for the poll tick. */
defineExpose({ refresh });

onMounted(() => {
  refresh();
  // Light polling as a safety net in case another terminal is also writing
  // movements; explicit refresh() calls after local actions keep it snappy.
  pollTimer = setInterval(refresh, 15000);
});

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
});
</script>

<style scoped>
.log-row-enter-active {
  transition: all 0.3s ease-out;
}
.log-row-enter-from {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
