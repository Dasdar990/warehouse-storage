<template>
  <section class="card">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div class="min-w-0 flex-1">
        <h2 class="text-[1.5rem] font-bold leading-tight text-ink">
          {{ item.name }}
        </h2>
        <div class="mt-2 flex flex-wrap gap-1.5">
          <span v-if="item.pn" class="badge badge--pn">P/N {{ item.pn }}</span>
          <span v-if="item.serial" class="badge badge--serial"
            >S/N {{ item.serial }}</span
          >
          <span class="badge badge--category">{{ item.category }}</span>
          <span v-if="item.program" class="badge badge--program">{{
            item.program
          }}</span>
          <span class="badge badge--size" :class="`badge--size-${item.size}`">{{
            sizeLabel(item.size)
          }}</span>
        </div>
      </div>
      <NuxtLink
        v-if="item.shelf_position"
        class="flex flex-column btn btn--ghost cursor-pointer items-center gap-2"
        :to="{ path: '/', query: { locate: item.barcode } }"
        title="Locate on the map"
        aria-label="Locate on the map"
      >
        <div
          class="shrink-0 rounded-xl px-4 py-2.5 text-center"
          :class="item.shelf_position ? 'bg-accent/16' : 'bg-surface-2'"
        >
          <div
            class="text-[0.65rem] font-bold uppercase tracking-[0.12em]"
            :class="item.shelf_position ? 'text-accent' : 'text-muted'"
          >
            📍 Location
          </div>
          <div
            v-if="item.shelf_position"
            class="mt-1 text-[1.9rem] font-extrabold leading-none text-ink"
          >
            {{ item.shelf_position }}
          </div>
          <div
            v-else
            class="mt-1 text-[1.15rem] font-bold leading-none text-muted"
          >
            Not shelved
          </div>
          <div
            v-if="zoneLabel"
            class="mt-1 text-[0.75rem] font-medium text-muted"
          >
            Zone {{ zoneLabel }}
          </div>
        </div>
      </NuxtLink>
    </div>

    <p v-if="otherShelves.length" class="m-0 mt-2.5 text-[0.8rem] text-muted">
      Also on
      <span
        v-for="(o, i) in otherShelves"
        :key="o.shelf_position"
        class="font-semibold text-ink"
        >{{ o.shelf_position }} ({{ o.quantity }})<template
          v-if="i < otherShelves.length - 1"
          >,
        </template></span
      >
    </p>

    <div
      class="mt-3.5 inline-flex items-center gap-2.5 rounded-lg bg-surface-2 px-3.5 py-2"
    >
      <span
        class="text-[0.68rem] font-semibold uppercase tracking-wide text-muted"
        >Stock</span
      >
      <span class="text-[1.35rem] font-bold text-ink">{{ item.quantity }}</span>
    </div>

    <!-- Step 1: pick the movement -->
    <div
      v-if="!pendingAction"
      class="mt-3 flex flex-wrap gap-2.5 max-[640px]:flex-col"
    >
      <button
        type="button"
        class="group relative flex flex-1 items-center gap-3 overflow-hidden rounded-lg border border-bad/35 bg-bad/9 px-3.5 py-3 text-left transition-all duration-200 ease-out hover:-translate-y-0.5 hover:border-bad/60 hover:bg-bad/16 hover:shadow-[0_8px_20px_rgba(0,0,0,0.28)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bad/60 active:translate-y-0 active:shadow-none disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:translate-y-0 disabled:hover:shadow-none"
        :disabled="busy || item.quantity <= 0"
        @click="startAction('withdraw')"
      >
        <span
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-bad/22 transition-colors duration-200 group-hover:bg-bad/32"
        >
          <svg
            viewBox="0 0 24 24"
            class="h-5.5 w-5.5 text-red-200"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M20 12H4" />
          </svg>
        </span>
        <span class="flex min-w-0 flex-1 flex-col gap-0.5">
          <span class="text-[1.05rem] font-semibold text-ink">Withdraw</span>
        </span>
      </button>
      <button
        type="button"
        class="group relative flex flex-1 items-center gap-3 overflow-hidden rounded-lg border border-good/35 bg-good/9 px-3.5 py-3 text-left transition-all duration-200 ease-out hover:-translate-y-0.5 hover:border-good/60 hover:bg-good/16 hover:shadow-[0_8px_20px_rgba(0,0,0,0.28)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-good/60 active:translate-y-0 active:shadow-none disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:translate-y-0 disabled:hover:shadow-none"
        :disabled="busy"
        @click="startAction('deposit')"
      >
        <span
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-good/22 transition-colors duration-200 group-hover:bg-good/32"
        >
          <svg
            viewBox="0 0 24 24"
            class="h-5.5 w-5.5 text-green-200"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M12 4v16M4 12h16" />
          </svg>
        </span>
        <span class="flex min-w-0 flex-1 flex-col gap-0.5">
          <span class="text-[1.05rem] font-semibold text-ink">Add</span>
        </span>
      </button>
      <button
        type="button"
        class="group relative flex flex-1 items-center gap-3 overflow-hidden rounded-lg border border-accent/35 bg-accent/9 px-3.5 py-3 text-left transition-all duration-200 ease-out hover:-translate-y-0.5 hover:border-accent/60 hover:bg-accent/[0.16] hover:shadow-[0_8px_20px_rgba(0,0,0,0.28)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60 active:translate-y-0 active:shadow-none disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:translate-y-0 disabled:hover:shadow-none"
        :disabled="busy"
        @click="startAction('move')"
      >
        <span
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-accent/22 transition-colors duration-200 group-hover:bg-accent/32"
        >
          <img src="~/assets/icons/move.svg" class="w-6 h-auto" />
        </span>
        <span class="flex min-w-0 flex-1 flex-col gap-0.5">
          <span class="text-[1.05rem] font-semibold text-ink">Move</span>
        </span>
      </button>
    </div>

    <!-- Step 2: pick the quantity, then confirm -->
    <div
      v-else-if="pendingAction === 'withdraw' || pendingAction === 'deposit'"
      class="mt-3 flex flex-col gap-3 rounded-[10px] bg-surface-2 p-3"
    >
      <div class="flex items-center justify-between gap-2">
        <span
          class="text-[0.8rem] font-semibold uppercase tracking-wide"
          :class="
            pendingAction === 'withdraw' ? 'text-red-300' : 'text-green-300'
          "
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
          class="field-input w-17.5 px-1 text-center text-[1.1rem] no-spinner"
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

      <!-- Deposit only: let the operator send this stock to a different shelf -->
      <div
        v-if="pendingAction === 'deposit'"
        class="flex flex-col gap-2 rounded-lg bg-surface px-3 py-2.5"
      >
        <div class="flex items-center justify-between gap-2">
          <span class="text-[0.78rem] font-semibold text-muted"
            >Deposit onto</span
          >
          <button
            v-if="item.shelf_position && !depositElsewhere"
            type="button"
            class="text-sm font-extrabold text-accent underline-offset-2 hover:underline"
            @click="openDepositElsewhere"
          >
            Choose a different shelf
          </button>
          <button
            v-else-if="item.shelf_position && depositElsewhere"
            type="button"
            class="text-sm text-accent underline-offset-2 hover:underline"
            @click="resetDepositShelf"
          >
            Use this shelf instead
          </button>
        </div>

        <p v-if="!depositElsewhere" class="m-0 text-[0.85rem] text-ink">
          Shelf {{ item.shelf_position }}
          <span class="text-muted">(current)</span>
        </p>
        <template v-else>
          <p v-if="!item.shelf_position" class="m-0 text-[0.78rem] text-muted">
            This item isn't on a shelf yet -- pick where to deposit it.
          </p>
          <div
            v-if="otherShelves.length"
            class="flex flex-wrap items-center gap-1.5"
          >
            <span class="text-[0.75rem] text-muted"
              >You also have this on:</span
            >
            <button
              v-for="o in otherShelves"
              :key="o.id"
              type="button"
              class="rounded-full border px-2.5 py-1 text-[0.75rem] font-semibold"
              :class="
                depositShelfPosition === o.shelf_position
                  ? 'border-accent/60 bg-accent/15 text-ink'
                  : 'border-edge/70 text-muted hover:border-accent/40 hover:text-ink'
              "
              @click="pickDepositSuggestion(o)"
            >
              📍 {{ o.shelf_position }} ({{ o.quantity }} pcs)
            </button>
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-[0.78rem] text-muted">Destination shelf</label>
            <ShelfPicker
              v-model="depositShelfPosition"
              :options="shelfOptions"
              :loading="loadingShelves"
            />
          </div>
        </template>
      </div>

      <div
        class="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-surface px-3 py-2 text-[0.85rem]"
      >
        <span class="text-muted">
          {{ pendingAction === "withdraw" ? "Withdraw" : "Add" }}
          <strong class="text-ink">{{ qty }}</strong> unit(s) of
          <strong class="text-ink">{{ item.name }}</strong>
          <template
            v-if="
              pendingAction === 'deposit' &&
              depositElsewhere &&
              depositShelfPosition
            "
          >
            onto
            <strong class="text-ink">shelf {{ depositShelfPosition }}</strong>
          </template>
        </span>
        <span
          v-if="
            !(
              pendingAction === 'deposit' &&
              depositElsewhere &&
              depositShelfPosition
            )
          "
          class="whitespace-nowrap text-muted"
        >
          {{ item.quantity }} →
          <strong class="text-ink">{{ resultingQuantity }}</strong>
        </span>
      </div>

      <button
        type="button"
        class="cursor-pointer py-2.5 text-[0.95rem] font-semibold"
        :class="
          pendingAction === 'withdraw' ? 'btn btn--danger' : 'btn btn--confirm'
        "
        :disabled="
          busy ||
          !!qtyError ||
          (pendingAction === 'deposit' &&
            depositElsewhere &&
            !depositShelfPosition)
        "
        @click="confirmAction"
      >
        {{
          busy
            ? "Saving…"
            : pendingAction === "deposit" &&
                depositElsewhere &&
                depositShelfPosition
              ? `Confirm deposit onto shelf ${depositShelfPosition}`
              : `Confirm ${pendingAction === "withdraw" ? "removal" : "addition"}`
        }}
      </button>
    </div>

    <!-- Step 2 (move variant): pick the destination rack/shelf, then confirm -->
    <div
      v-else-if="pendingAction === 'move'"
      class="mt-3 flex flex-col gap-3 rounded-[10px] bg-surface-2 p-3"
    >
      <div class="flex items-center justify-between gap-2">
        <span
          class="text-[0.8rem] font-semibold uppercase tracking-wide text-accent"
        >
          Moving to another shelf
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

      <p class="m-0 text-[0.85rem] text-muted">
        <template v-if="item.shelf_position">
          Currently on
          <strong class="text-ink">Shelf {{ item.shelf_position }}</strong>
        </template>
        <template v-else>
          Not currently on a shelf -- pick where to put it.
        </template>
      </p>

      <div class="flex flex-wrap items-center gap-1.5">
        <button
          type="button"
          class="btn--icon h-9 w-9 cursor-pointer text-lg disabled:cursor-not-allowed disabled:opacity-40"
          :disabled="moveQty <= 1"
          title="Decrease"
          @click="moveQty = Math.max(1, moveQty - 1)"
        >
          −
        </button>
        <input
          v-model.number="moveQty"
          type="number"
          min="1"
          :max="item.quantity"
          class="field-input w-17.5 px-1 text-center text-[1.1rem] no-spinner"
        />
        <button
          type="button"
          class="btn--icon h-9 w-9 cursor-pointer text-lg disabled:cursor-not-allowed disabled:opacity-40"
          :disabled="moveQty >= item.quantity"
          title="Increase"
          @click="moveQty += 1"
        >
          +
        </button>

        <div class="ml-1 flex flex-wrap gap-1.5">
          <button
            v-for="preset in moveQuickQuantities"
            :key="preset.label"
            type="button"
            class="rounded-full border border-edge/70 px-2.5 py-1 text-[0.75rem] font-semibold text-muted hover:border-accent/50 hover:text-ink"
            :class="{ 'border-accent/60 text-ink': moveQty === preset.value }"
            @click="moveQty = preset.value"
          >
            {{ preset.label }}
          </button>
        </div>
      </div>
      <p class="m-0 text-[0.78rem] text-muted">
        {{
          moveQty >= item.quantity
            ? "Moving all of it -- the shelf will be freed up."
            : `${item.quantity - moveQty} unit(s) will stay on shelf ${item.shelf_position}.`
        }}
      </p>

      <div
        v-if="otherShelves.length"
        class="flex flex-wrap items-center gap-1.5"
      >
        <span class="text-[0.75rem] text-muted">You also have this on:</span>
        <button
          v-for="o in otherShelves"
          :key="o.id"
          type="button"
          class="rounded-full border px-2.5 py-1 text-[0.75rem] font-semibold"
          :class="
            moveShelfPosition === o.shelf_position
              ? 'border-accent/60 bg-accent/15 text-ink'
              : 'border-edge/70 text-muted hover:border-accent/40 hover:text-ink'
          "
          @click="pickMoveSuggestion(o)"
        >
          📍 {{ o.shelf_position }} ({{ o.quantity }} pcs)
        </button>
      </div>

      <div class="flex flex-col gap-1.5">
        <label class="text-[0.78rem] text-muted">Destination shelf</label>
        <ShelfPicker
          v-model="moveShelfPosition"
          :options="shelfOptions"
          :loading="loadingShelves"
        />
      </div>

      <p v-if="moveError" class="m-0 text-[0.8rem] text-red-300">
        {{ moveError }}
      </p>
      <p v-else-if="moveQtyError" class="m-0 text-[0.8rem] text-red-300">
        {{ moveQtyError }}
      </p>

      <button
        type="button"
        class="btn btn--confirm cursor-pointer py-2.5 text-[0.95rem] font-semibold"
        :disabled="
          busy ||
          !moveShelfPosition ||
          moveShelfPosition === item.shelf_position ||
          !!moveQtyError
        "
        @click="confirmMove"
      >
        {{
          busy
            ? "Moving…"
            : `Confirm move of ${moveQty} to ${moveShelfPosition || "…"}`
        }}
      </button>
    </div>

    <div class="mt-5">
      <div class="mb-1.5 flex items-center justify-between">
        <span
          class="text-[0.75rem] font-semibold uppercase tracking-wide text-muted"
          >Recent activity</span
        >
        <span v-if="loadingHistory" class="text-[0.75rem] text-muted"
          >Loading…</span
        >
      </div>
      <p
        v-if="!loadingHistory && !history.length"
        class="m-0 text-[0.8rem] text-muted"
      >
        No movements recorded yet for this item.
      </p>
      <ul v-else class="m-0 flex flex-col gap-1.5 p-0">
        <li
          v-for="h in history"
          :key="h.id"
          class="flex flex-wrap items-center justify-between gap-1.5 rounded-lg bg-surface-2 px-2.5 py-1.5 text-[0.8rem]"
          :class="{ 'opacity-45': h.voided }"
        >
          <span>
            <template v-if="h.action === 'move'">
              <strong class="text-accent">Moved </strong>
              <span class="text-muted">
                {{ h.from_shelf_position }} → {{ h.shelf_position }}</span
              >
            </template>
            <template v-else>
              <strong
                :class="
                  h.action === 'deposit' ? 'text-green-300' : 'text-red-300'
                "
              >
                {{ h.action === "deposit" ? "+" : "−" }}{{ h.quantity }}
              </strong>
            </template>
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
      <NuxtLink
        v-if="item.shelf_position"
        class="btn btn--ghost inline-flex cursor-pointer items-center gap-2"
        :to="{ path: '/', query: { locate: item.barcode } }"
        title="Locate on the map"
        aria-label="Locate on the map"
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
          <path
            d="M12 21s-7-6.1-7-11.5A7 7 0 0 1 19 9.5C19 14.9 12 21 12 21Z"
          />
          <circle cx="12" cy="9.5" r="2.5" />
        </svg>
        <span>Locate</span>
      </NuxtLink>
    </div>
  </section>
