/**
 * Client-side bridge to the local NFC badge reader.
 *
 * The MIKROE-2540 (PN7150) dongle is driven by NXP's precompiled binary,
 * which is not a keyboard-wedge device -- it just prints to its own
 * stdout. `nfc-bridge/bridge.py` runs that binary on the same machine as
 * the browser (the kiosk the dongle is plugged into) and re-broadcasts
 * each tap as a small JSON message over a local WebSocket. This composable
 * is the browser side of that bridge: it connects, listens for taps, and
 * hands the badge UID to the caller -- login.vue then calls the exact same
 * `badgeLogin()` used for a keyboard-wedge scan.
 *
 * The bridge is optional: if it isn't running (e.g. on a device with no
 * NFC reader attached), the socket simply fails to connect and we retry
 * quietly in the background rather than surfacing an error.
 */
export interface UseNfcBridgeOptions {
  onBadgeTap?: (uid: string) => void;
  onBadgeRemoved?: () => void;
}

type BridgeMessage =
  | { type: "badge_tap"; uid: string }
  | { type: "badge_removed" }
  | { type: "reader_status"; status: string };

const RECONNECT_DELAY_MS = 3000;

export function useNfcBridge(options: UseNfcBridgeOptions = {}) {
  const config = useRuntimeConfig();
  const bridgeUrl =
    (config.public.nfcBridgeUrl as string) || "ws://localhost:8765";

  // Shared across components so only one indicator is needed even if
  // multiple pages mount this composable.
  const connected = useState<boolean>("nfc-bridge-connected", () => false);

  let socket: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let stopped = false;

  function connect() {
    if (!import.meta.client || stopped || socket) return;

    try {
      socket = new WebSocket(bridgeUrl);
    } catch {
      socket = null;
      scheduleReconnect();
      return;
    }

    socket.onopen = () => {
      connected.value = true;
    };

    socket.onmessage = (event: MessageEvent) => {
      let msg: BridgeMessage;
      try {
        msg = JSON.parse(event.data);
      } catch {
        return;
      }
      if (msg.type === "badge_tap" && typeof msg.uid === "string" && msg.uid) {
        options.onBadgeTap?.(msg.uid);
      } else if (msg.type === "badge_removed") {
        options.onBadgeRemoved?.();
      }
    };

    socket.onclose = () => {
      connected.value = false;
      socket = null;
      scheduleReconnect();
    };

    // The close event fires right after error, so just let onclose drive
    // the reconnect -- no need to duplicate that logic here.
    socket.onerror = () => {
      socket?.close();
    };
  }

  function scheduleReconnect() {
    if (stopped || reconnectTimer) return;
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, RECONNECT_DELAY_MS);
  }

  function stop() {
    stopped = true;
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    socket?.close();
    socket = null;
    connected.value = false;
  }

  if (import.meta.client) {
    connect();
  }

  return { connected, stop };
}
