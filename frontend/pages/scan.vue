<script setup lang="ts">
import type { Item } from '~/composables/useWarehouseApi'

const { scanItem, withdrawItem } = useWarehouseApi()
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
  // withdrawal instead of re-looking the item up.
  if (activeItem.value && activeItem.value.barcode === code) {
    await confirmWithdrawal()
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

async function confirmWithdrawal() {
  if (!activeItem.value) return
  if (withdrawQty.value < 1) {
    show('error', 'Quantity must be at least 1')
    return
  }

  try {
    const res = await withdrawItem(activeItem.value.barcode, withdrawQty.value)
    show('success', res.message)
  } catch (err: any) {
    show('error', err?.data?.detail || 'Withdrawal failed')
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

<template>
  <div class="scan-page">
    <section class="scanner-panel">
      <label class="scanner-label" for="scanner">Scan barcode</label>
      <input
        id="scanner"
        ref="scannerInput"
        v-model="barcodeValue"
        class="scanner-input"
        type="text"
        placeholder="Ready to scan…"
        autocomplete="off"
        autofocus
        @keyup.enter="handleScan"
      />
    </section>

    <transition name="fade">
      <section v-if="activeItem" class="active-card">
        <div class="active-card__header">
          <h2>{{ activeItem.name }}</h2>
          <button class="btn btn--icon" title="Cancel" @click="cancelActiveItem">✕</button>
        </div>

        <div class="active-card__badges">
          <span class="badge badge--pn">P/N {{ activeItem.pn }}</span>
          <span class="badge badge--category">{{ activeItem.category }}</span>
          <span class="badge badge--size" :class="`badge--size-${activeItem.size}`">{{ sizeLabel(activeItem.size) }}</span>
          <span class="badge badge--shelf">Shelf {{ activeItem.shelf_position }}</span>
        </div>

        <div class="active-card__stock">
          Current stock: <strong>{{ activeItem.quantity }}</strong>
        </div>

        <div class="active-card__withdraw">
          <label for="qty">Withdraw quantity</label>
          <input
            id="qty"
            v-model.number="withdrawQty"
            type="number"
            min="1"
            :max="activeItem.quantity"
            class="qty-input"
            @keyup.enter="confirmWithdrawal"
          />
          <button class="btn btn--confirm" @click="confirmWithdrawal">Confirm Withdrawal</button>
        </div>
      </section>
    </transition>
  </div>
</template>

<style scoped>
.scan-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.scanner-panel {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow);
}

.scanner-label {
  display: block;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-dim);
  margin-bottom: 10px;
}

.scanner-input {
  width: 100%;
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  padding: 16px 18px;
  border-radius: 10px;
  border: 2px solid var(--accent-dim);
  background: #0a0e14;
  color: var(--text);
  outline: none;
}

.scanner-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.25);
}

.active-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow);
}

.active-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.active-card__badges {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.active-card__stock {
  margin-top: 16px;
  color: var(--text-dim);
  font-size: 1.05rem;
}

.active-card__stock strong {
  color: var(--text);
  font-size: 1.3rem;
}

.active-card__withdraw {
  margin-top: 18px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.active-card__withdraw label {
  color: var(--text-dim);
  font-size: 0.9rem;
}

.qty-input {
  width: 90px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #0a0e14;
  color: var(--text);
  font-size: 1.1rem;
  text-align: center;
}

.btn {
  cursor: pointer;
  border: none;
  border-radius: 8px;
  padding: 10px 18px;
  font-weight: 600;
  font-size: 0.95rem;
}

.btn--confirm {
  background: var(--green);
  color: #06280f;
}

.btn--icon {
  background: transparent;
  color: var(--text-dim);
  padding: 4px 10px;
  font-size: 1.1rem;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (max-width: 640px) {
  .scanner-input {
    font-size: 1.2rem;
    padding: 14px;
  }

  .active-card__withdraw {
    flex-direction: column;
    align-items: stretch;
  }

  .qty-input {
    width: 100%;
  }
}
</style>
