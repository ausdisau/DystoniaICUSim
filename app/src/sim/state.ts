export type VitalKey =
  | 'heartRate'
  | 'respRate'
  | 'spo2'
  | 'sbp'
  | 'dbp'
  | 'map'
  | 'temp'
  | 'gcsEye'
  | 'gcsVerbal'
  | 'gcsMotor'
  | 'dystoniaSeverity'

export interface PatientDemographics {
  ageYears: number
  sex: 'female' | 'male' | 'intersex' | 'other'
  weightKg: number
  heightCm: number
}

export interface PhysiologyState {
  t: number // seconds
  // hemodynamics
  heartRate: number // bpm
  respRate: number // breaths/min
  spo2: number // %
  sbp: number // mmHg systolic
  dbp: number // mmHg diastolic
  map: number // mean arterial pressure
  temp: number // Celsius
  // neuro
  gcsEye: number
  gcsVerbal: number
  gcsMotor: number
  dystoniaSeverity: number // 0-10
}

export interface InterventionEvent {
  at: number
  kind:
    | 'oxygen-mask'
    | 'bag-mask-ventilation'
    | 'cooling-blanket'
    | 'fluids-bolus'
    | 'analgesia'
    | 'sedation'
    | 'antipyretic'
    | 'environmental-calm'
    | 'positioning'
    | 'escalate-call'
  note?: string
}

export interface ScenarioConfig {
  id: string
  title: string
  description: string
  demographics: PatientDemographics
  initial: PhysiologyState
  scriptedEvents?: InterventionEvent[]
}

export interface SimState {
  scenario: ScenarioConfig
  physiology: PhysiologyState
  log: Array<{ t: number; message: string }>
  interventions: InterventionEvent[]
  isRunning: boolean
  speed: number // multiplier
}

export const defaultScenario: ScenarioConfig = {
  id: 'dystonic-storm-v1',
  title: 'Dystonic Storm - ICU Arrival',
  description:
    '18-year-old female with primary dystonia in dystonic storm. Deterministic model for training only. No dosing.',
  demographics: {
    ageYears: 18,
    sex: 'female',
    weightKg: 60,
    heightCm: 165,
  },
  initial: {
    t: 0,
    heartRate: 145,
    respRate: 28,
    spo2: 91,
    sbp: 95,
    dbp: 55,
    map: 68,
    temp: 39.6,
    gcsEye: 3,
    gcsVerbal: 2,
    gcsMotor: 4,
    dystoniaSeverity: 8.5,
  },
}

export function createInitialSimState(scenario: ScenarioConfig = defaultScenario): SimState {
  return {
    scenario,
    physiology: { ...scenario.initial },
    log: [
      {
        t: 0,
        message:
          'Simulation started. Training-only. Do not use for clinical care.',
      },
    ],
    interventions: [],
    isRunning: false,
    speed: 1,
  }
}
