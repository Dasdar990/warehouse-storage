<template>
  <section class="card border border-edge/70 bg-surface/95">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <div
          class="rounded-full border border-edge/70 bg-surface px-2.5 py-1 text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-muted"
        >
          Item
        </div>
        <h2 class="mt-2 text-[1rem] font-semibold">{{ item.name }}</h2>
        <div class="mt-2 flex flex-wrap gap-2">
          <span v-if="item.pn" class="badge badge--pn">P/N {{ item.pn }}</span>
          <span class="badge badge--category">{{ item.category }}</span>
          <span class="badge badge--size" :class="`badge--size-${item.size}`">{{
            sizeLabel(item.size)
          }}</span>
          <span class="badge badge--shelf"
            >📍
            <template v-if="zoneLabel">Zone {{ zoneLabel }} · </template>Shelf
            {{ item.shelf_position }}</span
          >
        </div>
      </div>
    </div>

    <div class="mt-3 flex flex-wrap items-center gap-3">
      <div class="rounded-lg border border-edge/80 bg-surface px-3 py-2">
        <div class="text-[0.7rem] uppercase tracking-wide text-muted">
          Current Stock
        </div>
        <div class="text-[1.2rem] font-semibold text-ink">
          {{ item.quantity }}
        </div>
      </div>
    </div>

    <!-- Step 1: pick the movement -->
    <div v-if="!pendingAction" class="mt-3 flex flex-wrap gap-2 max-[640px]:flex-col">
      <button
        type="button"
        class="btn btn--danger flex-1 cursor-pointer py-2.5 text-[0.95rem] font-semibold"
        :disabled="busy || item.quantity <= 0"
        @click="startAction('withdraw')"
      >
        Remove
      </button>
      <button
        type="button"
        class="btn btn--confirm flex-1 cursor-pointer py-2.5 text-[0.95rem] font-semibold"
        :disabled="busy"
        @click="startAction('deposit')"
      >
        Add
      </button>
    </div>

    <!-- Step 2: pick the quantity, then confirm -->
    <div
      v-else
      class="mt-3 flex flex-col gap-3 rounded-[10px] border border-edge/80 bg-surface p-3"
    >
      <div class="flex items-center justify-between gap-2">
        <span
          class="text-[0.8rem] font-semibold uppercase tracking-wide"
          :class="pendingAction === 'withdraw' ? 'text-red-300' : 'text-green-300'"
        >
          {{ pendingAction === "withdraw" ? "Removing stock" : "Adding stock" }}
        </span>
        <button
          type="button"
          class="text-[0.8rem] text-muted underline-offset-2 hover:underline"
          :disabled="busy"
          @click="cancelAction"
        >
          Cancel
        </button>
      </div>

      <div class="flex flex-wrap items-center gap-1.5">
        <button
          type="button"
          class="btn--icon h-9 w-9 cursor-pointer text-lg disabled:cursor-not-allowed disabled:opacity-40"
          :disabled="qty <= 1"
          title="Decrease"
          @click="qty = Math.max(1, qty - 1)"
        >
          −
        </button>
        <input
          id="qty-input"
          v-model.number="qty"
          type="number"
          min="1"
          :max="pendingAction === 'withdraw' ? item.quantity : undefined"
          class="field-input w-17.5 px-1 text-center text-[1.1rem]"
        />
        <button
          type="button"
          class="btn--icon h-9 w-9 cursor-pointer text-lg disabled:cursor-not-allowed disabled:opacity-40"
          :disabled="pendingAction === 'withdraw' && qty >= item.quantity"
          title="Increase"
          @click="qty += 1"
        >
          +
        </button>

        <div class="ml-1 flex flex-wrap gap-1.5">
          <button
            v-for="preset in quickQuantities"
            :key="preset.label"
            type="button"
            class="rounded-full border border-edge/70 px-2.5 py-1 text-[0.75rem] font-semibold text-muted hover:border-accent/50 hover:text-ink"
            :class="{ 'border-accent/60 text-ink': qty === preset.value }"
            @click="qty = preset.value"
          >
            {{ preset.label }}
          </button>
        </div>
      </div>

      <p v-if="qtyError" class="m-0 text-[0.8rem] text-red-300">
        {{ qtyError }}
      </p>

      <div
        class="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-surface-2 px-3 py-2 text-[0.85rem]"
      >
        <span class="text-muted">
          {{ pendingAction === "withdraw" ? "Remove" : "Add" }}
          <strong class="text-ink">{{ qty }}</strong> unit(s) of
          <strong class="text-ink">{{ item.name }}</strong>
        </span>
        <span class="whitespace-nowrap text-muted">
          {{ item.quantity }} →
          <strong class="text-ink">{{ resultingQuantity }}</strong>
        </span>
      </div>

      <button
        type="button"
        class="cursor-pointer py-2.5 text-[0.95rem] font-semibold"
        :class="pendingAction === 'withdraw' ? 'btn btn--danger' : 'btn btn--confirm'"
        :disabled="busy || !!qtyError"
        @click="confirmAction"
      >
        {{ busy ? "Saving…" : `Confirm ${pendingAction === "withdraw" ? "removal" : "addition"}` }}
      </button>
    </div>

    <div class="mt-3.5 border-t border-edge/60 pt-3">
      <div class="mb-1.5 flex items-center justify-between">
        <span class="text-[0.75rem] font-semibold uppercase tracking-wide text-muted"
          >Recent activity</span
        >
        <span v-if="loadingHistory" class="text-[0.75rem] text-muted">Loading…</span>
      </div>
      <p v-if="!loadingHistory && !history.length" class="m-0 text-[0.8rem] text-muted">
        No movements recorded yet for this item.
      </p>
      <ul v-else class="m-0 flex flex-col gap-1.5 p-0">
        <li
          v-for="h in history"
          :key="h.id"
          class="flex flex-wrap items-center justify-between gap-1.5 rounded-lg bg-surface px-2.5 py-1.5 text-[0.8rem]"
          :class="{ 'opacity-45': h.voided }"
        >
          <span>
            <strong :class="h.action === 'deposit' ? 'text-green-300' : 'text-red-300'">
              {{ h.action === "deposit" ? "+" : "−" }}{{ h.quantity }}
            </strong>
            <span class="text-muted"> by </span>
            <span class="text-ink">{{ h.operator }}</span>
          </span>
          <span class="whitespace-nowrap text-[0.72rem] text-muted">{{
            formatHistoryTime(h.timestamp)
          }}</span>
        </li>
      </ul>
    </div>

    <div class="mt-2.5 flex flex-wrap gap-2">
      <a
        :href="labelUrl(item.id)"
        target="_blank"
        rel="noopener"
        class="btn btn--ghost inline-flex cursor-pointer items-center gap-2"
        title="Print label"
        aria-label="Print label"
      >
        <svg
          viewBox="0 0 24 24"
          class="h-4.5 w-4.5"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M8 3h8" />
          <path
            d="M8 3v3H6a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-2V3"
          />
          <rect x="8" y="12" width="8" height="8" rx="1" />
          <path d="M9 16h6" />
        </svg>
        <span>Print Label</span>
      </a>
      <NuxtLink
        class="btn btn--ghost inline-flex cursor-pointer items-center gap-2"
        :to="{
          path: '/dashboard',
          query: { shelf_position: item.shelf_position },
        }"
        title="Open in Dashboard"
        aria-label="Open in Dashboard"
      >
        <svg
          viewBox="0 0 24 24"
          class="h-4.5 w-4.5"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <rect x="4" y="4" width="7" height="7" rx="1" />
          <rect x="13" y="4" width="7" height="7" rx="1" />
          <rect x="4" y="13" width="7" height="7" rx="1" />
          <rect x="13" y="13" width="7" height="7" rx="1" />
        </svg>
        <span>View in Dashboard</span>
      </NuxtLink>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { Item, Movement, MovementSource } from "~/composables/useWarehouseApi";

