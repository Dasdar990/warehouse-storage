<template>
  <form
    class="grid grid-cols-2 gap-3.5 max-[640px]:grid-cols-1"
    @submit.prevent="submit"
  >
    <div class="flex flex-col gap-1.5 col-span-full">
      <label class="text-[0.8rem] text-muted">Item name</label>
      <input
        v-model="form.name"
        required
        type="text"
        placeholder="Hex Bolt M8x30"
        class="field-input disabled:cursor-not-allowed disabled:opacity-60"
      />
    </div>
    <div class="flex flex-col gap-1.5">
      <label class="text-[0.8rem] text-muted"
        >Part Number
        <span class="text-[0.72rem] text-muted">(optional)</span></label
      >
      <input
        v-model="form.pn"
        type="text"
        placeholder="HB-M8-30"
        class="field-input disabled:cursor-not-allowed disabled:opacity-60"
      />
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="text-[0.8rem] text-muted"
        >Serial Number
        <span class="text-[0.72rem] text-muted">(optional)</span></label
      >
      <input
        v-model="form.serial"
        type="text"
        placeholder="SN-00123"
        class="field-input disabled:cursor-not-allowed disabled:opacity-60"
      />
    </div>

    <div class="flex flex-col gap-1.5 col-span-full">
      <label class="text-[0.8rem] text-muted">Barcode</label>
      <div class="flex gap-2">
        <input
          v-model="form.barcode"
          required
          type="text"
          placeholder="Auto-generated"
          class="field-input min-w-0 flex-1 py-2.5 text-[0.95rem] font-mono tracking-wide disabled:cursor-not-allowed disabled:opacity-60"
        />
        <button
          class="btn btn--ghost whitespace-nowrap disabled:cursor-not-allowed disabled:opacity-60"
          type="button"
          :disabled="generatingBarcode"
          title="Generate a new unique barcode"
          @click="suggestBarcode"
        >
          {{ generatingBarcode ? "…" : "↻ Generate" }}
        </button>
      </div>
      <p class="m-0 text-[0.75rem] text-muted">
        Auto-generated, but you can type your own value.
      </p>
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="text-[0.8rem] text-muted">Category</label>
      <select
        v-model="form.category"
        required
        :disabled="loadingOptions"
        class="field-input disabled:cursor-not-allowed disabled:opacity-60"
      >
        <option value="" disabled>Select a category…</option>
        <option v-for="cat in categories" :key="cat.id" :value="cat.name">
          {{ cat.name }}
        </option>
      </select>
      <p
        v-if="!loadingOptions && !categories.length"
        class="m-0 text-[0.75rem] text-muted"
      >
        No categories yet —
        <NuxtLink to="/categories" class="text-accent"
          >create one first</NuxtLink
        >.
      </p>
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="text-[0.8rem] text-muted"
        >Program
        <span class="text-[0.72rem] text-muted">(optional)</span></label
      >
      <select
        v-model="form.program"
        :disabled="loadingOptions"
        class="field-input disabled:cursor-not-allowed disabled:opacity-60"
      >
        <option value="">— None —</option>
        <option v-for="prog in programs" :key="prog.id" :value="prog.name">
          {{ prog.name }}
        </option>
      </select>
      <p
        v-if="!loadingOptions && !programs.length"
        class="m-0 text-[0.75rem] text-muted"
      >
        No programs yet —
        <NuxtLink to="/categories" class="text-accent"
          >create one first</NuxtLink
        >.
      </p>
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="text-[0.8rem] text-muted">Size</label>
      <select
        v-model="form.size"
        class="field-input disabled:cursor-not-allowed disabled:opacity-60"
      >
        <option value="small">Small</option>
        <option value="big">Big</option>
        <option value="xl">XL</option>
      </select>
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="text-[0.8rem] text-muted">Rack</label>
      <select
        v-model="selectedRackCode"
        required
        :disabled="loadingOptions"
        class="field-input disabled:cursor-not-allowed disabled:opacity-60"
      >
        <option value="" disabled>Select a rack…</option>
        <option v-for="rack in racks" :key="rack.code" :value="rack.code">
          {{ rack.label }}
        </option>
      </select>
      <p
        v-if="!loadingOptions && !racks.length"
        class="m-0 text-[0.75rem] text-muted"
      >
        No shelves configured yet —
        <NuxtLink to="/map-config" class="text-accent"
          >set up the warehouse map first</NuxtLink
        >.
      </p>
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="text-[0.8rem] text-muted">Shelf</label>
      <select
        v-model="form.shelf_position"
        required
        :disabled="loadingOptions || !selectedRackCode"
        class="field-input disabled:cursor-not-allowed disabled:opacity-60"
      >
        <option value="" disabled>
          {{ selectedRackCode ? "Select a shelf…" : "Select a rack first" }}
        </option>
        <option
          v-for="opt in shelvesForSelectedRack"
          :key="opt.value"
          :value="opt.value"
        >
          Level {{ opt.level }} ({{ opt.value }})
        </option>
      </select>
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="text-[0.8rem] text-muted">Initial Quantity</label>
      <input
        v-model.number="form.quantity"
        type="number"
        min="0"
        class="field-input disabled:cursor-not-allowed disabled:opacity-60"
      />
    </div>

    <div
      v-if="duplicates.length"
      class="col-span-full flex flex-col gap-2.5 rounded-[10px] border border-amber-500/40 bg-amber-500/10 px-4 py-3"
    >
      <p class="m-0 text-[0.85rem] font-semibold text-amber-200">
        ⚠ {{ duplicates.length === 1 ? "An item" : "Items" }} with this
        {{ form.pn ? "name/PN" : "name" }} already exist{{
          duplicates.length === 1 ? "s" : ""
        }}. Add stock there instead of creating a near-duplicate?
      </p>
      <div
        v-for="dup in duplicates"
        :key="dup.id"
        class="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-surface px-3 py-2 text-[0.82rem]"
      >
        <span class="text-ink">
          <strong>{{ dup.name }}</strong>
          <span v-if="dup.pn" class="text-muted"> · P/N {{ dup.pn }}</span>
          <span class="text-muted"> · {{ dup.quantity }} in stock · Shelf {{ dup.shelf_position }}</span>
        </span>
        <button
          type="button"
          class="btn btn--confirm btn--small whitespace-nowrap disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="addingToExisting === dup.id"
          @click="addToExisting(dup)"
        >
          {{ addingToExisting === dup.id ? "Adding…" : `Add ${form.quantity || 1} here instead` }}
        </button>
      </div>
      <p class="m-0 text-[0.75rem] text-muted">
        Not the same item? You can ignore this and save below to create a new one anyway.
      </p>
    </div>

    <p v-if="error" class="col-span-full m-0 text-red-300">{{ error }}</p>
    <button
      class="btn col-span-full justify-self-start disabled:cursor-not-allowed disabled:opacity-60"
      :class="duplicates.length ? 'btn--ghost' : 'btn--confirm'"
      type="submit"
      :disabled="submitting"
    >
      {{
        submitting
          ? "Saving…"
          : duplicates.length
            ? "Create as new item anyway"
            : "Save Item"
      }}
    </button>

    <transition
      enter-active-class="transition duration-200 ease-out"
      leave-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-1.5"
      leave-to-class="opacity-0 -translate-y-1.5"
    >
      <div
        v-if="lastCreated"
        class="col-span-full flex flex-wrap items-center justify-between gap-3 rounded-[10px] border border-good bg-good-dim px-4 py-3 text-green-200"
      >
        <div>
          <strong>{{ lastCreated.name }}</strong> saved with barcode
          <span class="font-mono">{{ lastCreated.barcode }}</span>
        </div>
        <button
          class="btn btn--ghost btn--small"
          type="button"
          @click="printLabel"
        >
          🖨 Print Label
        </button>
      </div>
    </transition>
  </form>
