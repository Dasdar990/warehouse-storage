<template>
  <form
    class="grid grid-cols-4 gap-3.5 max-[900px]:grid-cols-2 max-[640px]:grid-cols-1"
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

    <div class="flex flex-col gap-1.5 col-span-3 max-[900px]:col-span-1">
      <label class="flex items-center justify-between text-[0.8rem] text-muted">
        <span v-if="!bulkMode"
          >Serial Number
          <span class="text-[0.72rem] text-muted">(optional)</span></span
        >
        <span v-else
          >Serial Numbers
          <span class="text-[0.72rem] text-muted">(one per line)</span></span
        >
        <button
          type="button"
          class="text-[0.95rem] text-accent underline-offset-2 hover:underline"
          @click="bulkMode = !bulkMode"
        >
          {{ bulkMode ? "Single item" : "Multiple serials…" }}
        </button>
      </label>
      <input
        v-if="!bulkMode"
        v-model="form.serial"
        type="text"
        placeholder="SN-00123"
        class="field-input disabled:cursor-not-allowed disabled:opacity-60 w-full"
      />
      <TagsInput
        v-else
        v-model="bulkSerials"
        placeholder="Type a serial, press Enter…"
        class="font-mono w-full"
      />
      <p v-if="bulkMode" class="m-0 text-[0.75rem] text-muted">
        {{ bulkSerials.length }} item{{ bulkSerials.length === 1 ? "" : "s" }}
        will be created, one per serial, all with these same details.
      </p>
    </div>

    <div
      v-if="bulkMode"
      class="col-span-full m-0 rounded-[10px] border border-white/10 bg-surface px-4 py-2.5 text-[0.8rem] text-muted"
    >
      A unique barcode is auto-generated for each item -- one per serial.
    </div>
    <div v-else class="flex flex-col gap-1.5 col-span-2 max-[900px]:col-span-1">
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
        <option :value="NEW_CATEGORY_VALUE">+ New category…</option>
      </select>
      <div v-if="creatingCategory" class="mt-1 flex gap-2">
        <input
          ref="newCategoryInput"
          v-model="newCategoryName"
          type="text"
          maxlength="60"
          placeholder="New category name"
          class="field-input flex-1"
          :disabled="savingCategory"
          @keyup.enter="confirmNewCategory"
          @keyup.esc="cancelNewCategory"
        />
        <button
          type="button"
          class="btn btn--confirm btn--small whitespace-nowrap text-[#06280f] disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="savingCategory || !newCategoryName.trim()"
          @click="confirmNewCategory"
        >
          {{ savingCategory ? "…" : "Add" }}
        </button>
        <button
          type="button"
          class="btn btn--ghost btn--small whitespace-nowrap"
          :disabled="savingCategory"
          @click="cancelNewCategory"
        >
          Cancel
        </button>
      </div>
      <p
        v-if="!loadingOptions && !categories.length && !creatingCategory"
        class="m-0 text-[0.75rem] text-muted"
      >
        No categories yet — pick "+ New category…" above, or
        <NuxtLink to="/categories" class="text-accent"
          >manage them here</NuxtLink
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
        <option :value="NEW_PROGRAM_VALUE">+ New program…</option>
      </select>
      <div v-if="creatingProgram" class="mt-1 flex gap-2">
        <input
          ref="newProgramInput"
          v-model="newProgramName"
          type="text"
          maxlength="60"
          placeholder="New program name"
          class="field-input flex-1"
          :disabled="savingProgram"
          @keyup.enter="confirmNewProgram"
          @keyup.esc="cancelNewProgram"
        />
        <button
          type="button"
          class="btn btn--confirm btn--small whitespace-nowrap text-[#06280f] disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="savingProgram || !newProgramName.trim()"
          @click="confirmNewProgram"
        >
          {{ savingProgram ? "…" : "Add" }}
        </button>
        <button
          type="button"
          class="btn btn--ghost btn--small whitespace-nowrap"
          :disabled="savingProgram"
          @click="cancelNewProgram"
        >
          Cancel
        </button>
      </div>
      <p
        v-if="!loadingOptions && !programs.length && !creatingProgram"
        class="m-0 text-[0.75rem] text-muted"
      >
        No programs yet — pick "+ New program…" above, or
        <NuxtLink to="/categories" class="text-accent"
          >manage them here</NuxtLink
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
      <label class="text-[0.8rem] text-muted">Initial Quantity</label>
      <input
        v-model.number="form.quantity"
        type="number"
        min="0"
        :disabled="hasSerial"
        class="field-input no-spinner disabled:cursor-not-allowed disabled:opacity-60"
      />
      <p v-if="hasSerial" class="m-0 text-[0.75rem] text-muted">
        Locked to 1 -- a serial number identifies a single physical unit.
      </p>
    </div>

    <div class="flex flex-col gap-1.5 col-span-full">
      <label class="flex items-center justify-between text-[0.8rem] text-muted">
        <span
          >Shelf
          <span class="text-[0.72rem] text-muted"
            >(required unless quantity is 0)</span
          ></span
        >
        <button
          v-if="!boxMode && !bulkMode"
          type="button"
          class="text-[0.95rem] text-accent underline-offset-2 hover:underline"
          @click="openBoxMode"
        >
          📦 Put it in a box instead…
        </button>
        <button
          v-else-if="boxMode"
          type="button"
          class="text-[0.95rem] text-accent underline-offset-2 hover:underline"
          @click="closeBoxMode"
        >
          Pick a shelf instead
        </button>
      </label>

      <ShelfPicker
        v-if="!boxMode"
        v-model="form.shelf_position"
        v-model:zone-id="form.zone_id"
        :options="shelfOptions"
        :zones="zones"
        :loading="loadingOptions"
      />
      <p
        v-if="!boxMode && !loadingOptions && !shelfOptions.length && !zones.length"
        class="m-0 text-[0.75rem] text-muted"
      >
        No shelves configured yet —
        <NuxtLink to="/map-config" class="text-accent"
          >set up the warehouse map first</NuxtLink
        >.
      </p>

      <!-- Box mode: for generic items with no room for their own label
           (e.g. loose cables) -- pick an existing box on any shelf, or
           create a new one on the spot. Not offered in bulk-serial mode:
           serialized units are individually identifiable and don't need
           this. -->
      <div
        v-if="boxMode"
        class="flex flex-col gap-2 rounded-[10px] border border-edge bg-surface px-4 py-3"
      >
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
          <div class="flex gap-2">
            <input
              v-model="newBoxShelfPosition"
              type="text"
              placeholder="Shelf, e.g. 12B"
              maxlength="12"
              class="field-input w-32 font-mono uppercase"
            />
            <input
              v-model="newBoxName"
              type="text"
              placeholder="Box name (optional)"
              maxlength="80"
              class="field-input flex-1"
            />
          </div>
        </template>
      </div>
    </div>

    <div class="flex flex-col gap-1.5 col-span-full">
      <label class="text-[0.8rem] text-muted"
        >Tags
        <span class="text-[0.72rem] text-muted"
          >(optional -- helps find this item later)</span
        ></label
      >
      <TagsInput v-model="form.tags" placeholder="e.g. spare, critical…" />
    </div>

    <div class="flex flex-col gap-1.5 col-span-full">
      <label class="text-[0.8rem] text-muted"
        >Notes <span class="text-[0.72rem] text-muted">(optional)</span></label
      >
      <textarea
        v-model="form.notes"
        rows="2"
        placeholder="Anything that helps identify or find this item later…"
        class="field-input resize-y disabled:cursor-not-allowed disabled:opacity-60"
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
          <span class="text-muted">
            · {{ dup.quantity }} in stock<template v-if="dup.shelf_position">
              · Shelf {{ dup.shelf_position }}</template
            ><template v-else-if="dup.zone_id"> · in a zone</template></span
          >
        </span>
        <button
          type="button"
          class="btn btn--confirm btn--small whitespace-nowrap disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="addingToExisting === dup.id"
          @click="addToExisting(dup)"
        >
          {{
            addingToExisting === dup.id
              ? "Adding…"
              : `Add ${form.quantity || 1} here instead`
          }}
        </button>
      </div>
      <p class="m-0 text-[0.75rem] text-muted">
        Not the same item? You can ignore this and save below to create a new
        one anyway.
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
        v-if="lastCreated || lastCreatedBatch.length"
        class="col-span-full flex flex-col gap-3"
      >
        <div
          v-if="lastCreated"
          class="flex flex-wrap items-center justify-between gap-3 rounded-[10px] border border-good bg-good-dim px-4 py-3 text-green-200"
        >
          <div>
            <strong>{{ lastCreated.name }}</strong> saved with barcode
            <span class="font-mono">{{ lastCreated.barcode }}</span>
            -- label sent to print.
          </div>
          <button
            class="btn btn--ghost btn--small"
            type="button"
            @click="printLabel(lastCreated)"
          >
            🖨 Print Again
          </button>
        </div>
        <div
          v-if="lastCreatedBatch.length"
          class="flex flex-col gap-2 rounded-[10px] border border-good bg-good-dim px-4 py-3 text-green-200"
        >
          <div class="flex flex-wrap items-center justify-between gap-3">
            <span
              ><strong>{{ lastCreatedBatch.length }} items</strong> saved --
              labels sent to print.</span
            >
            <button
              class="btn btn--ghost btn--small"
              type="button"
              @click="printLabelBatch(lastCreatedBatch)"
            >
              🖨 Print All Again
            </button>
          </div>
          <div
            v-for="it in lastCreatedBatch"
            :key="it.id"
            class="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-surface px-3 py-1.5 text-[0.82rem] text-ink"
          >
            <span
              >{{ it.serial }} ·
              <span class="font-mono">{{ it.barcode }}</span></span
            >
            <button
              class="btn btn--ghost btn--small"
              type="button"
              @click="printLabel(it)"
            >
              🖨 Print Again
            </button>
          </div>
        </div>
      </div>
    </transition>
  </form>
