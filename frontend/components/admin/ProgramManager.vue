<template>
  <div class="flex flex-col gap-4">
    <form class="flex gap-2.5" @submit.prevent="add">
      <input v-model="newName" type="text" placeholder="e.g. Falcon Refit" maxlength="60" required class="field-input flex-1" />
      <button class="btn btn--confirm whitespace-nowrap text-[#06280f] disabled:cursor-not-allowed disabled:opacity-60" type="submit" :disabled="submitting">
        {{ submitting ? 'Adding…' : '+ Add program' }}
      </button>
    </form>

    <p v-if="loading" class="text-muted">Loading programs…</p>
    <ul v-else-if="programs.length" class="m-0 flex list-none flex-col gap-2 p-0">
      <li
        v-for="program in programs"
        :key="program.id"
        class="flex items-center justify-between gap-2 rounded-lg border border-edge bg-surface-2 px-3.5 py-2.5"
      >
        <template v-if="editingId === program.id">
          <input
            v-model="editName"
            type="text"
            maxlength="60"
            required
            class="field-input flex-1"
            :disabled="savingEdit"
            @keyup.enter="saveEdit(program)"
            @keyup.esc="cancelEdit"
          />
          <div class="flex shrink-0 items-center gap-1">
            <button
              class="rounded-lg bg-transparent px-2.5 py-1 text-base text-muted hover:text-accent disabled:cursor-not-allowed disabled:opacity-60"
              title="Save"
              :disabled="savingEdit"
              @click="saveEdit(program)"
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
          <span>{{ program.name }}</span>
          <div class="flex shrink-0 items-center gap-1">
            <button
              class="rounded-lg bg-transparent px-2.5 py-1 text-base text-muted hover:text-accent"
              title="Edit program"
              @click="startEdit(program)"
            >
              ✏️
            </button>
            <button
              class="rounded-lg bg-transparent px-2.5 py-1 text-base text-muted hover:text-red-300"
              title="Delete program"
              @click="remove(program)"
            >
              ✕
            </button>
          </div>
        </template>
      </li>
    </ul>
    <p v-else class="text-muted">No programs yet. Add the first one above.</p>
  </div>
</template>

<script setup lang="ts">
import type { Program } from '~/composables/useWarehouseApi'

const { listAdminPrograms, createProgram, updateProgram, deleteProgram } = useWarehouseApi()
const { show } = useToast()

const programs = ref<Program[]>([])
const loading = ref(false)
const submitting = ref(false)
const newName = ref('')

const editingId = ref<number | null>(null)
const editName = ref('')
const savingEdit = ref(false)

async function load() {
  loading.value = true
  try {
    programs.value = await listAdminPrograms()
  } catch (err: any) {
    show('error', err?.data?.detail || 'Failed to load programs')
  } finally {
    loading.value = false
  }
}

async function add() {
  const name = newName.value.trim()
  if (!name) return
  submitting.value = true
  try {
    const program = await createProgram(name)
    programs.value = [...programs.value, program].sort((a, b) => a.name.localeCompare(b.name))
    newName.value = ''
    show('success', `Program "${program.name}" created`)
  } catch (err: any) {
    show('error', err?.data?.detail || 'Failed to create program')
  } finally {
    submitting.value = false
  }
}

function startEdit(program: Program) {
  editingId.value = program.id
  editName.value = program.name
}

function cancelEdit() {
  editingId.value = null
  editName.value = ''
}

async function saveEdit(program: Program) {
  const name = editName.value.trim()
  if (!name) return
  if (name === program.name) {
    cancelEdit()
    return
  }
  savingEdit.value = true
  try {
    const updated = await updateProgram(program.id, name)
    programs.value = programs.value
      .map((p) => (p.id === program.id ? updated : p))
      .sort((a, b) => a.name.localeCompare(b.name))
    show('success', `Program renamed to "${updated.name}" -- existing items updated too`)
    cancelEdit()
  } catch (err: any) {
    show('error', err?.data?.detail || 'Failed to rename program')
  } finally {
    savingEdit.value = false
  }
}

async function remove(program: Program) {
  if (
    !confirm(
      `Delete program "${program.name}"? Items that already use it keep it, but it will no longer be selectable for new items.`
    )
  ) {
    return
  }
  try {
    await deleteProgram(program.id)
    programs.value = programs.value.filter((p) => p.id !== program.id)
    show('success', `Program "${program.name}" deleted`)
  } catch (err: any) {
    show('error', err?.data?.detail || 'Failed to delete program')
  }
}

onMounted(load)
</script>
