<template>
  <div class="flex flex-col gap-4">
    <p class="m-0 text-[0.85rem] text-muted">
      Moving <strong class="text-ink">{{ items.length }}</strong> item{{
        items.length === 1 ? "" : "s"
      }}: {{ itemNamesPreview }}
    </p>

    <div class="flex gap-1.5">
      <button
        type="button"
        class="flex-1 cursor-pointer rounded-lg border px-3 py-2 text-[0.85rem] font-semibold"
        :class="
          destMode === 'shelf'
            ? 'border-accent/60 bg-accent/15 text-ink'
            : 'border-edge/70 text-muted hover:text-ink'
        "
        @click="destMode = 'shelf'"
      >
        Shelf / Zone
      </button>
      <button
        type="button"
        class="flex-1 cursor-pointer rounded-lg border px-3 py-2 text-[0.85rem] font-semibold"
        :class="
          destMode === 'box'
            ? 'border-accent/60 bg-accent/15 text-ink'
            : 'border-edge/70 text-muted hover:text-ink'
        "
        @click="destMode = 'box'"
      >
        📦 Box
      </button>
    </div>

    <div v-if="destMode === 'shelf'" class="flex flex-col gap-1.5">
      <label class="text-[0.8rem] text-muted">Destination</label>
      <ShelfPicker
        v-model="shelfPosition"
        v-model:zone-id="zoneId"
        :options="shelfOptions"
        :zones="zones"
        :loading="loadingOptions"
        placeholder="Type a shelf, rack or zone…"
      />
    </div>

    <div v-else class="flex flex-col gap-2 rounded-[10px] border border-edge bg-surface px-4 py-3">
      <div class="flex gap-2">
        <button
          type="button"
          class="btn btn--small"
          :class="boxChoice === 'existing' ? 'btn--confirm' : 'btn--ghost'"
          @click="boxChoice = 'existing'"
        >
          Use existing box
        </button>
        <button
          type="button"
          class="btn btn--small"
          :class="boxChoice === 'new' ? 'btn--confirm' : 'btn--ghost'"
          @click="boxChoice = 'new'"
        >
          + New box
        </button>
      </div>

      <template v-if="boxChoice === 'existing'">
        <input
          v-model="boxSearch"
          type="text"
          placeholder="Find a box — code, name, or shelf…"
          class="field-input"
        />
        <p v-if="loadingBoxes" class="m-0 text-[0.75rem] text-muted">
          Loading boxes…
        </p>
        <p
          v-else-if="!filteredExistingBoxes.length"
          class="m-0 text-[0.75rem] text-muted"
        >
          No box matches -- switch to "+ New box" to create one.
        </p>
        <div v-else class="flex max-h-40 flex-col gap-1 overflow-y-auto">
          <button
            v-for="b in filteredExistingBoxes"
            :key="b.id"
            type="button"
            class="flex items-center justify-between gap-2 rounded-lg border px-3 py-1.5 text-left text-[0.85rem]"
            :class="
              selectedBoxId === b.id
                ? 'border-accent bg-accent/10'
                : 'border-edge hover:border-accent/50'
            "
            @click="selectedBoxId = b.id"
          >
            <span
              ><strong>{{ b.code }}</strong
              ><template v-if="b.name"> · {{ b.name }}</template></span
            >
            <span class="text-muted">Shelf {{ b.shelf_position }}</span>
          </button>
        </div>
      </template>

      <template v-else>
        <div class="flex flex-col gap-1.5">
          <label class="text-[0.8rem] text-muted">Shelf for the new box</label>
          <ShelfPicker
            v-model="newBoxShelfPosition"
            :options="shelfOptions"
            :loading="loadingOptions"
            placeholder="Type a shelf, e.g. 12B…"
          />
        </div>
        <input
          v-model="newBoxName"
          type="text"
          placeholder="Box name (optional)"
          maxlength="80"
          class="field-input"
        />
      </template>
    </div>

    <p v-if="error" class="m-0 text-[0.8rem] text-red-300">{{ error }}</p>

    <button
      type="button"
      class="btn btn--confirm py-2.5 text-[0.95rem] font-semibold text-[#06280f] disabled:cursor-not-allowed disabled:opacity-60"
      :disabled="submitting || !items.length"
      @click="submit"
    >
      {{
        submitting
          ? `Moving… (${progress}/${items.length})`
          : `Move ${items.length} item${items.length === 1 ? "" : "s"}`
      }}
    </button>
  </div>