</template>

<script setup lang="ts">
import type {
  Box,
  Category,
  Item,
  Program,
  ShelfPositionOption,
  Zone,
} from "~/composables/useWarehouseApi";

const emit = defineEmits<{ created: [item: Item] }>();

const {
  createItem,
  createItemsBulk,
  checkDuplicateItems,
  depositItem,
  generateBarcode,
  listAdminCategories,
  listAdminPrograms,
  createCategory,
  createProgram,
  getShelfPositions,
  getZones,
  labelUrl,
  labelBatchUrl,
  listBoxes,
  createBox,
  addItemToBox,
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
  zone_id: null as number | null,
  quantity: 0,
  tags: [] as string[],
  notes: "",
};

const form = ref({ ...EMPTY_FORM });
const error = ref("");
const submitting = ref(false);
const generatingBarcode = ref(false);
const loadingOptions = ref(false);

// Multiple-serials mode: same details, one item per serial -- entered as
// chips via TagsInput, same interaction as the Tags field below.
const bulkMode = ref(false);
const bulkSerials = ref<string[]>([]);
const lastCreatedBatch = ref<Item[]>([]);

const categories = ref<Category[]>([]);
const programs = ref<Program[]>([]);
const shelfOptions = ref<ShelfPositionOption[]>([]);
const zones = ref<Zone[]>([]);

