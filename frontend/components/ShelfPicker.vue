<template>
  <div class="flex flex-col gap-1.5">
    <div v-if="recentShelves.length" class="flex flex-wrap items-center gap-1.5">
      <span class="text-[0.72rem] text-muted">Recent:</span>
      <button
        v-for="code in recentShelves"
        :key="code"
        type="button"
        class="rounded-full border px-2.5 py-1 text-[0.75rem] font-semibold"
        :class="
          modelValue === code
            ? 'border-accent/60 bg-accent/15 text-ink'
            : 'border-edge/70 text-muted hover:border-accent/40 hover:text-ink'
        "
        @click="pick(code)"
      >
        {{ code }}
      </button>
    </div>

    <div class="relative">
      <input
        v-model="query"
        type="text"
        :disabled="disabled"
        :placeholder="loading ? 'Loading shelves…' : placeholder"
        class="field-input disabled:cursor-not-allowed disabled:opacity-60"
        autocomplete="off"
        @focus="open = true"
        @input="handleInput"
        @keydown.down.prevent="moveHighlight(1)"
        @keydown.up.prevent="moveHighlight(-1)"
        @keydown.enter.prevent="selectHighlighted"
        @keydown.esc="open = false"
        @blur="handleBlur"
      />

      <ul
        v-if="open && filteredOptions.length"
        class="absolute z-20 mt-1 max-h-52 w-full overflow-y-auto rounded-lg bg-surface-2 py-1 shadow-card"
      >
        <li
          v-for="(opt, i) in filteredOptions"
          :key="opt.value"
          class="cursor-pointer px-3 py-1.5 text-[0.85rem]"
          :class="i === highlighted ? 'bg-accent/20 text-ink' : 'text-ink hover:bg-surface'"
          @mousedown.prevent="pick(opt.value)"
          @mouseenter="highlighted = i"
        >
          <span class="font-semibold">{{ opt.value }}</span>
          <span class="text-muted"> — {{ opt.rack_label }}, Level {{ opt.level }}</span>
        </li>
      </ul>
      <p
        v-else-if="open && query && !loading"
        class="absolute z-20 mt-1 w-full rounded-lg bg-surface-2 px-3 py-2 text-[0.82rem] text-muted shadow-card"
      >
        No shelf matches "{{ query }}".
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ShelfPositionOption } from "~/composables/useWarehouseApi";

const props = withDefaults(
  defineProps<{
    modelValue: string;
    options: ShelfPositionOption[];
    loading?: boolean;
    disabled?: boolean;
    placeholder?: string;
  }>(),
  {
    loading: false,
    disabled: false,
    placeholder: "Type a shelf or rack, e.g. 12B…",
  },
);

const emit = defineEmits<{ "update:modelValue": [string] }>();

const query = ref(props.modelValue || "");
const open = ref(false);
const highlighted = ref(0);

// Keep the visible text in sync whenever the parent resets/changes the value
// from outside (e.g. a "Use this shelf instead" toggle, or clearing the form).
watch(
  () => props.modelValue,
  (v) => {
    if (v !== query.value) query.value = v || "";
  },
);

const filteredOptions = computed(() => {
  const q = query.value.trim().toLowerCase();
  const list = !q
    ? props.options
    : props.options.filter(
        (o) => o.value.toLowerCase().includes(q) || o.rack_label.toLowerCase().includes(q),
      );
  return list.slice(0, 8);
});

watch(filteredOptions, () => {
  highlighted.value = 0;
});

function handleInput() {
  open.value = true;
  // Typing something that no longer matches the committed value clears the
  // selection, so a stale shelf can't silently stay "selected" underneath.
  if (query.value !== props.modelValue) emit("update:modelValue", "");
}

function moveHighlight(delta: number) {
  if (!filteredOptions.value.length) return;
  open.value = true;
  const len = filteredOptions.value.length;
  highlighted.value = (highlighted.value + delta + len) % len;
}

function selectHighlighted() {
  const opt = filteredOptions.value[highlighted.value];
  if (opt) pick(opt.value);
}

function pick(value: string) {
  query.value = value;
  open.value = false;
  emit("update:modelValue", value);
  rememberRecent(value);
}

function handleBlur() {
  // Delay so a click on a dropdown option (mousedown) still registers
  // before the list disappears.
  setTimeout(() => {
    open.value = false;
  }, 120);
}

// -- Recently used shelves, remembered locally so this operator's usual
// spots are one click away next time, in any of the forms that use this
// picker (new item, deposit elsewhere, move). --
const RECENT_KEY = "warehouse:recent-shelves";
const MAX_RECENT = 6;
const recentShelves = ref<string[]>([]);

function loadRecent() {
  if (typeof window === "undefined") return;
  try {
    const raw = window.localStorage.getItem(RECENT_KEY);
    const parsed: string[] = raw ? JSON.parse(raw) : [];
    const known = new Set(props.options.map((o) => o.value));
    recentShelves.value = parsed.filter((v) => known.has(v)).slice(0, MAX_RECENT);
  } catch {
    recentShelves.value = [];
  }
}

function rememberRecent(value: string) {
  if (typeof window === "undefined") return;
  try {
    const raw = window.localStorage.getItem(RECENT_KEY);
    const parsed: string[] = raw ? JSON.parse(raw) : [];
    const next = [value, ...parsed.filter((v) => v !== value)].slice(0, MAX_RECENT);
    window.localStorage.setItem(RECENT_KEY, JSON.stringify(next));
  } catch {
    // Non-critical: worst case, no quick chips next time.
  }
  loadRecent();
}

watch(() => props.options, loadRecent, { immediate: true });
</script>
