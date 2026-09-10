<template>
  <div class="flex gap-1.5">
    <!-- Activity log -->
    <button
      type="button"
      class="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-lg border border-edge bg-transparent text-muted transition-colors hover:border-accent/40 hover:text-accent"
      title="Activity log for this item"
      aria-label="Activity log for this item"
      @click.stop="emit('info', item)"
    >
      <img src="~/assets/icons/activity.svg" class="h-5 w-auto" />
    </button>

    <!-- Locate on the map -->
    <button
      v-if="showLocate"
      :disabled="!item.shelf_position"
      type="button"
      class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-accent/40 bg-accent/10 text-accent transition-colors hover:bg-accent/20 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-accent/10"
      title="Locate on the map"
      aria-label="Locate on the map"
      @click.stop="emit('locate', item)"
    >
      <img src="~/assets/icons/locate.svg" class="h-5 w-auto" />
    </button>

    <!-- Deposit stock -->
    <button
      type="button"
      class="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-lg border border-good/40 bg-good/10 text-green-300 transition-colors hover:bg-good/20"
      title="Deposit stock"
      aria-label="Deposit stock"
      @click.stop="emit('move', item, 'deposit')"
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

    <!-- Withdraw stock -->
    <button
      type="button"
      class="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-lg border border-bad/40 bg-bad/10 text-red-300 transition-colors hover:bg-bad/20 disabled:cursor-not-allowed disabled:opacity-40"
      title="Withdraw stock"
      aria-label="Withdraw stock"
      :disabled="item.quantity <= 0"
      @click.stop="emit('move', item, 'withdraw')"
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

    <!-- Move to another shelf -->
    <button
      type="button"
      class="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-lg border border-edge bg-transparent text-ink transition-colors hover:border-accent/40 hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-40"
      title="Move to another shelf"
      aria-label="Move to another shelf"
      :disabled="item.quantity <= 0"
      @click.stop="emit('relocate', item)"
    >
      <img src="~/assets/icons/move.svg" class="h-4 w-auto" />
    </button>

    <!-- Label -->
    <a
      class="inline-flex items-center gap-1.5 rounded-lg border border-edge px-2.5 py-1.5 text-[0.78rem] font-semibold text-ink no-underline hover:border-accent/40 hover:bg-surface-2 transition-colors"
      :href="labelUrl(item.id)"
      target="_blank"
      rel="noopener"
      title="Print label"
      aria-label="Print label"
      @click.stop
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
</template>

<script setup lang="ts">
import type { Item } from "~/composables/useWarehouseApi";

withDefaults(
  defineProps<{
    item: Item;
    showLocate?: boolean;
  }>(),
  { showLocate: true },
);

const { labelUrl } = useWarehouseApi();

const emit = defineEmits<{
  info: [item: Item];
  locate: [item: Item];
  move: [item: Item, action: "deposit" | "withdraw"];
  relocate: [item: Item];
}>();
</script>
