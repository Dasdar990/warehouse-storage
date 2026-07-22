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
      <label class="text-[0.8rem] text-muted">Barcode</label>
      <div class="flex gap-2">
        <input
          v-model="form.barcode"
          required
          type="text"
          placeholder="Auto-generated"
          class="field-input min-w-0 flex-1 font-mono disabled:cursor-not-allowed disabled:opacity-60"
        />
        <button
          class="btn btn--ghost btn--small whitespace-nowrap disabled:cursor-not-allowed disabled:opacity-60"
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
      <label class="text-[0.8rem] text-muted">Shelf Position</label>
      <select
        v-model="form.shelf_position"
        required
        :disabled="loadingOptions"
        class="field-input disabled:cursor-not-allowed disabled:opacity-60"
      >
        <option value="" disabled>Select a shelf…</option>
        <option v-for="opt in shelfOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
      <p
        v-if="!loadingOptions && !shelfOptions.length"
        class="m-0 text-[0.75rem] text-muted"
      >
        No shelves configured yet —
        <NuxtLink to="/map-config" class="text-accent"
          >set up the warehouse map first</NuxtLink
        >.
      </p>
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

    <p v-if="error" class="col-span-full m-0 text-red-300">{{ error }}</p>
    <button
      class="btn btn--confirm col-span-full justify-self-start disabled:cursor-not-allowed disabled:opacity-60"
      type="submit"
      :disabled="submitting"
    >
      {{ submitting ? "Saving…" : "Save Item" }}
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
  ShelfPositionOption,
} from "~/composables/useWarehouseApi";

const emit = defineEmits<{ created: [item: Item] }>();

const {
  createItem,
  generateBarcode,
  listAdminCategories,
  getShelfPositions,
  labelUrl,
} = useWarehouseApi();
const { show } = useToast();

const EMPTY_FORM = {
  name: "",
  pn: "",
  barcode: "",
  category: "",
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
const shelfOptions = ref<ShelfPositionOption[]>([]);

// Shown after a successful save so the barcode can be printed onto the
// physical item right away, without leaving the form.
const lastCreated = ref<Item | null>(null);

async function loadOptions() {
  loadingOptions.value = true;
  try {
    const [cats, shelves] = await Promise.all([
      listAdminCategories(),
      getShelfPositions(),
    ]);
    categories.value = cats;
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
