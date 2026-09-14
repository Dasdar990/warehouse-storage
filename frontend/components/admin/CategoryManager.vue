<template>
  <div class="flex flex-col gap-4">
    <form class="flex gap-2.5" @submit.prevent="add">
      <input v-model="newName" type="text" placeholder="e.g. Fasteners" maxlength="60" required class="field-input flex-1" />
      <button class="btn btn--confirm whitespace-nowrap text-[#06280f] disabled:cursor-not-allowed disabled:opacity-60" type="submit" :disabled="submitting">
        {{ submitting ? 'Adding…' : '+ Add category' }}
      </button>
    </form>

    <p v-if="loading" class="text-muted">Loading categories…</p>
    <ul v-else-if="categories.length" class="m-0 flex list-none flex-col gap-2 p-0">
      <li
        v-for="category in categories"
        :key="category.id"
        class="flex items-center justify-between gap-2 rounded-lg border border-edge bg-surface-2 px-3.5 py-2.5"
      >
        <template v-if="editingId === category.id">
          <input
            v-model="editName"
            type="text"
            maxlength="60"
            required
            class="field-input flex-1"
            :disabled="savingEdit"
            @keyup.enter="saveEdit(category)"
            @keyup.esc="cancelEdit"
          />
          <div class="flex shrink-0 items-center gap-1">
            <button
              class="rounded-lg bg-transparent px-2.5 py-1 text-base text-muted hover:text-accent disabled:cursor-not-allowed disabled:opacity-60"
              title="Save"
              :disabled="savingEdit"
              @click="saveEdit(category)"
            >
              ✓
            </button>
            <button
              class="rounded-lg bg-transparent px-2.5 py-1 text-base text-muted hover:text-red-300"
              title="Cancel"
              :disabled="savingEdit"
              @click="cancelEdit"
            >
              ✕
            </button>
          </div>
        </template>
        <template v-else>
          <span>{{ category.name }}</span>
          <div class="flex shrink-0 items-center gap-1">
            <button
              class="rounded-lg bg-transparent px-2.5 py-1 text-base text-muted hover:text-accent"
              title="Edit category"
              @click="startEdit(category)"
            >
              ✏️
            </button>
            <button
              class="rounded-lg bg-transparent px-2.5 py-1 text-base text-muted hover:text-red-300"
              title="Delete category"
              @click="remove(category)"
            >
              ✕
            </button>
          </div>
        </template>
      </li>
    </ul>
    <p v-else class="text-muted">No categories yet. Add the first one above.</p>
  </div>
</template>

<script setup lang="ts">
import type { Category } from '~/composables/useWarehouseApi'

const { listAdminCategories, createCategory, updateCategory, deleteCategory } = useWarehouseApi()
const { show } = useToast()

const categories = ref<Category[]>([])
const loading = ref(false)
const submitting = ref(false)
const newName = ref('')

const editingId = ref<number | null>(null)
const editName = ref('')
const savingEdit = ref(false)

async function load() {
  loading.value = true
  try {
    categories.value = await listAdminCategories()
  } catch (err: any) {
    show('error', err?.data?.detail || 'Failed to load categories')
  } finally {
    loading.value = false
  }
}

async function add() {
  const name = newName.value.trim()
  if (!name) return
  submitting.value = true
  try {
    const category = await createCategory(name)
    categories.value = [...categories.value, category].sort((a, b) => a.name.localeCompare(b.name))
    newName.value = ''
    show('success', `Category "${category.name}" created`)
  } catch (err: any) {
    show('error', err?.data?.detail || 'Failed to create category')
  } finally {
    submitting.value = false
  }
}

function startEdit(category: Category) {
  editingId.value = category.id
  editName.value = category.name
}

function cancelEdit() {
  editingId.value = null
  editName.value = ''
}

async function saveEdit(category: Category) {
  const name = editName.value.trim()
  if (!name) return
  if (name === category.name) {
    cancelEdit()
    return
  }
  savingEdit.value = true
  try {
    const updated = await updateCategory(category.id, name)
    categories.value = categories.value
      .map((c) => (c.id === category.id ? updated : c))
      .sort((a, b) => a.name.localeCompare(b.name))
    show('success', `Category renamed to "${updated.name}" -- existing items updated too`)
    cancelEdit()
  } catch (err: any) {
    show('error', err?.data?.detail || 'Failed to rename category')
  } finally {
    savingEdit.value = false
  }
}

async function remove(category: Category) {
  if (
    !confirm(
      `Delete category "${category.name}"? Items that already use it keep it, but it will no longer be selectable for new items.`
    )
  ) {
    return
  }
  try {
    await deleteCategory(category.id)
    categories.value = categories.value.filter((c) => c.id !== category.id)
    show('success', `Category "${category.name}" deleted`)
  } catch (err: any) {
    show('error', err?.data?.detail || 'Failed to delete category')
  }
}

onMounted(load)
</script>
