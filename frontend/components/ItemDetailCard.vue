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

    <div class="mt-3 flex flex-wrap gap-2 max-[640px]:flex-col">
      <button
        type="button"
        class="btn btn--danger flex-1 cursor-pointer py-2.5 text-[0.95rem] font-semibold"
        :disabled="busy"
        @click="performAction('withdraw')"
      >
        Remove
      </button>
      <button
        type="button"
        class="btn btn--confirm flex-1 cursor-pointer py-2.5 text-[0.95rem] font-semibold"
        :disabled="busy"
        @click="performAction('deposit')"
      >
        Add
      </button>
    </div>

    <div class="mt-3 flex flex-wrap items-center justify-between gap-2.5">
      <div class="flex items-center gap-1.5">
        <label class="mr-1 text-sm text-muted" for="qty-input">Quantity</label>
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
          class="field-input w-17.5 px-1 text-center text-[1.1rem]"
        />
        <button
          type="button"
          class="btn--icon h-9 w-9 cursor-pointer text-lg"
          title="Increase"
          @click="qty += 1"
        >
          +
        </button>
      </div>
    </div>

    <p class="mt-1 text-[0.78rem] text-muted">
      Choose the movement first, then set the quantity.
    </p>

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
        <span>Print</span>
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
        <span>Dashboard</span>
      </NuxtLink>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { Item, MovementSource } from "~/composables/useWarehouseApi";

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

const { withdrawItem, depositItem, labelUrl } = useWarehouseApi();
const { show } = useToast();

const qty = ref(1);
const busy = ref(false);

// Common quick-pick amounts, plus "All" (the full current stock) so clearing
// out a shelf in one withdrawal doesn't require typing the exact number.
const quickQuantities = computed(() => {
  const presets = [1, 5, 10]
    .filter((n) => n <= Math.max(props.item.quantity, 1))
    .map((n) => ({ label: String(n), value: n }));
  if (
    props.item.quantity > 0 &&
    !presets.some((p) => p.value === props.item.quantity)
  ) {
    presets.push({ label: "All", value: props.item.quantity });
  }
  return presets;
});

function sizeLabel(size: string) {
  return (
    ({ small: "Small", big: "Big", xl: "XL" } as Record<string, string>)[
      size
    ] || size
  );
}

async function performAction(action: "withdraw" | "deposit") {
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
    qty.value = 1;
  } catch (err: any) {
    show("error", err?.data?.detail || "Operation failed");
  } finally {
    busy.value = false;
  }
}
</script>
