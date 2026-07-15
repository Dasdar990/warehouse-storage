<script setup lang="ts">
import type { ShelfNode, ZoneInput } from '~/composables/useWarehouseApi'

const { getShelfConfig, saveShelfConfig, getZones, saveZones, getWarehouseLayout } = useWarehouseApi()
const { show } = useToast()

const tab = ref<'zones' | 'racks'>('zones')

const zones = ref<ZoneInput[]>([])
const nodes = ref<ShelfNode[]>([])
const loading = ref(false)
const saving = ref(false)
const dirty = ref(false)

// Zones need real IDs on the racks editor (to populate the zone dropdown
// and to validate zone_id references), so we keep the last-saved zone IDs
// around separately from the in-progress `zones` array being edited.
const savedZoneIds = ref<number[]>([])
const zonesForRackEditor = computed(() =>
  zones.value.map((z, i) => ({ ...z, id: savedZoneIds.value[i] ?? -(i + 1) }))
)

async function load() {
  loading.value = true
  try {
    const [zoneConfig, shelfConfig] = await Promise.all([getZones(), getShelfConfig()])
    zones.value = zoneConfig.map(({ id, ...rest }) => rest)
    savedZoneIds.value = zoneConfig.map((z) => z.id)
    nodes.value = shelfConfig.map(({ id, ...rest }) => rest)
    dirty.value = false
  } catch (err: any) {
    show('error', err?.data?.detail || 'Failed to load the saved layout')
  } finally {
    loading.value = false
  }
}

function onZonesChange(next: ZoneInput[]) {
  zones.value = next
  dirty.value = true
}

function onNodesChange(next: ShelfNode[]) {
  nodes.value = next
  dirty.value = true
}

function validate(): string | null {
  const zoneNames = zones.value.map((z) => z.name.trim())
  if (zoneNames.some((n) => !n)) return 'Every zone needs a name before saving.'

  const codes = nodes.value.map((n) => n.rack_code.trim())
  if (codes.some((n) => !n)) return 'Every rack needs a numeric code before saving (e.g. "12").'
  const seen = new Set<string>()
  for (const n of codes) {
    if (seen.has(n.toUpperCase())) return `Rack code "${n}" is used more than once.`
    seen.add(n.toUpperCase())
  }
  if (nodes.value.some((n) => !n.levels.length)) return 'Every rack needs at least one level (mensola).'
  return null
}

async function save() {
  const error = validate()
  if (error) {
    show('error', error)
    return
  }
  saving.value = true
  try {
    // Zones first, so freshly-created zones get real IDs the rack editor
    // (and the saved rack.zone_id values) can reference.
    const savedZones = await saveZones(zones.value)
    zones.value = savedZones.map(({ id, ...rest }) => rest)
    savedZoneIds.value = savedZones.map((z) => z.id)

    // Remap any placeholder (negative) zone_id on the racks to the real,
    // just-saved zone id at the same index, then persist the racks.
    const remapped = nodes.value.map((n) => {
      if (n.zone_id != null && n.zone_id < 0) {
        const idx = -n.zone_id - 1
        return { ...n, zone_id: savedZoneIds.value[idx] ?? null }
      }
      return n
    })
    const savedNodes = await saveShelfConfig(remapped)
    nodes.value = savedNodes.map(({ id, ...rest }) => rest)

    dirty.value = false
    show('success', 'Warehouse map saved')
  } catch (err: any) {
    show('error', err?.data?.detail || 'Failed to save the layout')
  } finally {
    saving.value = false
  }
}

