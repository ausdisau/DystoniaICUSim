import { PhysiologyState, SimState, InterventionEvent } from './state'

export interface UpdateOutput {
  next: PhysiologyState
  notes: string[]
}

// Pure deterministic physiology step over dt seconds
export function stepPhysiology(current: PhysiologyState, interventions: InterventionEvent[], dt: number): UpdateOutput {
  const notes: string[] = []
  const clamp = (v: number, min: number, max: number) => Math.max(min, Math.min(max, v))

  // Baseline trends representing dystonic storm stress response
  const stress = current.dystoniaSeverity / 10

  // Cooling reduces temperature slowly
  const hasCooling = interventions.some((e) => e.kind === 'cooling-blanket')
  const coolingEffect = hasCooling ? -0.03 : 0

  // Oxygen support improves SpO2 gradually
  const hasOxygen = interventions.some((e) => e.kind === 'oxygen-mask' || e.kind === 'bag-mask-ventilation')
  const oxygenEffect = hasOxygen ? 0.15 : -0.05 // decline without support

  // Environmental calm and positioning reduce dystonia severity slightly
  const calmEffect = interventions.some((e) => e.kind === 'environmental-calm' || e.kind === 'positioning')
    ? -0.05
    : 0.02

  // Hemodynamic support (fluids) slightly raises BP
  const hasFluids = interventions.some((e) => e.kind === 'fluids-bolus')
  const fluidsEffect = hasFluids ? 0.2 : 0

  // Sedation attenuates sympathetic surge and increases GCS variability
  const hasSedation = interventions.some((e) => e.kind === 'sedation')
  const sedationAttenuation = hasSedation ? 0.4 : 0

  // Temperature dynamics
  const temp = clamp(
    current.temp + (0.02 * stress + coolingEffect) * dt,
    35.5,
    42.0,
  )

  // Heart rate influenced by stress and temp; sedation attenuates
  const hrTarget = 90 + 70 * stress + (temp - 37) * 8
  const hrDelta = (hrTarget - current.heartRate) * (0.12 + (hasSedation ? -0.06 : 0)) * dt
  const heartRate = clamp(current.heartRate + hrDelta, 40, 220)

  // Respiratory rate responds to temp and oxygen need
  const rrTarget = 14 + 10 * stress + (temp - 37) * 3
  const rrDelta = (rrTarget - current.respRate) * 0.12 * dt
  const respRate = clamp(current.respRate + rrDelta, 6, 60)

  // Oxygen saturation drifts; improved by oxygen support
  const spo2 = clamp(current.spo2 + oxygenEffect * dt, 75, 100)

  // Blood pressure dynamics; fluids and sedation influence
  const mapTarget = 70 + 8 * stress - sedationAttenuation * 8 + fluidsEffect * 10
  const mapDelta = (mapTarget - current.map) * 0.15 * dt
  const map = clamp(current.map + mapDelta, 45, 120)
  const sbp = clamp(map + 20, 60, 180)
  const dbp = clamp(map - 20, 30, 120)

  // GCS dynamics: generally low with storm; slight improvement with sedation
  const gcsEye = clamp(Math.round(2.5 + (hasSedation ? 0.5 : 0)), 1, 4)
  const gcsVerbal = clamp(Math.round(2 + (hasSedation ? 1 : 0)), 1, 5)
  const gcsMotor = clamp(Math.round(4 + (hasSedation ? 0.5 : 0)), 1, 6)

  // Dystonia severity trends
  const dystoniaSeverity = clamp(current.dystoniaSeverity + calmEffect * dt - (hasSedation ? 0.08 * dt : 0), 0, 10)

  if (hasOxygen) notes.push('Oxygen support improving SpO2')
  if (hasCooling) notes.push('Active cooling reducing temperature')
  if (hasFluids) notes.push('Fluids modestly supporting MAP')
  if (hasSedation) notes.push('Sedation attenuating sympathetic surge')

  return {
    next: {
      t: current.t + dt,
      heartRate,
      respRate,
      spo2,
      sbp,
      dbp,
      map,
      temp,
      gcsEye,
      gcsVerbal,
      gcsMotor,
      dystoniaSeverity,
    },
    notes,
  }
}

export function updateSim(state: SimState, dt: number): SimState {
  const recentInterventions = state.interventions.filter((i) => i.at >= state.physiology.t - 60)
  const { next, notes } = stepPhysiology(state.physiology, recentInterventions, dt)
  return {
    ...state,
    physiology: next,
    log: notes.length > 0 ? [...state.log, ...notes.map((m) => ({ t: next.t, message: m }))] : state.log,
  }
}
