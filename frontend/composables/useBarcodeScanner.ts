/**
 * Distinguishes a barcode-reader keystroke burst from normal manual typing
 * on the *same* input field, without needing a separate hidden input.
 *
 * Barcode readers behave like a very fast keyboard: they emit every
 * character of the code in a few milliseconds and finish with an Enter
 * keypress. A human typing on a keyboard is orders of magnitude slower
 * between keystrokes. So: track the time-gap between keystrokes, and if
 * the whole string leading up to Enter was typed faster than
 * `maxIntervalMs` per character on average, treat it as a scan.
 *
 * Usage:
 *   const { onKeydown, onEnter } = useBarcodeScanner({
 *     onScan: (value) => { ... },   // fast burst + Enter
 *     onManualSubmit: (value) => { ... }, // slow typing + Enter
 *   })
 *   <input @keydown="onKeydown" @keyup.enter="onEnter($event, inputValue)" />
 */
export interface UseBarcodeScannerOptions {
  /** Average ms/char below which a burst is classified as a scanner read. Default 35ms. */
  maxIntervalMs?: number;
  /** Minimum characters required before we even consider it a "scan" (avoids false positives on 1-2 char bursts). */
  minScanLength?: number;
  onScan?: (value: string) => void;
  onManualSubmit?: (value: string) => void;
}

export function useBarcodeScanner(options: UseBarcodeScannerOptions = {}) {
  const maxIntervalMs =
    options.minScanLength !== undefined
      ? (options.maxIntervalMs ?? 35)
      : (options.maxIntervalMs ?? 35);
  const minScanLength = options.minScanLength ?? 4;

  let firstKeyTime = 0;
  let lastKeyTime = 0;
  let keyCount = 0;

  /** Wire to @keydown on the input to sample keystroke timing. */
  function onKeydown(event: KeyboardEvent) {
    // Defensive: a real KeyboardEvent always has a string `.key` (even ''
    // for an unidentified key), but some browser extensions (password
    // managers, autofill) and synthetic/automation-driven events can fire
    // a keydown listener with an incomplete event object. Ignore anything
    // that doesn't look like a real keystroke rather than crashing on it.
    if (typeof event?.key !== "string") return;

    // Ignore modifier/navigation keys so they don't skew timing.
    if (
      event.key.length > 1 &&
      event.key !== "Enter" &&
      event.key !== "Backspace"
    )
      return;

    const now = performance.now();
    if (keyCount === 0) {
      firstKeyTime = now;
    }
    lastKeyTime = now;
    keyCount += 1;
  }

  /** Wire to @keyup.enter; classifies and fires the right callback, then resets. */
  function onEnter(_event: KeyboardEvent, value: string) {
    const trimmed = value.trim();
    if (!trimmed) {
      resetTiming();
      return;
    }

    const elapsed = lastKeyTime - firstKeyTime;
    const avgIntervalMs = keyCount > 1 ? elapsed / (keyCount - 1) : Infinity;
    const looksLikeScan =
      trimmed.length >= minScanLength && avgIntervalMs <= maxIntervalMs;

    if (looksLikeScan) {
      options.onScan?.(trimmed);
    } else {
      options.onManualSubmit?.(trimmed);
    }
    resetTiming();
  }

  function resetTiming() {
    firstKeyTime = 0;
    lastKeyTime = 0;
    keyCount = 0;
  }

  /**
   * Non-destructive peek at the burst captured so far (does not reset
   * state). Useful to preempt a keydown's own default action -- e.g. a
   * form's implicit "Enter submits" behavior -- *before* that Enter
   * keystroke's default action runs, which happens too early for
   * `onEnter` (fired on keyup) to intervene.
   */
  function looksLikeScan(): boolean {
    const elapsed = lastKeyTime - firstKeyTime;
    const avgIntervalMs = keyCount > 1 ? elapsed / (keyCount - 1) : Infinity;
    return keyCount >= minScanLength && avgIntervalMs <= maxIntervalMs;
  }

  return { onKeydown, onEnter, resetTiming, looksLikeScan };
}
