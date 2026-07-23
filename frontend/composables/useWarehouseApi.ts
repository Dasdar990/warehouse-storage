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

export interface Wall {
  id: number
  x: number
  y: number
  width: number
  height: number
  rotation: number
}

export type WallInput = Omit<Wall, 'id'>

export interface Door {
  id: number
  x: number
  y: number
  width: number
  /** Degrees, matching how the door opening is physically oriented in the room. */
  rotation: number
}

export type DoorInput = Omit<Door, 'id'>

export interface RoomLayout {
  walls: Wall[]
  doors: Door[]
}

export interface RoomLayoutInput {
  walls: WallInput[]
  doors: DoorInput[]
}

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
  walls: Wall[]
  doors: Door[]
}

export interface ShelfItemsResponse {
  shelf_position: string
  items: Item[]
}

export interface LevelSummary {
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
  levels: LevelSummary[]
}

export interface Category {
  id: number
  name: string
}

export interface ShelfPositionOption {
  value: string
  label: string
}

export interface BarcodeSuggestion {
  barcode: string
}

export interface ItemFilters {
  search?: string
  category?: string
  size?: ItemSize | ''
  shelf_position?: string
  low_stock?: boolean
}

export type MovementAction = 'withdraw' | 'deposit'
export type MovementSource = 'barcode' | 'manual'

export interface StockMoveResult {
  item: Item
  moved: number
  action: MovementAction
  message: string
}

export interface StockMoveInput {
  barcode: string
  quantity: number
  source: MovementSource
}

export interface Movement {
  id: number
  timestamp: string
  item_id: number | null
  item_name: string
  pn: string
  shelf_position: string
  action: MovementAction
  quantity: number
  balance_after: number
  source: MovementSource
  operator: string
  voided: boolean
  reversal_of_id: number | null
}

export type UserRole = 'admin' | 'operator'

