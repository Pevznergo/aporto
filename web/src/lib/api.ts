export type Task = {
  id: number
  url: string
  mode: 'simple' | 'auto'
  status: string
  stage?: string | null
  progress?: number | null
  video_id?: string | null
  original_filename?: string | null
  downloaded_path?: string | null
  processed_path?: string | null
  clips_dir?: string | null
  transcript_path?: string | null
  clips_json_path?: string | null
  error?: string | null
  start_time?: number | null
  end_time?: number | null
}

export type DownloadedItem = {
  id: number
  url: string
  title: string
  created_at: string
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'

export async function listTasks(): Promise<Task[]> {
  const res = await fetch(`${API_BASE}/api/tasks`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch tasks')
  return res.json()
}

export async function createTask(payload: { url: string; mode?: 'simple' | 'auto'; start?: string | number | null; end?: string | number | null }): Promise<Task> {
  const res = await fetch(`${API_BASE}/api/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error('Failed to create task')
  return res.json()
}

export async function deleteTask(id: number): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE}/api/tasks/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete task')
  return res.json()
}

export async function clearTasks(): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE}/api/tasks`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to clear tasks')
  return res.json()
}

export async function retryTask(id: number): Promise<Task> {
  const res = await fetch(`${API_BASE}/api/tasks/${id}/retry`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to retry task')
  return res.json()
}

export async function listDownloads(): Promise<DownloadedItem[]> {
  const res = await fetch(`${API_BASE}/api/downloads`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch downloads')
  return res.json()
}

export async function deleteDownload(id: number): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE}/api/downloads/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete download')
  return res.json()
}
