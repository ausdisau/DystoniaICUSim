import { parse } from 'yaml'
import type { ScenarioConfig } from '../sim/state'

export async function loadScenarioFromYaml(url: string): Promise<ScenarioConfig> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Failed to load scenario YAML: ${res.status}`)
  const text = await res.text()
  const data = parse(text) as unknown
  // Basic structural check
  if (typeof data !== 'object' || data == null) throw new Error('Invalid YAML structure')
  const cfg = data as ScenarioConfig
  return cfg
}
