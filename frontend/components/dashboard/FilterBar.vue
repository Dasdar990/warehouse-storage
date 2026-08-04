<template>
  <div
    class="flex flex-wrap items-center gap-2 max-[640px]:flex-col max-[640px]:items-stretch"
  >
    <input
      class="field-input flex-1 basis-55"
      type="text"
      placeholder="Search name, P/N, or barcode…"
      :value="modelValue.search"
      @input="update('search', ($event.target as HTMLInputElement).value)"
    />

    <select
      class="field-input"
      :value="modelValue.category || ''"
      @change="update('category', ($event.target as HTMLSelectElement).value)"
    >
      <option value="">All categories</option>
      <option v-for="cat in categories" :key="cat" :value="cat">
        {{ cat }}
      </option>
    </select>

    <select
      class="field-input"
      :value="modelValue.program || ''"
      @change="update('program', ($event.target as HTMLSelectElement).value)"
    >
      <option value="">All programs</option>
      <option v-for="prog in programs" :key="prog" :value="prog">
        {{ prog }}
      </option>
    </select>

    <select
      class="field-input"
      :value="modelValue.size || ''"
      @change="
        update('size', ($event.target as HTMLSelectElement).value as any)
      "
    >
      <option value="">All sizes</option>
      <option value="small">Small</option>
      <option value="big">Big</option>
      <option value="xl">XL</option>
    </select>

    <select
      class="field-input w-35 max-[640px]:w-full"
      :value="modelValue.shelf_position || ''"
      @change="
        update('shelf_position', ($event.target as HTMLSelectElement).value)
      "
    >
      <option value="" default>All shelves</option>
      <option v-for="shelf in shelves" :key="shelf" :value="shelf">
        {{ shelf }}
      </option>
    </select>

    <div class="flex items-center gap-1.5">
      <input
        class="field-input no-spinner w-30"
        type="number"
        min="0"
        placeholder="Min qty"
        :value="modelValue.min_qty ?? ''"
        @input="
          update(
            'min_qty',
            ($event.target as HTMLInputElement).value === ''
              ? undefined
              : Number(($event.target as HTMLInputElement).value),
          )
        "
      />
      <span class="text-sm text-muted">–</span>
      <input
        class="field-input no-spinner w-30"
        type="number"
        min="0"
        placeholder="Max qty"
        :value="modelValue.max_qty ?? ''"
        @input="
          update(
            'max_qty',
            ($event.target as HTMLInputElement).value === ''
              ? undefined
              : Number(($event.target as HTMLInputElement).value),
          )
        "
      />
    </div>

    <button class="btn btn--ghost btn--small" @click="reset">Clear</button>
  </div>
</template>

<script setup lang="ts">
import type { ItemFilters } from "~/composables/useWarehouseApi";

const props = defineProps<{
  modelValue: ItemFilters;
  categories: string[];
  programs: string[];
  shelves: string[];
}>();

const emit = defineEmits<{
  "update:modelValue": [ItemFilters];
}>();

function update<K extends keyof ItemFilters>(key: K, value: ItemFilters[K]) {
  emit("update:modelValue", { ...props.modelValue, [key]: value });
}

function reset() {
  emit("update:modelValue", {});
}
</script>