</template>

<script setup lang="ts">
import type {
  Item,
  Movement,
  MovementSource,
  ShelfPositionOption,
} from "~/composables/useWarehouseApi";

const props = defineProps<{
  item: Item;
  zoneLabel?: string;
  /** Where the current selection came from -- tags the *next* quick action for the audit log. */
  defaultSource?: MovementSource;
  /** Skip step 1 and jump straight into this action (used by the quick-action popups). */
  autoStartAction?: "withdraw" | "deposit" | "move";
}>();

const emit = defineEmits<{
  close: [];
  updated: [item: Item];
}>();

const {
  withdrawItem,
  depositItem,
  moveItem,
  getShelfPositions,
  labelUrl,
  listMovements,
  listItems,
} = useWarehouseApi();
const { show } = useToast();

const qty = ref<number>(1);
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
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const time = d.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  });
  return `${day}/${month} ${time}`;
}

// Step 1 only picks *which* movement; step 2 (below) then asks for the
// quantity (or destination shelf) and shows a confirmation summary before
// anything is sent.
const pendingAction = ref<"withdraw" | "deposit" | "move" | null>(null);

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

function sizeLabel(size: string) {
  return (
    ({ small: "Small", big: "Big", xl: "XL" } as Record<string, string>)[
      size
    ] || size
  );
}