</template>

<script setup lang="ts">
import type {
  Category,
  Item,
  Program,
  ShelfPositionOption,
} from "~/composables/useWarehouseApi";

const emit = defineEmits<{ created: [item: Item] }>();

const {
  createItem,
  checkDuplicateItems,
  depositItem,
  generateBarcode,
  listAdminCategories,
  listAdminPrograms,
  getShelfPositions,
  labelUrl,
} = useWarehouseApi();
const { show } = useToast();

const EMPTY_FORM = {
  name: "",
  pn: "",
  serial: "",
  barcode: "",
  category: "",
  program: "",
  size: "small" as Item["size"],
  shelf_position: "",
  quantity: 0,
};

const form = ref({ ...EMPTY_FORM });
const error = ref("");
const submitting = ref(false);
const generatingBarcode = ref(false);
const loadingOptions = ref(false);

const categories = ref<Category[]>([]);
const programs = ref<Program[]>([]);
const shelfOptions = ref<ShelfPositionOption[]>([]);
const selectedRackCode = ref("");

// Unique racks derived from the flat shelf-position list, in the order
// they first appear (already sorted by value/rack code from the API).
const racks = computed(() => {
  const seen = new Map<string, string>();
  for (const opt of shelfOptions.value) {
    if (!seen.has(opt.rack_code)) seen.set(opt.rack_code, opt.rack_label);
  }
  return Array.from(seen, ([code, label]) => ({ code, label }));
});

