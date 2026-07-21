<template>
  <div class="card w-full max-w-[380px]">
    <div class="mb-6 flex flex-col items-center gap-2 text-center">
      <span class="text-[2.5rem]">📦</span>
      <h1 class="m-0 text-[1.3rem] font-bold">Warehouse Storage</h1>
      <p class="m-0 text-sm text-muted">Sign in with your credentials to continue</p>
    </div>

    <form class="flex flex-col gap-3.5" @submit.prevent="handleSubmit">
      <div>
        <label for="username" class="mb-1.5 block text-[0.8rem] text-muted">Username</label>
        <input
          id="username"
          v-model="username"
          type="text"
          autocomplete="username"
          autofocus
          required
          class="field-input w-full"
        />
      </div>

      <div>
        <label for="password" class="mb-1.5 block text-[0.8rem] text-muted">Password</label>
        <input
          id="password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          required
          class="field-input w-full"
        />
      </div>

      <p v-if="errorMessage" class="m-0 rounded-lg border border-bad/40 bg-bad/15 px-3.5 py-2.5 text-[0.85rem] text-red-300">
        {{ errorMessage }}
      </p>

      <button type="submit" class="btn btn--primary mt-1.5 w-full py-3 text-[1rem]" :disabled="loading">
        {{ loading ? 'Signing in…' : 'Sign In' }}
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'blank' })

const { login } = useAuth()

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

async function handleSubmit() {
  errorMessage.value = ''
  loading.value = true
  try {
    await login(username.value.trim(), password.value)
    await navigateTo('/')
  } catch (err: any) {
    errorMessage.value = err?.data?.detail || 'Invalid username or password'
  } finally {
    loading.value = false
  }
}
</script>
