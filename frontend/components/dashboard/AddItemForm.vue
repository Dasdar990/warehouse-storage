<script setup lang="ts">
import type { Item } from '~/composables/useWarehouseApi'

const emit = defineEmits<{ created: [] }>()

const { createItem } = useWarehouseApi()
const { show } = useToast()

const form = ref({
  name: '',
  pn: '',
  barcode: '',
  category: '',
  size: 'small' as Item['size'],
  shelf_position: '',
  quantity: 0,
})
const error = ref('')
const submitting = ref(false)

async function submit() {
  error.value = ''
  submitting.value = true
  try {
    await createItem({ ...form.value, quantity: Number(form.value.quantity) || 0 })
    show('success', `Item "${form.value.name}" created`)
    form.value = { name: '', pn: '', barcode: '', category: '', size: 'small', shelf_position: '', quantity: 0 }
    emit('created')
  } catch (err: any) {
    error.value = err?.data?.detail || 'Failed to create item'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <form class="add-form" @submit.prevent="submit">
    <div class="field">
      <label>Name</label>
      <input v-model="form.name" required type="text" placeholder="Hex Bolt M8x30" />
    </div>
    <div class="field">
      <label>Part Number</label>
      <input v-model="form.pn" required type="text" placeholder="HB-M8-30" />
    </div>
    <div class="field">
      <label>Barcode</label>
      <input v-model="form.barcode" required type="text" placeholder="0123456789" />
    </div>
    <div class="field">
      <label>Category</label>
      <input v-model="form.category" required type="text" placeholder="Fasteners" />
    </div>
    <div class="field">
      <label>Size</label>
      <select v-model="form.size">
        <option value="small">Small</option>
        <option value="big">Big</option>
        <option value="xl">XL</option>
      </select>
    </div>
    <div class="field">
      <label>Shelf Position</label>
      <input v-model="form.shelf_position" required type="text" placeholder="12B" />
    </div>
    <div class="field">
      <label>Initial Quantity</label>
      <input v-model.number="form.quantity" type="number" min="0" />
    </div>
    <p v-if="error" class="form-error">{{ error }}</p>
    <button class="btn btn--confirm" type="submit" :disabled="submitting">
      {{ submitting ? 'Saving…' : 'Save Item' }}
    </button>
  </form>
</template>

<style scoped>
.add-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 0.8rem;
  color: var(--text-dim);
}

.field input,
.field select {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #0a0e14;
  color: var(--text);
}

.form-error {
  grid-column: 1 / -1;
  color: #fca5a5;
  margin: 0;
}

.btn {
  cursor: pointer;
  border: none;
  border-radius: 8px;
  padding: 10px 18px;
  font-weight: 600;
  font-size: 0.95rem;
  grid-column: 1 / -1;
  justify-self: start;
}

.btn--confirm {
  background: var(--green);
  color: #06280f;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 640px) {
  .add-form {
    grid-template-columns: 1fr;
  }
}
</style>
