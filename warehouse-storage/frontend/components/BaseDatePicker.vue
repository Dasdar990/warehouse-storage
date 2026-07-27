<template>
  <div ref="rootRef" class="relative">
    <button
      type="button"
      class="field-input flex h-8.5 w-full items-center justify-between gap-2 text-left text-[0.82rem]"
      :class="{ 'text-muted': !modelValue }"
      @click="toggleOpen"
    >
      <span class="truncate">{{ displayValue || placeholder }}</span>
      <svg
        viewBox="0 0 24 24"
        class="h-4 w-4 shrink-0 text-muted"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <rect x="3" y="5" width="18" height="16" rx="2" />
        <path d="M3 9h18M8 3v4M16 3v4" />
      </svg>
    </button>

    <div
      v-if="open"
      class="absolute left-0 top-[calc(100%+6px)] z-20 w-64 rounded-lg border border-edge bg-surface p-3 shadow-card"
    >
      <div class="mb-2 flex items-center justify-between gap-2">
        <button
          type="button"
          class="btn--icon h-7 w-7 text-sm"
          aria-label="Previous month"
          @click="shiftMonth(-1)"
        >
          ‹
        </button>
        <span class="text-[0.85rem] font-semibold text-ink">{{ monthLabel }}</span>
        <button
          type="button"
          class="btn--icon h-7 w-7 text-sm"
          aria-label="Next month"
          @click="shiftMonth(1)"
        >
          ›
        </button>
      </div>

      <div class="grid grid-cols-7 gap-0.5 text-center text-[0.68rem] font-semibold uppercase text-muted">
        <span v-for="d in weekdayLabels" :key="d">{{ d }}</span>
      </div>
      <div class="mt-1 grid grid-cols-7 gap-0.5">
        <button
          v-for="cell in calendarCells"
          :key="cell.key"
          type="button"
          class="flex h-7.5 w-7.5 items-center justify-center rounded-md text-[0.78rem] transition-colors"
          :class="cellClass(cell)"
          :disabled="cell.disabled"
          @click="pickDay(cell)"
        >
          {{ cell.day }}
        </button>
      </div>

      <div class="mt-2.5 flex items-center justify-between border-t border-edge/60 pt-2">
        <button
          type="button"
          class="text-[0.75rem] text-muted underline-offset-2 hover:underline"
          @click="pickToday"
        >
          Today
        </button>
        <button
          v-if="modelValue"
          type="button"
          class="text-[0.75rem] text-muted underline-offset-2 hover:underline"
          @click="clear"
        >
          Clear
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Lightweight dd/mm/yyyy date picker. The underlying model stays a plain
 * ISO "yyyy-mm-dd" string (same shape a native <input type="date"> would
 * give us) so callers -- and the API filters -- don't have to change; only
 * the on-screen display and the calendar picker UI are dd/mm/yyyy.
 */
const props = withDefaults(
  defineProps<{
    modelValue: string;
    min?: string;
    max?: string;
    placeholder?: string;
  }>(),
  { placeholder: "dd/mm/yyyy" },
);

const emit = defineEmits<{ "update:modelValue": [string] }>();

const rootRef = ref<HTMLElement | null>(null);
const open = ref(false);

function parseIso(value: string): Date | null {
  if (!value) return null;
  const [y, m, d] = value.split("-").map(Number);
  if (!y || !m || !d) return null;
  return new Date(y, m - 1, d);
}

function toIso(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

const displayValue = computed(() => {
  const date = parseIso(props.modelValue);
  if (!date) return "";
  const d = String(date.getDate()).padStart(2, "0");
  const m = String(date.getMonth() + 1).padStart(2, "0");
  return `${d}/${m}/${date.getFullYear()}`;
});

// The month currently shown in the calendar grid -- defaults to the
// selected date (or today) whenever the picker is opened.
const viewDate = ref(parseIso(props.modelValue) ?? new Date());

function toggleOpen() {
  if (!open.value) viewDate.value = parseIso(props.modelValue) ?? new Date();
  open.value = !open.value;
}

function shiftMonth(delta: number) {
  const d = new Date(viewDate.value);
  d.setMonth(d.getMonth() + delta);
  viewDate.value = d;
}

const monthLabel = computed(() =>
  viewDate.value.toLocaleDateString("it-IT", { month: "long", year: "numeric" }),
);

const weekdayLabels = ["L", "M", "M", "G", "V", "S", "D"];

type Cell = { key: string; day: number; iso: string; inMonth: boolean; disabled: boolean };

const calendarCells = computed<Cell[]>(() => {
  const year = viewDate.value.getFullYear();
  const month = viewDate.value.getMonth();
  const firstOfMonth = new Date(year, month, 1);
  // Monday-first grid: JS getDay() is 0=Sunday, shift so Monday=0.
  const leadingBlanks = (firstOfMonth.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const minDate = props.min ? parseIso(props.min) : null;
  const maxDate = props.max ? parseIso(props.max) : null;

  const cells: Cell[] = [];
  const gridStart = new Date(year, month, 1 - leadingBlanks);
  for (let i = 0; i < 42; i++) {
    const cellDate = new Date(gridStart);
    cellDate.setDate(gridStart.getDate() + i);
    const iso = toIso(cellDate);
    const disabled = !!((minDate && cellDate < minDate) || (maxDate && cellDate > maxDate));
    cells.push({
      key: iso,
      day: cellDate.getDate(),
      iso,
      inMonth: cellDate.getMonth() === month,
      disabled,
    });
    // Stop once we've completed the row that contains the month's last day.
    if (cellDate.getMonth() === month && cellDate.getDate() === daysInMonth && (i + 1) % 7 === 0) break;
  }
  return cells;
});

function cellClass(cell: Cell) {
  const isSelected = cell.iso === props.modelValue;
  const isToday = cell.iso === toIso(new Date());
  return {
    "text-ink": cell.inMonth && !isSelected,
    "text-muted/50": !cell.inMonth,
    "bg-accent text-white font-semibold": isSelected,
    "border border-accent/50": isToday && !isSelected,
    "hover:bg-surface-2": !isSelected && !cell.disabled,
    "opacity-30 cursor-not-allowed": cell.disabled,
  };
}

function pickDay(cell: Cell) {
  if (cell.disabled) return;
  emit("update:modelValue", cell.iso);
  open.value = false;
}

function pickToday() {
  const iso = toIso(new Date());
  const minDate = props.min ? parseIso(props.min) : null;
  const maxDate = props.max ? parseIso(props.max) : null;
  const today = new Date();
  if ((minDate && today < minDate) || (maxDate && today > maxDate)) return;
  emit("update:modelValue", iso);
  open.value = false;
}

function clear() {
  emit("update:modelValue", "");
  open.value = false;
}

function onDocumentMousedown(e: MouseEvent) {
  if (!open.value) return;
  if (rootRef.value && !rootRef.value.contains(e.target as Node)) {
    open.value = false;
  }
}

onMounted(() => document.addEventListener("mousedown", onDocumentMousedown));
onUnmounted(() => document.removeEventListener("mousedown", onDocumentMousedown));
</script>
