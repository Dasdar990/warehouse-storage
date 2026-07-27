<template>
  <div class="flex flex-col gap-6">
    <form class="grid grid-cols-1 gap-2.5 rounded-lg border border-edge bg-surface-2 p-4 sm:grid-cols-[1fr_1fr_1fr_auto_auto]" @submit.prevent="add">
      <input v-model="newUsername" type="text" placeholder="Username" autocomplete="off" required minlength="3" class="field-input" />
      <input v-model="newFullName" type="text" placeholder="Full name" required class="field-input" />
      <input v-model="newPassword" type="password" placeholder="Password (min. 6 characters)" autocomplete="new-password" required minlength="6" class="field-input" />
      <select v-model="newRole" class="field-input">
        <option value="operator">Operator</option>
        <option value="admin">Admin</option>
      </select>
      <button type="submit" class="btn btn--confirm whitespace-nowrap disabled:cursor-not-allowed disabled:opacity-60" :disabled="submitting">
        {{ submitting ? 'Creating…' : '+ Add User' }}
      </button>
    </form>

    <p v-if="loading" class="text-muted">Loading users…</p>
    <div v-else class="overflow-x-auto">
      <table class="w-full border-collapse text-sm">
        <thead>
          <tr class="border-b border-edge text-left text-muted">
            <th class="py-2 pr-3 font-medium">User</th>
            <th class="py-2 pr-3 font-medium">Role</th>
            <th class="py-2 pr-3 font-medium">Status</th>
            <th class="py-2 pr-3 font-medium">Created On</th>
            <th class="py-2 pr-3 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" class="border-b border-edge/60">
            <td class="py-2.5 pr-3">
              <div class="font-medium text-ink">{{ u.full_name }}</div>
              <div class="text-[0.78rem] text-muted">@{{ u.username }}</div>
            </td>
            <td class="py-2.5 pr-3">
              <select
                :value="u.role"
                :disabled="u.id === currentUserId"
                class="field-input py-1 text-[0.82rem] disabled:cursor-not-allowed disabled:opacity-60"
                @change="changeRole(u, ($event.target as HTMLSelectElement).value as UserRole)"
              >
                <option value="operator">Operator</option>
                <option value="admin">Admin</option>
              </select>
            </td>
            <td class="py-2.5 pr-3">
              <button
                type="button"
                class="rounded-full px-2.5 py-1 text-[0.75rem] font-semibold transition-opacity hover:opacity-80 disabled:cursor-not-allowed disabled:opacity-50"
                :class="u.is_active ? 'bg-good-dim text-green-200' : 'bg-bad-dim text-red-200'"
                :disabled="u.id === currentUserId"
                @click="toggleActive(u)"
              >
                {{ u.is_active ? 'Active' : 'Disabled' }}
              </button>
            </td>
            <td class="py-2.5 pr-3 text-muted">{{ formatDate(u.created_at) }}</td>
            <td class="py-2.5 pr-3 text-right">
              <div class="flex justify-end gap-1.5">
                <button type="button" class="rounded-lg border border-edge bg-transparent px-2.5 py-1 text-[0.78rem] text-ink transition-colors hover:bg-surface-2" @click="resetPassword(u)">
                  Reset Password
                </button>
                <button
                  type="button"
                  class="rounded-lg bg-transparent px-2.5 py-1 text-base text-muted hover:text-red-300 disabled:cursor-not-allowed disabled:opacity-40"
                  title="Delete user"
                  :disabled="u.id === currentUserId"
                  @click="remove(u)"
                >
                  ✕
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!users.length" class="text-muted">No users yet.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AppUser, UserRole } from '~/composables/useWarehouseApi'

const { listUsers, createUser, updateUser, deleteUser } = useWarehouseApi()
const { user: currentUser } = useAuth()
const { show } = useToast()

const users = ref<AppUser[]>([])
const loading = ref(false)
const submitting = ref(false)

const newUsername = ref('')
const newFullName = ref('')
const newPassword = ref('')
const newRole = ref<UserRole>('operator')

const currentUserId = computed(() => currentUser.value?.id ?? null)

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

async function refresh() {
  loading.value = true
  try {
    users.value = await listUsers()
  } catch (err: any) {
    show('error', err?.data?.detail || 'Unable to load users')
  } finally {
    loading.value = false
  }
}

async function add() {
  submitting.value = true
  try {
    await createUser({
      username: newUsername.value.trim(),
      full_name: newFullName.value.trim(),
      password: newPassword.value,
      role: newRole.value,
    })
    newUsername.value = ''
    newFullName.value = ''
    newPassword.value = ''
    newRole.value = 'operator'
    show('success', 'User created')
    await refresh()
  } catch (err: any) {
    show('error', err?.data?.detail || 'Failed to create user')
  } finally {
    submitting.value = false
  }
}

async function changeRole(u: AppUser, role: UserRole) {
  try {
    await updateUser(u.id, { role })
    show('success', `${u.full_name}'s role updated`)
    await refresh()
  } catch (err: any) {
    show('error', err?.data?.detail || 'Failed to update role')
  }
}

async function toggleActive(u: AppUser) {
  try {
    await updateUser(u.id, { is_active: !u.is_active })
    await refresh()
  } catch (err: any) {
    show('error', err?.data?.detail || 'Failed to update status')
  }
}

async function resetPassword(u: AppUser) {
  const newPw = window.prompt(`New password for ${u.full_name} (min. 6 characters):`)
  if (!newPw) return
  if (newPw.length < 6) {
    show('error', 'Password must be at least 6 characters')
    return
  }
  try {
    await updateUser(u.id, { password: newPw })
    show('success', 'Password updated')
  } catch (err: any) {
    show('error', err?.data?.detail || 'Failed to reset password')
  }
}

async function remove(u: AppUser) {
  if (!window.confirm(`Delete user ${u.full_name}? This action cannot be undone.`)) return
  try {
    await deleteUser(u.id)
    show('success', 'User deleted')
    await refresh()
  } catch (err: any) {
    show('error', err?.data?.detail || 'Failed to delete user')
  }
}

onMounted(refresh)
</script>
