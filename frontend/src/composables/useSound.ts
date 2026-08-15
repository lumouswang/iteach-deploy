/**
 * useSound.ts — 0 依赖音效系统（Web Audio API 实时合成）
 * 
 * 不依赖任何音频文件，纯 Web Audio API 实时合成。
 * 支持：
 *   - 背景 BGM（氛围循环音）
 *   - UI 音效（点击、出卡、提问、合技、通关、错误）
 *   - 静音切换（用户偏好）
 * 
 * 调用示例：
 *   const sound = useSound()
 *   sound.playClick()
 *   sound.playCard()
 *   sound.bgm.start()
 *   sound.bgm.stop()
 */
import { ref, watch } from 'vue'

// 音效类型
export type SfxType =
  | 'click'      // 通用点击
  | 'card'       // 出卡（清脆铃铛）
  | 'question'   // 提问（弹起音）
  | 'combo'      // 合技（冲击波）
  | 'success'    // 成功（明亮上升）
  | 'fail'       // 错误（低沉下降）
  | 'layer'      // 解锁层（庄严钟声）
  | 'reveal'     // 揭晓（神秘鼓声）
  | 'firework'   // 烟花（散粒）
  | 'enter'      // 进入（欢迎）
  | 'broadcast'  // 教师广播

const STORAGE_KEY = 'tangtanju_sound_enabled'

class SoundEngine {
  private ctx: AudioContext | null = null
  private masterGain: GainNode | null = null
  private bgmGain: GainNode | null = null
  private sfxGain: GainNode | null = null
  public _enabled = ref(true)
  public _bgmPlaying = ref(false)
  private bgmNodes: { osc: OscillatorNode; gain: GainNode }[] = []
  private bgmTimer: number | null = null

