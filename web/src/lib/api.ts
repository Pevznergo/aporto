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

export type ClipFragment = {
  id: number
  start_time: string
  end_time: string
  text: string
  visual_suggestion?: string | null
  order: number
}

export type Clip = {
  id: number
  task_id: number
  short_id: number
  title: string
  description: string
  duration_estimate?: string | null
  hook_strength?: string | null
  why_it_works?: string | null
  file_path?: string | null
  created_at: string
  fragments: ClipFragment[]
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || ''

export async function listTasks(): Promise<Task[]> {
  try {
    console.log('listTasks: API_BASE =', API_BASE)
    console.log('listTasks: Making request to', `${API_BASE}/api/tasks`)
    const res = await fetch(`${API_BASE}/api/tasks`, { cache: 'no-store', mode: 'cors' })
    console.log('listTasks: Response status =', res.status)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    console.log('listTasks: Success, returned', data.length, 'tasks')
    return data
  } catch (e) {
    console.error('listTasks: Error =', e)
    return []
  }
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
  try {
    console.log('listDownloads: API_BASE =', API_BASE)
    console.log('listDownloads: Making request to', `${API_BASE}/api/downloads`)
    const res = await fetch(`${API_BASE}/api/downloads`, { cache: 'no-store', mode: 'cors' })
    console.log('listDownloads: Response status =', res.status)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    console.log('listDownloads: Success, returned', data.length, 'downloads')
    return data
  } catch (e) {
    console.error('listDownloads: Error =', e)
    return []
  }
}

export async function deleteDownload(id: number): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE}/api/downloads/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete download')
  return res.json()
}

export async function getTaskClips(taskId: number): Promise<Clip[]> {
  try {
    const res = await fetch(`${API_BASE}/api/tasks/${taskId}/clips`, { cache: 'no-store' })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  } catch (e) {
    console.error('Failed to fetch clips:', e)
    return []
  }
}

export async function getClip(clipId: number): Promise<Clip | null> {
  try {
    const res = await fetch(`${API_BASE}/api/clips/${clipId}`, { cache: 'no-store' })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  } catch (e) {
    console.error('Failed to fetch clip:', e)
    return null
  }
}
