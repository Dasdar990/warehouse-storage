<template>
  <div class="flex flex-col gap-4">
    <p class="m-0 text-[0.85rem] text-muted">
      Move everything currently on one shelf, or an entire rack's levels, to
      another location in one shot. Quantities are untouched -- only the
      shelf changes, and each moved item still gets its own entry in the
      Activity Log.
    </p>

    <div class="flex gap-1.5">
      <button
        type="button"
        class="flex-1 cursor-pointer rounded-lg border px-3 py-2 text-[0.85rem] font-semibold"
        :class="
          mode === 'shelf'
            ? 'border-accent/60 bg-accent/15 text-ink'
            : 'border-edge/70 text-muted hover:text-ink'
        "
        @click="setMode('shelf')"
      >
        Whole shelf
      </button>
      <button
        type="button"
        class="flex-1 cursor-pointer rounded-lg border px-3 py-2 text-[0.85rem] font-semibold"
        :class="
          mode === 'rack'
            ? 'border-accent/60 bg-accent/15 text-ink'
            : 'border-edge/70 text-muted hover:text-ink'
        "
        @click="setMode('rack')"
      >
        Whole rack
      </button>
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="text-[0.8rem] text-muted">{{
        mode === "shelf" ? "From shelf" : "From rack"
      }}</label>
      <ShelfPicker
        v-if="mode === 'shelf'"
        v-model="fromCode"
        :options="shelfOptions"
        :loading="loading"
        placeholder="Type a shelf, e.g. 12B…"
      />
      <select
        v-else
        v-model="fromCode"
        :disabled="loading"
        class="field-input disabled:cursor-not-allowed disabled:opacity-60"
      >
        <option value="" disabled>Select a rack…</option>
        <option v-for="r in racks" :key="r.code" :value="r.code">
          {{ r.label }} ({{ r.levelCount }} level{{ r.levelCount === 1 ? "" : "s" }})
        </option>
      </select>
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="text-[0.8rem] text-muted">{{
        mode === "shelf" ? "To shelf" : "To rack"
      }}</label>
      <ShelfPicker
        v-if="mode === 'shelf'"
        v-model="toCode"
        :options="shelfOptions"
        :loading="loading"
        placeholder="Type a shelf, e.g. 9C…"
      />
      <select
        v-else
        v-model="toCode"
        :disabled="loading"
        class="field-input disabled:cursor-not-allowed disabled:opacity-60"
      >
        <option value="" disabled>Select a rack…</option>
        <option
          v-for="r in racks"
          :key="r.code"
          :value="r.code"
          :disabled="r.code === fromCode"
        >
          {{ r.label }} ({{ r.levelCount }} level{{ r.levelCount === 1 ? "" : "s" }})
        </option>
      </select>
    </div>

    <p
      v-if="mode === 'rack' && fromRackInfo && toRackInfo && toRackInfo.levelCount < fromRackInfo.levelCount"
      class="m-0 text-[0.8rem] text-red-300"
    >
      "{{ toRackInfo.label }}" only has {{ toRackInfo.levelCount }} level(s), but
      "{{ fromRackInfo.label }}" has {{ fromRackInfo.levelCount }} -- pick a rack
      with at least as many levels.
    </p>

    <p v-if="error" class="m-0 text-[0.8rem] text-red-300">{{ error }}</p>

    <button
      type="button"
      class="btn btn--danger cursor-pointer py-2.5 text-[0.95rem] font-semibold"
      :disabled="submitting || !fromCode || !toCode || fromCode === toCode"
      @click="submit"
    >
      {{
        submitting
          ? "Moving…"
          : mode === "shelf"
            ? `Move everything from ${fromCode || "…"} to ${toCode || "…"}`
            : `Move rack ${fromCode || "…"} to ${toCode || "…"}`
      }}
    </button>
  </div>
</template>

<script setup lang="ts">
import type { ShelfPositionOption } from "~/composables/useWarehouseApi";

const emit = defineEmits<{ done: [] }>();

const { getShelfPositions, specialMove } = useWarehouseApi();
const { show } = useToast();

const mode = ref<"shelf" | "rack">("shelf");
const fromCode = ref("");
const toCode = ref("");
const shelfOptions = ref<ShelfPositionOption[]>([]);
const loading = ref(false);
const submitting = ref(false);
const error = ref("");

async function load() {
  loading.value = true;
  try {
    shelfOptions.value = await getShelfPositions();
  } catch {
    // Non-critical: the pickers just won't have options to show.
  } finally {
    loading.value = false;
  }
}
load();

function setMode(m: "shelf" | "rack") {
  mode.value = m;
  fromCode.value = "";
  toCode.value = "";
  error.value = "";
}

// Unique racks derived from the flat shelf-position list, with how many
// levels each has -- needed to warn upfront if the destination rack can't
// fit the source rack's levels.
const racks = computed(() => {
  const seen = new Map<string, { code: string; label: string; levelCount: number }>();
  for (const opt of shelfOptions.value) {
    const existing = seen.get(opt.rack_code);
    if (existing) existing.levelCount += 1;
    else seen.set(opt.rack_code, { code: opt.rack_code, label: opt.rack_label, levelCount: 1 });
  }
  return Array.from(seen.values()).sort((a, b) => a.label.localeCompare(b.label));
});

const fromRackInfo = computed(() => racks.value.find((r) => r.code === fromCode.value));
const toRackInfo = computed(() => racks.value.find((r) => r.code === toCode.value));

async function submit() {
  if (!fromCode.value || !toCode.value || fromCode.value === toCode.value) return;
  error.value = "";
  submitting.value = true;
  try {
    const res = await specialMove({ mode: mode.value, from_code: fromCode.value, to_code: toCode.value });
    show("success", res.message);
    fromCode.value = "";
    toCode.value = "";
    emit("done");
  } catch (err: any) {
    error.value = err?.data?.detail || "Failed to move";
  } finally {
    submitting.value = false;
  }
}
</script>