// -- Move to another shelf --------------------------------------------
const shelfOptions = ref<ShelfPositionOption[]>([]);
const loadingShelves = ref(false);
const moveShelfPosition = ref("");
const moveQty = ref(1);

// Same part (same P/N) can legitimately live on more than one shelf --
// surface the other locations so an operator doesn't miss stock elsewhere,
// and let them jump straight to one as a deposit/move destination.
const otherShelves = ref<Item[]>([]);

async function loadOtherShelves() {
  if (!props.item.pn) {
    otherShelves.value = [];
    return;
  }
  try {
    const matches = await listItems({ pn: props.item.pn });
    otherShelves.value = matches.filter((i) => i.id !== props.item.id);
  } catch {
    otherShelves.value = [];
  }
}

// -- Deposit onto a different shelf ------------------------------------
const depositElsewhere = ref(false);
const depositShelfPosition = ref("");

watch(
  () => props.item.id,
  () => {
    pendingAction.value = null;
    qty.value = 1;
    moveShelfPosition.value = "";
    moveQty.value = props.item.quantity || 1;
    depositElsewhere.value = false;
    depositShelfPosition.value = "";
    loadHistory();
    loadOtherShelves();
    if (props.autoStartAction) startAction(props.autoStartAction);
  },
  { immediate: true },
);

