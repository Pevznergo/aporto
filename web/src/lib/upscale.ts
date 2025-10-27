import { useEffect, useState } from 'react'

export type UpscaleTask = {
  id: number
  file_path: string
  status: string
  stage?: string | null
  progress?: number | null
  result_path?: string | null
  error?: string | null
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'

export async function listUpscaleTasks(): Promise<UpscaleTask[]> {
  try {
    console.log('listUpscaleTasks: API_BASE =', API_BASE)
    console.log('listUpscaleTasks: Making request to', `${API_BASE}/api/upscale/tasks`)
    const res = await fetch(`${API_BASE}/api/upscale/tasks`, { cache: 'no-store', mode: 'cors' })
    console.log('listUpscaleTasks: Response status =', res.status)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    console.log('listUpscaleTasks: Success, returned', data.length, 'upscale tasks')
    return data
  } catch (e) {
    console.error('listUpscaleTasks: Error =', e)
    // Swallow network errors so UI remains usable
    return []
  }
}

export async function triggerUpscaleScan(): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/api/upscale/scan`, { method: 'POST', mode: 'cors', headers: { 'Content-Type': 'application/json' } })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
  } catch (e) {
    // no-op; caller can refresh later
  }
}

export async function retryUpscale(id: number): Promise<UpscaleTask> {
  const res = await fetch(`${API_BASE}/api/upscale/tasks/${id}/retry`, { method: 'POST', mode: 'cors', headers: { 'Content-Type': 'application/json' } })
  if (!res.ok) throw new Error('Failed to retry upscale task')
  return res.json()
}

export async function getUpscaleSettings(): Promise<{ UPSCALE_IMAGE: string; UPSCALE_CONCURRENCY: number; VAST_INSTANCE_ID?: string }> {
  const res = await fetch(`${API_BASE}/api/upscale/settings`)
  if (!res.ok) throw new Error('Failed to get settings')
  return res.json()
}

export async function saveUpscaleSettings(payload: { UPSCALE_IMAGE: string; UPSCALE_CONCURRENCY: number; VAST_INSTANCE_ID?: string }) {
  const res = await fetch(`${API_BASE}/api/upscale/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error('Failed to save settings')
  return res.json()
}

export async function ensureUpscaleInstance(): Promise<{ id?: string; state?: string }> {
  const res = await fetch(`${API_BASE}/api/upscale/ensure`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to ensure instance')
  return res.json()
}

export async function deleteUpscale(id: number): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE}/api/upscale/tasks/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete upscale task')
  return res.json()
}

export async function clearUpscale(): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE}/api/upscale/tasks`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to clear upscale tasks')
  return res.json()
}

export async function clearGpuQueue(): Promise<{ ok: boolean; cleared?: any }> {
  try {
    // Get GPU URL from settings
    const settings = await getUpscaleSettings()
    const gpuUrl = (settings as any).VAST_UPSCALE_URL
    
    if (!gpuUrl) {
      throw new Error('VAST_UPSCALE_URL not configured')
    }
    
    const baseUrl = gpuUrl.replace(/\/$/, '')
    const res = await fetch(`${baseUrl}/clear_queue`, { 
      method: 'POST',
      mode: 'cors',
      headers: { 'Content-Type': 'application/json' }
    })
    
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  } catch (e) {
    console.error('clearGpuQueue: Error =', e)
    throw e
  }
}

export async function getGpuQueueStatus(): Promise<{ total_jobs: number; status_counts: any }> {
  try {
    const settings = await getUpscaleSettings()
    const gpuUrl = (settings as any).VAST_UPSCALE_URL
    
    if (!gpuUrl) {
      return { total_jobs: 0, status_counts: {} }
    }
    
    const baseUrl = gpuUrl.replace(/\/$/, '')
    const res = await fetch(`${baseUrl}/queue_status`, { 
      method: 'GET',
      mode: 'cors'
    })
    
    if (!res.ok) return { total_jobs: 0, status_counts: {} }
    return res.json()
  } catch (e) {
    console.error('getGpuQueueStatus: Error =', e)
    return { total_jobs: 0, status_counts: {} }
  }
}

export function useUpscaleTasks() {
  const [tasks, setTasks] = useState<UpscaleTask[]>([])
  const [loading, setLoading] = useState(false)

  async function refresh() {
    const data = await listUpscaleTasks()
    setTasks(data)
  }

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 4000)
    return () => clearInterval(id)
  }, [])

  return { tasks, loading, refresh }
}