export interface AppUser {
  id: number
  username: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface UserCreateInput {
  username: string
  full_name: string
  password: string
  role: UserRole
}

export interface UserUpdateInput {
  full_name?: string
  password?: string
  role?: UserRole
  is_active?: boolean
}

/**
 * Central place for every call to the FastAPI backend. Keeps the
 * `apiBase` + endpoint paths out of individual pages/components, and
 * makes sure every request carries the logged-in user's Bearer token
 * (a 401 anywhere logs the session out, since it means the token expired
 * or was revoked).
 */
export function useWarehouseApi() {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase as string
  const { token, logout } = useAuth()

  async function apiFetch<T>(path: string, options: Record<string, any> = {}): Promise<T> {
    try {
      return await $fetch<T>(`${apiBase}${path}`, {
        ...options,
        headers: {
          ...(options.headers || {}),
          ...(token.value ? { Authorization: `Bearer ${token.value}` } : {}),
        },
      })
    } catch (err: any) {
      if (err?.response?.status === 401) {
        logout()
        navigateTo('/login')
      }
      throw err
    }
  }

  function listItems(filters: ItemFilters = {}) {
    const params: Record<string, string | boolean> = {}
    if (filters.search) params.search = filters.search
    if (filters.category) params.category = filters.category
    if (filters.size) params.size = filters.size
    if (filters.shelf_position) params.shelf_position = filters.shelf_position
    if (filters.low_stock) params.low_stock = true
    return apiFetch<Item[]>('/items', { params })
  }

  function listCategories() {
    return apiFetch<string[]>('/items/categories')
  }

  function scanItem(barcode: string) {
    return apiFetch<Item>('/items/scan', { params: { barcode } })
  }

  function createItem(payload: Omit<Item, 'id'>) {
    return apiFetch<Item>('/items', { method: 'POST', body: payload })
  }

  /** Existing items that look like duplicates of a candidate name/PN (used by the New Item form). */
  function checkDuplicateItems(candidate: { name?: string; pn?: string }) {
    const params: Record<string, string> = {}
    if (candidate.name) params.name = candidate.name
    if (candidate.pn) params.pn = candidate.pn
    return apiFetch<Item[]>('/items/check-duplicate', { params })
  }

  function generateBarcode() {
    return apiFetch<BarcodeSuggestion>('/items/barcode/next')
  }

  /** Admin-managed category catalog (distinct from `listCategories`, which only reflects categories already in use). */
  function listAdminCategories() {
    return apiFetch<Category[]>('/categories')
  }

  function createCategory(name: string) {
    return apiFetch<Category>('/categories', { method: 'POST', body: { name } })
  }

  function deleteCategory(id: number) {
    return apiFetch<void>(`/categories/${id}`, { method: 'DELETE' })
  }

  /** Selectable shelf positions (rack + level) for the item form's dropdown. */
  function getShelfPositions() {
    return apiFetch<ShelfPositionOption[]>('/shelves/positions')
  }

  function withdrawItem(payload: StockMoveInput) {
    return apiFetch<StockMoveResult>('/items/withdraw', { method: 'POST', body: payload })
  }

  function depositItem(payload: StockMoveInput) {
    return apiFetch<StockMoveResult>('/items/deposit', { method: 'POST', body: payload })
  }

  function listMovements(limit = 50, filters: { operator?: string; item_id?: number } = {}) {
    return apiFetch<Movement[]>('/movements', {
      params: { limit, ...filters },
    })
  }

  /** Admin-only: undo a past movement (see backend for the compensating-entry logic). */
  function rollbackMovement(movementId: number) {
    return apiFetch<{ item: Item; reversal: Movement; message: string }>(
      `/movements/${movementId}/rollback`,
      { method: 'POST' },
    )
  }


  function labelUrl(id: number) {
    // GET, HTML wrapper that auto-prints the freshly regenerated label and
    // closes itself -- safe to use directly as an <a href target="_blank">.
    // The token travels as a query param (not a header) because this link
    // opens as a plain browser navigation, which can't attach one.
    const qs = token.value ? `?token=${encodeURIComponent(token.value)}` : ''
    return `${apiBase}/items/${id}/label${qs}`
  }

  function getWarehouseLayout() {
    return apiFetch<WarehouseLayout>('/shelves')
  }

  function getRackLevels(rackCode: string) {
    return apiFetch<RackLevelsResponse>(`/shelves/${encodeURIComponent(rackCode)}/levels`)
  }

  function getShelfItems(shelfPosition: string) {
    return apiFetch<ShelfItemsResponse>(`/shelves/${encodeURIComponent(shelfPosition)}/items`)
  }

  function getShelfConfig() {
    return apiFetch<ShelfNodeOut[]>('/shelves/config')
  }

  function saveShelfConfig(nodes: ShelfNode[]) {
    return apiFetch<ShelfNodeOut[]>('/shelves/config', { method: 'PUT', body: { nodes } })
  }

  function getZones() {
    return apiFetch<Zone[]>('/zones')
  }

  function saveZones(zones: ZoneInput[]) {
    return apiFetch<Zone[]>('/zones', { method: 'PUT', body: { zones } })
  }

  function getRoomLayout() {
    return apiFetch<RoomLayout>('/room-layout')
  }

  function saveRoomLayout(layout: RoomLayoutInput) {
    return apiFetch<RoomLayout>('/room-layout', { method: 'PUT', body: layout })
  }

  /** Admin-only: user management (login accounts + audit-log attribution). */
  function listUsers() {
    return apiFetch<AppUser[]>('/users')
  }

  function createUser(payload: UserCreateInput) {
    return apiFetch<AppUser>('/users', { method: 'POST', body: payload })
  }

  function updateUser(id: number, payload: UserUpdateInput) {
    return apiFetch<AppUser>(`/users/${id}`, { method: 'PATCH', body: payload })
  }

  function deleteUser(id: number) {
    return apiFetch<void>(`/users/${id}`, { method: 'DELETE' })
  }

  return {
    apiBase,
    listItems,
    listCategories,
    scanItem,
    createItem,
    checkDuplicateItems,
    generateBarcode,
    listAdminCategories,
    createCategory,
    deleteCategory,
    getShelfPositions,
    withdrawItem,
    depositItem,
    listMovements,
    rollbackMovement,
    labelUrl,
    getWarehouseLayout,
    getRackLevels,
    getShelfItems,
    getShelfConfig,
    saveShelfConfig,
    getZones,
    saveZones,
    getRoomLayout,
    saveRoomLayout,
    listUsers,
    createUser,
    updateUser,
    deleteUser,
  }
}
