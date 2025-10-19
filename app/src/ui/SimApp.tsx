import { useEffect, useMemo, useRef, useState } from 'react'
import { create } from 'zustand'
import { createInitialSimState, updateSim, defaultScenario, InterventionEvent, ScenarioConfig } from '../sim/state'
import { SimState } from '../sim/state'
import { ThreeScene } from './ThreeScene'
import { loadScenarioFromYaml } from '../data'

interface StoreState {
  sim: SimState
  toggleRun: () => void
  addIntervention: (e: InterventionEvent) => void
  tick: (dt: number) => void
  setSpeed: (s: number) => void
}

export const useSimStore = create<StoreState>((set, get) => ({
  sim: createInitialSimState(defaultScenario),
  toggleRun: () => set((s) => ({ sim: { ...s.sim, isRunning: !s.sim.isRunning } })),
  addIntervention: (e) => set((s) => ({ sim: { ...s.sim, interventions: [...s.sim.interventions, e] } })),
  tick: (dt) => set((s) => ({ sim: updateSim(s.sim, dt) })),
  setSpeed: (speed) => set((s) => ({ sim: { ...s.sim, speed } })),
}))

export function SimApp() {
  const { sim, toggleRun, addIntervention, tick, setSpeed } = useSimStore()
  const last = useRef<number | null>(null)

  useEffect(() => {
    const onFrame = (t: number) => {
      if (last.current == null) last.current = t
      const dtSec = (t - last.current) / 1000
      last.current = t
      if (sim.isRunning) {
        tick(dtSec * sim.speed)
      }
      requestAnimationFrame(onFrame)
    }
    const id = requestAnimationFrame(onFrame)
    return () => cancelAnimationFrame(id)
  }, [sim.isRunning, sim.speed, tick])

  const gcs = useMemo(() => sim.physiology.gcsEye + sim.physiology.gcsVerbal + sim.physiology.gcsMotor, [sim.physiology])

  const handleIntervention = (kind: InterventionEvent['kind']) => () => {
    addIntervention({ at: sim.physiology.t, kind })
  }

  const handleLoadYaml = async () => {
    const url = '/src/data/example-scenario.yaml'
    try {
      const cfg: ScenarioConfig = await loadScenarioFromYaml(url)
      useSimStore.setState({ sim: { ...createInitialSimState(cfg), isRunning: sim.isRunning, speed: sim.speed } })
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div role="main" aria-label="ICU Dystonic Storm Simulator" className="container" style={{ padding: 16 }}>
      <header aria-label="Header" style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <h1 style={{ margin: 0, fontSize: 22 }}>ICU Dystonic Storm Simulator</h1>
        <div role="group" aria-label="Run controls" style={{ display: 'flex', gap: 8 }}>
          <button onClick={toggleRun} aria-pressed={sim.isRunning} accessKey="r">
            {sim.isRunning ? 'Pause (Alt+R)' : 'Run (Alt+R)'}
          </button>
          <button onClick={handleLoadYaml}>Load Example YAML</button>
          <label>
            Speed
            <input
              type="range"
              min={0.25}
              max={4}
              step={0.25}
              value={sim.speed}
              onChange={(e) => setSpeed(parseFloat(e.currentTarget.value))}
              aria-valuemin={0.25}
              aria-valuemax={4}
              aria-valuenow={sim.speed}
            />
          </label>
        </div>
      </header>
      <ThreeScene />

      <section aria-label="Vitals" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        <Vital label="HR" value={sim.physiology.heartRate.toFixed(0)} unit="bpm" />
        <Vital label="RR" value={sim.physiology.respRate.toFixed(0)} unit="/min" />
        <Vital label="SpO2" value={sim.physiology.spo2.toFixed(0)} unit="%" />
        <Vital label="Temp" value={sim.physiology.temp.toFixed(1)} unit="°C" />
        <Vital label="SBP" value={sim.physiology.sbp.toFixed(0)} unit="mmHg" />
        <Vital label="DBP" value={sim.physiology.dbp.toFixed(0)} unit="mmHg" />
        <Vital label="MAP" value={sim.physiology.map.toFixed(0)} unit="mmHg" />
        <Vital label="GCS" value={gcs.toFixed(0)} unit="/15" />
      </section>

      <section aria-label="Interventions" style={{ marginTop: 16 }}>
        <div role="group" aria-label="Support" style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {(
            [
              'oxygen-mask',
              'bag-mask-ventilation',
              'cooling-blanket',
              'fluids-bolus',
              'environmental-calm',
              'positioning',
              'sedation',
              'antipyretic',
              'analgesia',
              'escalate-call',
            ] as InterventionEvent['kind'][]
          ).map((k) => (
            <button key={k} onClick={handleIntervention(k)}>{k}</button>
          ))}
        </div>
      </section>

      <section aria-label="Log" style={{ marginTop: 16 }}>
        <ul aria-live="polite">
          {sim.log.slice(-8).map((l, i) => (
            <li key={i}>
              t={l.t.toFixed(1)}s — {l.message}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

function Vital({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <div role="region" aria-label={`${label} ${value} ${unit}`} style={{ padding: 8, border: '1px solid #ccc', borderRadius: 8 }}>
      <div style={{ fontSize: 12, color: '#555' }}>{label}</div>
      <div style={{ fontWeight: 700, fontSize: 22 }}>
        {value} <span style={{ fontSize: 12 }}>{unit}</span>
      </div>
    </div>
  )
}
