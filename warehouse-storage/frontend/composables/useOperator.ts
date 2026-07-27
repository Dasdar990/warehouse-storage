/**
 * Shared "who is currently operating this terminal" name, used to tag
 * every movement in the audit log. Kept in useState (not persisted to
 * storage) so it survives page navigation within the app but resets on
 * reload -- appropriate for a shared warehouse terminal where the
 * next shift should re-identify themselves.
 */
export function useOperator() {
  const operator = useState<string>('warehouse-operator', () => 'Operator')

  function setOperator(name: string) {
    const trimmed = name.trim()
    operator.value = trimmed || 'Operator'
  }

  return { operator, setOperator }
}
