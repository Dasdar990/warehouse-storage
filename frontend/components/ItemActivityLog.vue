<template>
  <div>
    <p v-if="loading" class="py-3 text-[0.85rem] text-muted">Loading…</p>
    <p v-else-if="!history.length" class="py-3 text-[0.85rem] text-muted">
      No movements recorded yet for this item.
    </p>
    <ul v-else class="m-0 flex flex-col gap-1.5 p-0">
      <li
        v-for="h in history"
        :key="h.id"
        class="flex flex-wrap items-center justify-between gap-1.5 rounded-lg bg-surface-2 px-2.5 py-1.5 text-[0.8rem]"
        :class="{ 'opacity-45': h.voided }"
      >
        <span class="flex flex-wrap items-center gap-1.5 cursor-default">
          <template v-if="h.action === 'move'">
            <strong class="text-accent">Moved</strong>
            <span class="text-muted">
              {{ h.from_shelf_position }} → {{ h.shelf_position }}</span
            >
          </template>
          <template v-else>
            <strong
              :class="
                h.action === 'deposit'
                  ? 'text-green-300'
                  : h.action === 'withdraw'
                    ? 'text-red-300'
                    : 'text-ink'
              "
            >
              {{
                h.action === "edit"
                  ? getMovementActionLabel(h.action)
                  : `${h.action === "deposit" ? "+" : "−"}${h.quantity}`
              }}
            </strong>
          </template>
          <span class="text-muted"> by </span>
          <span class="text-ink">{{ h.operator }}</span>
          <span v-if="h.voided" class="text-muted"> (rolled back)</span>
        </span>
        <span class="whitespace-nowrap text-[0.72rem] text-muted">{{
          formatHistoryTime(h.timestamp)
        }}</span>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import type { Movement } from "~/composables/useWarehouseApi";
import { getMovementActionLabel } from "~/utils/movementActions";

const props = defineProps<{ itemId: number }>();

const { listMovements } = useWarehouseApi();

const history = ref<Movement[]>([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    history.value = await listMovements(25, { item_id: props.itemId });
  } catch {
    history.value = [];
  } finally {
    loading.value = false;
  }
}

watch(() => props.itemId, load, { immediate: true });

function formatHistoryTime(iso: string) {
  const d = new Date(iso);
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const time = d.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  });
  return `${day}/${month} ${time}`;
}
</script>
