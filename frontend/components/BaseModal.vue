<template>
  <Teleport to="body">
    <transition
      enter-active-class="transition duration-150 ease-out"
      leave-active-class="transition duration-100 ease-in"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/60 p-4 pt-[8vh] backdrop-blur-sm"
        @mousedown.self="close"
      >
        <transition
          enter-active-class="transition duration-150 ease-out"
          leave-active-class="transition duration-100 ease-in"
          enter-from-class="opacity-0 scale-95 -translate-y-1"
          leave-to-class="opacity-0 scale-95 -translate-y-1"
        >
          <div
            v-if="modelValue"
            class="w-full rounded-card border border-edge bg-surface shadow-card"
            :class="maxWidthClass"
            @keydown.esc="close"
          >
            <div class="flex items-center justify-between gap-3 border-b border-edge px-5 py-4">
              <h2 class="m-0 text-[1.05rem] font-bold">{{ title }}</h2>
              <button type="button" class="rounded-lg bg-transparent px-2 py-1 text-[1.1rem] text-muted hover:text-ink" title="Close" @click="close">✕</button>
            </div>
            <div class="p-5">
              <slot />
            </div>
          </div>
        </transition>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: boolean
    title: string
    size?: 'sm' | 'md' | 'lg'
  }>(),
  { size: 'md' }
)

const emit = defineEmits<{ 'update:modelValue': [boolean] }>()

const maxWidthClass = computed(() => ({
  sm: 'max-w-[420px]',
  md: 'max-w-[640px]',
  lg: 'max-w-[880px]',
}[props.size]))

function close() {
  emit('update:modelValue', false)
}
</script>