const props = defineProps<{
  item: Item;
  zoneLabel?: string;
  /** Where the current selection came from -- tags the *next* quick action for the audit log. */
  defaultSource?: MovementSource;
}>();

const emit = defineEmits<{
  close: [];
  updated: [item: Item];
}>();

const { withdrawItem, depositItem, labelUrl, listMovements } = useWarehouseApi();
const { show } = useToast();

const qty = ref(1);
const busy = ref(false);

// Small "who did what with this item" panel, refreshed whenever the
// selected item changes or a new movement is confirmed on it.
const history = ref<Movement[]>([]);
const loadingHistory = ref(false);

async function loadHistory() {
  loadingHistory.value = true;
  try {
    history.value = await listMovements(6, { item_id: props.item.id });
  } catch {
    // Non-critical: the card still works without the history panel.
  } finally {
    loadingHistory.value = false;
  }
}

function formatHistoryTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Step 1 only picks *which* movement; step 2 (below) then asks for the
// quantity and shows a confirmation summary before anything is sent.
const pendingAction = ref<"withdraw" | "deposit" | null>(null);

// Common quick-pick amounts, plus "All" (the full current stock) so clearing
// out a shelf in one withdrawal doesn't require typing the exact number.
const quickQuantities = computed(() => {
  const cap =
    pendingAction.value === "withdraw"
      ? props.item.quantity
      : Math.max(props.item.quantity, 1);
  const presets = [1, 5, 10]
    .filter((n) => n <= Math.max(cap, 1))
    .map((n) => ({ label: String(n), value: n }));
  if (
    pendingAction.value === "withdraw" &&
    props.item.quantity > 0 &&
    !presets.some((p) => p.value === props.item.quantity)
  ) {
    presets.push({ label: "All", value: props.item.quantity });
  }
  return presets;
});

const resultingQuantity = computed(() =>
  pendingAction.value === "withdraw"
    ? props.item.quantity - qty.value
    : props.item.quantity + qty.value,
);

const qtyError = computed(() => {
  if (!pendingAction.value) return "";
  if (!qty.value || qty.value < 1) return "Enter a quantity of at least 1.";
  if (pendingAction.value === "withdraw" && qty.value > props.item.quantity) {
    return `Only ${props.item.quantity} unit(s) available.`;
  }
  return "";
});

watch(
  () => props.item.id,
  () => {
    pendingAction.value = null;
    qty.value = 1;
    loadHistory();
  },
  { immediate: true },
);

function sizeLabel(size: string) {
  return (
    ({ small: "Small", big: "Big", xl: "XL" } as Record<string, string>)[
      size
    ] || size
  );
}

function startAction(action: "withdraw" | "deposit") {
  pendingAction.value = action;
  qty.value = 1;
}

function cancelAction() {
  pendingAction.value = null;
  qty.value = 1;
}

async function confirmAction() {
  const action = pendingAction.value;
  if (!action || qtyError.value) return;
  busy.value = true;
  try {
    const payload = {
      barcode: props.item.barcode,
      quantity: qty.value,
      source: (props.defaultSource ?? "manual") as MovementSource,
    };
    const res =
      action === "withdraw"
        ? await withdrawItem(payload)
        : await depositItem(payload);
    show("success", res.message);
    emit("updated", res.item);
    pendingAction.value = null;
    qty.value = 1;
    await loadHistory();
  } catch (err: any) {
    show("error", err?.data?.detail || "Operation failed");
  } finally {
    busy.value = false;
  }
}
</script>