// -- Box mode: put the new item straight into a box instead of picking a
// shelf/zone -- for generic items with no room for their own label (e.g.
// loose cables). Not offered in bulk-serial mode.
const boxMode = ref(false);
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

async function openBoxMode() {
  boxMode.value = true;
  form.value.shelf_position = "";
  form.value.zone_id = null;
  if (!allBoxes.value.length) {
    loadingBoxes.value = true;
    try {
      allBoxes.value = await listBoxes();
    } catch {
      allBoxes.value = [];
    } finally {
      loadingBoxes.value = false;
    }
  }
}

function closeBoxMode() {
  boxMode.value = false;
  selectedBoxId.value = null;
  newBoxShelfPosition.value = "";
  newBoxName.value = "";
  boxSearch.value = "";
}

function resetBoxMode() {
  boxMode.value = false;
  boxChoice.value = "existing";
  selectedBoxId.value = null;
  newBoxShelfPosition.value = "";
  newBoxName.value = "";
  boxSearch.value = "";
}

/** Resolves box mode to a concrete box (creating it first if needed) and
 * points `form` at its shelf_position, so the normal item-create payload
 * already satisfies the "needs a shelf/zone" rule. Returns the box so the
 * caller can assign the freshly created item to it afterwards. */
async function resolveTargetBox(): Promise<Box> {
  if (boxChoice.value === "existing") {
    const box = allBoxes.value.find((b) => b.id === selectedBoxId.value);
    if (!box) throw new Error("Pick a box from the list, or create a new one.");
    return box;
  }
  const shelfPosition = newBoxShelfPosition.value.trim();
  if (!shelfPosition) throw new Error("Enter a shelf position for the new box.");
  return createBox({
    name: newBoxName.value.trim() || null,
    shelf_position: shelfPosition,
  });
}


