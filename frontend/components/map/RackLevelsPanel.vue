<template>
  <section :class="showHeader ? 'card' : ''">
    <div
      v-if="showHeader"
      class="mb-3.5 flex flex-wrap items-start justify-between gap-3"
    >
      <div>
        <h2>Rack {{ rack.label || rack.rack_code }}</h2>
        <p class="mt-1 mb-0 text-[0.85rem] text-muted">
          {{ rack.levels.length }} level(s) — click a level to see its items
        </p>
      </div>
      <button
        class="rounded-lg bg-transparent px-2.5 py-1 text-base transition-colors hover:text-ink"
        title="Close"
        @click="emit('close')"
      >
        ✕
      </button>
    </div>
    <p v-else class="mb-3.5 text-[0.85rem] text-muted">
      {{ rack.levels.length }} level(s) — click a level to see its items
    </p>

    <p v-if="loading" class="py-5 text-muted">Loading…</p>
    <div
      v-else
      class="grid grid-cols-[repeat(auto-fill,minmax(140px,1fr))] gap-2.5"
    >
      <button
        v-for="lvl in rack.levels"
        :key="lvl.shelf_position"
        class="flex cursor-pointer flex-col gap-1 rounded-[10px] border p-3 text-left text-ink transition duration-80 ease-out hover:-translate-y-0.5 hover:shadow-[0_4px_14px_rgba(0,0,0,0.35)]"
        :class="levelClass(lvl.shelf_position, lvl.item_count > 0)"
        @click="emit('select-level', lvl.shelf_position)"
      >
        <span class="text-[0.85rem] font-bold">Level {{ lvl.level }}</span>
        <span
          class="text-[0.72rem]"
          :class="lvl.item_count > 0 ? 'text-muted' : 'text-sky-300/80'"
          >{{ lvl.shelf_position }}</span
        >
        <span v-if="lvl.item_count" class="mt-1 text-[0.75rem] font-semibold"
          >{{ lvl.item_count }} item(s) · {{ lvl.total_quantity }} unit(s)</span
        >
        <span
          v-else
          class="mt-1 inline-flex items-center gap-1 text-[0.78rem] font-bold text-sky-300"
          >＋ Empty · Available</span
        >
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { RackLevelsResponse } from "~/composables/useWarehouseApi";

const props = withDefaults(
  defineProps<{
    rack: RackLevelsResponse;
    selectedLevel: string | null;
    loading: boolean;
    showHeader?: boolean;
  }>(),
  { showHeader: true },
);

const emit = defineEmits<{ "select-level": [string]; close: [] }>();

function levelClass(shelfPosition: string, hasItems: boolean) {
  const base = !hasItems
    ? "border-dashed border-sky-400/40 bg-sky-500/[0.07] hover:bg-sky-500/[0.12]"
    : "bg-accent/[0.14] border-accent/45";
  const selected =
    props.selectedLevel === shelfPosition
      ? "outline outline-2 outline-offset-2 outline-accent"
      : "";
  return [base, selected];
}
</script>