  constructor() {
    // 从 localStorage 恢复偏好
    if (typeof localStorage !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEY)
      this._enabled.value = stored === null ? true : stored === 'true'
    }
  }

  get enabled() {
    return this._enabled.value
  }

  get bgmPlaying() {
    return this._bgmPlaying.value
  }

  setEnabled(v: boolean) {
    this._enabled.value = v
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, String(v))
    }
    if (!v && this.bgmGain) {
      this.bgmGain.gain.value = 0
    } else if (v && this.bgmGain && this._bgmPlaying.value) {
      this.bgmGain.gain.value = 0.15
    }
  }

  toggle() {
    this.setEnabled(!this._enabled.value)
    return this._enabled.value
  }

  // ============================================================
  // 初始化（首次播放时调用，需要用户交互）
  // ============================================================
  private ensureContext() {
    if (this.ctx) return
    try {
      // @ts-ignore - webkit fallback
      const AC = window.AudioContext || (window as any).webkitAudioContext
      if (!AC) return
      this.ctx = new AC()
      this.masterGain = this.ctx.createGain()
      this.masterGain.gain.value = 0.7
      this.masterGain.connect(this.ctx.destination)

      this.bgmGain = this.ctx.createGain()
      this.bgmGain.gain.value = 0
      this.bgmGain.connect(this.masterGain)

      this.sfxGain = this.ctx.createGain()
      this.sfxGain.gain.value = 0.6
      this.sfxGain.connect(this.masterGain)
    } catch (e) {
      console.warn('Web Audio API 不可用', e)
    }
  }

  private resume() {
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {})
    }
  }

  // ============================================================
  // 通用 ADSR 包装
  // ============================================================
  private envelope(
    gain: GainNode,
    attack: number,
    decay: number,
    sustain: number,
    release: number,
    peak = 0.3,
    duration = 0
  ) {
    if (!this.ctx) return
    const t = this.ctx.currentTime
    gain.gain.setValueAtTime(0, t)
    gain.gain.linearRampToValueAtTime(peak, t + attack)
    gain.gain.linearRampToValueAtTime(peak * sustain, t + attack + decay)
    if (duration > 0) {
      gain.gain.setValueAtTime(peak * sustain, t + duration)
    }
    gain.gain.linearRampToValueAtTime(0, t + attack + decay + release)
  }

  // ============================================================
  // SFX 音效
  // ============================================================
  playSfx(type: SfxType) {
    if (!this._enabled.value) return
    this.ensureContext()
    this.resume()
    if (!this.ctx || !this.sfxGain) return

    switch (type) {
      case 'click': return this.sfxClick()
      case 'card': return this.sfxCard()
      case 'question': return this.sfxQuestion()
      case 'combo': return this.sfxCombo()
      case 'success': return this.sfxSuccess()
      case 'fail': return this.sfxFail()
      case 'layer': return this.sfxLayer()
      case 'reveal': return this.sfxReveal()
      case 'firework': return this.sfxFirework()
      case 'enter': return this.sfxEnter()
      case 'broadcast': return this.sfxBroadcast()
    }
  }

  // ---- 各音效具体实现 ----
  private sfxClick() {
    if (!this.ctx || !this.sfxGain) return
    const osc = this.ctx.createOscillator()
    const gain = this.ctx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(800, this.ctx.currentTime)
    osc.frequency.exponentialRampToValueAtTime(1200, this.ctx.currentTime + 0.05)
    this.envelope(gain, 0.001, 0.04, 0.2, 0.05, 0.15)
    osc.connect(gain).connect(this.sfxGain)
    osc.start(); osc.stop(this.ctx.currentTime + 0.1)
  }

  private sfxCard() {
    if (!this.ctx || !this.sfxGain) return
    // 铃铛声：双正弦叠加 + 快速衰减
    const osc1 = this.ctx.createOscillator()
    const osc2 = this.ctx.createOscillator()
    const gain = this.ctx.createGain()
    osc1.type = 'sine'; osc2.type = 'triangle'
    osc1.frequency.value = 1046 // C6
    osc2.frequency.value = 2093 // C7
    this.envelope(gain, 0.005, 0.08, 0.15, 0.3, 0.2, 0.15)
    osc1.connect(gain); osc2.connect(gain); gain.connect(this.sfxGain)
    osc1.start(); osc2.start()
    osc1.stop(this.ctx.currentTime + 0.4); osc2.stop(this.ctx.currentTime + 0.4)
  }

  private sfxQuestion() {
    if (!this.ctx || !this.sfxGain) return
    // 弹起音：频率上升 + 短促
    const osc = this.ctx.createOscillator()
    const gain = this.ctx.createGain()
    osc.type = 'sine'
    const t0 = this.ctx.currentTime
    osc.frequency.setValueAtTime(400, t0)
    osc.frequency.exponentialRampToValueAtTime(900, t0 + 0.15)
    this.envelope(gain, 0.005, 0.1, 0.3, 0.15, 0.18, 0.15)
    osc.connect(gain).connect(this.sfxGain)
    osc.start(); osc.stop(t0 + 0.35)
  }

  private sfxCombo() {
    if (!this.ctx || !this.sfxGain) return
    // 合技：冲击波 - 多层叠加
    const t0 = this.ctx.currentTime
    for (let i = 0; i < 3; i++) {
      const osc = this.ctx.createOscillator()
      const gain = this.ctx.createGain()
      osc.type = i === 0 ? 'sawtooth' : 'square'
      osc.frequency.setValueAtTime(120 + i * 80, t0 + i * 0.05)
      osc.frequency.exponentialRampToValueAtTime(60, t0 + 0.5 + i * 0.05)
      this.envelope(gain, 0.01, 0.1, 0.4, 0.3, 0.25, 0.4 + i * 0.05)
      osc.connect(gain).connect(this.sfxGain)
      osc.start(t0 + i * 0.05)
      osc.stop(t0 + 0.6 + i * 0.05)
    }
  }

  private sfxSuccess() {
    if (!this.ctx || !this.sfxGain) return
    // 上升三和弦：C-E-G
    const t0 = this.ctx.currentTime
    const freqs = [523.25, 659.25, 783.99] // C5 E5 G5
    freqs.forEach((f, i) => {
      const osc = this.ctx.createOscillator()
      const gain = this.ctx.createGain()
      osc.type = 'triangle'
      osc.frequency.value = f
      this.envelope(gain, 0.005, 0.05, 0.3, 0.3, 0.18, 0.3 + i * 0.05)
      osc.connect(gain).connect(this.sfxGain)
      osc.start(t0 + i * 0.08)
      osc.stop(t0 + 0.6 + i * 0.08)
    })
  }

  private sfxFail() {
    if (!this.ctx || !this.sfxGain) return
    // 下降音
    const osc = this.ctx.createOscillator()
    const gain = this.ctx.createGain()
    osc.type = 'sawtooth'
    const t0 = this.ctx.currentTime
    osc.frequency.setValueAtTime(300, t0)
    osc.frequency.exponentialRampToValueAtTime(80, t0 + 0.4)
    this.envelope(gain, 0.01, 0.15, 0.3, 0.2, 0.2, 0.4)
    osc.connect(gain).connect(this.sfxGain)
    osc.start(); osc.stop(t0 + 0.55)
  }

  private sfxLayer() {
    if (!this.ctx || !this.sfxGain) return
    // 解锁层：庄严钟声 - 多个泛音
    const t0 = this.ctx.currentTime
    const partials = [261.63, 523.25, 784, 1046] // C4 + 泛音
    partials.forEach((f, i) => {
      const osc = this.ctx.createOscillator()
      const gain = this.ctx.createGain()
      osc.type = 'sine'
      osc.frequency.value = f
      this.envelope(gain, 0.02, 0.5, 0.4, 1.0, 0.18, 1.2)
      osc.connect(gain).connect(this.sfxGain)
      osc.start(t0 + i * 0.04)
      osc.stop(t0 + 1.5 + i * 0.04)
    })
  }

  private sfxReveal() {
    if (!this.ctx || !this.sfxGain) return
    // 揭晓：神秘鼓声 - 低频 + 滤波
    const osc = this.ctx.createOscillator()
    const gain = this.ctx.createGain()
    osc.type = 'sine'
    const t0 = this.ctx.currentTime
    osc.frequency.setValueAtTime(60, t0)
    osc.frequency.exponentialRampToValueAtTime(40, t0 + 0.8)
    this.envelope(gain, 0.02, 0.2, 0.5, 0.6, 0.4, 0.8)
    osc.connect(gain).connect(this.sfxGain)
    osc.start(); osc.stop(t0 + 1.2)
  }

  private sfxFirework() {
    if (!this.ctx || !this.sfxGain) return
    // 烟花：散粒高频 + 噪声
    const t0 = this.ctx.currentTime
    for (let i = 0; i < 5; i++) {
      const osc = this.ctx.createOscillator()
      const gain = this.ctx.createGain()
      osc.type = 'sine'
      const baseFreq = 1500 + Math.random() * 1000
      osc.frequency.setValueAtTime(baseFreq, t0 + i * 0.03)
      osc.frequency.exponentialRampToValueAtTime(baseFreq * 0.5, t0 + 0.2 + i * 0.03)
      this.envelope(gain, 0.001, 0.05, 0.1, 0.15, 0.1, 0.2)
      osc.connect(gain).connect(this.sfxGain)
      osc.start(t0 + i * 0.03)
      osc.stop(t0 + 0.4 + i * 0.03)
    }
  }

  private sfxEnter() {
    if (!this.ctx || !this.sfxGain) return
    // 进入欢迎音：上升扫频
    const osc = this.ctx.createOscillator()
    const gain = this.ctx.createGain()
    osc.type = 'triangle'
    const t0 = this.ctx.currentTime
    osc.frequency.setValueAtTime(220, t0)
    osc.frequency.exponentialRampToValueAtTime(880, t0 + 0.6)
    this.envelope(gain, 0.05, 0.2, 0.3, 0.4, 0.2, 0.6)
    osc.connect(gain).connect(this.sfxGain)
    osc.start(); osc.stop(t0 + 1)
  }

  private sfxBroadcast() {
    if (!this.ctx || !this.sfxGain) return
    // 教师广播：通知音
    const t0 = this.ctx.currentTime
    const freqs = [880, 1108] // A5 + C#6
    freqs.forEach((f, i) => {
      const osc = this.ctx.createOscillator()
      const gain = this.ctx.createGain()
      osc.type = 'sine'
      osc.frequency.value = f
      this.envelope(gain, 0.005, 0.1, 0.2, 0.2, 0.2, 0.2)
      osc.connect(gain).connect(this.sfxGain)
      osc.start(t0 + i * 0.12)
      osc.stop(t0 + 0.4 + i * 0.12)
    })
  }

  // ============================================================
  // BGM（氛围循环）
  // ============================================================
  bgm = {
    start: () => this.startBgm(),
    stop: () => this.stopBgm(),
    toggle: () => {
      if (this._bgmPlaying.value) this.stopBgm()
      else this.startBgm()
    },
  }

  private startBgm() {
    if (!this._enabled.value) return
    this.ensureContext()
    this.resume()
    if (!this.ctx || !this.bgmGain || this._bgmPlaying.value) return

    this._bgmPlaying.value = true
    this.bgmGain.gain.linearRampToValueAtTime(0.15, this.ctx.currentTime + 1)

    // 合成一段氛围 BGM：缓慢变化的 pad
    this.scheduleBgmLoop()
  }

  private stopBgm() {
    if (!this.ctx || !this.bgmGain) return
    this._bgmPlaying.value = false
    this.bgmGain.gain.linearRampToValueAtTime(0, this.ctx.currentTime + 0.5)
    if (this.bgmTimer) {
      clearTimeout(this.bgmTimer)
      this.bgmTimer = null
    }
    // 停止所有正在播放的 BGM 节点
    this.bgmNodes.forEach(({ osc }) => {
      try { osc.stop() } catch {}
    })
    this.bgmNodes = []
  }

  private scheduleBgmLoop() {
    if (!this._bgmPlaying.value || !this.ctx || !this.bgmGain) return

    // 简化版 BGM：低频 pad + 偶尔高音点缀
    const t0 = this.ctx.currentTime
    const scale = [130.81, 146.83, 164.81, 196.00, 220.00, 261.63] // C3 D3 E3 G3 A3 C4 (五声)
    const dur = 8 // 8 秒一循环

    // 主旋律 pad
    scale.forEach((freq, i) => {
      const osc = this.ctx!.createOscillator()
      const gain = this.ctx!.createGain()
      osc.type = 'sine'
      osc.frequency.value = freq
      const startTime = t0 + (i % 3) * 2
      gain.gain.setValueAtTime(0, startTime)
      gain.gain.linearRampToValueAtTime(0.08, startTime + 0.5)
      gain.gain.linearRampToValueAtTime(0, startTime + 5)
      osc.connect(gain).connect(this.bgmGain!)
      osc.start(startTime)
      osc.stop(startTime + 6)
      this.bgmNodes.push({ osc, gain })
    })

    // 排程下一次循环
    this.bgmTimer = window.setTimeout(() => {
      // 清理已结束的节点
      this.bgmNodes = this.bgmNodes.filter(n => {
        try {
          return n.osc.context.state === 'running'
        } catch {
          return false
        }
      })
      this.scheduleBgmLoop()
    }, dur * 1000)
  }

  // ============================================================
  // 测试音效（用户首次点击解锁 AudioContext）
  // ============================================================
  test() {
    this.playSfx('enter')
  }
}

let _instance: SoundEngine | null = null

export function useSound() {
  if (!_instance) {
    _instance = new SoundEngine()
  }
  return {
    play: (type: SfxType) => _instance!.playSfx(type),
    enabled: _instance._enabled,
    bgmPlaying: _instance._bgmPlaying,
    bgm: _instance.bgm,
    toggle: () => _instance!.toggle(),
    setEnabled: (v: boolean) => _instance!.setEnabled(v),
    test: () => _instance!.test(),
  }
}
