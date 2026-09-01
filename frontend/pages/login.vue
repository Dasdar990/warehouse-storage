<template>
  <div class="card w-full max-w-98">
    <div class="mb-6 flex flex-col items-center gap-1 text-center">
      <img src="~/assets/images/logo.svg" class="w-64 h-32" />
      <h1 class="m-0 text-[1.4rem] font-bold">
        Industrial Engineering Warehouse
      </h1>
      <p class="text-xl text-muted">Tap your badge to sign in</p>
      <p class="m-0 text-sm text-muted">or sign in with your credentials instead</p>
      <NfcAnimation v-if="!showCredentialForm" />
    </div>

    <p
      v-if="errorMessage && !showCredentialForm"
      role="alert"
      aria-live="polite"
      class="m-0 mb-3.5 rounded-lg border border-bad/40 bg-bad/15 px-3.5 py-2.5 text-[0.85rem] text-red-300"
    >
      {{ errorMessage }}
    </p>

    <button
      type="button"
      class="btn btn--primary mt-1.5 w-full py-3 text-[1rem]"
      :disabled="loading"
      v-if="!showCredentialForm"
      @click="openCredentialForm"
    >
      Sign in with credentials
    </button>

    <form
      v-if="showCredentialForm"
      class="flex flex-col gap-3.5"
      @submit.prevent="handleSubmit"
    >
      <div>
        <label for="username" class="mb-1.5 block text-[0.8rem] text-muted"
          >Username</label
        >
        <input
          id="username"
          ref="usernameInput"
          v-model="username"
          type="text"
          autocomplete="username"
          required
          :disabled="loading"
          class="field-input w-full"
          @keydown="handleUsernameKeydown"
          @keyup.enter="handleUsernameEnter"
        />
      </div>

      <div>
        <label for="password" class="mb-1.5 block text-[0.8rem] text-muted"
          >Password</label
        >
        <input
          id="password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          required
          :disabled="loading"
          class="field-input w-full"
        />
      </div>

      <p
        v-if="errorMessage"
        role="alert"
        aria-live="polite"
        class="m-0 rounded-lg border border-bad/40 bg-bad/15 px-3.5 py-2.5 text-[0.85rem] text-red-300"
      >
        {{ errorMessage }}
      </p>

      <button
        type="submit"
        class="btn btn--primary mt-1.5 w-full py-3 text-[1rem]"
        :disabled="loading"
      >
        {{ loading ? "Signing in…" : "Sign In" }}
      </button>

      <button
        type="button"
        class="mt-0.5 text-sm text-muted underline-offset-2 hover:underline"
        :disabled="loading"
        @click="closeCredentialForm"
      >
        ← Use your badge instead
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: "blank" });

const { login, badgeLogin } = useAuth();
const { onKeydown, onEnter, looksLikeScan } = useBarcodeScanner({
  onScan: handleBadgeScan,
  // A slow, manually-typed Enter in the username field: nothing to do here,
  // the browser's own implicit form submission (or its required-field
  // validation, if password is still empty) already handles it -- we only
  // intervened to catch the *fast* case.
  onManualSubmit: () => {},
});

// PN7150 dongle (MIKROE-2540): not a keyboard wedge, so taps arrive over
// a local WebSocket from nfc-bridge/bridge.py rather than as keystrokes.
// Same handleBadgeScan() as the burst-detected path above either way.
const { connected: nfcConnected, stop: stopNfcBridge } = useNfcBridge({
  onBadgeTap: handleBadgeScan,
});
onUnmounted(stopNfcBridge);

const username = ref("");
const password = ref("");
const loading = ref(false);
const errorMessage = ref("");

const showCredentialForm = ref(false);
const usernameInput = ref<HTMLInputElement | null>(null);

async function openCredentialForm() {
  showCredentialForm.value = true;
  errorMessage.value = "";
  await nextTick();
  usernameInput.value?.focus();
}

function closeCredentialForm() {
  showCredentialForm.value = false;
  username.value = "";
  password.value = "";
  errorMessage.value = "";
}

function handleUsernameKeydown(event: KeyboardEvent) {
  onKeydown(event);
  // If this Enter is capping off a fast burst, it's a badge tap, not a
  // person confirming their typed username -- stop the browser from
  // trying to implicitly submit the form (which would fail on the empty
  // required password field) so our own handling below can take over.
  if (event.key === "Enter" && looksLikeScan()) {
    event.preventDefault();
  }
}

function handleUsernameEnter(event: KeyboardEvent) {
  onEnter(event, username.value);
}

async function handleBadgeScan(badgeUid: string) {
  if (loading.value) return;
  showCredentialForm.value = false;
  errorMessage.value = "";
  loading.value = true;
  username.value = "";
  try {
    await badgeLogin(badgeUid);
    await navigateTo("/");
  } catch (err: any) {
    errorMessage.value = err?.data?.detail || "Badge not recognized";
  } finally {
    loading.value = false;
  }
}

async function handleSubmit() {
  errorMessage.value = "";
  loading.value = true;
  try {
    await login(username.value.trim(), password.value);
    await navigateTo("/");
  } catch (err: any) {
    errorMessage.value = err?.data?.detail || "Invalid username or password";
  } finally {
    loading.value = false;
  }
}
</script>
