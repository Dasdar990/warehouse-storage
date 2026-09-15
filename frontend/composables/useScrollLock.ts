// Shared, reference-counted body-scroll lock.
//
// Dashboard-style pages mount several <BaseModal> instances at once (one
// per dialog), each watching its own `modelValue`. If every instance just
// slammed `document.body.style.overflow` on open/close independently,
// whichever one closes *last* always wins -- so if modal A opens (locks),
// then modal B opens too (locks again, harmless), then A closes first
// (unlocks) while B is still open, the page scroll comes back even though
// a modal is still on screen. Worse, in the opposite order it can also
// leave the page stuck locked after everything visibly closed. A shared
// counter makes "locked" a property of "is anything open", not of
// whichever modal last touched the DOM.
const state = {
  count: 0,
  previousOverflow: "",
};

export function useScrollLock() {
  function lock() {
    if (typeof document === "undefined") return;
    if (state.count === 0) {
      state.previousOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
    }
    state.count += 1;
  }

  function unlock() {
    if (typeof document === "undefined") return;
    if (state.count === 0) return; // already balanced, nothing to undo
    state.count -= 1;
    if (state.count === 0) {
      document.body.style.overflow = state.previousOverflow;
    }
  }

  return { lock, unlock };
}
