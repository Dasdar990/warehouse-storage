<template>
  <div>
    <div v-if="modelValue.length" class="mb-1.5 flex flex-wrap gap-1.5">
      <span
        v-for="(tag, i) in modelValue"
        :key="tag"
        class="inline-flex items-center gap-1 rounded-full border border-accent/30 bg-accent/10 py-1 pl-2.5 pr-1.5 text-[0.78rem] font-semibold text-emerald-200"
      >
        {{ tag }}
        <button
          type="button"
          class="flex h-4 w-4 cursor-pointer items-center justify-center rounded-full bg-transparent text-emerald-200/70 transition-colors hover:bg-bad/20 hover:text-red-300"
          :title="`Remove '${tag}'`"
          @click="remove(i)"
        >
          ×
        </button>
      </span>
    </div>
    <input
      v-model="draft"
      type="text"
      :disabled="disabled"
      :placeholder="placeholder"
      class="field-input disabled:cursor-not-allowed disabled:opacity-60"
      @keydown.enter.prevent="commit"
      @keydown="handleKeydown"
      @blur="commit"
    />
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: string[];
    placeholder?: string;
    disabled?: boolean;
  }>(),
  { placeholder: "Add a tag and press Enter…", disabled: false },
);

const emit = defineEmits<{ "update:modelValue": [string[]] }>();

const draft = ref("");

function commit() {
  const tag = draft.value.trim().replace(/,/g, "");
  draft.value = "";
  if (!tag) return;
  if (props.modelValue.some((t) => t.toLowerCase() === tag.toLowerCase())) return;
  emit("update:modelValue", [...props.modelValue, tag]);
}

function remove(i: number) {
  const next = [...props.modelValue];
  next.splice(i, 1);
  emit("update:modelValue", next);
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === ",") {
    e.preventDefault();
    commit();
  } else if (e.key === "Backspace" && !draft.value && props.modelValue.length) {
    remove(props.modelValue.length - 1);
  }
}
</script>