// "+ New category…" / "+ New program…" -- create a catalog entry without
// leaving the form, instead of having to go to /categories first.
const NEW_CATEGORY_VALUE = "__new_category__";
const NEW_PROGRAM_VALUE = "__new_program__";
const creatingCategory = ref(false);
const newCategoryName = ref("");
const savingCategory = ref(false);
const newCategoryInput = ref<HTMLInputElement | null>(null);
const creatingProgram = ref(false);
const newProgramName = ref("");
const savingProgram = ref(false);
const newProgramInput = ref<HTMLInputElement | null>(null);

watch(
  () => form.value.category,
  (value) => {
    if (value !== NEW_CATEGORY_VALUE) return;
    creatingCategory.value = true;
    newCategoryName.value = "";
    // Fall back to the empty placeholder while the name is being typed, so
    // the sentinel value never ends up submitted as the item's category.
    form.value.category = "";
    nextTick(() => newCategoryInput.value?.focus());
  },
);

async function confirmNewCategory() {
  const name = newCategoryName.value.trim();
  if (!name) return;
  savingCategory.value = true;
  try {
    const category = await createCategory(name);
    categories.value = [...categories.value, category].sort((a, b) =>
      a.name.localeCompare(b.name),
    );
    form.value.category = category.name;
    show("success", `Category "${category.name}" created`);
    cancelNewCategory();
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to create category");
  } finally {
    savingCategory.value = false;
  }
}

function cancelNewCategory() {
  creatingCategory.value = false;
  newCategoryName.value = "";
}

watch(
  () => form.value.program,
  (value) => {
    if (value !== NEW_PROGRAM_VALUE) return;
    creatingProgram.value = true;
    newProgramName.value = "";
    form.value.program = "";
    nextTick(() => newProgramInput.value?.focus());
  },
);

async function confirmNewProgram() {
  const name = newProgramName.value.trim();
  if (!name) return;
  savingProgram.value = true;
  try {
    const program = await createProgram(name);
    programs.value = [...programs.value, program].sort((a, b) =>
      a.name.localeCompare(b.name),
    );
    form.value.program = program.name;
    show("success", `Program "${program.name}" created`);
    cancelNewProgram();
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to create program");
  } finally {
    savingProgram.value = false;
  }
}

function cancelNewProgram() {
  creatingProgram.value = false;
  newProgramName.value = "";
}

// Shown after a successful save so the barcode can be printed onto the
// physical item right away, without leaving the form.
const lastCreated = ref<Item | null>(null);

// Items that look like duplicates of what's currently typed in the name/PN
// fields, so the user can top up an existing item instead of creating a
// near-duplicate row. Re-checked (debounced) as the user types.
const duplicates = ref<Item[]>([]);
const addingToExisting = ref<number | null>(null);
let duplicateCheckTimer: ReturnType<typeof setTimeout> | undefined;