// Shelves (levels) belonging to whichever rack is currently selected.
const shelvesForSelectedRack = computed(() =>
  shelfOptions.value.filter((opt) => opt.rack_code === selectedRackCode.value),
);

// Reset the shelf pick whenever the rack changes, since a previously
// selected shelf_position won't belong to the newly chosen rack.
watch(selectedRackCode, () => {
  form.value.shelf_position = "";
});

// Shown after a successful save so the barcode can be printed onto the
// physical item right away, without leaving the form.
const lastCreated = ref<Item | null>(null);

// Items that look like duplicates of what's currently typed in the name/PN
// fields, so the user can top up an existing item instead of creating a
// near-duplicate row. Re-checked (debounced) as the user types.
const duplicates = ref<Item[]>([]);
const addingToExisting = ref<number | null>(null);
let duplicateCheckTimer: ReturnType<typeof setTimeout> | undefined;

watch(
  () => [form.value.name, form.value.pn],
  () => {
    clearTimeout(duplicateCheckTimer);
    const name = form.value.name.trim();
    const pn = form.value.pn.trim();
    if (!name && !pn) {
      duplicates.value = [];
      return;
    }
    duplicateCheckTimer = setTimeout(async () => {
      try {
        duplicates.value = await checkDuplicateItems({ name, pn });
      } catch {
        // Non-critical: a failed duplicate check shouldn't block the form.
      }
    }, 400);
  },
);

async function addToExisting(dup: Item) {
  const quantity = Number(form.value.quantity) || 1;
  addingToExisting.value = dup.id;
  try {
    const res = await depositItem({
      barcode: dup.barcode,
      quantity,
      source: "manual",
    });
    show("success", res.message);
    form.value = { ...EMPTY_FORM };
    selectedRackCode.value = "";
    duplicates.value = [];
    await suggestBarcode();
    emit("created", res.item);
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to add stock to existing item");
  } finally {
    addingToExisting.value = null;
  }
}

async function loadOptions() {
  loadingOptions.value = true;
  try {
    const [cats, progs, shelves] = await Promise.all([
      listAdminCategories(),
      listAdminPrograms(),
      getShelfPositions(),
    ]);
    categories.value = cats;
    programs.value = progs;
    shelfOptions.value = shelves;
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to load categories/shelves");
  } finally {
    loadingOptions.value = false;
  }
}

async function suggestBarcode() {
  generatingBarcode.value = true;
  try {
    const res = await generateBarcode();
    form.value.barcode = res.barcode;
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to generate a barcode");
  } finally {
    generatingBarcode.value = false;
  }
}

async function submit() {
  error.value = "";
  submitting.value = true;
  lastCreated.value = null;
  try {
    const item = await createItem({
      ...form.value,
      quantity: Number(form.value.quantity) || 0,
    });
    lastCreated.value = item;
    show("success", `Item "${item.name}" created`);
    form.value = { ...EMPTY_FORM };
    selectedRackCode.value = "";
    duplicates.value = [];
    await suggestBarcode();
    emit("created", item);
  } catch (err: any) {
    error.value = err?.data?.detail || "Failed to create item";
  } finally {
    submitting.value = false;
  }
}

function printLabel() {
  if (!lastCreated.value) return;
  const printWindow = window.open(labelUrl(lastCreated.value.id), "_blank");
  // Best-effort auto-print once the label image has finished loading;
  // if the browser blocks it, the user still has the tab open to print manually.
  printWindow?.addEventListener?.("load", () => printWindow.print());
}

onMounted(async () => {
  await Promise.all([loadOptions(), suggestBarcode()]);
});
</script>
