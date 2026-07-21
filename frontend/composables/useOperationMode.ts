export type OperationMode = 'deposit' | 'withdraw'

/**
 * Shared "DEPOSIT (+1) / WITHDRAW (-1)" toggle. Drives which action fires
 * automatically when a barcode is scanned in the UnifiedSearchBar, and
 * pre-highlights the matching quick-action button in ItemDetailCard.
 */
export function useOperationMode() {
  const mode = useState<OperationMode>('warehouse-operation-mode', () => 'withdraw')

  function setMode(next: OperationMode) {
    mode.value = next
  }

  function toggle() {
    mode.value = mode.value === 'deposit' ? 'withdraw' : 'deposit'
  }

  return { mode, setMode, toggle }
}