async function generateFromStock() {
  if (nodes.value.length && !confirm('This adds a rack for every shelf number currently used by an item, grouping levels together. Continue?')) {
    return
  }
  try {
    const layout = await getWarehouseLayout()
    const byRack = new Map<string, Set<string>>()
    for (const shelf of layout.shelves) {
      if (!byRack.has(String(shelf.shelf_number))) byRack.set(String(shelf.shelf_number), new Set())
      byRack.get(String(shelf.shelf_number))!.add(shelf.level)
    }

    const existing = new Set(nodes.value.map((n) => n.rack_code))
    const perRow = 8
    let index = nodes.value.length
    const additions: ShelfNode[] = []
    for (const [rackCode, levelSet] of byRack) {
      if (existing.has(rackCode)) continue
      const col = index % perRow
      const row = Math.floor(index / perRow)
      additions.push({
        rack_code: rackCode,
        label: null,
        x: 24 + col * 130,
        y: 24 + row * 170,
        width: 90,
        height: 140,
        levels: Array.from(levelSet).sort(),
        zone_id: null,
        rotation: 0,
      })
      existing.add(rackCode)
      index += 1
    }
    // Reassign (not push) so the editor's prop-change watcher picks it up.
    nodes.value = [...nodes.value, ...additions]
    dirty.value = true
    show('success', `Added ${additions.length} rack(s) from existing stock`)
  } catch (err: any) {
    show('error', err?.data?.detail || 'Failed to read existing shelf positions')
  }
}

onMounted(load)
</script>

<template>
  <div class="config-page">
    <section class="intro">
      <h2>Configure Warehouse Map</h2>
      <p>
        Design the physical warehouse layout: first delimit zones, then place racks ("scaffali") inside them.
        Each rack gets a numeric code and one or more levels ("mensole", e.g. "A,B,C"). The rack code + level
        must match the shelf codes used on items (e.g. rack "12" + level "B" → item shelf "12B").
      </p>
    </section>

    <section class="config-panel">
      <div class="config-panel__actions">
        <div class="tabs">
          <button class="tab" :class="{ 'tab--active': tab === 'zones' }" type="button" @click="tab = 'zones'">
            1. Zone ({{ zones.length }})
          </button>
          <button class="tab" :class="{ 'tab--active': tab === 'racks' }" type="button" @click="tab = 'racks'">
            2. Scaffali ({{ nodes.length }})
          </button>
        </div>
        <button class="btn btn--confirm" type="button" :disabled="saving" @click="save">
          {{ saving ? 'Saving…' : 'Save layout' }}
        </button>
        <button v-if="tab === 'racks'" class="btn btn--ghost" type="button" @click="generateFromStock">
          Generate from existing stock
        </button>
        <span v-if="dirty" class="dirty-flag">Unsaved changes</span>
      </div>

      <p v-if="loading" class="loading">Loading saved layout…</p>
      <template v-else>
        <ZoneMapEditor v-show="tab === 'zones'" :model-value="zones" @update:model-value="onZonesChange" />
        <ShelfMapEditor
          v-show="tab === 'racks'"
          :model-value="nodes"
          :zones="zonesForRackEditor"
          @update:model-value="onNodesChange"
        />
      </template>
    </section>
  </div>
</template>

<style scoped>
.config-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.intro h2 {
  font-size: 1.15rem;
  margin-bottom: 6px;
}

.intro p {
  color: var(--text-dim);
  margin: 0;
  font-size: 0.9rem;
  max-width: 78ch;
}

.config-panel {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.config-panel__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.tabs {
  display: flex;
  gap: 4px;
  background: var(--bg-elevated-2);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 3px;
}

.tab {
  cursor: pointer;
  border: none;
  background: transparent;
  color: var(--text-dim);
  padding: 7px 12px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.8rem;
}

.tab--active {
  background: var(--accent-dim);
  color: #dbeafe;
}

.dirty-flag {
  color: var(--amber);
  font-size: 0.8rem;
  font-weight: 600;
}

.btn {
  cursor: pointer;
  border: none;
  border-radius: 8px;
  padding: 10px 18px;
  font-weight: 600;
  font-size: 0.9rem;
}

.btn--confirm {
  background: var(--green);
  color: #06280f;
}

.btn--ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading {
  color: var(--text-dim);
}
</style>