// A serial number identifies one specific physical unit, so quantity
// doesn't make sense as anything but 1 -- both for a single serialized
// item and for bulk mode, where every row created carries its own serial.
const hasSerial = computed(
  () => bulkMode.value || form.value.serial.trim().length > 0,
);

watch(hasSerial, (locked) => {
  if (locked) form.value.quantity = 1;
});

watch(bulkMode, (locked) => {
  // Box mode is for a single generic item at a time -- bulk-serial
  // creation and box placement don't mix, so switching one off the other.
  if (locked) closeBoxMode();
});

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
    const [cats, progs, shelves, zoneList] = await Promise.all([
      listAdminCategories(),
      listAdminPrograms(),
      getShelfPositions(),
      getZones(),
    ]);
    categories.value = cats;
    programs.value = progs;
    shelfOptions.value = shelves;
    zones.value = zoneList;
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
  let targetBox: Box | null = null;
  if (boxMode.value) {
    try {
      targetBox = await resolveTargetBox();
    } catch (err: any) {
      error.value = err?.message || "Pick or create a box first.";
      return;
    }
    // A boxed item's location is the box's own shelf -- fill it in so the
    // usual "needs a shelf/zone" rule below is naturally satisfied too.
    form.value.shelf_position = targetBox.shelf_position;
    form.value.zone_id = null;
  }

  const quantity = Number(form.value.quantity) || 0;
  if (quantity > 0 && !form.value.shelf_position && !form.value.zone_id) {
    error.value =
      "Pick a shelf or a zone before saving, or set the quantity to 0 to create it without one for now.";
    return;
  }
  submitting.value = true;
  lastCreated.value = null;
  lastCreatedBatch.value = [];
  try {
    if (bulkMode.value) {
      if (!bulkSerials.value.length) {
        error.value = "Enter at least one serial number.";
        return;
      }
      const items = await createItemsBulk({
        name: form.value.name,
        pn: form.value.pn,
        category: form.value.category,
        program: form.value.program,
        size: form.value.size,
        shelf_position: form.value.shelf_position,
        zone_id: form.value.zone_id,
        quantity,
        tags: form.value.tags,
        notes: form.value.notes,
        serials: bulkSerials.value,
      });
      lastCreatedBatch.value = items;
      show("success", `${items.length} items created`);
      // One tab, one print dialog for the whole batch instead of a popup
      // per item.
      printLabelBatch(items);
      form.value = { ...EMPTY_FORM };
      bulkSerials.value = [];
      duplicates.value = [];
      await suggestBarcode();
      items.forEach((item) => emit("created", item));
    } else {
      let item = await createItem({ ...form.value, quantity });
      if (targetBox) {
        item = await addItemToBox(targetBox.id, item.id);
        show(
          "success",
          `Item "${item.name}" created and put in box ${targetBox.code}`,
        );
      } else {
        show("success", `Item "${item.name}" created`);
      }
      lastCreated.value = item;
      printLabel(item);
      form.value = { ...EMPTY_FORM };
      duplicates.value = [];
      resetBoxMode();
      await suggestBarcode();
      emit("created", item);
    }
  } catch (err: any) {
    error.value = err?.data?.detail || "Failed to create item";
  } finally {
    submitting.value = false;
  }
}

function printLabel(item: Item | null) {
  if (!item) return;
  // labelUrl() points at a small self-contained page that regenerates the
  // label, auto-prints, and closes itself -- no extra JS needed here.
  window.open(labelUrl(item.id), "_blank");
}

function printLabelBatch(items: Item[]) {
  if (!items.length) return;
  // labelBatchUrl() opens one tab with all labels, one page each, printed
  // in a single dialog -- avoids a popup-per-item (and popup blockers).
  window.open(labelBatchUrl(items.map((it) => it.id)), "_blank");
}

onMounted(async () => {
  await Promise.all([loadOptions(), suggestBarcode()]);
});
</script>