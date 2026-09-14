<template>
  <form class="flex flex-col gap-3.5" @submit.prevent="submit">
    <div class="rounded-[10px] border border-white/10 bg-surface px-3.5 py-3 text-[0.85rem]">
      <p class="m-0 font-semibold text-ink">{{ baseItem.name }}</p>
      <p class="m-0 mt-1 text-muted">
        <span v-if="baseItem.pn">P/N {{ baseItem.pn }} · </span>
        <span class="badge badge--category">{{ baseItem.category }}</span>
        <span v-if="baseItem.program" class="badge badge--program ml-1">{{
          baseItem.program
        }}</span>
        <span class="badge badge--size ml-1" :class="`badge--size-${baseItem.size}`">{{
          sizeLabel(baseItem.size)
        }}</span>
      </p>
      <p class="m-0 mt-1.5 text-[0.75rem] text-muted">
        The new serial(s) will share these same details -- only serial number,
        location, and (optionally) notes change per unit below.
      </p>
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="text-[0.8rem] text-muted"
        >Serial number{{ serials.length === 1 ? "" : "s" }}
        <span class="text-[0.72rem] text-muted">(one per line, at least one)</span></label
      >
      <TagsInput
        v-model="serials"
        placeholder="Type a serial, press Enter…"
        class="w-full font-mono"
      />
      <p class="m-0 text-[0.75rem] text-muted">
        {{ serials.length }} new item{{ serials.length === 1 ? "" : "s" }} will be
        created, quantity 1 each.
      </p>
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="text-[0.8rem] text-muted"
        >Shelf
        <span class="text-[0.72rem] text-muted">(required unless quantity is 0)</span></label
      >
      <ShelfPicker
        v-model="shelfPosition"
        v-model:zone-id="zoneId"
        :options="shelfOptions"
        :zones="zones"
        :loading="loadingOptions"
      />
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="text-[0.8rem] text-muted"
        >Notes
        <span class="text-[0.72rem] text-muted">(optional, applied to every new serial)</span></label
      >
      <textarea
        v-model="notes"
        rows="2"
        class="field-input resize-none"
        placeholder="e.g. received with this batch"
      ></textarea>
    </div>

    <p v-if="error" class="m-0 text-[0.85rem] text-red-300">{{ error }}</p>

    <div class="flex justify-end gap-2">
      <button
        type="button"
        class="btn btn--ghost btn--small"
        :disabled="submitting"
        @click="emit('close')"
      >
        Cancel
      </button>
      <button
        type="submit"
        class="btn btn--confirm btn--small text-[#06280f] disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="submitting || !serials.length"
      >
        {{ submitting ? "Creating…" : `Create ${serials.length || ""} item${serials.length === 1 ? "" : "s"}` }}
      </button>
    </div>
  </form>
</template>

<script setup lang="ts">
import type { Item, ShelfPositionOption, Zone } from "~/composables/useWarehouseApi";

const props = defineProps<{
  /** Representative item of the group -- supplies the descriptive fields
   *  (name, P/N, category, program, size) shared by every serial. */
  baseItem: Item;
}>();

const emit = defineEmits<{
  close: [];
  created: [items: Item[]];
}>();

const { createItemsBulk, getShelfPositions, getZones, labelBatchUrl } =
  useWarehouseApi();
const { show } = useToast();

const serials = ref<string[]>([]);
const shelfPosition = ref(props.baseItem.shelf_position || "");
const zoneId = ref<number | null>(props.baseItem.zone_id ?? null);
const notes = ref("");
const submitting = ref(false);
const loadingOptions = ref(false);
const error = ref("");

const shelfOptions = ref<ShelfPositionOption[]>([]);
const zones = ref<Zone[]>([]);

function sizeLabel(size: string) {
  return { small: "S", big: "B", xl: "XL" }[size] || size;
}

async function loadOptions() {
  loadingOptions.value = true;
  try {
    const [shelves, zoneList] = await Promise.all([
      getShelfPositions(),
      getZones(),
    ]);
    shelfOptions.value = shelves;
    zones.value = zoneList;
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to load shelves/zones");
  } finally {
    loadingOptions.value = false;
  }
}

async function submit() {
  error.value = "";
  if (!serials.value.length) {
    error.value = "Enter at least one serial number.";
    return;
  }
  if (!shelfPosition.value && !zoneId.value) {
    error.value = "Pick a shelf or a zone for the new serial(s).";
    return;
  }
  submitting.value = true;
  try {
    const items = await createItemsBulk({
      name: props.baseItem.name,
      pn: props.baseItem.pn,
      category: props.baseItem.category,
      program: props.baseItem.program || "",
      size: props.baseItem.size,
      shelf_position: shelfPosition.value,
      zone_id: zoneId.value,
      quantity: 1,
      tags: props.baseItem.tags || [],
      notes: notes.value,
      serials: serials.value,
    });
    show(
      "success",
      `${items.length} item${items.length === 1 ? "" : "s"} created`,
    );
    // Same one-tab, one-print-dialog pattern as the New Item form's bulk mode.
    window.open(
      labelBatchUrl(items.map((it) => it.id)),
      "_blank",
    );
    emit("created", items);
  } catch (err: any) {
    error.value = err?.data?.detail || "Failed to create the new serial(s)";
  } finally {
    submitting.value = false;
  }
}

onMounted(loadOptions);
</script>