async function loadShelfOptions() {
  loadingShelves.value = true;
  try {
    shelfOptions.value = await getShelfPositions();
  } catch {
    // Non-critical: the move/deposit panels just won't have options to pick from.
  } finally {
    loadingShelves.value = false;
  }
}

const moveError = computed(() => {
  if (pendingAction.value !== "move") return "";
  if (
    moveShelfPosition.value &&
    moveShelfPosition.value === props.item.shelf_position
  ) {
    return "This item is already on that shelf.";
  }
  return "";
});

// Common quick-pick amounts for a move, same idea as quickQuantities but
// capped to what's actually on the shelf right now.
const moveQuickQuantities = computed(() => {
  const cap = Math.max(props.item.quantity, 1);
  const presets = [1, 5, 10]
    .filter((n) => n < cap)
    .map((n) => ({ label: String(n), value: n }));
  presets.push({ label: "All", value: props.item.quantity });
  return presets;
});

const moveQtyError = computed(() => {
  if (pendingAction.value !== "move") return "";
  if (!moveQty.value || moveQty.value < 1)
    return "Enter a quantity of at least 1.";
  if (moveQty.value > props.item.quantity) {
    return `Only ${props.item.quantity} unit(s) available.`;
  }
  return "";
});

/** Quick-pick one of `otherShelves` as the move destination. */
function pickMoveSuggestion(o: Item) {
  moveShelfPosition.value = o.shelf_position;
  if (!shelfOptions.value.length) loadShelfOptions();
}

