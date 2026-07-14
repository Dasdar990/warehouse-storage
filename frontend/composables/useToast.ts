export interface ToastState {
  type: 'success' | 'error'
  message: string
}

/**
 * Tiny global toast system built on Nuxt's useState, so any page or
 * component can trigger a success/error banner without prop drilling.
 * The banner itself is rendered once in layouts/default.vue.
 */
export function useToast() {
  const toast = useState<ToastState | null>('warehouse-toast', () => null)
  const timer = useState<ReturnType<typeof setTimeout> | null>('warehouse-toast-timer', () => null)

  function show(type: ToastState['type'], message: string) {
    toast.value = { type, message }
    if (timer.value) clearTimeout(timer.value)
    timer.value = setTimeout(() => {
      toast.value = null
    }, 4000)
  }

  function dismiss() {
    toast.value = null
  }

  return { toast, show, dismiss }
}
