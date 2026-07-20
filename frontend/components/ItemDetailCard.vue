<template>
  <section class="card border-2 border-accent/40">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-[1.2rem]">{{ item.name }}</h2>
        <div class="mt-2 flex flex-wrap gap-2">
          <span class="badge badge--pn">P/N {{ item.pn }}</span>
          <span class="badge badge--category">{{ item.category }}</span>
          <span class="badge badge--size" :class="`badge--size-${item.size}`">{{ sizeLabel(item.size) }}</span>
          <span class="badge badge--shelf">📍 <template v-if="zoneLabel">Zona {{ zoneLabel }} · </template>Scaffale {{ item.shelf_position }}</span>
        </div>
      </div>
      <button class="rounded-lg bg-transparent px-2.5 py-1 text-[1.1rem] text-muted" title="Chiudi" @click="emit('close')">✕</button>
    </div>

    <div class="mt-4 flex flex-wrap items-center gap-6">
      <div>
        <div class="text-[0.75rem] uppercase tracking-wide text-muted">Giacenza attuale</div>
        <div class="text-[2rem] font-bold" :class="isLowStock ? 'text-red-400' : 'text-ink'">{{ item.quantity }}</div>
      </div>
      <div>
        <div class="text-[0.75rem] uppercase tracking-wide text-muted">Scorta minima</div>
        <div class="text-[1.2rem] font-semibold text-muted">{{ lowStockThreshold }}</div>
      </div>
      <span v-if="isLowStock" class="badge bg-bad/20 text-red-300 border border-bad/45">⚠️ Scorta minima raggiunta</span>
    </div>

    <div class="mt-5 flex flex-wrap items-center gap-3 max-[640px]:flex-col max-[640px]:items-stretch">
      <div class="flex items-center gap-3 max-[640px]:justify-between">
        <label class="text-sm text-muted" for="qty-input">Quantità</label>
        <input
          id="qty-input"
          v-model.number="qty"
          type="number"
          min="1"
          class="field-input w-[90px] text-center text-[1.1rem]"
        />
      </div>

      <div class="flex flex-1 gap-3 max-[640px]:flex-col">
        <button
          type="button"
          class="btn flex-1 bg-bad py-4 text-[1.1rem] font-bold text-white hover:bg-red-600 disabled:opacity-40"
          :disabled="busy || qty < 1 || qty > item.quantity"
          @click="performAction('withdraw')"
        >
          🔴 -1 Preleva
        </button>
        <button
          type="button"
          class="btn flex-1 bg-good py-4 text-[1.1rem] font-bold text-white hover:bg-green-600 disabled:opacity-40"
          :disabled="busy || qty < 1"
          @click="performAction('deposit')"
        >
          🟢 +1 Deposita
        </button>
      </div>
    </div>

    <div class="mt-3.5 flex flex-wrap gap-2.5">
      <a
        :href="labelUrl(item.id)"
        target="_blank"
        rel="noopener"
        class="btn btn--ghost inline-flex items-center gap-2"
      >
        🖨️ Stampa Etichetta
      </a>
      <NuxtLink
        class="btn btn--ghost inline-flex items-center gap-2"
        :to="{ path: '/dashboard', query: { shelf_position: item.shelf_position } }"
      >
        Apri nel Dashboard
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
const { operator } = useOperator()
const { show } = useToast()

const qty = ref(1)
const busy = ref(false)

const lowStockThreshold = computed(() => props.lowStockThreshold ?? 3)
const isLowStock = computed(() => props.item.quantity <= lowStockThreshold.value)

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
      operator: operator.value,
    }
    const res = action === 'withdraw' ? await withdrawItem(payload) : await depositItem(payload)
    show('success', res.message)
    emit('updated', res.item)
    qty.value = 1
  } catch (err: any) {
    show('error', err?.data?.detail || "Operazione non riuscita")
  } finally {
    busy.value = false
  }
}
</script>
