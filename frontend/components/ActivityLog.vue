<template>
  <section class="card">
    <div class="mb-3.5 flex flex-wrap items-center justify-between gap-2">
      <h2 class="text-[1.05rem]">Activity Log</h2>
      <div class="flex items-center gap-2">
        <input
          v-model="operatorQuery"
          type="text"
          placeholder="Search by operator…"
          class="field-input h-8.5 w-45 text-[0.82rem]"
        />
        <button
          type="button"
          class="btn btn--ghost btn--small"
          :disabled="loading"
          @click="refresh"
        >
          {{ loading ? "Refreshing…" : "Refresh" }}
        </button>
      </div>
    </div>

    <p v-if="loading && movements.length === 0" class="py-4 text-muted">
      Loading log…
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
                :class="
                  m.action === 'deposit'
                    ? 'bg-good/15 text-green-300'
                    : 'bg-bad/15 text-red-300'
                "
              >
                {{ m.action === "deposit" ? "Added" : "Removed" }}
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
              {{ m.quantity }}
            </td>
            <td class="py-2.5 pr-3">
              <div class="font-medium text-ink">{{ m.item_name }}</div>
              <div class="text-[0.75rem] text-muted">
                P/N {{ m.pn }} · Shelf {{ m.shelf_position }}
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
  </section>
</template>

<script setup lang="ts">
import type { Movement } from "~/composables/useWarehouseApi";

const { listMovements, rollbackMovement } = useWarehouseApi();
const { isAdmin } = useAuth();
const { show } = useToast();

const movements = ref<Movement[]>([]);
const loading = ref(false);
const rollingBack = ref<number | null>(null);
const operatorQuery = ref("");
let pollTimer: ReturnType<typeof setInterval> | null = null;
let searchDebounce: ReturnType<typeof setTimeout> | undefined;

async function refresh() {
  loading.value = true;
  try {
    movements.value = await listMovements(50, {
      operator: operatorQuery.value.trim() || undefined,
    });
  } finally {
    loading.value = false;
  }
}

watch(operatorQuery, () => {
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(refresh, 300);
});

async function confirmRollback(m: Movement) {
  const verb = m.action === "deposit" ? "removing" : "adding back";
  const ok = window.confirm(
    `Roll back this movement? This will log a compensating entry ${verb} ${m.quantity} unit(s) of "${m.item_name}".`,
  );
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
