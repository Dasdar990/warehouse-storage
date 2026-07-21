<template>
  <div class="flex flex-col gap-4">
    <section class="card">
      <div class="mb-3.5 flex overflow-hidden rounded-[10px] border-2 border-edge">
        <button
          type="button"
          class="flex-1 whitespace-nowrap px-5 py-3 text-[0.95rem] font-bold transition-colors"
          :class="mode === 'deposit' ? 'bg-good text-white' : 'bg-transparent text-muted hover:text-ink'"
          @click="setMode('deposit')"
        >
          🟢 DEPOSIT
        </button>
        <button
          type="button"
          class="flex-1 whitespace-nowrap px-5 py-3 text-[0.95rem] font-bold transition-colors"
          :class="mode === 'withdraw' ? 'bg-bad text-white' : 'bg-transparent text-muted hover:text-ink'"
          @click="setMode('withdraw')"
        >
          🔴 WITHDRAW
        </button>
      </div>

      <label class="mb-2.5 block text-[0.8rem] uppercase tracking-wider text-muted" for="scanner">Scan barcode</label>
      <input
        id="scanner"
        ref="scannerInput"
        v-model="barcodeValue"
        class="w-full rounded-[10px] border-2 border-accent-dim bg-input px-[18px] py-4 text-[1.6rem] font-bold tracking-wide text-ink outline-none focus:border-accent focus:shadow-[0_0_0_4px_rgba(59,130,246,0.25)] max-[640px]:p-3.5 max-[640px]:text-xl"
        type="text"
        placeholder="Ready to scan…"
        autocomplete="off"
        autofocus
        @keyup.enter="handleScan"
      />
    </section>

    <transition
      enter-active-class="transition duration-200 ease-out"
      leave-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-1.5"
      leave-to-class="opacity-0 -translate-y-1.5"
    >
      <section v-if="activeItem" class="card">
        <div class="flex items-center justify-between">
          <h2>{{ activeItem.name }}</h2>
          <button class="rounded-lg bg-transparent px-2.5 py-1 text-[1.1rem] text-muted" title="Cancel" @click="cancelActiveItem">✕</button>
        </div>

        <div class="mt-3 flex flex-wrap gap-2.5">
          <span class="badge badge--pn">P/N {{ activeItem.pn }}</span>
          <span class="badge badge--category">{{ activeItem.category }}</span>
          <span class="badge badge--size" :class="`badge--size-${activeItem.size}`">{{ sizeLabel(activeItem.size) }}</span>
          <span class="badge badge--shelf">Shelf {{ activeItem.shelf_position }}</span>
        </div>

        <div class="mt-4 text-[1.05rem] text-muted">
          Current stock: <strong class="text-[1.3rem] text-ink">{{ activeItem.quantity }}</strong>
        </div>

        <div class="mt-[18px] flex flex-wrap items-center gap-3 max-[640px]:flex-col max-[640px]:items-stretch">
          <label class="text-sm text-muted" for="qty">{{ mode === 'deposit' ? 'Deposit quantity' : 'Withdraw quantity' }}</label>
          <input
            id="qty"
            v-model.number="withdrawQty"
            type="number"
            min="1"
            :max="mode === 'withdraw' ? activeItem.quantity : undefined"
            class="field-input w-[90px] text-center text-[1.1rem] max-[640px]:w-full"
            @keyup.enter="confirmAction"
          />
          <button
            class="btn text-white"
            :class="mode === 'deposit' ? 'bg-good hover:bg-green-600' : 'bg-bad hover:bg-red-600'"
            @click="confirmAction"
          >{{ mode === 'deposit' ? 'Confirm Deposit' : 'Confirm Withdrawal' }}</button>
        </div>
      </section>
    </transition>
  </div>
</template>

<script setup lang="ts">
import type { Item } from '~/composables/useWarehouseApi'

const { scanItem, withdrawItem, depositItem } = useWarehouseApi()
const { mode, setMode } = useOperationMode()
const { show } = useToast()

const scannerInput = ref<HTMLInputElement | null>(null)
const barcodeValue = ref('')
const activeItem = ref<Item | null>(null)
const withdrawQty = ref(1)

function focusScanner() {
  nextTick(() => scannerInput.value?.focus())
}

function sizeLabel(size: string) {
  return { small: 'Small', big: 'Big', xl: 'XL' }[size] || size
}

async function handleScan() {
  const code = barcodeValue.value.trim()
  if (!code) return

  // A second Enter on the same barcode (already active) confirms the
  // action instead of re-looking the item up.
  if (activeItem.value && activeItem.value.barcode === code) {
    await confirmAction()
    return
  }

  try {
    activeItem.value = await scanItem(code)
    withdrawQty.value = 1
    barcodeValue.value = ''
  } catch (err: any) {
    activeItem.value = null
    show('error', err?.data?.detail || `No item found for barcode "${code}"`)
    barcodeValue.value = ''
  } finally {
    focusScanner()
  }
}

async function confirmAction() {
  if (!activeItem.value) return
  if (withdrawQty.value < 1) {
    show('error', 'Quantity must be at least 1')
    return
  }

  try {
    const payload = {
      barcode: activeItem.value.barcode,
      quantity: withdrawQty.value,
      source: 'barcode' as const,
    }
    const res = mode.value === 'deposit' ? await depositItem(payload) : await withdrawItem(payload)
    show('success', res.message)
  } catch (err: any) {
    show('error', err?.data?.detail || (mode.value === 'deposit' ? 'Deposit failed' : 'Withdrawal failed'))
  } finally {
    activeItem.value = null
    barcodeValue.value = ''
    focusScanner()
  }
}

function cancelActiveItem() {
  activeItem.value = null
  barcodeValue.value = ''
  focusScanner()
}

onMounted(focusScanner)
</script>
