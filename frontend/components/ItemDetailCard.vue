<template>
  <section class="card border-2 border-accent/40">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-[1.2rem]">{{ item.name }}</h2>
        <div class="mt-2 flex flex-wrap gap-2">
          <span class="badge badge--pn">P/N {{ item.pn }}</span>
          <span class="badge badge--category">{{ item.category }}</span>
          <span class="badge badge--size" :class="`badge--size-${item.size}`">{{ sizeLabel(item.size) }}</span>
          <span class="badge badge--shelf">📍 <template v-if="zoneLabel">Zone {{ zoneLabel }} · </template>Shelf {{ item.shelf_position }}</span>
        </div>
      </div>
      <button class="rounded-lg bg-transparent px-2.5 py-1 text-[1.1rem] text-muted" title="Close" @click="emit('close')">✕</button>
    </div>

    <div class="mt-4 flex flex-wrap items-center gap-6">
      <div>
        <div class="text-[0.75rem] uppercase tracking-wide text-muted">Current Stock</div>
        <div class="text-[2rem] font-bold" :class="isLowStock ? 'text-red-400' : 'text-ink'">{{ item.quantity }}</div>
      </div>
      <div>
        <div class="text-[0.75rem] uppercase tracking-wide text-muted">Minimum Stock</div>
        <div class="text-[1.2rem] font-semibold text-muted">{{ lowStockThreshold }}</div>
      </div>
      <span v-if="isLowStock" class="badge bg-bad/20 text-red-300 border border-bad/45">⚠️ Low stock reached</span>
    </div>

    <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-1.5">
        <label class="mr-1.5 text-sm text-muted" for="qty-input">Quantity</label>
        <button
          type="button"
          class="btn--icon h-9 w-9 text-lg disabled:cursor-not-allowed disabled:opacity-40"
          :disabled="qty <= 1"
          title="Decrease"
          @click="qty = Math.max(1, qty - 1)"
        >−</button>
        <input
          id="qty-input"
          v-model.number="qty"
          type="number"
          min="1"
          class="field-input w-[70px] px-1 text-center text-[1.1rem]"
        />
        <button
          type="button"
          class="btn--icon h-9 w-9 text-lg"
          title="Increase"
          @click="qty += 1"
        >+</button>
      </div>

      <div class="flex flex-wrap gap-1.5">
        <button
          v-for="preset in quickQuantities"
          :key="preset.label"
          type="button"
          class="rounded-lg border border-edge px-2.5 py-1 text-[0.78rem] font-semibold text-muted hover:border-accent/50 hover:text-ink"
          :class="{ 'border-accent/60 bg-accent/10 text-ink': qty === preset.value }"
          @click="qty = preset.value"
        >{{ preset.label }}</button>
      </div>
    </div>

    <div class="mt-3 flex flex-wrap gap-3 max-[640px]:flex-col">
      <button
        type="button"
        class="btn flex-1 bg-bad py-4 text-[1.1rem] font-bold text-white hover:bg-red-600 disabled:opacity-40"
        :disabled="busy || qty < 1 || qty > item.quantity"
        @click="performAction('withdraw')"
      >
        🔴 Withdraw −{{ qty }}
      </button>
      <button
        type="button"
        class="btn flex-1 bg-good py-4 text-[1.1rem] font-bold text-white hover:bg-green-600 disabled:opacity-40"
        :disabled="busy || qty < 1"
        @click="performAction('deposit')"
      >
        🟢 Deposit +{{ qty }}
      </button>
    </div>

    <div class="mt-3.5 flex flex-wrap gap-2.5">
      <a
        :href="labelUrl(item.id)"
        target="_blank"
        rel="noopener"
        class="btn btn--ghost inline-flex items-center gap-2"
      >
        🖨️ Print Label
      </a>
      <NuxtLink
        class="btn btn--ghost inline-flex items-center gap-2"
        :to="{ path: '/dashboard', query: { shelf_position: item.shelf_position } }"
      >
        Open in Dashboard
      </NuxtLink>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { Item, MovementSource } from '~/composables/useWarehouseApi'

const props = defineProps<{
  item: Item
  lowStockThreshold?: number
  zoneLabel?: string
  /** Where the current selection came from -- tags the *next* quick action for the audit log. */
  defaultSource?: MovementSource
}>()

const emit = defineEmits<{
  close: []
  updated: [item: Item]
}>()

const { withdrawItem, depositItem, labelUrl } = useWarehouseApi()
const { show } = useToast()

const qty = ref(1)
const busy = ref(false)

const lowStockThreshold = computed(() => props.lowStockThreshold ?? 3)
const isLowStock = computed(() => props.item.quantity <= lowStockThreshold.value)

// Common quick-pick amounts, plus "All" (the full current stock) so clearing
// out a shelf in one withdrawal doesn't require typing the exact number.
const quickQuantities = computed(() => {
  const presets = [1, 5, 10]
    .filter((n) => n <= Math.max(props.item.quantity, 1))
    .map((n) => ({ label: String(n), value: n }))
  if (props.item.quantity > 0 && !presets.some((p) => p.value === props.item.quantity)) {
    presets.push({ label: 'All', value: props.item.quantity })
  }
  return presets
})

function sizeLabel(size: string) {
  return ({ small: 'Small', big: 'Big', xl: 'XL' } as Record<string, string>)[size] || size
}

async function performAction(action: 'withdraw' | 'deposit') {
  busy.value = true
  try {
    const payload = {
      barcode: props.item.barcode,
      quantity: qty.value,
      source: (props.defaultSource ?? 'manual') as MovementSource,
    }
    const res = action === 'withdraw' ? await withdrawItem(payload) : await depositItem(payload)
    show('success', res.message)
    emit('updated', res.item)
    qty.value = 1
  } catch (err: any) {
    show('error', err?.data?.detail || "Operation failed")
  } finally {
    busy.value = false
  }
}
</script>
