"use client"

import { useEffect, useState } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'

function colorForState(state: string) {
  switch (state) {
    case 'running':
      return '#16a34a'
    case 'stopped':
      return '#6b7280'
    case 'unknown':
    default:
      return '#f59e0b'
  }
}

export default function VastStatus() {
  const [state, setState] = useState('unknown')

  async function refresh() {
    try {
      const res = await fetch(`${API_BASE}/api/upscale/status`, { cache: 'no-store' })
      const data = await res.json()
      setState(data.state || 'unknown')
    } catch {
      setState('unknown')
    }
  }

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 8000)
    return () => clearInterval(id)
  }, [])

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, padding: '4px 8px', borderRadius: 999, background: '#0f1624', border: '1px solid #223046' }}>
      <span style={{ width: 8, height: 8, borderRadius: 999, background: colorForState(state) }} />
      <span>Vast: {state}</span>
    </div>
  )
}
