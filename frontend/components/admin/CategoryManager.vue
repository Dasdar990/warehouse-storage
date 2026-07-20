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
        class="flex items-center justify-between rounded-lg border border-edge bg-surface-2 px-3.5 py-2.5"
      >
        <span>{{ category.name }}</span>
        <button
          class="rounded-lg bg-transparent px-2.5 py-1 text-base text-muted hover:text-red-300"
          title="Delete category"
          @click="remove(category)"
        >
          ✕
        </button>
      </li>
    </ul>
    <p v-else class="text-muted">No categories yet. Add the first one above.</p>
  </div>
</template>

<script setup lang="ts">
import type { Category } from '~/composables/useWarehouseApi'

const { listAdminCategories, createCategory, deleteCategory } = useWarehouseApi()
const { show } = useToast()

const categories = ref<Category[]>([])
const loading = ref(false)
const submitting = ref(false)
const newName = ref('')

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