function openDepositElsewhere() {
  depositElsewhere.value = true;
  if (!shelfOptions.value.length) loadShelfOptions();
}

function resetDepositShelf() {
  depositElsewhere.value = false;
  depositShelfPosition.value = "";
}

/** Quick-pick one of `otherShelves` as the deposit destination. */
function pickDepositSuggestion(o: Item) {
  depositElsewhere.value = true;
  depositShelfPosition.value = o.shelf_position;
  if (!shelfOptions.value.length) loadShelfOptions();
}

function startAction(action: "withdraw" | "deposit" | "move") {
  pendingAction.value = action;
  qty.value = 1;
  if (action === "move") {
    moveQty.value = props.item.quantity || 1;
    moveShelfPosition.value = "";
    if (!shelfOptions.value.length) loadShelfOptions();
  }
  if (action === "deposit") {
    // No current shelf to fall back to -- go straight into "pick a shelf".
    depositElsewhere.value = !props.item.shelf_position;
    depositShelfPosition.value = "";
    if (depositElsewhere.value && !shelfOptions.value.length)
      loadShelfOptions();
  }
}

function cancelAction() {
  pendingAction.value = null;
  qty.value = 1;
  moveShelfPosition.value = "";
  depositElsewhere.value = false;
  depositShelfPosition.value = "";
}