</template>

<script setup lang="ts">
import type { Box, Item, ShelfPositionOption, Zone } from "~/composables/useWarehouseApi";

const props = defineProps<{ items: Item[] }>();
const emit = defineEmits<{ done: [] }>();

const { getShelfPositions, getZones, listBoxes, createBox, addItemToBox, moveItem } =
  useWarehouseApi();
const { show } = useToast();

const itemNamesPreview = computed(() => {
  const names = props.items.map((i) => i.name);
  if (names.length <= 3) return names.join(", ");
  return `${names.slice(0, 3).join(", ")}, +${names.length - 3} more`;
});

// -- Shelf / Zone destination --
const destMode = ref<"shelf" | "box">("shelf");
const shelfPosition = ref("");
const zoneId = ref<number | null>(null);
const shelfOptions = ref<ShelfPositionOption[]>([]);
const zones = ref<Zone[]>([]);
const loadingOptions = ref(false);

// -- Box destination (same picker as "create item -> put in a box") --
const boxChoice = ref<"existing" | "new">("existing");
const allBoxes = ref<Box[]>([]);
const loadingBoxes = ref(false);
const boxSearch = ref("");
const selectedBoxId = ref<number | null>(null);
const newBoxShelfPosition = ref("");
const newBoxName = ref("");

const filteredExistingBoxes = computed(() => {
  const q = boxSearch.value.trim().toLowerCase();
  if (!q) return allBoxes.value;
  return allBoxes.value.filter((b) =>
    [b.code, b.name, b.shelf_position]
      .filter(Boolean)
      .some((f) => f!.toLowerCase().includes(q)),
  );
});

const submitting = ref(false);
const progress = ref(0);
const error = ref("");

async function loadOptions() {
  loadingOptions.value = true;
  loadingBoxes.value = true;
  try {
    const [shelves, zoneList, boxes] = await Promise.all([
      getShelfPositions(),
      getZones(),
      listBoxes(),
    ]);
    shelfOptions.value = shelves;
    zones.value = zoneList;
    allBoxes.value = boxes;
  } catch {
    // Non-critical: pickers just won't have options to show.
  } finally {
    loadingOptions.value = false;
    loadingBoxes.value = false;
  }
}
loadOptions();

/** Resolves the box destination to a concrete box, creating it first if needed. */
async function resolveTargetBox(): Promise<Box> {
  if (boxChoice.value === "existing") {
    const box = allBoxes.value.find((b) => b.id === selectedBoxId.value);
    if (!box) throw new Error("Pick a box from the list, or create a new one.");
    return box;
  }
  const shelf = newBoxShelfPosition.value.trim();
  if (!shelf) throw new Error("Enter a shelf position for the new box.");
  return createBox({ name: newBoxName.value.trim() || null, shelf_position: shelf });
}

async function submit() {
  error.value = "";
  if (!props.items.length) return;

  if (destMode.value === "shelf" && !shelfPosition.value && !zoneId.value) {
    error.value = "Pick a shelf or a zone.";
    return;
  }

  let targetBox: Box | null = null;
  if (destMode.value === "box") {
    try {
      targetBox = await resolveTargetBox();
    } catch (err: any) {
      error.value = err?.message || "Pick or create a box first.";
      return;
    }
  }

  submitting.value = true;
  progress.value = 0;
  let failed = 0;

  for (const item of props.items) {
    try {
      if (targetBox) {
        await addItemToBox(targetBox.id, item.id);
      } else {
        await moveItem({
          barcode: item.barcode,
          shelf_position: shelfPosition.value || undefined,
          zone_id: zoneId.value,
        });
      }
    } catch {
      failed += 1;
    } finally {
      progress.value += 1;
    }
  }

  submitting.value = false;
  const moved = props.items.length - failed;
  if (failed) {
    show(
      "error",
      `Moved ${moved} of ${props.items.length} item(s) -- ${failed} failed (see Activity Log for what went through).`,
    );
  } else {
    show(
      "success",
      targetBox
        ? `${moved} item(s) put in box ${targetBox.code}`
        : `${moved} item(s) moved`,
    );
  }
  emit("done");
}
</script>
