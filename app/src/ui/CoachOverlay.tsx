import { useEffect, useRef, useState } from 'react'
import { streamCoaching } from '../lib/ai'
import { useSimStore } from './SimApp'

export function CoachOverlay() {
  const sim = useSimStore((s) => s.sim)
  const [text, setText] = useState('')
  const [open, setOpen] = useState(false)
  const controllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    if (!open) return
    controllerRef.current?.abort()
    controllerRef.current = new AbortController()
    const run = async () => {
      const msgs = [
        {
          role: 'user' as const,
          content: `Provide training-safe commentary on simulated state. vitals: HR ${sim.physiology.heartRate.toFixed(0)}, RR ${sim.physiology.respRate.toFixed(0)}, SpO2 ${sim.physiology.spo2.toFixed(0)}, MAP ${sim.physiology.map.toFixed(0)}, Temp ${sim.physiology.temp.toFixed(1)}, dystonia ${sim.physiology.dystoniaSeverity.toFixed(1)}. Avoid medical advice.`,
        },
      ]
      try {
        setText('')
        for await (const chunk of streamCoaching(msgs)) {
          setText((t) => t + chunk.text)
        }
      } catch (e) {
        setText('AI unavailable or not configured.')
      }
    }
    void run()
    return () => controllerRef.current?.abort()
  }, [open, sim.physiology])

  return (
    <aside role="complementary" aria-label="AI Coaching" style={{ position: 'fixed', right: 12, bottom: 12, width: 320 }}>
      <button onClick={() => setOpen((o) => !o)} aria-pressed={open} accessKey="c">
        {open ? 'Hide Coaching (Alt+C)' : 'Show Coaching (Alt+C)'}
      </button>
      {open && (
        <div style={{ marginTop: 8, padding: 8, border: '1px solid #ccc', borderRadius: 8, background: '#fff' }}>
          <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{text || 'Connecting...'}</p>
        </div>
      )}
    </aside>
  )
}
