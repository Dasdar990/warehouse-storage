// composables/useToast.ts
export type ToastType = "success" | "error" | "info";

export interface ToastItem {
  id: number;
  type: ToastType;
  message: string;
  duration: number;
  startedAt: number;
  remaining: number;
}

// Gli errori restano un po' più a lungo -- di solito c'è più da leggere.
const DEFAULT_DURATION: Record<ToastType, number> = {
  success: 3500,
  info: 4000,
  error: 6000,
};

let nextId = 0;

export function useToast() {
  const toasts = useState<ToastItem[]>("warehouse-toasts", () => []);
  const timers = useState<Map<number, ReturnType<typeof setTimeout>>>(
    "warehouse-toast-timers",
    () => new Map(),
  );

  function scheduleDismiss(id: number, delay: number) {
    timers.value.set(
      id,
      setTimeout(() => dismiss(id), delay),
    );
  }

  function show(type: ToastType, message: string, duration?: number) {
    const id = ++nextId;
    const finalDuration = duration ?? DEFAULT_DURATION[type];
    toasts.value = [
      ...toasts.value,
      {
        id,
        type,
        message,
        duration: finalDuration,
        startedAt: Date.now(),
        remaining: finalDuration,
      },
    ];
    scheduleDismiss(id, finalDuration);
    return id;
  }

  function dismiss(id: number) {
    toasts.value = toasts.value.filter((t) => t.id !== id);
    const timer = timers.value.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.value.delete(id);
    }
  }

  function pause(id: number) {
    const toast = toasts.value.find((t) => t.id === id);
    const timer = timers.value.get(id);
    if (!toast || !timer) return;
    clearTimeout(timer);
    timers.value.delete(id);
    toast.remaining = Math.max(
      toast.remaining - (Date.now() - toast.startedAt),
      0,
    );
  }

  function resume(id: number) {
    const toast = toasts.value.find((t) => t.id === id);
    if (!toast || timers.value.has(id)) return;
    toast.startedAt = Date.now();
    scheduleDismiss(id, Math.max(toast.remaining, 300));
  }

  return { toasts, show, dismiss, pause, resume };
}
