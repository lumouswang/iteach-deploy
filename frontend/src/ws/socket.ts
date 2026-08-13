/**
 * WebSocket 客户端封装 + P2 #17 自动重连（指数回退）
 * 用法:
 *   const ws = useRoomWS(roomId)
 *   ws.connect()
 *   ws.on('state_update', applyState)
 *   ws.on('combo', (msg) => ...)
 *   ws.send('ask', { qid })
 */
import { ref, onUnmounted } from 'vue'

export interface WSMessage {
  ok?: boolean
  action?: string
  state?: any
  error?: string
  [k: string]: any
}

export function useRoomWS(roomId: string | (() => string)) {
  const connected = ref(false)
  const lastMessage = ref<WSMessage | null>(null)
  const retryDelay = ref(0)
  let ws: WebSocket | null = null
  let retry = 0
  let manualClose = false
  const listeners = new Set<(msg: WSMessage) => void>()

  const rid = (): string => (typeof roomId === 'function' ? roomId() : roomId)

  function computeUrl(): string {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${location.host}/ws/${rid()}`
  }

  function connect() {
    if (!rid()) return
    manualClose = false
    try {
      ws = new WebSocket(computeUrl())
    } catch (e) {
      scheduleReconnect()
      return
    }
    ws.onopen = () => {
      connected.value = true
      retry = 0
      retryDelay.value = 0
    }
    ws.onmessage = (e) => {
      try {
        const msg: WSMessage = JSON.parse(e.data)
        lastMessage.value = msg
        listeners.forEach(fn => {
          try { fn(msg) } catch { /* */ }
        })
      } catch (e) {
        console.warn('[ws] parse failed', e)
      }
    }
    ws.onclose = () => {
      connected.value = false
      if (!manualClose) scheduleReconnect()
    }
    ws.onerror = () => {
      // onclose 紧接着会触发
    }
  }

  function scheduleReconnect() {
    retry++
    const delay = Math.min(1000 * Math.pow(2, retry), 15000)
    retryDelay.value = delay
    setTimeout(connect, delay)
  }

  function send(action: string, payload: Record<string, any> = {}) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action, ...payload }))
      return true
    }
    return false
  }

  function on(fn: (msg: WSMessage) => void) {
    listeners.add(fn)
    return () => listeners.delete(fn)
  }

  function close() {
    manualClose = true
    try { ws?.close() } catch { /* */ }
    ws = null
  }

  onUnmounted(close)

  return { connect, send, close, on, connected, lastMessage, retryDelay }
}
