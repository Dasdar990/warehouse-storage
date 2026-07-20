<template>
  <div ref="scrollContainer" class="scrollbar-slim overflow-x-auto pb-1.5">
    <div
      class="grid w-max gap-1"
      :style="{ gridTemplateColumns: `56px repeat(${layout.shelf_numbers.length}, 52px)` }"
    >
      <!-- Column header row -->
      <div class="h-8 w-14"></div>
      <div v-for="n in layout.shelf_numbers" :key="`col-${n}`" class="flex h-8 items-center justify-center text-[0.75rem] font-bold text-muted">{{ n }}</div>

      <!-- One row per level -->
      <template v-for="level in layout.levels" :key="`row-${level}`">
        <div class="flex h-8 w-14 items-center justify-center text-[0.75rem] font-bold text-muted">{{ level }}</div>
        <button
          v-for="n in layout.shelf_numbers"
          :key="`${n}${level}`"
          :ref="(el) => setCellRef(`${n}${level}`, el)"
          class="relative flex h-[52px] flex-col items-center justify-center gap-0.5 rounded-lg border text-ink transition duration-[80ms] ease-out hover:-translate-y-0.5 hover:shadow-[0_4px_14px_rgba(0,0,0,0.35)]"
          :class="cellClass(n, level)"
          :style="cellStyle(n, level)"
          :title="`Shelf ${n}${level}${shelfAt(n, level) ? ` — ${shelfAt(n, level)!.item_count} item(s)` : ' — empty'}`"
          @click="emit('select', `${n}${level}`)"
        >
          <span class="text-[0.7rem] font-bold">{{ n }}{{ level }}</span>
          <span v-if="shelfAt(n, level)" class="text-[0.65rem] text-muted">{{ shelfAt(n, level)!.item_count }}</span>
        </button>
      </template>
    </div>

    <div class="mt-3.5 flex flex-wrap gap-[18px]">
      <span class="flex items-center gap-1.5 text-[0.8rem] text-muted"><i class="inline-block h-2.5 w-2.5 rounded-[3px] border border-edge bg-surface"></i> Empty</span>
      <span class="flex items-center gap-1.5 text-[0.8rem] text-muted"><i class="inline-block h-2.5 w-2.5 rounded-[3px] bg-accent/60"></i> Stocked</span>
      <span class="flex items-center gap-1.5 text-[0.8rem] text-muted"><i class="inline-block h-2.5 w-2.5 rounded-[3px] bg-bad/60"></i> Low stock (≤ {{ layout.low_stock_threshold }})</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ComponentPublicInstance } from 'vue'
import type { WarehouseLayout } from '~/composables/useWarehouseApi'

const props = defineProps<{
  layout: WarehouseLayout
  selectedShelf: string | null
}>()

const emit = defineEmits<{ select: [string] }>()

const scrollContainer = ref<HTMLElement | null>(null)
const cellRefs = new Map<string, HTMLElement>()

function setCellRef(position: string, el: Element | ComponentPublicInstance | null) {
  if (el instanceof HTMLElement) cellRefs.set(position, el)
}

const shelfByPosition = computed(() => {
  const map = new Map<string, WarehouseLayout['shelves'][number]>()
  for (const shelf of props.layout.shelves) {
    map.set(shelf.shelf_position, shelf)
  }
  return map
})

function shelfAt(shelfNumber: number, level: string) {
  return shelfByPosition.value.get(`${shelfNumber}${level}`)
}

function cellClass(shelfNumber: number, level: string) {
  const shelf = shelfAt(shelfNumber, level)
  const base = !shelf
    ? 'bg-surface border-edge'
    : shelf.has_low_stock
      ? 'bg-bad/[0.18] border-bad/55'
      : 'bg-accent/[0.18] border-accent/50'
  return base
}

// Pulsing glow animation loop, only runs while a shelf is actually selected.
const glowBlur = ref(8)
let glowRaf: number | null = null
function tickGlow(timestamp: number) {
  glowBlur.value = 8 + Math.sin(timestamp / 250) * 5
  glowRaf = requestAnimationFrame(tickGlow)
}

function cellStyle(shelfNumber: number, level: string) {
  const position = `${shelfNumber}${level}`
  if (props.selectedShelf !== position) return {}
  return {
    outline: '2px solid #22c55e',
    outlineOffset: '2px',
    boxShadow: `0 0 ${glowBlur.value}px 2px rgba(34, 197, 94, 0.75)`,
  }
}

watch(
  () => props.selectedShelf,
  (position) => {
    if (!position) return
    nextTick(() => {
      cellRefs.get(position)?.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' })
    })
  }
)

onMounted(() => {
  glowRaf = requestAnimationFrame(tickGlow)
})

onUnmounted(() => {
  if (glowRaf) cancelAnimationFrame(glowRaf)
})
</script>
