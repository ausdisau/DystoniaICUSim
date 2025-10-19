/**
 * Lightweight AI integration using fetch and streamed responses.
 * SAFE: Coaching only; no dosing or medical advice.
 */

export interface CoachMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface CoachingStep {
  t: number
  text: string
}

export async function* streamCoaching(messages: CoachMessage[]): AsyncGenerator<CoachingStep> {
  const apiBase = import.meta.env.VITE_OPENAI_API_BASE || 'https://api.openai.com/v1'
  const apiKey = import.meta.env.VITE_OPENAI_API_KEY
  const url = `${apiBase}/chat/completions`

  const safeSystem = 'You are an ICU simulation coach. Provide educational, non-clinical feedback. Never give real-world dosing or medical advice.'

  const payload = {
    model: 'gpt-4o-mini',
    stream: true,
    messages: [{ role: 'system', content: safeSystem }, ...messages],
    temperature: 0.2,
  }

  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
    },
    body: JSON.stringify(payload),
  })

  if (!resp.ok || !resp.body) throw new Error(`AI request failed: ${resp.status}`)

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let t = 0

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split(/\n\n/)
    buffer = parts.pop() ?? ''
    for (const p of parts) {
      const line = p.trim()
      if (!line.startsWith('data:')) continue
      const data = line.slice(5).trim()
      if (data === '[DONE]') return
      try {
        const obj = JSON.parse(data) as any
        const delta = obj.choices?.[0]?.delta?.content
        if (typeof delta === 'string' && delta.length > 0) {
          yield { t: ++t, text: delta }
        }
      } catch {
        // ignore partial JSON chunks
      }
    }
  }
}
