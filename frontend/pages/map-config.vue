<template>
  <div class="flex flex-col gap-4">
    <section>
      <h2 class="mb-1.5 text-[1.15rem]">Configure Warehouse Map</h2>
      <p class="m-0 max-w-[78ch] text-sm text-muted">
        Design the physical warehouse layout on a single canvas: sketch the
        room's walls and door for orientation, delimit zones, and place racks
        inside them. Each rack gets a numeric code and one or more levels
        (e.g. "A,B,C"). The rack code + level must match the shelf codes used
        on items (e.g. rack "12" + level "B" → item shelf "12B").
      </p>
    </section>

    <section class="card flex flex-col gap-4">
      <div class="flex flex-wrap items-center gap-3">
        <button
          class="btn btn--confirm text-[#06280f] disabled:cursor-not-allowed disabled:opacity-60"
          type="button"
          :disabled="saving"
          @click="save"
        >
          {{ saving ? "Saving…" : "Save layout" }}
        </button>
        <span v-if="dirty" class="text-[0.8rem] font-semibold text-warn">Unsaved changes</span>
      </div>

      <p v-if="loading" class="text-muted">Loading saved layout…</p>
      <MapEditor
        v-else
        :zones="zones"
        :nodes="nodes"
        :walls="walls"
        :doors="doors"
        :zone-ids="savedZoneIds"
        @update:zones="onChange('zones', $event)"
        @update:nodes="onChange('nodes', $event)"
        @update:walls="onChange('walls', $event)"
        @update:doors="onChange('doors', $event)"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import type { DoorInput, ShelfNode, WallInput, ZoneInput } from "~/composables/useWarehouseApi";

const {
  getShelfConfig,
  saveShelfConfig,
  getZones,
  saveZones,
  getRoomLayout,
  saveRoomLayout,
} = useWarehouseApi();
const { show } = useToast();

const zones = ref<ZoneInput[]>([]);
const nodes = ref<ShelfNode[]>([]);
const walls = ref<WallInput[]>([]);
const doors = ref<DoorInput[]>([]);
const loading = ref(false);
const saving = ref(false);
const dirty = ref(false);

// Zones need real IDs on the rack editor (to populate the zone dropdown and
// to validate zone_id references), so we keep the last-saved zone IDs around
// separately from the in-progress `zones` array being edited.
const savedZoneIds = ref<number[]>([]);

async function load() {
  loading.value = true;
  try {
    const [zoneConfig, shelfConfig, room] = await Promise.all([
      getZones(),
      getShelfConfig(),
      getRoomLayout(),
    ]);
    zones.value = zoneConfig.map(({ id, ...rest }) => rest);
    savedZoneIds.value = zoneConfig.map((z) => z.id);
    nodes.value = shelfConfig.map(({ id, ...rest }) => rest);
    walls.value = room.walls.map(({ id, ...rest }) => rest);
    doors.value = room.doors.map(({ id, ...rest }) => rest);
    dirty.value = false;
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to load the saved layout");
  } finally {
    loading.value = false;
  }
}

function onChange(kind: "zones" | "nodes" | "walls" | "doors", value: any) {
  if (kind === "zones") zones.value = value;
  else if (kind === "nodes") nodes.value = value;
  else if (kind === "walls") walls.value = value;
  else doors.value = value;
  dirty.value = true;
}

function validate(): string | null {
  const zoneNames = zones.value.map((z) => z.name.trim());
  if (zoneNames.some((n) => !n)) return "Every zone needs a name before saving.";

  const codes = nodes.value.map((n) => n.rack_code.trim());
  if (codes.some((n) => !n))
    return 'Every rack needs a numeric code before saving (e.g. "12").';
  const seen = new Set<string>();
  for (const n of codes) {
    if (seen.has(n.toUpperCase())) return `Rack code "${n}" is used more than once.`;
    seen.add(n.toUpperCase());
  }
  if (nodes.value.some((n) => !n.levels.length)) return "Every rack needs at least one level.";
  return null;
}

async function save() {
  const error = validate();
  if (error) {
    show("error", error);
    return;
  }
  saving.value = true;
  try {
    // Room outline first: purely visual, no id remapping needed elsewhere.
    const savedRoom = await saveRoomLayout({ walls: walls.value, doors: doors.value });
    walls.value = savedRoom.walls.map(({ id, ...rest }) => rest);
    doors.value = savedRoom.doors.map(({ id, ...rest }) => rest);

    // Zones next, so freshly-created zones get real IDs the rack editor
    // (and the saved rack.zone_id values) can reference.
    const savedZones = await saveZones(zones.value);
    zones.value = savedZones.map(({ id, ...rest }) => rest);
    savedZoneIds.value = savedZones.map((z) => z.id);

    // Remap any placeholder (negative) zone_id on the racks to the real,
    // just-saved zone id at the same index, then persist the racks.
    const remapped = nodes.value.map((n) => {
      if (n.zone_id != null && n.zone_id < 0) {
        const idx = -n.zone_id - 1;
        return { ...n, zone_id: savedZoneIds.value[idx] ?? null };
      }
      return n;
    });
    const savedNodes = await saveShelfConfig(remapped);
    nodes.value = savedNodes.map(({ id, ...rest }) => rest);

    dirty.value = false;
    show("success", "Warehouse map saved");
  } catch (err: any) {
    show("error", err?.data?.detail || "Failed to save the layout");
  } finally {
    saving.value = false;
  }
}

onMounted(load);
</script>
