<template>
  <div class="flex flex-col gap-2.5">
    <p class="m-0 text-[0.85rem] text-muted">
      "{{ name }}"<template v-if="pn"> · P/N {{ pn }}</template> is stocked in
      {{ locations.length }} different location{{ locations.length === 1 ? "" : "s" }}.
      Pick one to see it on the map.
    </p>

    <div
      v-for="loc in locations"
      :key="loc.id"
      class="flex flex-wrap items-center justify-between gap-3 rounded-[10px] border border-edge/70 bg-surface px-3.5 py-3"
    >
      <div class="flex min-w-0 flex-col gap-1.5">
        <div class="flex flex-wrap items-center gap-2">
          <span class="badge badge--shelf">📍 Shelf {{ loc.shelf_position }}</span>
          <span
            class="rounded-full px-2.5 py-1 text-[0.75rem] font-bold"
            :class="loc.quantity > 0 ? 'bg-good/15 text-green-300' : 'bg-bad/15 text-red-300'"
            >{{ loc.quantity }} pcs</span
          >
        </div>
        <div class="flex flex-wrap items-center gap-1.5 text-[0.78rem] text-muted">
          <span v-if="loc.serial" class="badge badge--serial">S/N {{ loc.serial }}</span>
          <span v-if="loc.program" class="badge badge--program">{{ loc.program }}</span>
          <span v-if="!loc.serial && !loc.program">No serial or program set</span>
        </div>
      </div>
      <button
        type="button"
        class="btn btn--confirm btn--small shrink-0 whitespace-nowrap"
        @click="emit('locate', loc)"
      >
        📍 Locate
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Item } from "~/composables/useWarehouseApi";

defineProps<{
  name: string;
  pn?: string;
  locations: Item[];
}>();

const emit = defineEmits<{ locate: [item: Item] }>();
</script>
