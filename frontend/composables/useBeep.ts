/**
 * Short audio feedback for hardware scan events (NFC badge tap, barcode
 * scan) -- a high-pitched beep on success, a low one on failure, so the
 * operator gets confirmation without having to look at the screen.
 *
 * A fresh AudioContext is created per call rather than kept around: this
 * is only called a few times a minute at most, and browsers require the
 * context to be created/resumed from a user gesture anyway (a badge tap
 * or keyboard-wedge scan both count).
 */
export function useBeep() {
  function playBeep(success = true) {
    if (!import.meta.client) return;
    const AudioContextCtor =
      window.AudioContext ||
      (window as any).webkitAudioContext;
    if (!AudioContextCtor) return;

    try {
      const audioCtx = new AudioContextCtor();
      const oscillator = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();
      oscillator.connect(gainNode);
      gainNode.connect(audioCtx.destination);
      oscillator.frequency.value = success ? 880 : 300;
      oscillator.type = "sine";
      const now = audioCtx.currentTime;
      gainNode.gain.setValueAtTime(0.1, now);
      gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
      oscillator.start(now);
      oscillator.stop(now + 0.15);
      // Release the context once the tone is done playing -- nothing else
      // uses it, and leaving contexts open piles up over a long kiosk session.
      oscillator.onended = () => audioCtx.close().catch(() => {});
    } catch {
      // Audio isn't essential to the flow (e.g. autoplay policies before
      // any user gesture has happened yet) -- fail silently.
    }
  }

  return { playBeep };
}
