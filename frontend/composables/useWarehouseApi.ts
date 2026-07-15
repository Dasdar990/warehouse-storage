export type ItemSize = 'small' | 'big' | 'xl'

export interface Item {
  id: number
  name: string
  pn: string
  barcode: string
  category: string
  size: ItemSize
  shelf_position: string
  quantity: number
}

export interface ShelfSummary {
  shelf_position: string
  shelf_number: number
  level: string
  item_count: number
  total_quantity: number
  categories: string[]
  has_low_stock: boolean
}

export interface Zone {
  id: number
  name: string
  color: string
  x: number
  y: number
  width: number
  height: number
}

export type ZoneInput = Omit<Zone, 'id'>

export interface ShelfNode {
  rack_code: string
  label: string | null
  x: number
  y: number
  width: number
  height: number
  levels: string[]
  zone_id: number | null
  /** Degrees, matching how the rack is physically oriented in the room. */
  rotation: number
}

export interface ShelfNodeOut extends ShelfNode {
  id: number
}

export interface ShelfMapNode extends ShelfNode {
  item_count: number
  total_quantity: number
  categories: string[]
  has_low_stock: boolean
}

export interface WarehouseLayout {
  shelf_numbers: number[]
  levels: string[]
  low_stock_threshold: number
  shelves: ShelfSummary[]
  has_custom_layout: boolean
  nodes: ShelfMapNode[]
  zones: Zone[]
}

export interface ShelfItemsResponse {
  shelf_position: string
  items: Item[]
}

export interface MensolaSummary {
  shelf_position: string
  level: string
  item_count: number
  total_quantity: number
  categories: string[]
  has_low_stock: boolean
}

export interface RackLevelsResponse {
  rack_code: string
  label: string | null
  levels: MensolaSummary[]
}

export interface ItemFilters {
  search?: string
  category?: string
  size?: ItemSize | ''
  shelf_position?: string
  low_stock?: boolean
}

export interface WithdrawResult {
  item: Item
  withdrawn: number
  message: string
}

/**
 * Central place for every call to the FastAPI backend. Keeps the
 * `apiBase` + endpoint paths out of individual pages/components.
 */
export function useWarehouseApi() {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase as string

  function listItems(filters: ItemFilters = {}) {
    const params: Record<string, string | boolean> = {}
    if (filters.search) params.search = filters.search
    if (filters.category) params.category = filters.category
    if (filters.size) params.size = filters.size
    if (filters.shelf_position) params.shelf_position = filters.shelf_position
    if (filters.low_stock) params.low_stock = true
    return $fetch<Item[]>(`${apiBase}/items`, { params })
  }

  function listCategories() {
    return $fetch<string[]>(`${apiBase}/items/categories`)
  }

  function scanItem(barcode: string) {
    return $fetch<Item>(`${apiBase}/items/scan`, { params: { barcode } })
  }

  function createItem(payload: Omit<Item, 'id'>) {
    return $fetch<Item>(`${apiBase}/items`, { method: 'POST', body: payload })
  }

  function withdrawItem(barcode: string, quantity: number) {
    return $fetch<WithdrawResult>(`${apiBase}/items/withdraw`, {
      method: 'POST',
      body: { barcode, quantity },
    })
  }

  function labelUrl(id: number) {
    return `${apiBase}/items/label/${id}`
  }

  function getWarehouseLayout() {
    return $fetch<WarehouseLayout>(`${apiBase}/shelves`)
  }

  function getRackLevels(rackCode: string) {
    return $fetch<RackLevelsResponse>(`${apiBase}/shelves/${encodeURIComponent(rackCode)}/levels`)
  }

  function getShelfItems(shelfPosition: string) {
    return $fetch<ShelfItemsResponse>(`${apiBase}/shelves/${encodeURIComponent(shelfPosition)}/items`)
  }

  function getShelfConfig() {
    return $fetch<ShelfNodeOut[]>(`${apiBase}/shelves/config`)
  }

  function saveShelfConfig(nodes: ShelfNode[]) {
    return $fetch<ShelfNodeOut[]>(`${apiBase}/shelves/config`, {
      method: 'PUT',
      body: { nodes },
    })
  }

  function getZones() {
    return $fetch<Zone[]>(`${apiBase}/zones`)
  }

  function saveZones(zones: ZoneInput[]) {
    return $fetch<Zone[]>(`${apiBase}/zones`, {
      method: 'PUT',
      body: { zones },
    })
  }

  return {
    apiBase,
    listItems,
    listCategories,
    scanItem,
    createItem,
    withdrawItem,
    labelUrl,
    getWarehouseLayout,
    getRackLevels,
    getShelfItems,
    getShelfConfig,
    saveShelfConfig,
    getZones,
    saveZones,
  }
}
