/**
 * useFireworks.ts — 撒花动画（0 依赖，纯 CSS + 少量 JS）
 * 调用: const fw = useFireworks(); fw.burst(80)  // 撒 80 颗
 *
 * P2 #18 修复：单 raf 链 + 引用保存，避免 burst 多次启动并行的 raf。
 */
import { ref } from 'vue'

interface Particle {
  id: number
  x: number
  y: number
  vx: number
  vy: number
  color: string
  size: number
  life: number
  rotation: number
  rotationSpeed: number
  shape: 'square' | 'circle' | 'star'
}

const PALETTE = [
  '#ff5722', '#ff9800', '#ffc107', '#ffeb3b',
  '#8bc34a', '#4caf50', '#03a9f4', '#9c27b0',
  '#e91e63', '#00bcd4',
]

const SHAPES: Particle['shape'][] = ['square', 'circle', 'star']

let pid = 0

export function useFireworks() {
  const containerRef = ref<HTMLElement | null>(null)
  const particles = ref<Particle[]>([])
  let rafId: number | null = null

  /** 在指定位置（默认屏幕中心）撒 N 颗烟花 */
  function burst(count = 60, options?: { x?: number; y?: number; spread?: number }) {
    const x = options?.x ?? window.innerWidth / 2
    const y = options?.y ?? window.innerHeight / 3
    const spread = options?.spread ?? 400

    const newParticles: Particle[] = []
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 * i) / count + Math.random() * 0.3
      const speed = 200 + Math.random() * spread
      newParticles.push({
        id: ++pid,
        x, y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 80, // 向上偏置
        color: PALETTE[Math.floor(Math.random() * PALETTE.length)],
        size: 6 + Math.random() * 8,
        life: 1,
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * 720,
        shape: SHAPES[Math.floor(Math.random() * SHAPES.length)],
      })
    }
    particles.value = [...particles.value, ...newParticles]
    if (rafId == null) animate()
  }

  /** 全屏金色礼炮（揭晓汤底用） */
  function celebrate() {
    // 中心爆炸 + 两侧副爆炸
    burst(80)
    setTimeout(() => burst(50, { x: window.innerWidth * 0.2, y: window.innerHeight / 2 }), 200)
    setTimeout(() => burst(50, { x: window.innerWidth * 0.8, y: window.innerHeight / 2 }), 400)
  }

  function animate() {
    if (particles.value.length === 0) {
      rafId = null
      return
    }
    const dt = 1 / 60
    const gravity = 600
    const next: Particle[] = []
    for (const p of particles.value) {
      const np: Particle = {
        ...p,
        x: p.x + p.vx * dt,
        y: p.y + p.vy * dt,
        vy: p.vy + gravity * dt,
        life: p.life - dt * 0.8,
        rotation: p.rotation + p.rotationSpeed * dt,
      }
      if (np.life > 0 && np.y < window.innerHeight + 50) next.push(np)
    }
    particles.value = next
    if (next.length > 0) {
      rafId = requestAnimationFrame(animate)
    } else {
      rafId = null
    }
  }

  /** SVG 模板（用 mask 而非 emoji，保证可缩放） */
  function shapePath(shape: Particle['shape']): string {
    if (shape === 'square') return 'M10 0 L20 10 L10 20 L0 10 Z'  // 菱形
    if (shape === 'circle') return 'M10 1 A9 9 0 1 1 9.99 1 Z'
    return 'M10 0 L12 8 L20 10 L12 12 L10 20 L8 12 L0 10 L8 8 Z'  // 星形
  }

  return { particles, containerRef, burst, celebrate, shapePath }
}
