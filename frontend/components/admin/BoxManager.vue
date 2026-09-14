<template>
  <div class="flex flex-col gap-4">
    <form class="flex flex-wrap items-end gap-2.5" @submit.prevent="add">
      <div class="flex flex-col gap-1.5">
        <label class="text-[0.8rem] text-muted">Shelf position</label>
        <ShelfPicker
          v-model="newShelfPosition"
          :options="shelfOptions"
          :loading="loadingShelfOptions"
          placeholder="Type a shelf, e.g. 12B…"
        />
      </div>
      <div class="flex flex-col gap-1.5">
        <label class="text-[0.8rem] text-muted"
          >Name <span class="text-[0.72rem]">(optional)</span></label
        >
        <input
          v-model="newName"
          type="text"
          placeholder="e.g. Cavi HDMI"
          maxlength="80"
          class="field-input w-56"
        />
      </div>
      <button
        class="btn btn--confirm whitespace-nowrap text-[#06280f] disabled:cursor-not-allowed disabled:opacity-60"
        type="submit"
        :disabled="submitting"
      >
        {{ submitting ? "Creating…" : "+ New box" }}
      </button>
    </form>
    <p v-if="createError" class="m-0 text-red-300">{{ createError }}</p>

    <div class="relative">
      <input
        v-model="query"
        type="text"
        placeholder="Find a box — code, name, or shelf…"
        class="field-input w-full max-w-96"
      />
    </div>

    <p v-if="loading" class="text-muted">Loading boxes…</p>
    <p v-else-if="!filteredBoxes.length && !boxes.length" class="text-muted">
      No boxes yet. Create the first one above.
    </p>
    <p v-else-if="!filteredBoxes.length" class="text-muted">
      No box matches "{{ query }}".
    </p>
    <ul v-else class="m-0 flex list-none flex-col gap-2 p-0">
      <li
        v-for="box in filteredBoxes"
        :key="box.id"
        class="rounded-lg border border-edge bg-surface-2 px-3.5 py-2.5"
      >
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="flex min-w-0 flex-1 flex-wrap items-center gap-2.5">
            <span
              class="rounded-full bg-accent/12 px-2.5 py-0.5 font-mono text-[0.78rem] font-bold text-accent"
              >{{ box.code }}</span
            >

            <template v-if="editingId === box.id">
              <input
                v-model="editName"
                type="text"
                maxlength="80"
                placeholder="Box name"
                class="field-input h-8 w-48 text-[0.85rem]"
                :disabled="savingEdit"
                @keyup.enter="saveEdit(box)"
                @keyup.esc="cancelEdit"
              />
              <div class="w-36">
                <ShelfPicker
                  v-model="editShelfPosition"
                  :options="shelfOptions"
                  :loading="loadingShelfOptions"
                  :disabled="savingEdit"
                  placeholder="Shelf…"
                />
              </div>
              <button
                class="rounded-lg bg-transparent px-2 py-1 text-muted hover:text-accent disabled:cursor-not-allowed disabled:opacity-60"
                title="Save"
                :disabled="savingEdit"
                @click="saveEdit(box)"
              >
                ✓
              </button>
              <button
                class="rounded-lg bg-transparent px-2 py-1 text-muted hover:text-red-300"
                title="Cancel"
                :disabled="savingEdit"
                @click="cancelEdit"
              >
                ✕
              </button>
            </template>
            <template v-else>
              <span class="truncate font-semibold text-ink">{{
                box.name || "(unnamed box)"
              }}</span>
              <span
                class="shrink-0 rounded-full border border-edge px-2 py-0.5 text-[0.75rem] text-muted"
                >Shelf {{ box.shelf_position }}</span
              >
              <span class="shrink-0 text-[0.78rem] text-muted"
                >{{ box.item_count }} item(s) ·
                {{ box.total_quantity }} pcs</span
              >
            </template>
          </div>

          <div
            v-if="editingId !== box.id"
            class="flex shrink-0 items-center gap-1"
          >
            <button
              class="rounded-lg bg-transparent px-2.5 py-1 text-muted hover:text-accent"
              title="Rename or move this box"
              @click="startEdit(box)"
            >
              <img
                src="~/assets/icons/edit.svg"
                class="w-5 h-auto inline-block mr-1"
              />
            </button>
            <a
              :href="boxLabelUrl(box.id)"
              target="_blank"
              rel="noopener"
              class="rounded-lg bg-transparent px-2.5 py-1 text-muted hover:text-accent"
              title="Print box label"
            >
              🖨
            </a>
            <button
              class="rounded-lg bg-transparent px-2.5 py-1 text-muted hover:text-accent"
              title="Show items inside"
              @click="toggleExpand(box)"
            >
              {{ expandedId === box.id ? "▲" : "▼" }}
            </button>
            <button
              class="rounded-lg bg-transparent px-2.5 py-1 text-muted hover:text-red-300 disabled:cursor-not-allowed disabled:opacity-40"
              title="Delete empty box"
              :disabled="box.item_count > 0"
              @click="remove(box)"
            >
              ✕
            </button>
          </div>
        </div>

        <div
          v-if="expandedId === box.id"
          class="mt-2 border-t border-edge pt-2"
        >
          <p v-if="loadingItems" class="m-0 text-[0.8rem] text-muted">
            Loading…
          </p>
          <p v-else-if="!boxItems.length" class="m-0 text-[0.8rem] text-muted">
            Empty box.
          </p>
          <div
            v-for="it in boxItems"
            :key="it.id"
            class="flex items-center justify-between gap-2 py-1 text-[0.82rem]"
          >
            <span class="min-w-0 flex-1 truncate"
              >{{ it.name }}<template v-if="it.pn"> · {{ it.pn }}</template> ({{
                it.quantity
              }})</span
            >
            <button
              type="button"
              class="shrink-0 text-[0.78rem] text-muted underline"
              @click="takeOut(it, box)"
            >
              Take out
            </button>
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import type {
  Box,
  Item,
  ShelfPositionOption,
} from "~/composables/useWarehouseApi";