async function confirmMove() {
  if (!moveShelfPosition.value || moveError.value || moveQtyError.value) return;
  busy.value = true;
  try {
    const res = await moveItem({
      barcode: props.item.barcode,
      shelf_position: moveShelfPosition.value,
      quantity: moveQty.value,
      source: (props.defaultSource ?? "manual") as MovementSource,
    });
    show("success", res.message);
    emit("updated", res.item);
    cancelAction();
    await loadHistory();
    await loadOtherShelves();
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to move item");
  } finally {
    busy.value = false;
  }
}

async function confirmAction() {
  const action = pendingAction.value;
  if (!action || action === "move" || qtyError.value) return;
  if (
    action === "deposit" &&
    depositElsewhere.value &&
    !depositShelfPosition.value
  )
    return;
  busy.value = true;
  try {
    const payload: {
      barcode: string;
      quantity: number;
      shelf_position?: string;
      source: MovementSource;
    } = {
      barcode: props.item.barcode,
      quantity: qty.value,
      source: (props.defaultSource ?? "manual") as MovementSource,
    };
    if (
      action === "deposit" &&
      depositElsewhere.value &&
      depositShelfPosition.value
    ) {
      payload.shelf_position = depositShelfPosition.value;
    }
    const res =
      action === "withdraw"
        ? await withdrawItem(payload)
        : await depositItem(payload);
    show("success", res.message);
    emit("updated", res.item);
    cancelAction();
    await loadHistory();
    await loadOtherShelves();
  } catch (err: any) {
    show("error", err?.data?.detail || "Operation failed");
  } finally {
    busy.value = false;
  }
}
</script>