const {
  listBoxes,
  createBox,
  updateBox,
  deleteBox,
  listBoxItems,
  removeItemFromBox,
  boxLabelUrl,
  getShelfPositions,
} = useWarehouseApi();
const { show } = useToast();

const boxes = ref<Box[]>([]);
const loading = ref(false);
const query = ref("");

const shelfOptions = ref<ShelfPositionOption[]>([]);
const loadingShelfOptions = ref(false);

const newShelfPosition = ref("");
const newName = ref("");
const submitting = ref(false);
const createError = ref("");

const editingId = ref<number | null>(null);
const editName = ref("");
const editShelfPosition = ref("");
const savingEdit = ref(false);

const expandedId = ref<number | null>(null);
const boxItems = ref<Item[]>([]);
const loadingItems = ref(false);

const filteredBoxes = computed(() => {
  const q = query.value.trim().toLowerCase();
  if (!q) return boxes.value;
  return boxes.value.filter((b) =>
    [b.code, b.name, b.shelf_position]
      .filter(Boolean)
      .some((f) => f!.toLowerCase().includes(q)),
  );
});

async function load() {
  loading.value = true;
  try {
    boxes.value = await listBoxes();
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to load boxes");
  } finally {
    loading.value = false;
  }
}

async function loadShelfOptions() {
  loadingShelfOptions.value = true;
  try {
    shelfOptions.value = await getShelfPositions();
  } catch {
    // Non-critical: the picker just won't have options to show.
  } finally {
    loadingShelfOptions.value = false;
  }
}

async function add() {
  const shelfPosition = newShelfPosition.value.trim();
  if (!shelfPosition) return;
  createError.value = "";
  submitting.value = true;
  try {
    const box = await createBox({
      name: newName.value.trim() || null,
      shelf_position: shelfPosition,
    });
    boxes.value = [box, ...boxes.value];
    newShelfPosition.value = "";
    newName.value = "";
    show("success", `Box "${box.code}" created on shelf ${box.shelf_position}`);
  } catch (err: any) {
    createError.value = err?.data?.detail || "Failed to create the box";
  } finally {
    submitting.value = false;
  }
}

function startEdit(box: Box) {
  editingId.value = box.id;
  editName.value = box.name || "";
  editShelfPosition.value = box.shelf_position;
}

function cancelEdit() {
  editingId.value = null;
}

async function saveEdit(box: Box) {
  const name = editName.value.trim();
  const shelfPosition = editShelfPosition.value.trim();
  if (!shelfPosition) return;
  if (name === (box.name || "") && shelfPosition === box.shelf_position) {
    cancelEdit();
    return;
  }
  savingEdit.value = true;
  try {
    const updated = await updateBox(box.id, {
      name: name || null,
      shelf_position: shelfPosition,
    });
    boxes.value = boxes.value.map((b) => (b.id === box.id ? updated : b));
    show(
      "success",
      shelfPosition !== box.shelf_position
        ? `Box "${updated.code}" moved to shelf ${updated.shelf_position} -- its items moved with it`
        : `Box "${updated.code}" renamed`,
    );
    cancelEdit();
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to update the box");
  } finally {
    savingEdit.value = false;
  }
}

async function remove(box: Box) {
  if (!confirm(`Delete box "${box.code}"? This can't be undone.`)) return;
  try {
    await deleteBox(box.id);
    boxes.value = boxes.value.filter((b) => b.id !== box.id);
    if (expandedId.value === box.id) expandedId.value = null;
    show("success", `Box "${box.code}" deleted`);
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to delete the box");
  }
}

async function toggleExpand(box: Box) {
  if (expandedId.value === box.id) {
    expandedId.value = null;
    return;
  }
  expandedId.value = box.id;
  loadingItems.value = true;
  try {
    boxItems.value = await listBoxItems(box.id);
  } catch {
    boxItems.value = [];
  } finally {
    loadingItems.value = false;
  }
}

async function takeOut(item: Item, box: Box) {
  try {
    await removeItemFromBox(item.id);
    show("success", `"${item.name}" taken out of ${box.code}`);
    boxItems.value = await listBoxItems(box.id);
    await load();
  } catch (err: any) {
    show(
      "error",
      err?.data?.detail || "Failed to take this item out of the box",
    );
  }
}

onMounted(() => {
  load();
  loadShelfOptions();
});
</script>
